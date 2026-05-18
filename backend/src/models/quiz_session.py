"""Quiz session model."""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

from src.database import Base
from src.models.base import TimestampMixin

CURRICULUM_SLUGS = (
    "basics", "control_flow", "data_structures", "functions",
    "oop", "files", "errors", "libraries",
)


class QuizSession(Base, TimestampMixin):
    """A single student quiz attempt."""

    __tablename__ = "quiz_sessions"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    chat_session_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False
    )
    module_slug: str = Column(String(50), nullable=False)
    topic_label: str = Column(String(200), nullable=False)
    status: str = Column(String(20), nullable=False, default="generated")
    score: Optional[float] = Column(Float, nullable=True)
    questions: list[dict[str, Any]] = Column(JSONB, nullable=False)
    student_answers: dict[str, Any] = Column(JSONB, nullable=False, default=dict)
    grades: dict[str, Any] = Column(JSONB, nullable=False, default=dict)
    completed_at: Optional[datetime] = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('generated','in_progress','completed')",
            name="ck_quiz_status",
        ),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_quiz_score",
        ),
        CheckConstraint(
            "module_slug IN ('basics','control_flow','data_structures','functions',"
            "'oop','files','errors','libraries')",
            name="ck_quiz_module_slug",
        ),
        Index("idx_quiz_sessions_student_id", "student_id"),
        Index("idx_quiz_sessions_chat_session", "chat_session_id"),
        Index("idx_quiz_sessions_status", "status"),
        Index("idx_quiz_sessions_module_slug", "module_slug"),
        Index("idx_quiz_sessions_created_at", "created_at"),
    )
