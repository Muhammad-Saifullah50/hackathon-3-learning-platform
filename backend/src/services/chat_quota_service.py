"""Chat quota enforcement using RateLimitCounter."""

import uuid
from datetime import date, datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import IdentifierType, RateLimitCounter

DAILY_LIMIT = 15


class ChatQuotaService:
    """Enforces 15 messages/student/day using the rate_limit_counters table."""

    @staticmethod
    def _identifier(user_id: uuid.UUID) -> str:
        today = date.today().isoformat()
        return f"{user_id}:chat:{today}"

    async def check_and_get_remaining(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, int]:
        """Atomically check quota and increment if allowed.

        Returns (allowed, remaining_after).
        """
        identifier = self._identifier(user_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        stmt = (
            pg_insert(RateLimitCounter)
            .values(
                identifier=identifier,
                identifier_type=IdentifierType.USER_DAILY,
                attempt_count=1,
                last_attempt_at=now,
                created_at=now,
            )
            .on_conflict_do_update(
                index_elements=["identifier"],
                set_={
                    "attempt_count": RateLimitCounter.attempt_count + 1,
                    "last_attempt_at": now,
                },
                where=RateLimitCounter.attempt_count < DAILY_LIMIT,
            )
            .returning(RateLimitCounter.attempt_count)
        )

        result = await db.execute(stmt)
        row = result.fetchone()

        if row is None:
            return False, 0

        await db.commit()
        used = row[0]
        return True, max(0, DAILY_LIMIT - used)

    async def get_status(self, db: AsyncSession, user_id: uuid.UUID) -> dict:
        """Return quota status without incrementing (read-only)."""
        identifier = self._identifier(user_id)

        stmt = sa.select(RateLimitCounter).where(
            RateLimitCounter.identifier == identifier
        )
        result = await db.execute(stmt)
        counter = result.scalar_one_or_none()

        used = counter.attempt_count if counter else 0
        now_utc = datetime.now(timezone.utc)
        tomorrow = (now_utc.date() + timedelta(days=1))
        quota_reset_at = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=timezone.utc)

        return {
            "messages_sent_today": used,
            "daily_limit": DAILY_LIMIT,
            "remaining": max(0, DAILY_LIMIT - used),
            "quota_reset_at": quota_reset_at,
        }
