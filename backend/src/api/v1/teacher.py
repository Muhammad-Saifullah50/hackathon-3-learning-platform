"""Teacher API endpoints — class management, student search, exercise generation/assignment."""

import logging
import uuid

from agents import Runner
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_user, require_role
from src.dependencies import get_db, get_exercise_repository
from src.models.classroom import Class, ClassMembership
from src.models.user import User
from src.repositories.exercise_repository import ExerciseRepository
from src.services.agents.agents import get_exercise_agent
from src.services.agents.context import LearnPyByAIContext
from src.services.agents.model_provider import get_run_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/teacher", tags=["Teacher"])

_require_teacher = require_role(["teacher", "admin"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ClassCreateRequest(BaseModel):
    name: str


class ClassResponse(BaseModel):
    id: str
    name: str
    teacher_id: str
    member_count: int


class ClassMemberOut(BaseModel):
    student_id: str
    display_name: str
    email: str
    status: str


class ClassDetailResponse(BaseModel):
    id: str
    name: str
    teacher_id: str
    members: list[ClassMemberOut]


class StudentSearchResult(BaseModel):
    id: str
    display_name: str
    email: str


class InvitationRequest(BaseModel):
    student_id: str


class ExerciseGenerateRequest(BaseModel):
    prompt: str


class ExerciseQuestion(BaseModel):
    index: int
    description: str
    starter_code: str


class TeacherExercise(BaseModel):
    id: str
    title: str
    topic: str
    difficulty: str
    target_module: str
    questions: list[ExerciseQuestion]


class GuardrailRejection(BaseModel):
    code: str
    message: str
    missing: list[str]


class AssignRequest(BaseModel):
    class_id: str


class AssignResponse(BaseModel):
    class_exercise_id: str
    assigned_to_count: int
    warning: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_teacher_class(
    class_id: str, teacher_id: uuid.UUID, db: AsyncSession
) -> Class:
    stmt = select(Class).where(
        Class.id == uuid.UUID(class_id),
        Class.teacher_id == teacher_id,
    )
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/classes", response_model=ClassResponse)
async def create_class(
    request: ClassCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Class name cannot be empty")

    cls = Class(teacher_id=current_user.id, name=name)
    db.add(cls)
    await db.commit()
    await db.refresh(cls)

    return ClassResponse(
        id=str(cls.id),
        name=cls.name,
        teacher_id=str(cls.teacher_id),
        member_count=0,
    )


@router.get("/classes", response_model=list[ClassResponse])
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    stmt = (
        select(Class, func.count(ClassMembership.id).label("member_count"))
        .outerjoin(ClassMembership, ClassMembership.class_id == Class.id)
        .where(Class.teacher_id == current_user.id)
        .group_by(Class.id)
        .order_by(Class.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        ClassResponse(
            id=str(cls.id),
            name=cls.name,
            teacher_id=str(cls.teacher_id),
            member_count=count,
        )
        for cls, count in rows
    ]


@router.get("/classes/{class_id}", response_model=ClassDetailResponse)
async def get_class_detail(
    class_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    stmt = (
        select(Class)
        .options(selectinload(Class.memberships).selectinload(ClassMembership.student))
        .where(
            Class.id == uuid.UUID(class_id),
            Class.teacher_id == current_user.id,
        )
    )
    cls = (await db.execute(stmt)).scalar_one_or_none()
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found")

    members = [
        ClassMemberOut(
            student_id=str(m.student_id),
            display_name=m.student.display_name,
            email=m.student.email,
            status=m.status,
        )
        for m in cls.memberships
    ]
    return ClassDetailResponse(
        id=str(cls.id),
        name=cls.name,
        teacher_id=str(cls.teacher_id),
        members=members,
    )


@router.get("/students/search", response_model=list[StudentSearchResult])
async def search_students(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    pattern = f"%{q.lower()}%"
    stmt = (
        select(User)
        .where(
            User.role == "student",
            User.deleted_at.is_(None),
            (func.lower(User.display_name).like(pattern))
            | (func.lower(User.email).like(pattern)),
        )
        .limit(20)
    )
    users = (await db.execute(stmt)).scalars().all()
    return [
        StudentSearchResult(id=str(u.id), display_name=u.display_name, email=u.email)
        for u in users
    ]


@router.post("/classes/{class_id}/invitations", status_code=201)
async def invite_student(
    class_id: str,
    request: InvitationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    await _get_teacher_class(class_id, current_user.id, db)

    student_result = await db.execute(
        select(User).where(User.id == uuid.UUID(request.student_id), User.role == "student")
    )
    if student_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Student not found")

    existing = await db.execute(
        select(ClassMembership).where(
            ClassMembership.class_id == uuid.UUID(class_id),
            ClassMembership.student_id == uuid.UUID(request.student_id),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Student already invited or enrolled")

    from datetime import datetime, timezone
    membership = ClassMembership(
        class_id=uuid.UUID(class_id),
        student_id=uuid.UUID(request.student_id),
        status="pending",
        invited_at=datetime.now(timezone.utc),
    )
    db.add(membership)
    await db.commit()
    return {"status": "invited"}


@router.post("/exercises/generate")
async def generate_teacher_exercise(
    request: ExerciseGenerateRequest,
    db: AsyncSession = Depends(get_db),
    exercise_repo: ExerciseRepository = Depends(get_exercise_repository),
    current_user: User = Depends(_require_teacher),
):
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt cannot be empty")

    lf_ctx = LearnPyByAIContext(user_id=current_user.id, db=db)
    agent = get_exercise_agent()
    try:
        result = await Runner.run(
            agent,
            input=f"Generate a Python coding exercise for this teacher request: {prompt}",
            context=lf_ctx,
            run_config=get_run_config(),
        )
    except Exception as exc:
        logger.exception("Exercise generation error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    final = result.final_output
    if final is None:
        raise HTTPException(status_code=502, detail="Agent returned no output")

    # Map ExerciseAgentResponse → TeacherExercise and persist it
    difficulty = final.difficulty if hasattr(final, "difficulty") else "beginner"
    description = final.description if hasattr(final, "description") else str(final)
    starter = (final.starter_code.code if hasattr(final, "starter_code") and final.starter_code else "")

    saved = await exercise_repo.create_exercise(
        topic=prompt[:100],
        difficulty=difficulty,
        description=description,
        test_cases=[],
        starter_code=starter,
        creator="teacher",
        created_by_user_id=current_user.id,
    )

    return TeacherExercise(
        id=str(saved.id),
        title=final.title if hasattr(final, "title") else prompt[:60],
        topic=prompt[:100],
        difficulty=difficulty,
        target_module="",
        questions=[
            ExerciseQuestion(index=1, description=description, starter_code=starter)
        ],
    )


@router.post("/exercises/{exercise_id}/assign", response_model=AssignResponse)
async def assign_exercise(
    exercise_id: str,
    request: AssignRequest,
    db: AsyncSession = Depends(get_db),
    exercise_repo: ExerciseRepository = Depends(get_exercise_repository),
    current_user: User = Depends(_require_teacher),
):
    exercise = await exercise_repo.get_exercise(exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")

    await _get_teacher_class(request.class_id, current_user.id, db)

    # Count accepted members to report how many students will receive the exercise
    count_result = await db.execute(
        select(func.count(ClassMembership.id)).where(
            ClassMembership.class_id == uuid.UUID(request.class_id),
            ClassMembership.status == "accepted",
        )
    )
    accepted_count = count_result.scalar_one() or 0

    warning = "No accepted students in this class yet" if accepted_count == 0 else None

    return AssignResponse(
        class_exercise_id=str(uuid.uuid4()),
        assigned_to_count=accepted_count,
        warning=warning,
    )
