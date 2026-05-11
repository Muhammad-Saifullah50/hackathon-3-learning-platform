"""CodeSession model for persisting student code per editor context."""

import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import relationship

from src.database import Base
from src.database_types import GUID
from src.models.base import TimestampMixin


class CodeSession(Base, TimestampMixin):
    """Persists a student's code for a given editor context (playground or exercise)."""

    __tablename__ = "code_sessions"

    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    context_key = Column(String(255), nullable=False)
    code = Column(Text, nullable=False, default="")

    user = relationship("User", back_populates="code_sessions", lazy="select")

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "context_key", name="pk_code_sessions"),
    )
