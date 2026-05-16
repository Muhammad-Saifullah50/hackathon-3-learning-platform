"""Agent session repository.

CRUD operations for agent sessions.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent_session import AgentSession


class AgentSessionRepository:
    """Repository for agent session operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user_id: uuid.UUID) -> AgentSession:
        """
        Create a new agent session.

        Args:
            user_id: UUID of the user owning the session

        Returns:
            Created AgentSession
        """
        session_obj = AgentSession(
            user_id=user_id,
            status="active",
            conversation_history=[],
        )
        self.session.add(session_obj)
        await self.session.commit()
        await self.session.refresh(session_obj)
        return session_obj

    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """
        Get an agent session by ID.

        Args:
            session_id: UUID string of the session

        Returns:
            AgentSession if found, None otherwise
        """
        stmt = select(AgentSession).where(AgentSession.id == uuid.UUID(session_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_session(self, session_id: str, **kwargs: Any) -> Optional[AgentSession]:
        """
        Update an agent session.

        Args:
            session_id: UUID string of the session
            **kwargs: Fields to update (status, active_agent, conversation_history)

        Returns:
            Updated AgentSession if found, None otherwise
        """
        session_obj = await self.get_session(session_id)
        if not session_obj:
            return None

        for key, value in kwargs.items():
            if hasattr(session_obj, key):
                setattr(session_obj, key, value)

        await self.session.commit()
        await self.session.refresh(session_obj)
        return session_obj

    async def add_message_to_history(
        self, session_id: str, role: str, content: str, agent_type: str | None = None
    ) -> Optional[AgentSession]:
        """
        Add a message to the session conversation history.

        Args:
            session_id: UUID string of the session
            role: Message role ('user' or 'assistant')
            content: Message content
            agent_type: Optional agent name (e.g. 'concepts', 'debug') for assistant messages

        Returns:
            Updated AgentSession if found, None otherwise
        """
        session_obj = await self.get_session(session_id)
        if not session_obj:
            return None

        # Build a new list (not in-place mutation) so SQLAlchemy detects the change
        # on the JSONB column and includes it in the UPDATE statement.
        history = list(session_obj.conversation_history or [])
        entry: dict = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if agent_type is not None:
            entry["agent_type"] = agent_type
        history.append(entry)
        session_obj.conversation_history = history

        await self.session.commit()
        await self.session.refresh(session_obj)
        return session_obj

    async def list_sessions(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[AgentSession]:
        """Return sessions for user ordered by updated_at descending.

        Used by the session list endpoint (T012).
        """
        stmt = (
            select(AgentSession)
            .where(AgentSession.user_id == user_id)
            .order_by(AgentSession.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_session_detail(self, session_id: str) -> Optional[AgentSession]:
        """Return a session with full conversation history (alias of get_session)."""
        return await self.get_session(session_id)

    async def get_user_sessions(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[AgentSession]:
        """
        Get all sessions for a user, ordered by updated_at descending.

        Args:
            user_id: UUID of the user
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of AgentSession objects
        """
        stmt = (
            select(AgentSession)
            .where(AgentSession.user_id == user_id)
            .order_by(AgentSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
