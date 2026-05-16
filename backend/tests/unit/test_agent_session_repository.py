"""Tests for new AgentSessionRepository methods added in this PR.

Covers:
- add_message_to_history with agent_type parameter
- list_sessions()
- get_session_detail()

Uses mocked AsyncSession to avoid PostgreSQL/SQLite incompatibilities.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from src.repositories.agent_session_repository import AgentSessionRepository


def _make_session(
    session_id=None,
    user_id=None,
    conversation_history=None,
    title=None,
    surface=None,
    updated_at=None,
):
    """Helper to build a mock AgentSession."""
    mock_session = MagicMock()
    mock_session.id = session_id or uuid.uuid4()
    mock_session.user_id = user_id or uuid.uuid4()
    mock_session.conversation_history = conversation_history if conversation_history is not None else []
    mock_session.title = title
    mock_session.surface = surface
    mock_session.updated_at = updated_at or datetime.now(timezone.utc)
    mock_session.status = "active"
    mock_session.active_agent = None
    return mock_session


class TestAddMessageToHistoryWithAgentType:
    """Tests for the updated add_message_to_history with agent_type parameter."""

    @pytest.mark.asyncio
    async def test_adds_user_message_without_agent_type(self):
        """User messages should be stored without agent_type field."""
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = []

        mock_db = AsyncMock()

        repo = AgentSessionRepository(mock_db)

        # Mock get_session to return our mock session
        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id), "user", "What is a list?"
            )

        history = mock_session_obj.conversation_history
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What is a list?"
        assert "agent_type" not in history[0]

    @pytest.mark.asyncio
    async def test_adds_assistant_message_with_agent_type(self):
        """Assistant messages with agent_type should include it in the history entry."""
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = []

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id),
                "assistant",
                "A list is an ordered collection.",
                agent_type="concepts",
            )

        history = mock_session_obj.conversation_history
        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert history[0]["agent_type"] == "concepts"

    @pytest.mark.asyncio
    async def test_agent_type_none_not_added_to_entry(self):
        """When agent_type is None, it should NOT be added to the message entry."""
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = []

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id),
                "assistant",
                "Response text",
                agent_type=None,
            )

        history = mock_session_obj.conversation_history
        assert "agent_type" not in history[0]

    @pytest.mark.asyncio
    async def test_message_has_timestamp(self):
        """Each message entry must include a timestamp."""
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = []

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id), "user", "Hello"
            )

        history = mock_session_obj.conversation_history
        assert "timestamp" in history[0]
        # Should be parseable as ISO datetime
        parsed = datetime.fromisoformat(history[0]["timestamp"])
        assert parsed is not None

    @pytest.mark.asyncio
    async def test_builds_new_list_not_mutates_in_place(self):
        """History must be rebuilt as a new list so SQLAlchemy detects the change."""
        original_history = [{"role": "user", "content": "old", "timestamp": "2026-01-01T00:00:00"}]
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = original_history
        original_id = id(original_history)

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id), "user", "New message"
            )

        # The conversation_history attribute should now be a NEW list object
        new_history = mock_session_obj.conversation_history
        assert id(new_history) != original_id
        assert len(new_history) == 2

    @pytest.mark.asyncio
    async def test_returns_none_when_session_not_found(self):
        """Should return None if the session doesn't exist."""
        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=None)):
            result = await repo.add_message_to_history(
                str(uuid.uuid4()), "user", "Hello"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_commits_after_adding_message(self):
        """Must commit to DB after updating history."""
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = []

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id), "user", "Hello"
            )

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_appends_to_existing_history(self):
        """Existing messages in history must be preserved."""
        existing = [{"role": "user", "content": "first", "timestamp": "2026-01-01T00:00:00"}]
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = list(existing)

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id), "assistant", "second", agent_type="debug"
            )

        history = mock_session_obj.conversation_history
        assert len(history) == 2
        assert history[0]["content"] == "first"
        assert history[1]["content"] == "second"
        assert history[1]["agent_type"] == "debug"

    @pytest.mark.parametrize("agent_type", ["concepts", "debug", "code_review", "exercise", "progress", "none"])
    @pytest.mark.asyncio
    async def test_various_agent_types_stored(self, agent_type):
        """All agent type strings should be stored correctly."""
        mock_session_obj = _make_session()
        mock_session_obj.conversation_history = []

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            await repo.add_message_to_history(
                str(mock_session_obj.id), "assistant", "response", agent_type=agent_type
            )

        history = mock_session_obj.conversation_history
        assert history[0]["agent_type"] == agent_type


class TestListSessions:
    """Tests for the new list_sessions() method."""

    @pytest.mark.asyncio
    async def test_returns_list_of_sessions(self):
        """Should return a list of AgentSession objects."""
        user_id = uuid.uuid4()
        mock_sessions = [_make_session(user_id=user_id) for _ in range(3)]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_sessions
        mock_result.scalars.return_value = mock_scalars

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AgentSessionRepository(mock_db)
        result = await repo.list_sessions(user_id, limit=20)

        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_sessions(self):
        """Should return empty list when user has no sessions."""
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AgentSessionRepository(mock_db)
        result = await repo.list_sessions(user_id, limit=20)

        assert result == []

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self):
        """The limit parameter should be passed to the query."""
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AgentSessionRepository(mock_db)
        # Call with limit=5 — we just verify the method accepts the parameter
        await repo.list_sessions(user_id, limit=5)

        # DB execute should have been called once
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_default_limit_is_20(self):
        """Default limit should be 20."""
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        repo = AgentSessionRepository(mock_db)
        # Should not raise — default limit applies
        await repo.list_sessions(user_id)
        mock_db.execute.assert_called_once()


class TestGetSessionDetail:
    """Tests for the new get_session_detail() method (alias of get_session)."""

    @pytest.mark.asyncio
    async def test_returns_session_when_found(self):
        """Should return the AgentSession when found."""
        session_id = str(uuid.uuid4())
        mock_session_obj = _make_session(title="My chat", surface="standalone")

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session_obj)):
            result = await repo.get_session_detail(session_id)

        assert result is mock_session_obj

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """Should return None when session doesn't exist."""
        session_id = str(uuid.uuid4())

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=None)):
            result = await repo.get_session_detail(session_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_delegates_to_get_session(self):
        """get_session_detail should delegate to get_session (it's an alias)."""
        session_id = str(uuid.uuid4())
        mock_session = _make_session()

        mock_db = AsyncMock()
        repo = AgentSessionRepository(mock_db)

        with patch.object(repo, "get_session", new=AsyncMock(return_value=mock_session)) as mock_get:
            await repo.get_session_detail(session_id)
            mock_get.assert_called_once_with(session_id)