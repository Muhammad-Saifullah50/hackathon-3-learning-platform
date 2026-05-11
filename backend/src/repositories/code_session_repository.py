"""CodeSession repository — UPSERT and GET for code persistence."""

import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.code_session import CodeSession


class CodeSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, user_id: uuid.UUID, context_key: str, code: str) -> CodeSession:
        stmt = (
            pg_insert(CodeSession)
            .values(user_id=user_id, context_key=context_key, code=code)
            .on_conflict_do_update(
                constraint="pk_code_sessions",
                set_={"code": code, "updated_at": sa.text("NOW()")},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get(user_id, context_key)

    async def get(self, user_id: uuid.UUID, context_key: str) -> Optional[CodeSession]:
        stmt = select(CodeSession).where(
            CodeSession.user_id == user_id,
            CodeSession.context_key == context_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
