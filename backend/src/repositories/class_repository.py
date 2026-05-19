"""Repository for Class CRUD operations."""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.teacher_classes import Class, ClassMembership


class ClassRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, teacher_id: uuid.UUID) -> Class:
        class_ = Class(name=name, teacher_id=teacher_id)
        self.session.add(class_)
        await self.session.commit()
        await self.session.refresh(class_)
        return class_

    async def get_by_id(self, class_id: uuid.UUID) -> Optional[Class]:
        stmt = select(Class).where(Class.id == class_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_teacher(self, teacher_id: uuid.UUID) -> list[Class]:
        stmt = select(Class).where(Class.teacher_id == teacher_id).order_by(Class.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_member_count(self, teacher_id: uuid.UUID) -> list[dict]:
        """Return classes with accepted member counts."""
        stmt = (
            select(Class, func.count(ClassMembership.id).label("member_count"))
            .outerjoin(ClassMembership, (ClassMembership.class_id == Class.id) & (ClassMembership.status == "accepted"))
            .where(Class.teacher_id == teacher_id)
            .group_by(Class.id)
            .order_by(Class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [{"class": row[0], "member_count": row[1]} for row in rows]
