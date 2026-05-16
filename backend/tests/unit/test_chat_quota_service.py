"""Tests for ChatQuotaService (src/services/chat_quota_service.py).

The check_and_get_remaining method uses PostgreSQL-specific pg_insert (ON CONFLICT),
so database-dependent tests mock the async session to avoid SQLite incompatibilities.
Pure logic (identifier format, get_status response shape) is tested directly.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.chat_quota_service import DAILY_LIMIT, ChatQuotaService


class TestChatQuotaServiceIdentifier:
    """Tests for the _identifier static method."""

    def test_identifier_format(self):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        identifier = ChatQuotaService._identifier(user_id)
        today = date.today().isoformat()
        expected = f"{user_id}:chat:{today}"
        assert identifier == expected

    def test_identifier_contains_user_id(self):
        user_id = uuid.uuid4()
        identifier = ChatQuotaService._identifier(user_id)
        assert str(user_id) in identifier

    def test_identifier_contains_chat(self):
        user_id = uuid.uuid4()
        identifier = ChatQuotaService._identifier(user_id)
        assert ":chat:" in identifier

    def test_identifier_contains_today_date(self):
        user_id = uuid.uuid4()
        identifier = ChatQuotaService._identifier(user_id)
        today = date.today().isoformat()
        assert today in identifier

    def test_identifier_different_users_different_identifiers(self):
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        assert ChatQuotaService._identifier(user1) != ChatQuotaService._identifier(user2)

    def test_daily_limit_constant(self):
        assert DAILY_LIMIT == 15

    def test_identifier_changes_per_day(self):
        """Verify identifier format includes date so it resets daily."""
        user_id = uuid.uuid4()
        identifier = ChatQuotaService._identifier(user_id)
        # Should have 3 colon-separated parts: uuid:chat:date
        parts = identifier.split(":")
        # UUID has 5 parts with hyphens, then 'chat', then date portions
        assert "chat" in parts
        # The last 3 parts should form the ISO date: YYYY-MM-DD
        date_part = parts[-1]
        # Verify it's a valid date format
        parsed = date.fromisoformat(date_part)
        assert parsed == date.today()


class TestChatQuotaServiceGetStatus:
    """Tests for get_status (read-only quota query)."""

    @pytest.mark.asyncio
    async def test_get_status_no_counter_returns_zero_used(self):
        """When no rate limit counter exists, messages_sent_today should be 0."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        status = await service.get_status(mock_db, user_id)

        assert status["messages_sent_today"] == 0
        assert status["daily_limit"] == DAILY_LIMIT
        assert status["remaining"] == DAILY_LIMIT

    @pytest.mark.asyncio
    async def test_get_status_with_counter_returns_used_count(self):
        """When a counter exists, messages_sent_today equals attempt_count."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_counter = MagicMock()
        mock_counter.attempt_count = 5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_counter

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        status = await service.get_status(mock_db, user_id)

        assert status["messages_sent_today"] == 5
        assert status["remaining"] == DAILY_LIMIT - 5
        assert status["daily_limit"] == DAILY_LIMIT

    @pytest.mark.asyncio
    async def test_get_status_at_limit_returns_zero_remaining(self):
        """When at daily limit, remaining should be 0."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_counter = MagicMock()
        mock_counter.attempt_count = DAILY_LIMIT

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_counter

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        status = await service.get_status(mock_db, user_id)

        assert status["remaining"] == 0
        assert status["messages_sent_today"] == DAILY_LIMIT

    @pytest.mark.asyncio
    async def test_get_status_over_limit_remaining_floored_to_zero(self):
        """remaining should never be negative (max(0, ...))."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_counter = MagicMock()
        mock_counter.attempt_count = DAILY_LIMIT + 5  # over limit

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_counter

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        status = await service.get_status(mock_db, user_id)

        assert status["remaining"] == 0

    @pytest.mark.asyncio
    async def test_get_status_returns_quota_reset_at(self):
        """quota_reset_at should be a datetime at midnight UTC tomorrow."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        status = await service.get_status(mock_db, user_id)
        reset_at = status["quota_reset_at"]

        assert isinstance(reset_at, datetime)
        # Should be tomorrow at midnight UTC
        now_utc = datetime.now(timezone.utc)
        tomorrow = now_utc.date().isoformat()
        # reset_at should be in the future (tomorrow or beyond)
        assert reset_at > now_utc

    @pytest.mark.asyncio
    async def test_get_status_does_not_commit(self):
        """get_status is read-only — must NOT commit to the database."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        await service.get_status(mock_db, user_id)

        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_status_status_keys_present(self):
        """Status dict must have all required keys."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        status = await service.get_status(mock_db, user_id)

        required_keys = {"messages_sent_today", "daily_limit", "remaining", "quota_reset_at"}
        assert required_keys == set(status.keys())


class TestCheckAndGetRemainingMocked:
    """Tests for check_and_get_remaining using mocked DB."""

    @pytest.mark.asyncio
    async def test_allowed_when_quota_not_exhausted(self):
        """Returns (True, remaining) when DB insert succeeds."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: 3  # attempt_count after increment

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        allowed, remaining = await service.check_and_get_remaining(mock_db, user_id)

        assert allowed is True
        assert remaining == DAILY_LIMIT - 3

    @pytest.mark.asyncio
    async def test_not_allowed_when_quota_exhausted(self):
        """Returns (False, 0) when DB returns no row (ON CONFLICT skipped update)."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # quota exceeded, no update

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        allowed, remaining = await service.check_and_get_remaining(mock_db, user_id)

        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_commits_on_success(self):
        """Should commit to DB when allowed."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: 1

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        await service.check_and_get_remaining(mock_db, user_id)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_commit_when_quota_exhausted(self):
        """Should NOT commit when quota is exhausted."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        await service.check_and_get_remaining(mock_db, user_id)

        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_remaining_floored_at_zero(self):
        """remaining should be max(0, DAILY_LIMIT - used)."""
        service = ChatQuotaService()
        user_id = uuid.uuid4()

        mock_row = MagicMock()
        # Simulate attempt_count = DAILY_LIMIT (at limit)
        mock_row.__getitem__ = lambda self, idx: DAILY_LIMIT

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        allowed, remaining = await service.check_and_get_remaining(mock_db, user_id)

        assert allowed is True
        assert remaining == 0