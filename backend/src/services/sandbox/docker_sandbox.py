import ast
import asyncio
import json
import logging
import os
import re
import tempfile
import time
from typing import Dict, Optional, Tuple

import docker

from .base import ExecutionResult, SandboxInterface
from .error_parser import ErrorParser
from .import_validator import ImportValidator

# Set up logging
logger = logging.getLogger(__name__)


class DockerSandbox(SandboxInterface):
    """Docker-based implementation of the code execution sandbox."""

    def __init__(self):
        self._client = None  # lazy — connect on first use so app starts without Docker
        self.python_image = os.getenv("SANDBOX_PYTHON_IMAGE", "python:3.11-alpine")
        self.import_validator = ImportValidator()
        self.error_parser = ErrorParser()

    @property
    def client(self):
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    async def execute_code(
        self, code: str, timeout_seconds: int = 5, memory_limit: str = "50MB"
    ) -> ExecutionResult:
        """Execute Python code in a Docker container."""
        start_time = time.time()
        logger.info(
            f"Sandbox execution started with timeout={timeout_seconds}s, memory_limit={memory_limit}"
        )

        # First, validate imports
        is_valid, error_msg = await self.validate_imports(code)
        if not is_valid:
            execution_time = int((time.time() - start_time) * 1000)
            logger.warning(f"Import validation failed: {error_msg}")
            return ExecutionResult(
                success=False,
                output="",
                error_message=error_msg,
                error_type="SecurityViolation",
                execution_time_ms=execution_time,
                status="blocked",
            )

        # Apply constraints from environment variables if provided
        timeout_seconds = int(
            os.getenv("SANDBOX_TIMEOUT_SECONDS", str(timeout_seconds))
        )
        memory_limit = os.getenv("SANDBOX_MEMORY_LIMIT", memory_limit)

        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file_path = f.name

        try:
            # Create a wrapper script to handle input/output properly
            wrapper_script = f"""
import sys
import io

# Redirect stdin to prevent hanging on input()
sys.stdin = io.StringIO()

try:
    # Execute the code
    exec(open('/workspace/code.py').read())
except Exception as e:
    # Print the exception info to stderr
    import traceback
    sys.stderr.write(traceback.format_exc())
    sys.exit(1)
"""

            # Write the wrapper script to the same directory as the code file
            wrapper_file_path = os.path.join(
                os.path.dirname(temp_file_path), "wrapper.py"
            )
            with open(wrapper_file_path, "w") as f:
                f.write(wrapper_script)

            # Rename the code file to a consistent name
            code_file_path = os.path.join(os.path.dirname(temp_file_path), "code.py")
            os.rename(temp_file_path, code_file_path)
            temp_file_path = code_file_path

            try:
                # Run the code in a Docker container with detach=True for timeout control
                logger.debug(
                    f"Running container with image {self.python_image}, memory limit {memory_limit}"
                )
                container = self.client.containers.run(
                    image=self.python_image,
                    volumes={
                        os.path.dirname(temp_file_path): {
                            "bind": "/workspace",
                            "mode": "ro",
                        }
                    },
                    working_dir="/workspace",
                    command="python wrapper.py",
                    network_disabled=os.getenv(
                        "SANDBOX_NETWORK_DISABLED", "true"
                    ).lower()
                    == "true",
                    mem_limit=memory_limit,
                    remove=False,  # Don't auto-remove so we can get logs
                    detach=True,  # Run in background so we can control timeout
                )

                # Wait for container to finish with timeout
                try:
                    exit_code = container.wait(timeout=timeout_seconds)
                    execution_time = int((time.time() - start_time) * 1000)

                    # Get logs
                    stdout = container.logs(stdout=True, stderr=False)
                    stderr = container.logs(stdout=False, stderr=True)

                    output_str = stdout.decode("utf-8") if stdout else ""
                    error_str = stderr.decode("utf-8") if stderr else ""

                except Exception as wait_error:
                    # Timeout or other error during wait
                    execution_time = int((time.time() - start_time) * 1000)
                    logger.warning(f"Container wait error: {wait_error}")

                    # Try to get partial logs
                    try:
                        stdout = container.logs(stdout=True, stderr=False)
                        stderr = container.logs(stdout=False, stderr=True)
                        output_str = stdout.decode("utf-8") if stdout else ""
                        error_str = stderr.decode("utf-8") if stderr else ""
                    except:
                        output_str = ""
                        error_str = ""

                    # Kill the container
                    try:
                        container.kill()
                    except:
                        pass

                    # Remove the container
                    try:
                        container.remove(force=True)
                    except:
                        pass

                    # Return timeout error
                    return ExecutionResult(
                        success=False,
                        output=output_str,
                        error_message="Execution timed out after 5 seconds",
                        error_type="TimeoutError",
                        execution_time_ms=timeout_seconds * 1000,
                        status="timeout",
                    )

                # Clean up container
                try:
                    container.remove(force=True)
                except:
                    pass

                if error_str:
                    # If there's an error, return error result
                    classified_error_type = self._classify_error(error_str)
                    line_number = self._extract_line_number(error_str)

                    # Enhance the error message for student friendliness
                    enhanced_error = self.error_parser.enhance_error_message(
                        error_message=error_str,
                        error_type=classified_error_type,
                        line_number=line_number,
                    )

                    return ExecutionResult(
                        success=False,
                        output=output_str,
                        error_message=enhanced_error,
                        error_type=classified_error_type,
                        execution_time_ms=execution_time,
                        status="error",
                    )
                else:
                    # Success case
                    return ExecutionResult(
                        success=True,
                        output=output_str,
                        execution_time_ms=execution_time,
                        memory_used_bytes=self._estimate_memory_usage(output_str),
                        status="success",
                    )

            except docker.errors.ContainerError as e:
                execution_time = int((time.time() - start_time) * 1000)
                error_msg = e.stderr.decode("utf-8") if e.stderr else str(e)
                logger.error(f"Container execution error: {error_msg}")
                return ExecutionResult(
                    success=False,
                    output="",
                    error_message=error_msg,
                    error_type=self._classify_error(error_msg),
                    execution_time_ms=execution_time,
                    status="error",
                )

            except docker.errors.ImageNotFound:
                execution_time = int((time.time() - start_time) * 1000)
                error_msg = "Python image not found in Docker"
                logger.error(error_msg)
                return ExecutionResult(
                    success=False,
                    output="",
                    error_message=error_msg,
                    error_type="InfrastructureError",
                    execution_time_ms=execution_time,
                    status="infrastructure_failure",
                )

            except Exception as e:
                execution_time = int((time.time() - start_time) * 1000)
                error_msg = str(e)
                logger.error(f"Unexpected error during execution: {error_msg}")
                if "timeout" in error_msg.lower():
                    return ExecutionResult(
                        success=False,
                        output="",
                        error_message="Execution timed out",
                        error_type="TimeoutError",
                        execution_time_ms=timeout_seconds
                        * 1000,  # Use the timeout limit
                        status="timeout",
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        output="",
                        error_message=error_msg,
                        error_type="UnknownError",
                        execution_time_ms=execution_time,
                        status="error",
                    )

        finally:
            # Clean up temporary files using the cleanup method
            self.cleanup_temp_files(temp_file_path, wrapper_file_path)

    async def validate_imports(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate that the code only imports allowed modules."""
        return self.import_validator.validate_imports(code)

    def _classify_error(self, error_str: str) -> str:
        """Classify the type of error from the error message."""
        if "SyntaxError" in error_str:
            return "SyntaxError"
        elif "IndentationError" in error_str:
            return "IndentationError"
        elif "NameError" in error_str:
            return "NameError"
        elif "TypeError" in error_str:
            return "TypeError"
        elif "ValueError" in error_str:
            return "ValueError"
        elif "ZeroDivisionError" in error_str:
            return "ZeroDivisionError"
        elif "IndexError" in error_str:
            return "IndexError"
        elif "KeyError" in error_str:
            return "KeyError"
        elif "AttributeError" in error_str:
            return "AttributeError"
        elif "ImportError" in error_str or "ModuleNotFoundError" in error_str:
            return "ImportError"
        elif "timeout" in error_str.lower():
            return "TimeoutError"
        else:
            return "UnknownError"

    def _extract_line_number(self, error_str: str) -> Optional[int]:
        """Extract the line number from an error message if available."""
        # Prefer the user-code frame: exec'd code shows as File "<string>", line N
        match = re.search(r'File "<string>", line (\d+)', error_str)
        if match:
            return int(match.group(1))
        # Fallback: last "line N" in the traceback avoids the wrapper script frame
        matches = re.findall(r"line (\d+)", error_str)
        return int(matches[-1]) if matches else None

    def _estimate_memory_usage(self, output_str: str) -> Optional[int]:
        """Estimate memory usage based on output size."""
        # This is a rough estimate - actual memory usage would require more sophisticated tracking
        # For now, we'll return a placeholder based on output size
        if output_str:
            return (
                len(output_str.encode("utf-8")) * 10
            )  # Rough estimate: 10x output size
        return 1024  # 1KB baseline

    async def run_test_cases(
        self, code: str, test_cases: list, timeout: int = 5
    ) -> list:
        """Run submitted code against a list of test cases.

        Each test case is a dict with 'assert_statement' (and optionally 'input',
        'expected_output'). Returns a list of result dicts with 'passed', 'error'
        and 'test_index' fields.
        """
        results = []
        for i, tc in enumerate(test_cases):
            assert_stmt = tc.get("assert_statement", "")
            full_code = f"{code}\n\n{assert_stmt}" if assert_stmt else code
            result = await self.execute_code(full_code, timeout_seconds=timeout)
            results.append(
                {
                    "test_index": i,
                    "passed": result.success,
                    "error": result.error_message if not result.success else None,
                }
            )
        return results

    def cleanup_temp_files(self, *file_paths):
        """Clean up temporary files after execution."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temporary file: {file_path}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary file {file_path}: {e}")

    def cleanup_containers(self, max_age_minutes=10):
        """Clean up old/stale containers."""
        try:
            # Find containers created by this sandbox that are older than max_age_minutes
            old_containers = self.client.containers.list(
                filters={"label": "sandbox=learnpybyai"}, all=True
            )

            import datetime

            cutoff_time = datetime.datetime.now() - datetime.timedelta(
                minutes=max_age_minutes
            )

            cleaned_count = 0
            for container in old_containers:
                # Note: Docker API doesn't directly expose creation time easily,
                # so this is a simplified approach
                try:
                    container.reload()
                    # Remove stopped containers
                    if container.status == "exited":
                        container.remove()
                        cleaned_count += 1
                        logger.info(f"Removed old container: {container.short_id}")
                except:
                    continue

            logger.info(f"Cleanup completed: removed {cleaned_count} old containers")
        except Exception as e:
            logger.error(f"Error during container cleanup: {e}")
