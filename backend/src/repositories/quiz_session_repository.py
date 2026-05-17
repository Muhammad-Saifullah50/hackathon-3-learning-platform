"""Quiz session repository.

CRUD operations for quiz_sessions.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.quiz_session import QuizSession


class QuizSessionRepository:
    """Repository for quiz session operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        student_id: uuid.UUID,
        chat_session_id: uuid.UUID,
        module_slug: str,
        topic_label: str,
        questions: list[dict],
    ) -> QuizSession:
        """Create a new quiz session with generated questions."""
        quiz = QuizSession(
            student_id=student_id,
            chat_session_id=chat_session_id,
            module_slug=module_slug,
            topic_label=topic_label,
            status="generated",
            questions=questions,
            student_answers={},
            grades={},
        )
        self.session.add(quiz)
        await self.session.commit()
        await self.session.refresh(quiz)
        return quiz

    async def get_by_id(self, quiz_session_id: uuid.UUID) -> Optional[QuizSession]:
        """Return a quiz session by PK."""
        stmt = select(QuizSession).where(QuizSession.id == quiz_session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_answers_and_grades(
        self,
        quiz_session_id: uuid.UUID,
        card_index: int,
        student_answer: Any,
        grade: str,
        new_status: Optional[str] = None,
    ) -> Optional[QuizSession]:
        """Persist a single card's answer and grade, optionally updating status."""
        quiz = await self.get_by_id(quiz_session_id)
        if not quiz:
            return None

        answers = dict(quiz.student_answers or {})
        answers[str(card_index)] = student_answer
        quiz.student_answers = answers

        grades = dict(quiz.grades or {})
        grades[str(card_index)] = grade
        quiz.grades = grades

        if new_status:
            quiz.status = new_status

        await self.session.commit()
        await self.session.refresh(quiz)
        return quiz

    async def mark_completed(
        self,
        quiz_session_id: uuid.UUID,
        mcq_answers: dict[str, Any],
        mcq_grades: dict[str, str],
        final_score: float,
    ) -> Optional[QuizSession]:
        """Merge MCQ answers/grades and mark the session completed with a score."""
        quiz = await self.get_by_id(quiz_session_id)
        if not quiz:
            return None

        answers = dict(quiz.student_answers or {})
        answers.update(mcq_answers)
        quiz.student_answers = answers

        grades = dict(quiz.grades or {})
        grades.update(mcq_grades)
        quiz.grades = grades

        quiz.score = final_score
        quiz.status = "completed"
        quiz.completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(quiz)
        return quiz

    async def list_by_student(
        self, student_id: uuid.UUID, limit: int = 50
    ) -> list[QuizSession]:
        """Return quiz sessions for a student ordered by created_at DESC."""
        stmt = (
            select(QuizSession)
            .where(QuizSession.student_id == student_id)
            .order_by(QuizSession.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
