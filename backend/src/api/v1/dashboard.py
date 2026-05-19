"""Dashboard API endpoints (F017).

Stateless read-only endpoints for mastery history charts and SSE agent streams.
These endpoints do NOT consume chat quota and do NOT persist sessions.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.auth.dependencies import get_current_user
from src.dependencies import get_analytics_repository, get_db, get_mastery_repository
from src.models import User
from src.repositories.analytics_repository import AnalyticsRepository
from src.repositories.mastery_repository import MasteryRepository
from src.repositories.mastery_snapshot_repository import MasterySnapshotRepository
from src.schemas.dashboard import (
    MasteryHistoryResponse,
    MasterySnapshot,
    ModuleMasteryItem,
    StrugglingStudent,
    TeacherAnalyticsResponse,
)
from src.services import dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Separate router for /module/{moduleId}/progress/stream (no /dashboard prefix)
module_router = APIRouter(prefix="/module", tags=["Dashboard"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

# Valid module slugs for URL validation; integer values are unused — only keys matter.
MODULE_SLUG_MAP: dict[str, int] = {
    "basics": 1,
    "control-flow": 2,
    "data-structures": 3,
    "functions": 4,
    "oop": 5,
    "files": 6,
    "errors": 7,
    "libraries": 8,
}


async def get_mastery_snapshot_repository(
    db=Depends(get_db),
) -> MasterySnapshotRepository:
    return MasterySnapshotRepository(db)


@router.get(
    "/mastery-history",
    response_model=MasteryHistoryResponse,
    summary="Get student mastery history (daily averages)",
    description="Return daily average mastery scores for the authenticated student.",
)
async def get_mastery_history(
    current_user: User = Depends(get_current_user),
    snapshot_repo: MasterySnapshotRepository = Depends(get_mastery_snapshot_repository),
) -> MasteryHistoryResponse:
    rows = await snapshot_repo.get_daily_averages(str(current_user.id))
    snapshots = [MasterySnapshot(day=str(row["day"]), avg_score=round(row["avg_score"], 2)) for row in rows]
    return MasteryHistoryResponse(snapshots=snapshots)


@router.get(
    "/recommendations/stream",
    summary="Stream AI-generated recommendations via SSE",
    description="Run the Progress Agent in recommendations mode and stream results as SSE.",
)
async def stream_recommendations(
    current_user: User = Depends(get_current_user),
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    db=Depends(get_db),
) -> StreamingResponse:
    return StreamingResponse(
        dashboard_service.recommendations_generator(current_user, mastery_repo, db),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@module_router.get(
    "/{moduleId}/progress/stream",
    summary="Stream agent-generated module topic breakdown via SSE",
    description="Run the Progress Agent in module_detail mode and stream topic SSE events.",
)
async def stream_module_progress(
    moduleId: str,
    current_user: User = Depends(get_current_user),
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    db=Depends(get_db),
) -> StreamingResponse:
    if moduleId not in MODULE_SLUG_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown module: '{moduleId}'")
    return StreamingResponse(
        dashboard_service.module_progress_generator(moduleId, current_user, mastery_repo, db),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get(
    "/teacher/analytics",
    response_model=TeacherAnalyticsResponse,
    summary="Get teacher analytics overview",
    description=(
        "Returns live class analytics for teacher/admin users: total students, "
        "average mastery, struggling student count, per-module mastery breakdown, "
        "and list of students whose most recent completed quiz score is below 50%."
    ),
)
async def get_teacher_analytics(
    current_user: User = Depends(get_current_user),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository),
) -> TeacherAnalyticsResponse:
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teacher or admin role required.")

    teacher_id = current_user.id
    total_students = await analytics_repo.get_total_students(teacher_id)
    avg_mastery = await analytics_repo.get_avg_mastery(teacher_id)
    low_quiz_count = await analytics_repo.get_low_quiz_count(teacher_id)
    module_rows = await analytics_repo.get_module_mastery_breakdown(teacher_id)
    struggling_rows = await analytics_repo.get_struggling_students(teacher_id)

    return TeacherAnalyticsResponse(
        total_students=total_students,
        avg_mastery=avg_mastery,
        low_quiz_count=low_quiz_count,
        module_mastery=[ModuleMasteryItem(**row) for row in module_rows],
        struggling_students=[StrugglingStudent(**row) for row in struggling_rows],
    )
