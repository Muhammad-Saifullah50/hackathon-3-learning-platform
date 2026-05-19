"""Repository for ClassMembership CRUD operations."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.teacher_classes import ClassMembership


class ClassMembershipRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, class_id: uuid.UUID, student_id: uuid.UUID) -> ClassMembership:
        membership = ClassMembership(class_id=class_id, student_id=student_id, status="pending")
        self.session.add(membership)
        await self.session.commit()
        await self.session.refresh(membership)
        return membership

    async def get_by_class_and_student(self, class_id: uuid.UUID, student_id: uuid.UUID) -> Optional[ClassMembership]:
        stmt = select(ClassMembership).where(
            ClassMembership.class_id == class_id,
            ClassMembership.student_id == student_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, membership_id: uuid.UUID) -> Optional[ClassMembership]:
        stmt = select(ClassMembership).where(ClassMembership.id == membership_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pending_by_student(self, student_id: uuid.UUID) -> list[ClassMembership]:
        stmt = (
            select(ClassMembership)
            .options(selectinload(ClassMembership.class_).selectinload(ClassMembership.class_.property.mapper.class_.teacher))
            .where(ClassMembership.student_id == student_id, ClassMembership.status == "pending")
            .order_by(ClassMembership.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_accepted_by_student(self, student_id: uuid.UUID) -> list[ClassMembership]:
        stmt = (
            select(ClassMembership)
            .where(ClassMembership.student_id == student_id, ClassMembership.status == "accepted")
            .order_by(ClassMembership.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_accepted_by_class(self, class_id: uuid.UUID) -> list[ClassMembership]:
        stmt = (
            select(ClassMembership)
            .where(ClassMembership.class_id == class_id, ClassMembership.status == "accepted")
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_by_class(self, class_id: uuid.UUID) -> list[ClassMembership]:
        stmt = (
            select(ClassMembership)
            .where(ClassMembership.class_id == class_id)
            .order_by(ClassMembership.invited_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, membership_id: uuid.UUID, status: str) -> Optional[ClassMembership]:
        membership = await self.get_by_id(membership_id)
        if not membership:
            return None
        membership.status = status
        membership.responded_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(membership)
        return membership
