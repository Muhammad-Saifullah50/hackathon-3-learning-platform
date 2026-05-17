"""Agent session models.

Defines SQLAlchemy models for agent sessions, routing decisions,
and hint progression tracking.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.base import TimestampMixin


class AgentSession(Base, TimestampMixin):
    """Represents an ongoing tutoring conversation between a student and the agent system."""

    __tablename__ = "agent_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(20),
        nullable=False,
        default="active",
    )
    conversation_history = Column(JSONB, nullable=False, server_default="[]")
    active_agent = Column(String(30), nullable=True)
    title = Column(Text, nullable=True)
    surface = Column(String(20), nullable=True)

    # Relationships
    routing_decisions = relationship(
        "RoutingDecision", back_populates="session", cascade="all, delete-orphan"
    )
    hint_progressions = relationship(
        "HintProgression", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="check_agent_session_status",
        ),
        CheckConstraint(
            "surface IN ('standalone', 'embedded') OR surface IS NULL",
            name="check_agent_session_surface",
        ),
        Index("idx_agent_session_user_updated", "user_id", text("updated_at DESC")),
        Index("idx_agent_session_status", "status"),
    )


class RoutingDecision(Base, TimestampMixin):
    """Represents a single intent classification event for a student message."""

    __tablename__ = "routing_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message = Column(Text, nullable=False)
    intent = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=False)
    target_agent = Column(String(30), nullable=False)

    # Relationships
    session = relationship("AgentSession", back_populates="routing_decisions")

    __table_args__ = (
        CheckConstraint(
            "intent IN ('concept-explanation', 'code-debug', 'code-review', "
            "'exercise-generation', 'progress-summary', 'general')",
            name="check_routing_intent",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="check_routing_confidence",
        ),
        Index("idx_routing_session_id", "session_id"),
        Index("idx_routing_user_id", "user_id"),
        Index("idx_routing_intent", "intent"),
        Index("idx_routing_created_at", "created_at"),
    )


class HintProgression(Base, TimestampMixin):
    """Tracks a student's debugging session through the progressive hint system."""

    __tablename__ = "hint_progressions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    error_context = Column(JSONB, nullable=False)
    hint_level = Column(Integer, nullable=False, default=1)
    hints_provided = Column(JSONB, nullable=False, server_default="[]")
    solution_revealed = Column(Integer, nullable=False, default=0)
    resolved = Column(Integer, nullable=False, default=0)

    # Relationships
    session = relationship("AgentSession", back_populates="hint_progressions")

    __table_args__ = (
        CheckConstraint(
            "hint_level BETWEEN 1 AND 3",
            name="check_hint_level",
        ),
        Index("idx_hint_session_id", "session_id"),
        Index("idx_hint_user_id", "user_id"),
        Index("idx_hint_resolved", "resolved"),
    )
