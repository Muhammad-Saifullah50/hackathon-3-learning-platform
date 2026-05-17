"""Unit tests for LLM prompt constants."""

from src.llm.prompts import (
    get_code_review_agent_prompt,
    get_concept_agent_prompt,
    get_debug_agent_prompt,
    get_exercise_agent_prompt,
    get_progress_agent_prompt,
    get_triage_agent_prompt,
)


class TestPromptFunctions:
    """Tests for agent prompt functions."""

    def test_concept_agent_prompt_not_empty(self):
        prompt = get_concept_agent_prompt()
        assert len(prompt) > 0
        assert "Python" in prompt or "tutor" in prompt.lower()

    def test_code_review_agent_prompt_not_empty(self):
        prompt = get_code_review_agent_prompt()
        assert len(prompt) > 0
        assert "code" in prompt.lower()

    def test_debug_agent_prompt_not_empty(self):
        prompt = get_debug_agent_prompt()
        assert len(prompt) > 0
        assert "debug" in prompt.lower() or "error" in prompt.lower()

    def test_exercise_agent_prompt_not_empty(self):
        prompt = get_exercise_agent_prompt()
        assert len(prompt) > 0
        assert "exercise" in prompt.lower() or "challenge" in prompt.lower()

    def test_triage_agent_prompt_not_empty(self):
        prompt = get_triage_agent_prompt()
        assert len(prompt) > 0
        assert "route" in prompt.lower() or "triage" in prompt.lower()

    def test_progress_agent_prompt_not_empty(self):
        prompt = get_progress_agent_prompt()
        assert len(prompt) > 0
        assert "progress" in prompt.lower()

    def test_prompts_are_distinct(self):
        prompts = [
            get_concept_agent_prompt(),
            get_code_review_agent_prompt(),
            get_debug_agent_prompt(),
            get_exercise_agent_prompt(),
            get_triage_agent_prompt(),
            get_progress_agent_prompt(),
        ]
        unique_prompts = set(prompts)
        assert len(unique_prompts) == len(prompts), "All agent prompts should be distinct"

    def test_concept_prompt_includes_response_type_instruction(self):
        """Concept prompt must instruct the agent to use response_type='concept'."""
        prompt = get_concept_agent_prompt()
        assert "response_type" in prompt
        assert "concept" in prompt

    def test_code_review_prompt_includes_response_type_instruction(self):
        """Code review prompt must instruct the agent to use response_type='code_review'."""
        prompt = get_code_review_agent_prompt()
        assert "response_type" in prompt
        assert "code_review" in prompt

    def test_debug_prompt_includes_response_type_instruction(self):
        """Debug prompt must instruct the agent to use response_type='debug'."""
        prompt = get_debug_agent_prompt()
        assert "response_type" in prompt
        assert "debug" in prompt

    def test_exercise_prompt_includes_response_type_instruction(self):
        """Exercise prompt must instruct the agent to return structured JSON with response_type."""
        prompt = get_exercise_agent_prompt()
        assert "response_type" in prompt
        assert "exercise" in prompt

    def test_progress_prompt_includes_response_type_instruction(self):
        """Progress prompt must instruct the agent to use response_type='progress'."""
        prompt = get_progress_agent_prompt()
        assert "response_type" in prompt
        assert "progress" in prompt

    def test_exercise_prompt_requires_title_field(self):
        """Exercise prompt must specify 'title' as a required field."""
        prompt = get_exercise_agent_prompt()
        assert "title" in prompt

    def test_exercise_prompt_requires_difficulty_field(self):
        """Exercise prompt must specify 'difficulty' as a required field."""
        prompt = get_exercise_agent_prompt()
        assert "difficulty" in prompt

    def test_exercise_prompt_requires_starter_code(self):
        """Exercise prompt must specify 'starter_code' as a required field."""
        prompt = get_exercise_agent_prompt()
        assert "starter_code" in prompt

    def test_exercise_prompt_specifies_difficulty_levels(self):
        """Exercise prompt must specify beginner/intermediate/advanced difficulty levels."""
        prompt = get_exercise_agent_prompt()
        assert "beginner" in prompt
        assert "intermediate" in prompt
        assert "advanced" in prompt
