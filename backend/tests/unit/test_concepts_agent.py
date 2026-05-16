"""Tests for Concepts Agent (SDK-based)."""

import pytest

from src.services.agents.agents import get_concepts_agent
from src.services.agents.context import LearnFlowContext


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
