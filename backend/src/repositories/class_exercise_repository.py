"""Repository for ClassExercise CRUD operations."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.teacher_classes import ClassExercise, ClassMembership


class ClassExerciseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, class_id: uuid.UUID, exercise_id: uuid.UUID, assigned_by_id: uuid.UUID) -> ClassExercise:
        class_exercise = ClassExercise(
            class_id=class_id,
            exercise_id=exercise_id,
            assigned_by_id=assigned_by_id,
        )
        self.session.add(class_exercise)
        await self.session.commit()
        await self.session.refresh(class_exercise)
        return class_exercise

    async def get_by_id(self, class_exercise_id: uuid.UUID) -> Optional[ClassExercise]:
        stmt = select(ClassExercise).where(ClassExercise.id == class_exercise_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_class_and_exercise(self, class_id: uuid.UUID, exercise_id: uuid.UUID) -> Optional[ClassExercise]:
        stmt = select(ClassExercise).where(
            ClassExercise.class_id == class_id,
            ClassExercise.exercise_id == exercise_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_class(self, class_id: uuid.UUID) -> list[ClassExercise]:
        stmt = select(ClassExercise).where(ClassExercise.class_id == class_id).order_by(ClassExercise.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_assigned_to_student(self, student_id: uuid.UUID) -> list[ClassExercise]:
        """Return all ClassExercises for classes where the student is an accepted member."""
        stmt = (
            select(ClassExercise)
            .join(ClassMembership, ClassMembership.class_id == ClassExercise.class_id)
            .where(
                ClassMembership.student_id == student_id,
                ClassMembership.status == "accepted",
            )
            .order_by(ClassExercise.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
