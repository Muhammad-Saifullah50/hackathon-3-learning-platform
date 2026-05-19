"""InvitationService — business logic for class invitations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.teacher_classes import Class
from src.models.user import User
from src.repositories.class_membership_repository import ClassMembershipRepository
from src.repositories.class_repository import ClassRepository
from src.schemas.student_classes import AcceptedClass, PendingInvitation


class InvitationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repo = ClassMembershipRepository(session)
        self._class_repo = ClassRepository(session)

    async def invite_student(self, class_id: uuid.UUID, student_id: uuid.UUID, teacher_id: uuid.UUID) -> dict:
        """Invite a student to a class.

        Args:
            class_id: UUID of the class to invite the student to.
            student_id: UUID of the student to invite.
            teacher_id: UUID of the teacher (ownership check).

        Returns:
            Dict with membership_id and status, or error dict on failure.
        """
        class_ = await self._class_repo.get_by_id(class_id)
        if not class_ or class_.teacher_id != teacher_id:
            return {"error": "not_found", "detail": "Class not found."}

        existing = await self._repo.get_by_class_and_student(class_id, student_id)
        if existing:
            return {"error": "conflict", "detail": "Student already invited to this class."}

        membership = await self._repo.create(class_id=class_id, student_id=student_id)
        return {"membership_id": str(membership.id), "status": membership.status}

    async def respond_to_invitation(self, membership_id: uuid.UUID, student_id: uuid.UUID, action: str) -> dict:
        """Accept or decline an invitation.

        Args:
            membership_id: UUID of the membership record.
            student_id: UUID of the student (ownership check).
            action: 'accept' or 'decline'.

        Returns:
            Dict with updated membership_id and status, or error dict on failure.
        """
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
        """Return all pending invitations for a student with class/teacher info.

        Loads all classes and teacher users in batched queries to avoid N+1.

        Args:
            student_id: UUID of the student.

        Returns:
            List of PendingInvitation objects.
        """
        memberships = await self._repo.list_pending_by_student(student_id)
        if not memberships:
            return []

        class_ids = [m.class_id for m in memberships]
        classes_stmt = select(Class).where(Class.id.in_(class_ids))
        classes_result = await self.session.execute(classes_stmt)
        classes_by_id: dict[uuid.UUID, Class] = {c.id: c for c in classes_result.scalars().all()}

        teacher_ids = list({c.teacher_id for c in classes_by_id.values()})
        teachers_by_id: dict[uuid.UUID, User] = {}
        if teacher_ids:
            teachers_stmt = select(User).where(User.id.in_(teacher_ids))
            teachers_result = await self.session.execute(teachers_stmt)
            teachers_by_id = {u.id: u for u in teachers_result.scalars().all()}

        result = []
        for m in memberships:
            class_ = classes_by_id.get(m.class_id)
            if not class_:
                continue
            teacher = teachers_by_id.get(class_.teacher_id)
            result.append(PendingInvitation(
                id=m.id,
                class_id=m.class_id,
                class_name=class_.name,
                teacher_name=teacher.display_name if teacher else "Unknown",
                invited_at=str(m.invited_at),
            ))
        return result

    async def list_accepted_classes(self, student_id: uuid.UUID) -> list[AcceptedClass]:
        """Return all classes a student has accepted invitations to.

        Loads all classes and teacher users in batched queries to avoid N+1.

        Args:
            student_id: UUID of the student.

        Returns:
            List of AcceptedClass objects.
        """
        memberships = await self._repo.list_accepted_by_student(student_id)
        if not memberships:
            return []

        class_ids = [m.class_id for m in memberships]
        classes_stmt = select(Class).where(Class.id.in_(class_ids))
        classes_result = await self.session.execute(classes_stmt)
        classes_by_id: dict[uuid.UUID, Class] = {c.id: c for c in classes_result.scalars().all()}

        teacher_ids = list({c.teacher_id for c in classes_by_id.values()})
        teachers_by_id: dict[uuid.UUID, User] = {}
        if teacher_ids:
            teachers_stmt = select(User).where(User.id.in_(teacher_ids))
            teachers_result = await self.session.execute(teachers_stmt)
            teachers_by_id = {u.id: u for u in teachers_result.scalars().all()}

        result = []
        for m in memberships:
            class_ = classes_by_id.get(m.class_id)
            if not class_:
                continue
            teacher = teachers_by_id.get(class_.teacher_id)
            result.append(AcceptedClass(
                class_id=m.class_id,
                class_name=class_.name,
                teacher_name=teacher.display_name if teacher else "Unknown",
            ))
        return result
