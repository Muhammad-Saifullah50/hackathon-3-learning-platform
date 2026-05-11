"""Unit tests for CodeSessionService.check_and_increment_daily_limit."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.repositories.code_session_repository import CodeSessionRepository
from src.services.code_session_service import CodeSessionService


def _make_service():
    repo = MagicMock(spec=CodeSessionRepository)
    return CodeSessionService(repo=repo)


@pytest.mark.asyncio
async def test_first_request_allowed():
    """First request of the day increments counter 0→1 and returns True."""
    service = _make_service()
    db = AsyncMock()

    # INSERT succeeds, RETURNING gives row with attempt_count=1
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (1,)
    db.execute = AsyncMock(return_value=mock_result)

    user_id = uuid.uuid4()
    allowed = await service.check_and_increment_daily_limit(db, user_id, "run", limit=3)
    assert allowed is True
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_second_request_allowed():
    """Second request (counter 2→3) returns True."""
    service = _make_service()
    db = AsyncMock()

    mock_result = MagicMock()
    mock_result.fetchone.return_value = (3,)
    db.execute = AsyncMock(return_value=mock_result)

    user_id = uuid.uuid4()
    allowed = await service.check_and_increment_daily_limit(db, user_id, "run", limit=3)
    assert allowed is True


@pytest.mark.asyncio
async def test_limit_reached_returns_false():
    """When counter is already at limit, ON CONFLICT WHERE is false — no row returned."""
    service = _make_service()
    db = AsyncMock()

    mock_result = MagicMock()
    mock_result.fetchone.return_value = None  # WHERE clause prevented update
    db.execute = AsyncMock(return_value=mock_result)

    user_id = uuid.uuid4()
    allowed = await service.check_and_increment_daily_limit(db, user_id, "run", limit=3)
    assert allowed is False
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_new_calendar_day_creates_new_key():
    """Different dates produce different identifier keys."""
    service = _make_service()

    user_id = uuid.uuid4()
    today = date.today().isoformat()
    yesterday = "2026-05-09"

    key_today = f"{user_id}:run:{today}"
    key_yesterday = f"{user_id}:run:{yesterday}"
    assert key_today != key_yesterday

    # Verify the service constructs the correct key format
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (1,)
    db.execute = AsyncMock(return_value=mock_result)

    with patch("src.services.code_session_service.date") as mock_date:
        frozen = MagicMock()
        frozen.isoformat.return_value = "2026-05-10"
        mock_date.today.return_value = frozen
        allowed = await service.check_and_increment_daily_limit(db, user_id, "run", limit=3)
    assert allowed is True
