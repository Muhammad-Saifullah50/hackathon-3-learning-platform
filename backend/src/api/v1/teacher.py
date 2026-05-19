"""Teacher API router — all routes require role='teacher'."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_role
from src.dependencies import get_db
from src.models.user import User
from src.schemas.teacher import (
    AssignExerciseRequest,
    AssignResponse,
    ClassCreate,
    ClassDetail,
    ClassResponse,
    ExerciseGenerateRequest,
    GuardrailRejection,
    InviteStudentRequest,
    StudentSearchResult,
    TeacherExercise,
)
from src.services.class_service import ClassService
from src.services.invitation_service import InvitationService

router = APIRouter(prefix="/api/v1/teacher", tags=["Teacher"])


def _class_service(db: AsyncSession = Depends(get_db)) -> ClassService:
    return ClassService(db)


def _invitation_service(db: AsyncSession = Depends(get_db)) -> InvitationService:
    return InvitationService(db)


# --- Class management ---

@router.post(
    "/classes",
    response_model=ClassResponse,
    status_code=201,
    summary="Create a class",
    description="Creates a new class owned by the authenticated teacher.",
)
async def create_class(
    body: ClassCreate,
    current_user: User = Depends(require_role(["teacher"])),
    svc: ClassService = Depends(_class_service),
):
    return await svc.create_class(name=body.name, teacher_id=current_user.id)


@router.get(
    "/classes",
    response_model=list[ClassResponse],
    summary="List classes",
    description="Returns all classes created by the authenticated teacher, with accepted member counts.",
)
async def list_classes(
    current_user: User = Depends(require_role(["teacher"])),
    svc: ClassService = Depends(_class_service),
):
    return await svc.list_classes(teacher_id=current_user.id)


@router.get(
    "/classes/{class_id}",
    response_model=ClassDetail,
    summary="Get class detail",
    description="Returns full class detail including all members and their invitation statuses.",
)
async def get_class_detail(
    class_id: uuid.UUID,
    current_user: User = Depends(require_role(["teacher"])),
    svc: ClassService = Depends(_class_service),
):
    detail = await svc.get_class_detail(class_id=class_id, teacher_id=current_user.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Class not found.")
    return detail


@router.get(
    "/students/search",
    response_model=list[StudentSearchResult],
    summary="Search students",
    description="Returns students matching a partial name or email query. Used when inviting students to a class.",
)
async def search_students(
    q: str = Query(..., min_length=1, description="Partial name or email"),
    current_user: User = Depends(require_role(["teacher"])),
    svc: ClassService = Depends(_class_service),
):
    return await svc.search_students(query=q)


@router.post(
    "/classes/{class_id}/invitations",
    status_code=201,
    summary="Invite student to class",
    description="Sends a class invitation to a student. Returns 409 if already invited.",
)
async def invite_student(
    class_id: uuid.UUID,
    body: InviteStudentRequest,
    current_user: User = Depends(require_role(["teacher"])),
    svc: InvitationService = Depends(_invitation_service),
):
    result = await svc.invite_student(
        class_id=class_id,
        student_id=body.student_id,
        teacher_id=current_user.id,
    )
    if "error" in result:
        status_code = 404 if result["error"] == "not_found" else 409
        raise HTTPException(status_code=status_code, detail=result["detail"])
    return result


# --- Exercise generation and assignment (US3) ---

@router.post(
    "/exercises/generate",
    summary="Generate exercise",
    description="Uses AI to generate a 3-question coding exercise from a teacher prompt. Returns the exercise preview.",
)
async def generate_exercise(
    body: ExerciseGenerateRequest,
    current_user: User = Depends(require_role(["teacher"])),
    db: AsyncSession = Depends(get_db),
):
    from src.services.teacher_exercise_service import TeacherExerciseService
    svc = TeacherExerciseService(db)
    result = await svc.generate(prompt=body.prompt, teacher_id=current_user.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post(
    "/exercises/{exercise_id}/assign",
    response_model=AssignResponse,
    summary="Assign exercise to class",
    description="Assigns a previously generated exercise to one of the teacher's classes.",
)
async def assign_exercise(
    exercise_id: uuid.UUID,
    body: AssignExerciseRequest,
    current_user: User = Depends(require_role(["teacher"])),
    db: AsyncSession = Depends(get_db),
):
    from src.services.teacher_exercise_service import TeacherExerciseService
    svc = TeacherExerciseService(db)
    result = await svc.assign(
        exercise_id=exercise_id,
        class_id=body.class_id,
        teacher_id=current_user.id,
    )
    if "error" in result:
        status_code = 409 if result["error"] == "conflict" else 404
        raise HTTPException(status_code=status_code, detail=result["detail"])
    return result
