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
