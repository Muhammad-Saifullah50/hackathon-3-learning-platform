"""Tests for SDK-based agent definitions."""

import uuid

import pytest

from src.services.agents.agents import (
    get_code_review_agent,
    get_concepts_agent,
    get_debug_agent,
    get_exercise_agent,
    get_progress_agent,
    get_triage_agent,
)
from src.services.agents.context import LearnPyByAIContext


class TestLearnPyByAIContext:
    """Tests for the SDK context object."""

    def test_minimal_context(self):
        user_id = uuid.uuid4()
        ctx = LearnPyByAIContext(user_id=user_id)
        assert ctx.user_id == user_id
        assert ctx.session_id is None
        assert ctx.db is None
        assert ctx.topic is None
        assert ctx.code_snippet is None
        assert ctx.level is None
        assert ctx.intent is None

    def test_full_context(self):
        user_id = uuid.uuid4()
        session_id = uuid.uuid4()
        ctx = LearnPyByAIContext(
            user_id=user_id,
            session_id=session_id,
            topic="loops",
            code_snippet="for i in range(10): pass",
            level="beginner",
            intent="concept-explanation",
            extra={"key": "value"},
        )
        assert ctx.session_id == session_id
        assert ctx.topic == "loops"
        assert ctx.level == "beginner"
        assert ctx.extra == {"key": "value"}


class TestSDKAgentDefinitions:
    """Tests that SDK agents are properly defined."""

    def test_triage_agent_has_handoffs(self):
        agent = get_triage_agent()
        assert agent.name == "triage"
        assert agent.handoffs is not None
        assert len(agent.handoffs) == 5

    def test_concepts_agent_has_dynamic_instructions(self):
        agent = get_concepts_agent()
        assert agent.name == "concepts"
        assert callable(agent.instructions)

    def test_debug_agent_has_dynamic_instructions(self):
        agent = get_debug_agent()
        assert agent.name == "debug"
        assert callable(agent.instructions)

    def test_code_review_agent_has_tools(self):
        agent = get_code_review_agent()
        assert agent.name == "code_review"
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_exercise_agent_has_tools(self):
        agent = get_exercise_agent()
        assert agent.name == "exercise"
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_progress_agent_has_tools(self):
        agent = get_progress_agent()
        assert agent.name == "progress"
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_all_agents_have_model_settings(self):
        agents = [
            get_triage_agent(),
            get_concepts_agent(),
            get_debug_agent(),
            get_code_review_agent(),
            get_exercise_agent(),
            get_progress_agent(),
        ]
        for agent in agents:
            assert agent.model_settings is not None


class TestTriageAgentGuardrails:
    """Tests for the triage agent's new guardrails configuration."""

    def test_triage_agent_has_input_guardrails(self):
        """Triage agent must have input guardrails for off-topic detection."""
        agent = get_triage_agent()
        assert agent.input_guardrails is not None
        assert len(agent.input_guardrails) >= 1

    def test_triage_agent_guardrail_is_off_topic(self):
        """The triage guardrail must be the off_topic_guardrail."""
        from src.services.agents.guardrails import off_topic_guardrail
        agent = get_triage_agent()
        assert off_topic_guardrail in agent.input_guardrails

    def test_all_specialist_agents_have_guardrails(self):
        """All specialist agents should have the off-topic guardrail."""
        from src.services.agents.guardrails import off_topic_guardrail
        agents = [
            get_concepts_agent(),
            get_debug_agent(),
            get_code_review_agent(),
            get_exercise_agent(),
            get_progress_agent(),
        ]
        for agent in agents:
            assert agent.input_guardrails is not None, (
                f"{agent.name} is missing input_guardrails"
            )
            assert off_topic_guardrail in agent.input_guardrails, (
                f"{agent.name} is missing off_topic_guardrail"
            )

    def test_all_specialist_agents_have_output_type(self):
        """All specialist agents should have a structured output_type."""
        from src.schemas.agent_responses import (
            CodeReviewResponse,
            ConceptResponse,
            DebugResponse,
            ExerciseAgentResponse,
            ProgressAgentResponse,
        )
        expected_output_types = {
            "concepts": ConceptResponse,
            "debug": DebugResponse,
            "code_review": CodeReviewResponse,
            "exercise": ExerciseAgentResponse,
            "progress": ProgressAgentResponse,
        }
        agents = [
            get_concepts_agent(),
            get_debug_agent(),
            get_code_review_agent(),
            get_exercise_agent(),
            get_progress_agent(),
        ]
        for agent in agents:
            expected = expected_output_types.get(agent.name)
            assert agent.output_type is expected, (
                f"{agent.name}: expected output_type={expected}, got {agent.output_type}"
            )
