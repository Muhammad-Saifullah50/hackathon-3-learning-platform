"""Tests for Debug Agent (SDK-based)."""

import pytest

from src.services.agents.agents import get_debug_agent


class TestDebugAgent:
    def test_agent_name(self):
        agent = get_debug_agent()
        assert agent.name == "debug"

    def test_has_dynamic_instructions(self):
        agent = get_debug_agent()
        assert callable(agent.instructions)

    def test_has_model_settings(self):
        agent = get_debug_agent()
        assert agent.model_settings is not None
        assert agent.model_settings.temperature == 0.5

    def test_no_tools_by_default(self):
        agent = get_debug_agent()
        assert agent.tools is None or len(agent.tools) == 0
