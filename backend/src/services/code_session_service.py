"""CodeSession service — save/load code and daily rate limit enforcement."""

import uuid
from datetime import date, datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import IdentifierType, RateLimitCounter
from src.models.code_session import CodeSession
from src.repositories.code_session_repository import CodeSessionRepository


class CodeSessionService:
    def __init__(self, repo: CodeSessionRepository):
        self.repo = repo

    async def save_code(
        self, db: AsyncSession, user_id: uuid.UUID, context_key: str, code: str
    ) -> CodeSession:
        return await self.repo.upsert(user_id, context_key, code)

    async def load_code(
        self, db: AsyncSession, user_id: uuid.UUID, context_key: str
    ) -> Optional[CodeSession]:
        return await self.repo.get(user_id, context_key)

    async def check_and_increment_daily_limit(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        action: str,
        limit: int = 3,
    ) -> bool:
        """Return True if allowed (counter incremented), False if limit reached."""
        today = date.today().isoformat()
        identifier = f"{user_id}:{action}:{today}"

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
                where=RateLimitCounter.attempt_count < limit,
            )
            .returning(RateLimitCounter.attempt_count)
        )

        result = await db.execute(stmt)
        row = result.fetchone()

        if row is None:
            # ON CONFLICT WHERE was false — counter already at limit, no update happened
            return False

        await db.commit()
        return True
