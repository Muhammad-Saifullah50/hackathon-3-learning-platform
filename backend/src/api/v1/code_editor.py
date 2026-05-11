"""Code editor API — GET/PUT /api/v1/code-sessions/{context_key}."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.dependencies import get_current_user
from ...database import get_db
from ...dependencies import get_code_session_service
from ...models.user import User
from ...schemas.code_editor import CodeSessionResponse, SaveCodeRequest
from ...services.code_session_service import CodeSessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["code-editor"])


@router.get("/code-sessions/{context_key}", response_model=CodeSessionResponse)
async def get_code_session(
    context_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CodeSessionService = Depends(get_code_session_service),
):
    """Load a student's saved code for the given context."""
    session = await service.load_code(db, current_user.id, context_key)
    if not session:
        raise HTTPException(status_code=404, detail="Code session not found")
    return CodeSessionResponse(
        context_key=session.context_key,
        code=session.code,
        updated_at=session.updated_at,
    )


@router.put("/code-sessions/{context_key}", response_model=CodeSessionResponse)
async def put_code_session(
    context_key: str,
    request: SaveCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CodeSessionService = Depends(get_code_session_service),
):
    """Save (upsert) a student's code for the given context."""
    session = await service.save_code(db, current_user.id, context_key, request.code)
    return CodeSessionResponse(
        context_key=session.context_key,
        code=session.code,
        updated_at=session.updated_at,
    )
