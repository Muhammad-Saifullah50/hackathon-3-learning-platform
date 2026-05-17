"""Tests for Exercise Agent (SDK-based)."""

import pytest

from src.services.agents.agents import get_exercise_agent


class TestExerciseAgent:
    def test_agent_name(self):
        agent = get_exercise_agent()
        assert agent.name == "exercise"

    def test_has_dynamic_instructions(self):
        agent = get_exercise_agent()
        assert callable(agent.instructions)

    def test_has_model_settings(self):
        agent = get_exercise_agent()
        assert agent.model_settings is not None
        assert agent.model_settings.temperature == 0.1

    def test_has_exercise_tool(self):
        agent = get_exercise_agent()
        assert agent.tools is not None
        assert len(agent.tools) >= 1
        tool_names = [t.name for t in agent.tools]
        assert "get_exercise" in tool_names

    def test_output_type_is_exercise_agent_response(self):
        """Agent must have ExerciseAgentResponse as output_type."""
        from src.schemas.agent_responses import ExerciseAgentResponse
        agent = get_exercise_agent()
        assert agent.output_type is ExerciseAgentResponse

    def test_has_input_guardrails(self):
        """Agent must have off-topic guardrail configured."""
        agent = get_exercise_agent()
        assert agent.input_guardrails is not None
        assert len(agent.input_guardrails) >= 1

    def test_guardrail_is_off_topic_guardrail(self):
        """The input guardrail should be the off_topic_guardrail."""
        from src.services.agents.guardrails import off_topic_guardrail
        agent = get_exercise_agent()
        assert off_topic_guardrail in agent.input_guardrails

    def test_no_max_tokens(self):
        """max_tokens should not be set (removed in this PR)."""
        agent = get_exercise_agent()
        assert agent.model_settings.max_tokens is None

    def test_low_temperature_for_determinism(self):
        """Exercise agent should use low temperature for consistent output format."""
        agent = get_exercise_agent()
        assert agent.model_settings.temperature <= 0.2
