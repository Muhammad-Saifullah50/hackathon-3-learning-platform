import logging
import re
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.dependencies import get_current_user
from ...dependencies import get_code_session_service, get_db
from ...models.user import User
from ...repositories.submission_repository import SubmissionRepository
from ...schemas.code_editor import RateLimitErrorResponse
from ...schemas.code_execution import CodeExecutionRequest, CodeExecutionResponse
from ...services.code_execution_service import CodeExecutionService
from ...services.code_session_service import CodeSessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["code-execution"])


def parse_error_line(stderr: str) -> Optional[int]:
    """Extract the first line number from a Python traceback stderr string."""
    if not stderr:
        return None
    match = re.search(r'line (\d+)', stderr)
    return int(match.group(1)) if match else None


@router.post("/code-execution", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db),
    code_session_service: CodeSessionService = Depends(get_code_session_service),
) -> CodeExecutionResponse:
    """Execute Python code in a secure sandbox environment."""
    logger.info(
        f"Code execution API request from user_id={current_user.id}, code_length={len(request.code)}"
    )

    # Daily run rate limit check (5 runs/day per user)
    allowed = await code_session_service.check_and_increment_daily_limit(
        db_session, current_user.id, "run", limit=5
    )
    if not allowed:
        tomorrow = date.today().replace(day=date.today().day + 1) if date.today().day < 28 else (
            date.today().replace(month=date.today().month + 1, day=1)
            if date.today().month < 12
            else date.today().replace(year=date.today().year + 1, month=1, day=1)
        )
        # Simple next-day calculation
        from datetime import timedelta
        retry_after = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
        return JSONResponse(
            status_code=429,
            content=RateLimitErrorResponse(
                message="Daily run limit reached (5 runs/day). Try again tomorrow.",
                retry_after=retry_after,
            ).model_dump(),
        )

    submission_repo = SubmissionRepository(db_session)
    code_execution_service = CodeExecutionService(submission_repo=submission_repo)

    try:
        result = await code_execution_service.execute_code(
            code=request.code,
            user_id=str(current_user.id),
            module_id=request.module_id,
            lesson_id=request.lesson_id,
            exercise_id=None,
        )

        # Add error_line parsed from error_message/stderr
        if result.error_message and result.error_line is None:
            result.error_line = parse_error_line(result.error_message)

        logger.info(
            f"Code execution completed: status={result.status}, execution_time_ms={result.execution_time_ms}"
        )
        return result

    except Exception as e:
        logger.error(f"Error executing code for user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during code execution")


__all__ = ["router"]
