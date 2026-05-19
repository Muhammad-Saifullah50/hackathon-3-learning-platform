"""Classroom models: Class and ClassMembership (F019)."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.base import TimestampMixin


class Class(Base, TimestampMixin):
    """A teaching group owned by a teacher."""

    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)

    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id])
    memberships = relationship(
        "ClassMembership", back_populates="classroom", cascade="all, delete-orphan"
    )


class ClassMembership(Base, TimestampMixin):
    """Links a student user to a class.

    status: 'pending' (invited) | 'accepted' (enrolled)
    """

    __tablename__ = "class_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(20), nullable=False, default="pending")
    invited_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    classroom = relationship("Class", back_populates="memberships")
    student = relationship("User", foreign_keys=[student_id])

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_membership"),
    )
