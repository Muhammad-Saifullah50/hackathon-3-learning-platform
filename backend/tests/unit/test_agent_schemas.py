"""Tests for agent schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.schemas.agents import (
    AgentChatRequest,
    ChatQuotaStatus,
    ChatSessionDetail,
    ChatSessionListItem,
    ConversationMessage,
    ExerciseGenerationRequest,
    ExerciseSubmissionRequest,
    HintAdvanceRequest,
    HintResponse,
    ProgressSummaryResponse,
    StreakInfo,
    TestCase,
    TestResult,
    TopicMastery,
)


class TestAgentChatRequest:
    def test_valid_request(self):
        req = AgentChatRequest(message="What is a list?")
        assert req.message == "What is a list?"
        assert req.topic is None

    def test_with_all_fields(self):
        req = AgentChatRequest(
            message="Fix this code",
            topic="loops",
            session_id="abc-123",
            code_snippet="for i in range(10): print(i)",
        )
        assert req.message == "Fix this code"
        assert req.code_snippet == "for i in range(10): print(i)"

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError):
            AgentChatRequest(message="")


class TestExerciseGenerationRequest:
    def test_valid_request(self):
        req = ExerciseGenerationRequest(topic="loops", difficulty="beginner")
        assert req.difficulty == "beginner"

    def test_invalid_difficulty_raises(self):
        with pytest.raises(ValidationError):
            ExerciseGenerationRequest(topic="test", difficulty="expert")


class TestExerciseSubmissionRequest:
    def test_valid_request(self):
        req = ExerciseSubmissionRequest(code="print('hello')")
        assert req.code == "print('hello')"

    def test_empty_code_raises(self):
        with pytest.raises(ValidationError):
            ExerciseSubmissionRequest(code="")


class TestHintAdvanceRequest:
    def test_default_request_solution(self):
        req = HintAdvanceRequest(session_id="abc-123")
        assert req.request_solution is False


class TestProgressSummaryResponse:
    def test_with_streak(self):
        resp = ProgressSummaryResponse(
            overall_mastery=75.0,
            topics=[],
            weak_areas=[],
            streak=StreakInfo(current_streak=5, longest_streak=10),
            recommendations=["Keep going!"],
            missing_components=[],
        )
        assert resp.streak.current_streak == 5


class TestTopicMastery:
    def test_valid(self):
        tm = TopicMastery(
            topic="loops",
            score=85.0,
            level="Proficient",
            component_breakdown={"exercises": 90},
        )
        assert tm.score == 85.0


class TestTestResult:
    def test_passed(self):
        tr = TestResult(test_index=0, passed=True)
        assert tr.passed is True
        assert tr.error_message is None

    def test_failed(self):
        tr = TestResult(test_index=1, passed=False, error_message="Expected 5, got 3")
        assert tr.passed is False


class TestAgentChatRequestNewFields:
    """Tests for new fields added to AgentChatRequest in this PR."""

    def test_execution_output_field(self):
        req = AgentChatRequest(
            message="Help me debug this",
            execution_output="Traceback (most recent call last):\n  ...",
        )
        assert req.execution_output == "Traceback (most recent call last):\n  ..."

    def test_surface_standalone(self):
        req = AgentChatRequest(message="What is a list?", surface="standalone")
        assert req.surface == "standalone"

    def test_surface_embedded(self):
        req = AgentChatRequest(message="Review my code", surface="embedded")
        assert req.surface == "embedded"

    def test_surface_none_default(self):
        req = AgentChatRequest(message="Hello")
        assert req.surface is None

    def test_surface_invalid_raises(self):
        with pytest.raises(ValidationError):
            AgentChatRequest(message="Hello", surface="fullscreen")

    def test_code_snippet_max_length(self):
        # Exactly 4096 chars is allowed
        long_code = "x" * 4096
        req = AgentChatRequest(message="Review this", code_snippet=long_code)
        assert len(req.code_snippet) == 4096

    def test_code_snippet_over_limit_raises(self):
        with pytest.raises(ValidationError):
            AgentChatRequest(message="Review this", code_snippet="x" * 4097)

    def test_execution_output_max_length(self):
        # Exactly 2000 chars is allowed
        long_output = "y" * 2000
        req = AgentChatRequest(message="Debug this", execution_output=long_output)
        assert len(req.execution_output) == 2000

    def test_execution_output_over_limit_raises(self):
        with pytest.raises(ValidationError):
            AgentChatRequest(message="Debug", execution_output="y" * 2001)

    def test_all_new_fields_together(self):
        req = AgentChatRequest(
            message="Check my code",
            code_snippet="print('hello')",
            execution_output="hello",
            surface="embedded",
        )
        assert req.code_snippet == "print('hello')"
        assert req.execution_output == "hello"
        assert req.surface == "embedded"


class TestConversationMessageAgentType:
    """Tests for the new agent_type field on ConversationMessage."""

    def test_agent_type_defaults_to_none(self):
        msg = ConversationMessage(
            role="user",
            content="Hello",
            timestamp=datetime.now(timezone.utc),
        )
        assert msg.agent_type is None

    def test_agent_type_set(self):
        msg = ConversationMessage(
            role="assistant",
            content="Here is the answer",
            timestamp=datetime.now(timezone.utc),
            agent_type="concepts",
        )
        assert msg.agent_type == "concepts"

    def test_agent_type_accepts_any_string(self):
        for agent in ["concepts", "debug", "code_review", "exercise", "progress", "none"]:
            msg = ConversationMessage(
                role="assistant",
                content="response",
                timestamp=datetime.now(timezone.utc),
                agent_type=agent,
            )
            assert msg.agent_type == agent


class TestChatSessionListItem:
    """Tests for the new ChatSessionListItem schema."""

    def _make_item(self, **overrides):
        now = datetime.now(timezone.utc)
        defaults = {
            "id": "abc-123",
            "title": "My session",
            "surface": "standalone",
            "message_count": 5,
            "last_message_at": now,
            "created_at": now,
        }
        defaults.update(overrides)
        return ChatSessionListItem(**defaults)

    def test_valid_item(self):
        item = self._make_item()
        assert item.id == "abc-123"
        assert item.title == "My session"
        assert item.message_count == 5

    def test_surface_can_be_none(self):
        item = self._make_item(surface=None)
        assert item.surface is None

    def test_surface_standalone(self):
        item = self._make_item(surface="standalone")
        assert item.surface == "standalone"

    def test_surface_embedded(self):
        item = self._make_item(surface="embedded")
        assert item.surface == "embedded"

    def test_missing_required_fields_raise(self):
        with pytest.raises(ValidationError):
            ChatSessionListItem(
                id="abc",
                title="title",
                # missing surface, message_count, last_message_at, created_at
            )

    def test_message_count_zero(self):
        item = self._make_item(message_count=0)
        assert item.message_count == 0


class TestChatSessionDetail:
    """Tests for the new ChatSessionDetail schema."""

    def _make_detail(self, **overrides):
        now = datetime.now(timezone.utc)
        defaults = {
            "id": "sess-456",
            "title": "Chat about loops",
            "surface": "embedded",
            "conversation_history": [],
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        return ChatSessionDetail(**defaults)

    def test_valid_detail(self):
        detail = self._make_detail()
        assert detail.id == "sess-456"
        assert detail.title == "Chat about loops"
        assert detail.conversation_history == []

    def test_with_conversation_history(self):
        now = datetime.now(timezone.utc)
        msg = ConversationMessage(
            role="user",
            content="What is a loop?",
            timestamp=now,
        )
        detail = self._make_detail(conversation_history=[msg])
        assert len(detail.conversation_history) == 1
        assert detail.conversation_history[0].role == "user"

    def test_surface_none(self):
        detail = self._make_detail(surface=None)
        assert detail.surface is None

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            ChatSessionDetail(id="x", title="t")


class TestChatQuotaStatus:
    """Tests for the new ChatQuotaStatus schema."""

    def _make_status(self, **overrides):
        now = datetime.now(timezone.utc)
        defaults = {
            "messages_sent_today": 3,
            "daily_limit": 15,
            "remaining": 12,
            "quota_reset_at": now,
        }
        defaults.update(overrides)
        return ChatQuotaStatus(**defaults)

    def test_valid_status(self):
        status = self._make_status()
        assert status.messages_sent_today == 3
        assert status.daily_limit == 15
        assert status.remaining == 12

    def test_zero_remaining(self):
        now = datetime.now(timezone.utc)
        status = self._make_status(messages_sent_today=15, remaining=0)
        assert status.remaining == 0

    def test_all_fields_required(self):
        with pytest.raises(ValidationError):
            ChatQuotaStatus(messages_sent_today=0, daily_limit=15)

    def test_quota_reset_at_is_datetime(self):
        status = self._make_status()
        assert isinstance(status.quota_reset_at, datetime)
