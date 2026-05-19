"""InvitationService — business logic for class invitations."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.class_membership_repository import ClassMembershipRepository
from src.repositories.class_repository import ClassRepository
from src.schemas.student_classes import AcceptedClass, PendingInvitation


class InvitationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repo = ClassMembershipRepository(session)
        self._class_repo = ClassRepository(session)

    async def invite_student(self, class_id: uuid.UUID, student_id: uuid.UUID, teacher_id: uuid.UUID) -> dict:
        """Invite a student to a class. Returns 409 detail if duplicate."""
        # Verify class ownership
        class_ = await self._class_repo.get_by_id(class_id)
        if not class_ or class_.teacher_id != teacher_id:
            return {"error": "not_found", "detail": "Class not found."}

        existing = await self._repo.get_by_class_and_student(class_id, student_id)
        if existing:
            return {"error": "conflict", "detail": "Student already invited to this class."}

        membership = await self._repo.create(class_id=class_id, student_id=student_id)
        return {"membership_id": str(membership.id), "status": membership.status}

    async def respond_to_invitation(self, membership_id: uuid.UUID, student_id: uuid.UUID, action: str) -> dict:
        """Accept or decline an invitation. Returns 409 if already responded."""
        membership = await self._repo.get_by_id(membership_id)
        if not membership or membership.student_id != student_id:
            return {"error": "not_found", "detail": "Invitation not found."}
        if membership.status != "pending":
            return {"error": "conflict", "detail": "Invitation already responded to."}
        if action not in ("accept", "decline"):
            return {"error": "bad_request", "detail": "Action must be 'accept' or 'decline'."}

        new_status = "accepted" if action == "accept" else "declined"
        updated = await self._repo.update_status(membership_id, new_status)
        return {"membership_id": str(updated.id), "status": updated.status}

    async def list_pending_invitations(self, student_id: uuid.UUID) -> list[PendingInvitation]:
        memberships = await self._repo.list_pending_by_student(student_id)
        result = []
        for m in memberships:
            class_ = await self._class_repo.get_by_id(m.class_id)
            if not class_:
                continue
            # Get teacher name
            from sqlalchemy import select
            from src.models.user import User
            stmt = select(User).where(User.id == class_.teacher_id)
            res = await self.session.execute(stmt)
            teacher = res.scalar_one_or_none()
            result.append(PendingInvitation(
                id=m.id,
                class_id=m.class_id,
                class_name=class_.name,
                teacher_name=teacher.display_name if teacher else "Unknown",
                invited_at=str(m.invited_at),
            ))
        return result

    async def list_accepted_classes(self, student_id: uuid.UUID) -> list[AcceptedClass]:
        memberships = await self._repo.list_accepted_by_student(student_id)
        result = []
        for m in memberships:
            class_ = await self._class_repo.get_by_id(m.class_id)
            if not class_:
                continue
            from sqlalchemy import select
            from src.models.user import User
            stmt = select(User).where(User.id == class_.teacher_id)
            res = await self.session.execute(stmt)
            teacher = res.scalar_one_or_none()
            result.append(AcceptedClass(
                class_id=m.class_id,
                class_name=class_.name,
                teacher_name=teacher.display_name if teacher else "Unknown",
            ))
        return result
