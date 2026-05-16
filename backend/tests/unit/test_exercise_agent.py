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
