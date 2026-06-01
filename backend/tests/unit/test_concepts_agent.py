"""Tests for Concepts Agent (SDK-based)."""

import pytest

from src.schemas.agent_responses import ConceptResponse
from src.services.agents.agents import get_concepts_agent
from src.services.agents.context import LearnPyByAIContext


class TestConceptsAgent:
    def test_agent_name(self):
        agent = get_concepts_agent()
        assert agent.name == "concepts"

    def test_has_dynamic_instructions(self):
        agent = get_concepts_agent()
        assert callable(agent.instructions)

    def test_has_model_settings(self):
        agent = get_concepts_agent()
        assert agent.model_settings is not None
        assert agent.model_settings.temperature == 0.7

    def test_no_tools_by_default(self):
        agent = get_concepts_agent()
        assert agent.tools is None or len(agent.tools) == 0

    def test_output_type_is_concept_response(self):
        """Agent must have ConceptResponse as output_type for structured output."""
        agent = get_concepts_agent()
        assert agent.output_type is ConceptResponse

    def test_has_input_guardrails(self):
        """Agent must have off-topic guardrail configured."""
        agent = get_concepts_agent()
        assert agent.input_guardrails is not None
        assert len(agent.input_guardrails) >= 1

    def test_guardrail_is_off_topic_guardrail(self):
        """The input guardrail should be the off_topic_guardrail."""
        from src.services.agents.guardrails import off_topic_guardrail
        agent = get_concepts_agent()
        assert off_topic_guardrail in agent.input_guardrails

    def test_no_max_tokens(self):
        """max_tokens should not be set (removed in this PR)."""
        agent = get_concepts_agent()
        assert agent.model_settings.max_tokens is None
