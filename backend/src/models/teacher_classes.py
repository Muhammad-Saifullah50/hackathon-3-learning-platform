"""SQLAlchemy models for teacher dashboard: Class, ClassMembership, and related entities."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.base import TimestampMixin


class Class(Base, TimestampMixin):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    teacher = relationship("User", foreign_keys=[teacher_id])
    memberships = relationship("ClassMembership", back_populates="class_", cascade="all, delete-orphan")
    class_exercises = relationship("ClassExercise", back_populates="class_", cascade="all, delete-orphan")


class ClassMembership(Base, TimestampMixin):
    __tablename__ = "class_memberships"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_membership_class_student"),
        CheckConstraint("status IN ('pending', 'accepted', 'declined')", name="ck_membership_status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(10), nullable=False, default="pending")
    invited_at = Column(DateTime(timezone=True), nullable=False, server_default="NOW()")
    responded_at = Column(DateTime(timezone=True), nullable=True)

    class_ = relationship("Class", back_populates="memberships")
    student = relationship("User", foreign_keys=[student_id])


class TeacherGeneratedExercise(Base, TimestampMixin):
    __tablename__ = "teacher_generated_exercises"
    __table_args__ = (
        CheckConstraint("difficulty IN ('beginner', 'intermediate', 'advanced')", name="ck_teacher_exercise_difficulty"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    topic = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False)
    target_module = Column(String(100), nullable=False)
    generation_prompt = Column(Text(), nullable=False)
    questions = Column(JSONB(), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    class_exercises = relationship("ClassExercise", back_populates="exercise", cascade="all, delete-orphan")


class ClassExercise(Base, TimestampMixin):
    __tablename__ = "class_exercises"
    __table_args__ = (
        UniqueConstraint("class_id", "exercise_id", name="uq_class_exercise"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("teacher_generated_exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default="NOW()")

    class_ = relationship("Class", back_populates="class_exercises")
    exercise = relationship("TeacherGeneratedExercise", back_populates="class_exercises")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    submissions = relationship("ClassExerciseSubmission", back_populates="class_exercise", cascade="all, delete-orphan")


class ClassExerciseSubmission(Base, TimestampMixin):
    __tablename__ = "class_exercise_submissions"
    __table_args__ = (
        UniqueConstraint("class_exercise_id", "student_id", name="uq_submission_class_exercise_student"),
        CheckConstraint("status IN ('in_progress', 'submitted')", name="ck_submission_status"),
        CheckConstraint("overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)", name="ck_submission_score"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_exercise_id = Column(UUID(as_uuid=True), ForeignKey("class_exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score = Column(Float(), nullable=True)
    status = Column(String(15), nullable=False, default="in_progress", index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    class_exercise = relationship("ClassExercise", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])
    question_reviews = relationship("QuestionReview", back_populates="submission", cascade="all, delete-orphan")
    notifications = relationship("TeacherNotification", back_populates="submission", cascade="all, delete-orphan")


class QuestionReview(Base, TimestampMixin):
    __tablename__ = "question_reviews"
    __table_args__ = (
        UniqueConstraint("submission_id", "question_index", name="uq_question_review"),
        CheckConstraint("grade >= 0 AND grade <= 100", name="ck_review_grade"),
        CheckConstraint("question_index >= 0", name="ck_review_question_index"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("class_exercise_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_index = Column(Integer(), nullable=False)
    student_code = Column(Text(), nullable=False)
    ai_review = Column(Text(), nullable=False)
    grade = Column(Float(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=False, server_default="NOW()")

    submission = relationship("ClassExerciseSubmission", back_populates="question_reviews")


class TeacherNotification(Base, TimestampMixin):
    __tablename__ = "teacher_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("class_exercise_submissions.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(50), nullable=False, default="exercise_submitted")
    is_read = Column(Boolean(), nullable=False, default=False, index=True)

    teacher = relationship("User", foreign_keys=[teacher_id])
    student = relationship("User", foreign_keys=[student_id])
    submission = relationship("ClassExerciseSubmission", back_populates="notifications")
