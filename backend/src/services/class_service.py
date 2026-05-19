"""ClassService — business logic for teacher class management."""

import uuid
from typing import Optional

from sqlalchemy import cast, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.class_membership_repository import ClassMembershipRepository
from src.repositories.class_repository import ClassRepository
from src.schemas.teacher import ClassDetail, ClassMember, ClassResponse, StudentSearchResult


class ClassService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repo = ClassRepository(session)
        self._membership_repo = ClassMembershipRepository(session)

    async def create_class(self, name: str, teacher_id: uuid.UUID) -> ClassResponse:
        class_ = await self._repo.create(name=name, teacher_id=teacher_id)
        return ClassResponse(id=class_.id, name=class_.name, teacher_id=class_.teacher_id, member_count=0)

    async def list_classes(self, teacher_id: uuid.UUID) -> list[ClassResponse]:
        rows = await self._repo.get_with_member_count(teacher_id)
        return [
            ClassResponse(
                id=row["class"].id,
                name=row["class"].name,
                teacher_id=row["class"].teacher_id,
                member_count=row["member_count"],
            )
            for row in rows
        ]

    async def get_class_detail(self, class_id: uuid.UUID, teacher_id: uuid.UUID) -> Optional[ClassDetail]:
        class_ = await self._repo.get_by_id(class_id)
        if not class_ or class_.teacher_id != teacher_id:
            return None
        memberships = await self._membership_repo.list_all_by_class(class_id)
        members: list[ClassMember] = []
        for m in memberships:
            # Load student user
            stmt = select(User).where(User.id == m.student_id)
            result = await self.session.execute(stmt)
            student = result.scalar_one_or_none()
            if student:
                members.append(ClassMember(
                    student_id=m.student_id,
                    display_name=student.display_name,
                    email=student.email,
                    status=m.status,
                ))
        return ClassDetail(id=class_.id, name=class_.name, teacher_id=class_.teacher_id, members=members)

    async def search_students(self, query: str, limit: int = 20) -> list[StudentSearchResult]:
        """Search students by partial name or email (case-insensitive)."""
        stmt = (
            select(User)
            .where(
                cast(User.role, String) == "student",
                (User.display_name.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        return [StudentSearchResult(id=u.id, display_name=u.display_name, email=u.email) for u in users]
