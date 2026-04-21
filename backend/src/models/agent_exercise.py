"""Agent exercise models.

Defines SQLAlchemy models for exercises, exercise submissions,
and mastery records.
"""

import uuid

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.base import TimestampMixin


class AgentExercise(Base, TimestampMixin):
    """Represents a coding challenge generated for practice."""

    __tablename__ = "exercises_agent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=True)
    test_cases = Column(JSONB, nullable=False)
    solution_code = Column(Text, nullable=True)
    creator = Column(String(20), nullable=False, default="system")
    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    submissions = relationship(
        "AgentExerciseSubmission",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="check_exercise_difficulty",
        ),
        CheckConstraint(
            "creator IN ('system', 'teacher')",
            name="check_exercise_creator",
        ),
        Index("idx_exercise_topic", "topic"),
        Index("idx_exercise_difficulty", "difficulty"),
        Index("idx_exercise_creator", "creator"),
    )


class AgentExerciseSubmission(Base, TimestampMixin):
    """Represents a student's attempt at an exercise."""

    __tablename__ = "exercise_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exercises_agent.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_code = Column(Text, nullable=False)
    test_results = Column(JSONB, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    # Relationships
    exercise = relationship("AgentExercise", back_populates="submissions")

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="check_submission_score",
        ),
        Index("idx_submission_exercise_id", "exercise_id"),
        Index("idx_submission_user_id", "user_id"),
        Index("idx_submission_score", "score"),
        Index("idx_submission_created_at", "created_at"),
    )


class MasteryRecord(Base, TimestampMixin):
    """Represents a student's mastery score for a specific topic."""

    __tablename__ = "mastery_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic = Column(String(100), nullable=False, index=True)
    score = Column(Float, nullable=False)
    level = Column(String(20), nullable=False)
    component_breakdown = Column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="check_mastery_score",
        ),
        CheckConstraint(
            "level IN ('Beginner', 'Learning', 'Proficient', 'Mastered')",
            name="check_mastery_level",
        ),
        Index("idx_mastery_user_id", "user_id"),
        Index("idx_mastery_topic", "topic"),
        Index("idx_mastery_user_topic", "user_id", "topic", unique=True),
    )
