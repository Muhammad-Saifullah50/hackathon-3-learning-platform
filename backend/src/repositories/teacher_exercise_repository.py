"""Repositories for TeacherGeneratedExercise, ClassExerciseSubmission, and QuestionReview."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.teacher_classes import (
    ClassExerciseSubmission,
    QuestionReview,
    TeacherGeneratedExercise,
    TeacherNotification,
)


class TeacherExerciseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        title: str,
        topic: str,
        difficulty: str,
        target_module: str,
        generation_prompt: str,
        questions: list[dict],
        created_by_id: uuid.UUID,
    ) -> TeacherGeneratedExercise:
        exercise = TeacherGeneratedExercise(
            title=title,
            topic=topic,
            difficulty=difficulty,
            target_module=target_module,
            generation_prompt=generation_prompt,
            questions=questions,
            created_by_id=created_by_id,
        )
        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

    async def get_by_id(self, exercise_id: uuid.UUID) -> Optional[TeacherGeneratedExercise]:
        stmt = select(TeacherGeneratedExercise).where(TeacherGeneratedExercise.id == exercise_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ClassExerciseSubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, class_exercise_id: uuid.UUID, student_id: uuid.UUID) -> ClassExerciseSubmission:
        stmt = select(ClassExerciseSubmission).where(
            ClassExerciseSubmission.class_exercise_id == class_exercise_id,
            ClassExerciseSubmission.student_id == student_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        submission = ClassExerciseSubmission(
            class_exercise_id=class_exercise_id,
            student_id=student_id,
            status="in_progress",
        )
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission

    async def get_by_id(self, submission_id: uuid.UUID) -> Optional[ClassExerciseSubmission]:
        stmt = select(ClassExerciseSubmission).where(ClassExerciseSubmission.id == submission_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_class_exercise_and_student(
        self, class_exercise_id: uuid.UUID, student_id: uuid.UUID
    ) -> Optional[ClassExerciseSubmission]:
        stmt = select(ClassExerciseSubmission).where(
            ClassExerciseSubmission.class_exercise_id == class_exercise_id,
            ClassExerciseSubmission.student_id == student_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_submitted(self, submission: ClassExerciseSubmission, overall_score: float) -> ClassExerciseSubmission:
        submission.status = "submitted"
        submission.overall_score = overall_score
        submission.submitted_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission


class QuestionReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        submission_id: uuid.UUID,
        question_index: int,
        student_code: str,
        ai_review: str,
        grade: float,
    ) -> QuestionReview:
        stmt = select(QuestionReview).where(
            QuestionReview.submission_id == submission_id,
            QuestionReview.question_index == question_index,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.student_code = student_code
            existing.ai_review = ai_review
            existing.grade = grade
            existing.reviewed_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        review = QuestionReview(
            submission_id=submission_id,
            question_index=question_index,
            student_code=student_code,
            ai_review=ai_review,
            grade=grade,
        )
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def list_by_submission(self, submission_id: uuid.UUID) -> list[QuestionReview]:
        stmt = select(QuestionReview).where(QuestionReview.submission_id == submission_id).order_by(QuestionReview.question_index)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class TeacherNotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        teacher_id: uuid.UUID,
        student_id: uuid.UUID,
        submission_id: uuid.UUID,
    ) -> TeacherNotification:
        notif = TeacherNotification(
            teacher_id=teacher_id,
            student_id=student_id,
            submission_id=submission_id,
            notification_type="exercise_submitted",
        )
        self.session.add(notif)
        await self.session.commit()
        await self.session.refresh(notif)
        return notif
