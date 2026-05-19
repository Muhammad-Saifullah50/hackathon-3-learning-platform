"""Student-facing Pydantic schemas for F18 Teacher Dashboard."""

import uuid
from typing import Optional
from pydantic import BaseModel


# --- Invitations ---

class PendingInvitation(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    class_name: str
    teacher_name: str
    invited_at: str

    model_config = {"from_attributes": True}


class InvitationAction(BaseModel):
    action: str  # "accept" | "decline"


# --- Memberships ---

class AcceptedClass(BaseModel):
    class_id: uuid.UUID
    class_name: str
    teacher_name: str

    model_config = {"from_attributes": True}


# --- Assigned exercises ---

class AssignedExerciseSummary(BaseModel):
    class_exercise_id: uuid.UUID
    exercise_id: uuid.UUID
    title: str
    topic: str
    difficulty: str
    class_name: str
    status: str  # in_progress | submitted

    model_config = {"from_attributes": True}


class QuestionDetail(BaseModel):
    index: int
    description: str
    starter_code: str


class QuestionReviewResult(BaseModel):
    question_index: int
    student_code: str
    ai_review: str
    grade: float


class AssignedExerciseDetail(BaseModel):
    class_exercise_id: uuid.UUID
    exercise_id: uuid.UUID
    title: str
    topic: str
    difficulty: str
    class_name: str
    questions: list[QuestionDetail]
    reviews: list[QuestionReviewResult]
    status: str
    overall_score: Optional[float] = None

    model_config = {"from_attributes": True}


class ReviewQuestionRequest(BaseModel):
    question_index: int
    student_code: str


class SubmitResponse(BaseModel):
    submission_id: uuid.UUID
    overall_score: float
    submitted_at: str
