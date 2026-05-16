"""Tests for Progress Agent (SDK-based)."""

import pytest

from src.services.agents.agents import get_progress_agent
from src.services.agents.mastery import (
    COMPONENT_WEIGHTS,
    MASTERY_LEVELS,
    calculate_mastery_score,
    map_score_to_level,
)


class TestMasteryCalculation:
    def test_complete_data(self):
        components = {"exercises": 80.0, "quizzes": 70.0, "code_quality": 90.0, "streak": 100.0}
        score, breakdown = calculate_mastery_score(components)
        expected = 80.0 * 0.4 + 70.0 * 0.3 + 90.0 * 0.2 + 100.0 * 0.1
        assert score == round(expected, 2)

    def test_all_missing(self):
        score, breakdown = calculate_mastery_score({})
        assert score == 0.0
        assert len(breakdown["missing_components"]) == 4

    def test_only_exercises(self):
        score, breakdown = calculate_mastery_score({"exercises": 100.0})
        assert score == 100.0


class TestScoreToLevelMapping:
    def test_beginner(self):
        assert map_score_to_level(0) == "Beginner"
        assert map_score_to_level(40) == "Beginner"

    def test_learning(self):
        assert map_score_to_level(41) == "Learning"
        assert map_score_to_level(70) == "Learning"

    def test_proficient(self):
        assert map_score_to_level(71) == "Proficient"
        assert map_score_to_level(90) == "Proficient"

    def test_mastered(self):
        assert map_score_to_level(91) == "Mastered"
        assert map_score_to_level(100) == "Mastered"


class TestProgressAgent:
    def test_agent_name(self):
        agent = get_progress_agent()
        assert agent.name == "progress"

    def test_has_dynamic_instructions(self):
        agent = get_progress_agent()
        assert callable(agent.instructions)

    def test_has_model_settings(self):
        agent = get_progress_agent()
        assert agent.model_settings is not None
        assert agent.model_settings.temperature == 0.7

    def test_has_tools(self):
        agent = get_progress_agent()
        assert agent.tools is not None
        assert len(agent.tools) >= 1

    def test_component_weights_sum_to_100(self):
        assert sum(COMPONENT_WEIGHTS.values()) == 100

    def test_mastery_levels_cover_full_range(self):
        assert MASTERY_LEVELS["Beginner"][0] == 0
        assert MASTERY_LEVELS["Mastered"][1] == 100
