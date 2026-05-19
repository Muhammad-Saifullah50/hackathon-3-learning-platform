"""Analytics repository for teacher dashboard (F019)."""

import uuid
from typing import Optional

from sqlalchemy import distinct, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.classroom import Class, ClassMembership
from src.models.curriculum import Module
from src.models.progress import UserModuleMastery
from src.models.user import User


def _teacher_student_ids_subquery(teacher_id: uuid.UUID):
    """Subquery: distinct student_ids with accepted membership in this teacher's classes."""
    return (
        select(distinct(ClassMembership.student_id))
        .join(Class, Class.id == ClassMembership.class_id)
        .where(
            Class.teacher_id == teacher_id,
            ClassMembership.status == "accepted",
        )
        .scalar_subquery()
    )


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_total_students(self, teacher_id: uuid.UUID) -> int:
        student_ids = _teacher_student_ids_subquery(teacher_id)
        stmt = (
            select(func.count())
            .select_from(User)
            .where(
                User.id.in_(student_ids),
                User.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_avg_mastery(self, teacher_id: uuid.UUID) -> Optional[float]:
        student_ids = _teacher_student_ids_subquery(teacher_id)
        stmt = select(func.avg(UserModuleMastery.score)).where(
            UserModuleMastery.user_id.in_(student_ids)
        )
        result = await self.session.execute(stmt)
        value = result.scalar_one_or_none()
        return float(value) if value is not None else None

    async def get_module_mastery_breakdown(self, teacher_id: uuid.UUID) -> list[dict]:
        student_ids = _teacher_student_ids_subquery(teacher_id)
        slug_expr = func.replace(func.lower(Module.title), " ", "_")
        stmt = (
            select(
                slug_expr.label("module_slug"),
                Module.title.label("module_name"),
                func.coalesce(func.avg(UserModuleMastery.score), 0.0).label("avg_score"),
            )
            .select_from(Module)
            .outerjoin(
                UserModuleMastery,
                (UserModuleMastery.module_id == Module.id)
                & UserModuleMastery.user_id.in_(student_ids),
            )
            .where(Module.deleted_at.is_(None))
            .group_by(Module.id, Module.title)
            .order_by(Module.order)
        )
        result = await self.session.execute(stmt)
        return [
            {"module_slug": row.module_slug, "module_name": row.module_name, "avg_score": float(row.avg_score)}
            for row in result.fetchall()
        ]

    async def get_struggling_students(self, teacher_id: uuid.UUID) -> list[dict]:
        raw = text("""
            WITH teacher_students AS (
                SELECT DISTINCT cm.student_id
                FROM class_memberships cm
                JOIN classes c ON c.id = cm.class_id
                WHERE c.teacher_id = :teacher_id
                  AND cm.status = 'accepted'
            ),
            latest_quiz AS (
                SELECT DISTINCT ON (qs.student_id)
                    qs.student_id,
                    qs.score,
                    qs.module_slug,
                    qs.topic_label,
                    qs.completed_at
                FROM quiz_sessions qs
                JOIN teacher_students ts ON ts.student_id = qs.student_id
                WHERE qs.status = 'completed'
                  AND qs.score IS NOT NULL
                ORDER BY qs.student_id, qs.completed_at DESC
            )
            SELECT u.id AS student_id, u.display_name, lq.score, lq.module_slug, lq.topic_label
            FROM latest_quiz lq
            JOIN users u ON u.id = lq.student_id
            WHERE lq.score < 50
            ORDER BY lq.score ASC
        """)
        result = await self.session.execute(raw, {"teacher_id": str(teacher_id)})
        return [
            {
                "student_id": str(row.student_id),
                "display_name": row.display_name,
                "score": float(row.score),
                "module_slug": row.module_slug,
                "topic_label": row.topic_label,
            }
            for row in result.fetchall()
        ]

    async def get_low_quiz_count(self, teacher_id: uuid.UUID) -> int:
        raw = text("""
            WITH teacher_students AS (
                SELECT DISTINCT cm.student_id
                FROM class_memberships cm
                JOIN classes c ON c.id = cm.class_id
                WHERE c.teacher_id = :teacher_id
                  AND cm.status = 'accepted'
            )
            SELECT COUNT(*) FROM (
                SELECT DISTINCT ON (qs.student_id) qs.student_id, qs.score
                FROM quiz_sessions qs
                JOIN teacher_students ts ON ts.student_id = qs.student_id
                WHERE qs.status = 'completed' AND qs.score IS NOT NULL
                ORDER BY qs.student_id, qs.completed_at DESC
            ) sub
            WHERE sub.score < 50
        """)
        result = await self.session.execute(raw, {"teacher_id": str(teacher_id)})
        return result.scalar_one()
