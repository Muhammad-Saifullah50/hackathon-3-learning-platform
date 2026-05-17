"""Request and response schemas for quiz endpoints."""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Session state ─────────────────────────────────────────────────────────────

class QuizSessionState(BaseModel):
    quiz_session_id: UUID
    agent_session_id: UUID
    module_slug: str
    topic_label: str
    status: Literal["generated", "in_progress", "completed"]
    score: Optional[float] = None
    questions: list[dict]
    student_answers: dict[str, Any] = {}
    grades: dict[str, Any] = {}
    completed_at: Optional[datetime] = None
    created_at: datetime


class QuizListItem(BaseModel):
    quiz_session_id: UUID
    agent_session_id: UUID
    module_slug: str
    topic_label: str
    score: Optional[float] = None
    status: str
    created_at: datetime


# ── Grade flashcard ───────────────────────────────────────────────────────────

class GradeFlashcardRequest(BaseModel):
    card_index: int = Field(ge=3, le=5)
    student_answer: str = Field(min_length=1)


class GradeFlashcardResponse(BaseModel):
    card_index: int
    grade: Literal["Correct", "Partial", "Wrong"]
    feedback: str
    session_status: str


# ── Submit quiz ───────────────────────────────────────────────────────────────

class MCQAnswerItem(BaseModel):
    card_index: int = Field(ge=0, le=2)
    selected_index: int = Field(ge=0, le=3)
    is_correct: bool


class SubmitQuizRequest(BaseModel):
    mcq_answers: list[MCQAnswerItem] = Field(min_length=3, max_length=3)


class PerCardResult(BaseModel):
    card_index: int
    card_type: Literal["mcq", "flashcard"]
    grade: str
    points: float


class SubmitQuizResponse(BaseModel):
    session_id: UUID
    score: float
    score_out_of_6: float
    per_card_results: list[PerCardResult]
    mastery_updated: bool
    module_slug: str
    struggle_flagged: bool
