"""Progress repository - operations for UserExerciseProgress, UserQuizAttempt, UserModuleMastery."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError
import asyncio

from src.models.progress import UserExerciseProgress, UserQuizAttempt, UserModuleMastery


class ProgressRepository:
    """Repository for progress tracking operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Exercise progress operations
    async def record_exercise_completion(
        self,
        user_id: str,
        exercise_id: int,
        score: float,
        status: str = "completed"
    ) -> UserExerciseProgress:
        """Record or update exercise completion."""
        stmt = select(UserExerciseProgress).where(
            UserExerciseProgress.user_id == user_id,
            UserExerciseProgress.exercise_id == exercise_id
        )
        result = await self.session.execute(stmt)
        progress = result.scalar_one_or_none()

        if not progress:
            progress = UserExerciseProgress(
                user_id=user_id,
                exercise_id=exercise_id,
                status=status,
                score=score,
                attempts=1,
                completed_at=datetime.utcnow() if status == "completed" else None
            )
            self.session.add(progress)
        else:
            progress.status = status
            progress.score = score
            progress.attempts += 1
            progress.updated_at = datetime.utcnow()
            if status == "completed" and not progress.completed_at:
                progress.completed_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(progress)
        return progress

    async def get_user_exercise_progress(self, user_id: str, exercise_id: int) -> Optional[UserExerciseProgress]:
        """Get user's progress for a specific exercise."""
        stmt = select(UserExerciseProgress).where(
            UserExerciseProgress.user_id == user_id,
            UserExerciseProgress.exercise_id == exercise_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # Quiz attempt operations
    async def record_quiz_attempt(
        self,
        user_id: str,
        quiz_id: int,
        score: float,
        answers: dict
    ) -> UserQuizAttempt:
        """Record a quiz attempt."""
        attempt = UserQuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            answers=answers
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def get_user_quiz_attempts(self, user_id: str, quiz_id: int) -> List[UserQuizAttempt]:
        """Get all quiz attempts for a user."""
        stmt = (
            select(UserQuizAttempt)
            .where(
                UserQuizAttempt.user_id == user_id,
                UserQuizAttempt.quiz_id == quiz_id
            )
            .order_by(UserQuizAttempt.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Mastery calculation operations
    async def calculate_mastery_score(
        self,
        user_id: str,
        module_id: int,
        exercise_score: float,
        quiz_score: float,
        code_quality_score: float,
        streak_score: float
    ) -> float:
        """
        Calculate mastery score using the formula:
        40% exercises + 30% quizzes + 20% code quality + 10% streak
        """
        mastery = (
            exercise_score * 0.40 +
            quiz_score * 0.30 +
            code_quality_score * 0.20 +
            streak_score * 0.10
        )
        return min(100.0, max(0.0, mastery))

    async def update_mastery_score(
        self,
        user_id: str,
        module_id: int,
        new_score: float,
        max_retries: int = 3
    ) -> UserModuleMastery:
        """
        Update mastery score with optimistic locking and retry logic.

        Args:
            user_id: User ID
            module_id: Module ID
            new_score: New mastery score (0-100)
            max_retries: Maximum retry attempts for concurrent updates
        """
        for attempt in range(max_retries):
            try:
                stmt = select(UserModuleMastery).where(
                    UserModuleMastery.user_id == user_id,
                    UserModuleMastery.module_id == module_id
                )
                result = await self.session.execute(stmt)
                mastery = result.scalar_one_or_none()

                if not mastery:
                    mastery = UserModuleMastery(
                        user_id=user_id,
                        module_id=module_id,
                        score=new_score
                    )
                    self.session.add(mastery)
                else:
                    mastery.score = new_score
                    mastery.updated_at = datetime.utcnow()

                await self.session.commit()
                await self.session.refresh(mastery)

                # Side-effect: append to mastery_snapshots for time-series charting
                try:
                    await self.session.execute(
                        text(
                            "INSERT INTO mastery_snapshots (user_id, module_id, score) "
                            "VALUES (:user_id, :module_id, :score)"
                        ),
                        {"user_id": str(user_id), "module_id": module_id, "score": new_score},
                    )
                    await self.session.commit()
                except Exception:
                    # Non-critical — do not fail mastery update if snapshot insert fails
                    await self.session.rollback()

                return mastery

            except StaleDataError:
                await self.session.rollback()
                if attempt == max_retries - 1:
                    raise
                # Exponential backoff
                await asyncio.sleep(0.1 * (2 ** attempt))

        raise Exception("Failed to update mastery score after retries")

    async def get_user_mastery_scores(self, user_id: str) -> List[UserModuleMastery]:
        """Get all module mastery scores for a user."""
        stmt = select(UserModuleMastery).where(UserModuleMastery.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
