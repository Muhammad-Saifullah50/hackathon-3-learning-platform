"""Student classes API router — all routes require role='student'."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_role
from src.dependencies import get_db
from src.models.user import User
from src.schemas.student_classes import (
    AcceptedClass,
    AssignedExerciseDetail,
    AssignedExerciseSummary,
    InvitationAction,
    PendingInvitation,
    ReviewQuestionRequest,
    SubmitResponse,
)
from src.services.invitation_service import InvitationService

router = APIRouter(prefix="/api/v1/student/classes", tags=["Student Classes"])


def _invitation_service(db: AsyncSession = Depends(get_db)) -> InvitationService:
    return InvitationService(db)


# --- Invitations (US2) ---

@router.get(
    "/invitations",
    response_model=list[PendingInvitation],
    summary="List pending invitations",
    description="Returns all pending class invitations for the authenticated student.",
)
async def list_invitations(
    current_user: User = Depends(require_role(["student"])),
    svc: InvitationService = Depends(_invitation_service),
):
    return await svc.list_pending_invitations(student_id=current_user.id)


@router.patch(
    "/invitations/{invitation_id}",
    summary="Respond to invitation",
    description="Accept or decline a pending class invitation.",
)
async def respond_to_invitation(
    invitation_id: uuid.UUID,
    body: InvitationAction,
    current_user: User = Depends(require_role(["student"])),
    svc: InvitationService = Depends(_invitation_service),
):
    result = await svc.respond_to_invitation(
        membership_id=invitation_id,
        student_id=current_user.id,
        action=body.action,
    )
    if "error" in result:
        status_codes = {"not_found": 404, "conflict": 409, "bad_request": 400}
        raise HTTPException(status_code=status_codes.get(result["error"], 400), detail=result["detail"])
    return result


# --- Memberships (US5) ---

@router.get(
    "/memberships",
    response_model=list[AcceptedClass],
    summary="List accepted classes",
    description="Returns all classes the student has accepted an invitation to.",
)
async def list_memberships(
    current_user: User = Depends(require_role(["student"])),
    svc: InvitationService = Depends(_invitation_service),
):
    return await svc.list_accepted_classes(student_id=current_user.id)


# --- Assigned exercises (US4) ---

@router.get(
    "/assigned-exercises",
    response_model=list[AssignedExerciseSummary],
    summary="List assigned exercises",
    description="Returns all exercises assigned to the student across their accepted classes.",
)
async def list_assigned_exercises(
    current_user: User = Depends(require_role(["student"])),
    db: AsyncSession = Depends(get_db),
):
    from src.services.student_assignment_service import StudentAssignmentService
    svc = StudentAssignmentService(db)
    return await svc.list_assigned_exercises(student_id=current_user.id)


@router.get(
    "/assigned-exercises/{class_exercise_id}",
    response_model=AssignedExerciseDetail,
    summary="Get exercise detail",
    description="Returns full detail for a single assigned exercise including questions and prior reviews.",
)
async def get_assigned_exercise_detail(
    class_exercise_id: uuid.UUID,
    current_user: User = Depends(require_role(["student"])),
    db: AsyncSession = Depends(get_db),
):
    from src.services.student_assignment_service import StudentAssignmentService
    svc = StudentAssignmentService(db)
    detail = await svc.get_exercise_detail(class_exercise_id=class_exercise_id, student_id=current_user.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Exercise not found.")
    return detail


_REVIEW_ERROR_CODES = {
    "not_found": 404,
    "forbidden": 403,
    "conflict": 409,
    "bad_request": 400,
}


@router.post(
    "/assigned-exercises/{class_exercise_id}/review",
    summary="Review a question",
    description="Submits a student's code for a single question and returns AI code review and grade.",
)
async def review_question(
    class_exercise_id: uuid.UUID,
    body: ReviewQuestionRequest,
    current_user: User = Depends(require_role(["student"])),
    db: AsyncSession = Depends(get_db),
):
    from src.services.student_assignment_service import StudentAssignmentService
    svc = StudentAssignmentService(db)
    result = await svc.review_question(
        class_exercise_id=class_exercise_id,
        student_id=current_user.id,
        question_index=body.question_index,
        student_code=body.student_code,
    )
    if "error" in result:
        status_code = _REVIEW_ERROR_CODES.get(result["error"], 400)
        raise HTTPException(status_code=status_code, detail=result["detail"])
    return result


_SUBMIT_ERROR_CODES = {
    "not_found": 404,
    "forbidden": 403,
    "not_ready": 400,
    "conflict": 409,
}


@router.post(
    "/assigned-exercises/{class_exercise_id}/submit",
    response_model=SubmitResponse,
    summary="Submit exercise",
    description="Marks the exercise as submitted after all questions have been reviewed. Calculates the overall score.",
)
async def submit_exercise(
    class_exercise_id: uuid.UUID,
    current_user: User = Depends(require_role(["student"])),
    db: AsyncSession = Depends(get_db),
):
    from src.services.student_assignment_service import StudentAssignmentService
    svc = StudentAssignmentService(db)
    result = await svc.submit_exercise(class_exercise_id=class_exercise_id, student_id=current_user.id)
    if "error" in result:
        status_code = _SUBMIT_ERROR_CODES.get(result["error"], 400)
        raise HTTPException(status_code=status_code, detail=result["detail"])
    return result
