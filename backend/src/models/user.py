"""User-related models: User, UserProfile, UserStreak."""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.base import SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    User model - extends F01 authentication schema.

    Represents platform users with authentication credentials and role-based access.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student", index=True)
    display_name = Column(String(100), nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    mfa_enabled = Column(String, nullable=False, default=False)
    mfa_secret = Column(String(255), nullable=True)
    permissions = Column(JSONB, nullable=True)
    preferences = Column(JSONB, nullable=False, server_default="{}")

    # Relationships
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    streak = relationship(
        "UserStreak", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    exercise_progress = relationship(
        "UserExerciseProgress", back_populates="user", cascade="all, delete-orphan"
    )
    quiz_attempts = relationship(
        "UserQuizAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    module_mastery = relationship(
        "UserModuleMastery", back_populates="user", cascade="all, delete-orphan"
    )
    code_submissions = relationship(
        "CodeSubmission", back_populates="user", cascade="all, delete-orphan"
    )
    code_sessions = relationship(
        "CodeSession", back_populates="user", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )
    email_verification_tokens = relationship(
        "EmailVerificationToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('student', 'teacher', 'admin')", name="check_user_role"
        ),
    )


class UserProfile(Base, TimestampMixin):
    """
    User profile model - optional 1:1 extension of users.

    Stores role-specific metadata and additional user information.
    """

    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    bio = Column(String, nullable=True)
    profile_metadata = Column("metadata", JSONB, nullable=False, server_default="{}")

    # Relationships
    user = relationship("User", back_populates="profile")


class UserStreak(Base, TimestampMixin):
    """
    User streak model - tracks learning consistency.

    Stores current and longest streaks for mastery calculation (10% weight).
    """

    __tablename__ = "user_streaks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    current_streak = Column(Integer, nullable=False, server_default="0")
    longest_streak = Column(Integer, nullable=False, server_default="0")
    last_activity_date = Column(Date, nullable=False)

    # Relationships
    user = relationship("User", back_populates="streak")

    __table_args__ = (
        CheckConstraint("current_streak >= 0", name="check_current_streak_positive"),
        CheckConstraint(
            "longest_streak >= current_streak", name="check_longest_streak_valid"
        ),
    )
