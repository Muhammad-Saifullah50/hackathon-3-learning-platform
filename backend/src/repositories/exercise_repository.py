"""Exercise repository.

CRUD operations for exercises.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent_exercise import AgentExercise


class ExerciseRepository:
    """Repository for exercise operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_exercise(
        self,
        topic: str,
        difficulty: str,
        description: str,
        test_cases: list[dict],
        starter_code: Optional[str] = None,
        solution_code: Optional[str] = None,
        creator: str = "system",
        created_by_user_id: Optional[uuid.UUID] = None,
    ) -> AgentExercise:
        """
        Create a new exercise.

        Args:
            topic: Curriculum topic
            difficulty: Difficulty level (beginner/intermediate/advanced)
            description: Problem description
            test_cases: List of test case dicts
            starter_code: Optional starter code template
            solution_code: Optional reference solution
            creator: Who created it (system/teacher)
            created_by_user_id: User who created it

        Returns:
            Created Exercise
        """
        exercise = AgentExercise(
            topic=topic,
            difficulty=difficulty,
            description=description,
            test_cases=test_cases,
            starter_code=starter_code,
            solution_code=solution_code,
            creator=creator,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

    async def get_exercise(self, exercise_id: str) -> Optional[AgentExercise]:
        """
        Get an exercise by ID.

        Args:
            exercise_id: UUID string of the exercise

        Returns:
            Exercise if found, None otherwise
        """
        stmt = select(AgentExercise).where(AgentExercise.id == uuid.UUID(exercise_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_exercises(
        self,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AgentExercise]:
        """
        List exercises with optional filters.

        Args:
            topic: Filter by topic
            difficulty: Filter by difficulty
            limit: Maximum results
            offset: Skip count

        Returns:
            List of Exercise objects
        """
        stmt = select(AgentExercise)
        if topic:
            stmt = stmt.where(AgentExercise.topic == topic)
        if difficulty:
            stmt = stmt.where(AgentExercise.difficulty == difficulty)
        stmt = stmt.order_by(AgentExercise.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_exercise(self, exercise_id: str, **kwargs) -> Optional[AgentExercise]:
        """
        Update an exercise.

        Args:
            exercise_id: UUID string of the exercise
            **kwargs: Fields to update

        Returns:
            Updated Exercise if found, None otherwise
        """
        exercise = await self.get_exercise(exercise_id)
        if not exercise:
            return None

        for key, value in kwargs.items():
            if hasattr(exercise, key):
                setattr(exercise, key, value)

        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise
