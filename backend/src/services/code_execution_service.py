import html
import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from ..models.submission import CodeSubmission
from ..repositories.submission_repository import SubmissionRepository
from ..schemas.code_execution import CodeExecutionResponse
from ..services.sandbox.docker_sandbox import DockerSandbox
from ..services.sandbox.error_parser import ErrorParser

# Set up logging
logger = logging.getLogger(__name__)


class ExecutionMetrics:
    """Track execution metrics for monitoring and analytics."""

    def __init__(self):
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.timeout_executions = 0
        self.blocked_executions = 0
        self.total_execution_time_ms = 0
        self.execution_times: List[int] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_reset = datetime.utcnow()

    def record_execution(
        self, status: str, execution_time_ms: int, error_type: Optional[str] = None
    ):
        """Record an execution for metrics tracking."""
        self.total_executions += 1
        self.total_execution_time_ms += execution_time_ms
        self.execution_times.append(execution_time_ms)

        # Keep only last 1000 execution times to prevent memory growth
        if len(self.execution_times) > 1000:
            self.execution_times = self.execution_times[-1000:]

        if status == "success":
            self.successful_executions += 1
        elif status == "error":
            self.failed_executions += 1
            if error_type:
                self.error_counts[error_type] += 1
        elif status == "timeout":
            self.timeout_executions += 1
        elif status == "blocked":
            self.blocked_executions += 1

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    def get_average_execution_time(self) -> float:
        """Calculate average execution time in milliseconds."""
        if self.total_executions == 0:
            return 0.0
        return self.total_execution_time_ms / self.total_executions

    def get_p95_execution_time(self) -> int:
        """Calculate 95th percentile execution time."""
        if not self.execution_times:
            return 0
        sorted_times = sorted(self.execution_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]

    def get_metrics_summary(self) -> Dict:
        """Get a summary of all metrics."""
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "timeout_executions": self.timeout_executions,
            "blocked_executions": self.blocked_executions,
            "success_rate_percent": round(self.get_success_rate(), 2),
            "average_execution_time_ms": round(self.get_average_execution_time(), 2),
            "p95_execution_time_ms": self.get_p95_execution_time(),
            "error_counts": dict(self.error_counts),
            "last_reset": self.last_reset.isoformat(),
        }

    def reset(self):
        """Reset all metrics."""
        self.__init__()


# Global metrics instance
_metrics = ExecutionMetrics()


def sanitize_output(output: str) -> str:
    """Sanitize output to prevent XSS attacks."""
    if not output:
        return output
    # Escape HTML characters to prevent XSS
    return html.escape(output)


class CodeExecutionService:
    """Service class to handle code execution business logic."""

    def __init__(self, submission_repo: SubmissionRepository):
        if os.getenv("VERCEL") == "1":
            from ..services.sandbox.vercel_sandbox import VercelSandbox
            self.sandbox = VercelSandbox()
        else:
            self.sandbox = DockerSandbox()
        self.error_parser = ErrorParser()
        self.submission_repo = submission_repo
        self.metrics = _metrics

    def get_metrics(self) -> Dict:
        """Get current execution metrics."""
        return self.metrics.get_metrics_summary()

    def reset_metrics(self):
        """Reset execution metrics."""
        self.metrics.reset()
        logger.info("Execution metrics reset")

    async def execute_code(
        self,
        code: str,
        user_id: str,
        module_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        exercise_id: Optional[
            int
        ] = None,  # Changed back to int for compatibility with existing model
    ) -> CodeExecutionResponse:
        """Execute code and return structured response.

        Args:
            code: Python code to execute
            user_id: ID of the user executing the code
            module_id: Optional module ID this code relates to
            lesson_id: Optional lesson ID this code relates to
            exercise_id: Optional exercise ID this code is for (as integer for compatibility)

        Returns:
            CodeExecutionResponse with execution results
        """
        start_time = time.time()
        logger.info(
            f"Code execution request from user_id={user_id}, code_length={len(code)}, exercise_id={exercise_id}"
        )

        # Validate code length limit (10,000 characters max)
        if len(code) > 10000:
            logger.warning(
                f"Code length validation failed: {len(code)} characters (max 10,000)"
            )
            response = CodeExecutionResponse(
                id=str(uuid.uuid4()),
                status="error",
                execution_time_ms=0,
                output=None,
                error_message="Code exceeds maximum length of 10,000 characters",
                error_type="ValidationError",
                memory_used_bytes=None,
                code_submission_id=None,
            )
            # Record metrics
            self.metrics.record_execution("error", 0, "ValidationError")
            return response

        # Execute the code in the sandbox
        execution_result = await self.sandbox.execute_code(
            code=code,
            timeout_seconds=5,  # Fixed timeout as per requirements
            memory_limit="50MB",  # Fixed memory limit as per requirements
        )

        # Parse error message if there was an error
        error_message = None
        if execution_result.error_message:
            if execution_result.error_type == "SecurityViolation":
                # For security violations, use the original message as it's already clear
                error_message = execution_result.error_message
            else:
                # For other errors, enhance the message for student-friendliness
                error_message = self.error_parser.enhance_error_message(
                    error_message=execution_result.error_message,
                    error_type=execution_result.error_type or "Unknown",
                    line_number=self.error_parser.extract_line_number(
                        execution_result.error_message
                    ),
                )

        # Sanitize output and error messages to prevent XSS
        sanitized_output = (
            sanitize_output(execution_result.output)
            if execution_result.output
            else None
        )
        sanitized_error_message = (
            sanitize_output(error_message) if error_message else None
        )

        # Create the response
        response = CodeExecutionResponse(
            id=str(uuid.uuid4()),
            status=execution_result.status,
            execution_time_ms=execution_result.execution_time_ms,
            output=sanitized_output if execution_result.success else None,
            error_message=(
                sanitized_error_message if not execution_result.success else None
            ),
            error_type=execution_result.error_type,
            memory_used_bytes=execution_result.memory_used_bytes,
            code_submission_id=None,  # Will be set after storing if successful
        )

        # Record metrics
        self.metrics.record_execution(
            status=response.status,
            execution_time_ms=response.execution_time_ms,
            error_type=response.error_type,
        )

        # Store successful executions in the database
        if execution_result.success and exercise_id is not None:
            logger.info(
                f"Storing successful execution for user_id={user_id}, exercise_id={exercise_id}"
            )
            # Prepare result data for storage
            result_data = {
                "success": True,
                "output": execution_result.output,
                "execution_time_ms": execution_result.execution_time_ms,
                "memory_used_bytes": execution_result.memory_used_bytes,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Create a submission record
            submission = await self.submission_repo.create_submission(
                user_id=user_id,
                exercise_id=exercise_id,
                code_text=code,
                result=result_data,
            )

            # Update the response with the submission ID
            response.code_submission_id = str(submission.id)
            logger.info(f"Code submission stored with id={submission.id}")

        # For failed executions, we don't store them in the database as per requirements
        # Only successful executions are persisted
        else:
            logger.debug(
                f"Execution not stored: success={execution_result.success}, exercise_id={exercise_id}"
            )

        total_time = int((time.time() - start_time) * 1000)
        logger.info(
            f"Code execution completed: status={response.status}, execution_time_ms={response.execution_time_ms}, total_time_ms={total_time}"
        )

        # Log metrics summary periodically (every 100 executions)
        if self.metrics.total_executions % 100 == 0:
            logger.info(f"Execution metrics: {self.metrics.get_metrics_summary()}")

        return response
