"""Tests for Code Review Agent (SDK-based)."""

import pytest

from src.services.agents.agents import get_code_review_agent


class TestCodeReviewAgent:
    def test_agent_name(self):
        agent = get_code_review_agent()
        assert agent.name == "code_review"

    def test_has_dynamic_instructions(self):
        agent = get_code_review_agent()
        assert callable(agent.instructions)

    def test_has_model_settings(self):
        agent = get_code_review_agent()
        assert agent.model_settings is not None
        assert agent.model_settings.temperature == 0.5

    def test_has_static_analysis_tool(self):
        agent = get_code_review_agent()
        assert agent.tools is not None
        assert len(agent.tools) >= 1
        tool_names = [t.name for t in agent.tools]
        assert "run_static_analysis" in tool_names

    def test_output_type_is_code_review_response(self):
        """Agent must have CodeReviewResponse as output_type for structured output."""
        from src.schemas.agent_responses import CodeReviewResponse
        agent = get_code_review_agent()
        assert agent.output_type is CodeReviewResponse

    def test_has_input_guardrails(self):
        """Agent must have off-topic guardrail configured."""
        agent = get_code_review_agent()
        assert agent.input_guardrails is not None
        assert len(agent.input_guardrails) >= 1

    def test_guardrail_is_off_topic_guardrail(self):
        """The input guardrail should be the off_topic_guardrail."""
        from src.services.agents.guardrails import off_topic_guardrail
        agent = get_code_review_agent()
        assert off_topic_guardrail in agent.input_guardrails

    def test_no_max_tokens(self):
        """max_tokens should not be set (removed in this PR)."""
        agent = get_code_review_agent()
        assert agent.model_settings.max_tokens is None
