"""Tests for deterministic triage routing."""

import pytest

from src.services.agents.triage import (
    INTENT_PATTERNS,
    INTENT_TO_AGENT,
    TriageResult,
    classify_intent,
    get_agent_for_intent,
)


class TestTriageAgent:
    """Tests for the deterministic intent classifier."""

    @pytest.mark.parametrize(
        "message,expected",
        [
            ("What is a list comprehension in Python?", "concept-explanation"),
            ("Can you explain how decorators work?", "concept-explanation"),
            ("How does the garbage collector work?", "concept-explanation"),
            ("Define what a generator is", "concept-explanation"),
            ("What are Python modules?", "concept-explanation"),
            ("I am getting a TypeError in my code", "code-debug"),
            ("My code is not working, can you help?", "code-debug"),
            ("Traceback: IndexError: list index out of range", "code-debug"),
            ("How do I fix this bug?", "code-debug"),
            ("This function is broken, it gives wrong output", "code-debug"),
            ("Can you review my code?", "code-review"),
            ("How can I improve this function?", "code-review"),
            ("Is my code PEP 8 compliant?", "code-review"),
            ("Should I refactor this class?", "code-review"),
            ("Give me some practice exercises on loops", "exercise-generation"),
            ("I want a coding challenge on recursion", "exercise-generation"),
            ("Test me on dictionaries", "exercise-generation"),
            ("How am I doing in this course?", "progress-summary"),
            ("What is my mastery level in functions?", "progress-summary"),
            ("What is my current streak?", "progress-summary"),
            ("Hello, how are you?", "general"),
            ("Hi there!", "general"),
            ("WHAT IS A PYTHON LIST?", "concept-explanation"),
            ("I have an ERROR in my Code", "code-debug"),
        ],
    )
    def test_classify_intent(self, message, expected):
        result = classify_intent(message)
        assert result.intent == expected, f'"{message}" -> {result.intent} (expected {expected})'

    def test_confidence_capped_at_095(self):
        result = classify_intent(
            "What is explain how does what are what do define meaning of understand concept how do what does"
        )
        assert result.confidence <= 0.95

    def test_confidence_above_threshold(self):
        result = classify_intent("What is a Python list and how does it work?")
        assert result.confidence >= 0.08

    def test_matched_patterns_included(self):
        result = classify_intent("What is a list?")
        assert len(result.matched_patterns) > 0
        assert isinstance(result.matched_patterns[0], str)

    def test_no_matched_patterns_for_general(self):
        result = classify_intent("Hello world")
        assert result.matched_patterns == []
        assert result.confidence == 0.0

    @pytest.mark.parametrize(
        "intent,agent",
        [
            ("concept-explanation", "concepts"),
            ("code-debug", "debug"),
            ("code-review", "code_review"),
            ("exercise-generation", "exercise"),
            ("progress-summary", "progress"),
            ("general", "triage"),
        ],
    )
    def test_get_agent_for_intent(self, intent, agent):
        assert get_agent_for_intent(intent) == agent

    def test_get_agent_for_intent_unknown_defaults_triage(self):
        assert get_agent_for_intent("unknown-intent") == "triage"

    def test_triage_result_dataclass(self):
        result = TriageResult(intent="test", confidence=0.5, matched_patterns=["pattern1"])
        assert result.intent == "test"
        assert result.confidence == 0.5
        assert result.matched_patterns == ["pattern1"]

    def test_triage_result_default_matched_patterns(self):
        result = TriageResult(intent="test", confidence=0.5)
        assert result.matched_patterns == []

    def test_all_intent_categories_have_patterns(self):
        for intent in INTENT_PATTERNS:
            assert len(INTENT_PATTERNS[intent]) > 0

    def test_all_intents_mapped_to_agents(self):
        for intent in INTENT_PATTERNS:
            assert intent in INTENT_TO_AGENT
        assert "general" in INTENT_TO_AGENT


class TestIsOffTopic:
    """Tests for the _is_off_topic helper function."""

    def test_import(self):
        from src.services.agents.triage import _is_off_topic
        assert callable(_is_off_topic)

    @pytest.mark.parametrize(
        "message",
        [
            "Write me a poem about summer",
            "What is the recipe for lasagna?",
            "Tell me about the weather in Paris",
            "Who won the football game last night?",
            "What is the history of France?",
            "Tell me about the geography of Africa",
            "What movies are popular right now?",
            "Can you recommend some music songs?",
            "What are the latest politics news?",
            "Tell me a joke",
            "What is my horoscope today?",
            "How big is the ocean?",
            "Tell me about basketball",
            "What happened during the war?",
        ],
    )
    def test_off_topic_messages_detected(self, message):
        from src.services.agents.triage import _is_off_topic
        assert _is_off_topic(message) is True, f"Expected off-topic: '{message}'"

    @pytest.mark.parametrize(
        "message",
        [
            "What is a Python list?",
            "How do I fix this bug in my code?",
            "Can you review my function?",
            "Give me a practice exercise on loops",
            "How am I doing with my progress?",
            "What is a variable in Python?",
            "How do I import a module?",
            "Explain how classes work",
            "What is a Python program?",
            "def my_function(): pass — what does def mean?",
        ],
    )
    def test_on_topic_messages_not_flagged(self, message):
        from src.services.agents.triage import _is_off_topic
        assert _is_off_topic(message) is False, f"Expected on-topic: '{message}'"

    def test_off_topic_with_python_anchor_not_flagged(self):
        """A message with an off-topic word but Python context should pass through."""
        from src.services.agents.triage import _is_off_topic
        # "history" is off-topic but "python" anchors it
        assert _is_off_topic("What is the history of Python programming language?") is False

    def test_off_topic_with_code_anchor_not_flagged(self):
        from src.services.agents.triage import _is_off_topic
        # "movie" is off-topic but "code" anchors it
        assert _is_off_topic("My code is not working like in the movie tutorials") is False

    def test_plain_greeting_not_off_topic(self):
        from src.services.agents.triage import _is_off_topic
        # No off-topic keyword and no Python keyword — not off-topic (just general)
        assert _is_off_topic("Hello, how are you?") is False

    def test_empty_string_not_off_topic(self):
        from src.services.agents.triage import _is_off_topic
        assert _is_off_topic("") is False

    def test_case_insensitive_off_topic(self):
        from src.services.agents.triage import _is_off_topic
        assert _is_off_topic("WRITE ME A POEM ABOUT NATURE") is True

    def test_case_insensitive_python_anchor(self):
        from src.services.agents.triage import _is_off_topic
        assert _is_off_topic("Write me a poem in PYTHON") is False


class TestOffTopicClassification:
    """Tests for classify_intent returning off_topic intent."""

    def test_off_topic_message_returns_off_topic_intent(self):
        result = classify_intent("Write me a poem about roses")
        assert result.intent == "off_topic"

    def test_off_topic_has_high_confidence(self):
        result = classify_intent("What is the weather like today?")
        assert result.intent == "off_topic"
        assert result.confidence == 0.95

    def test_off_topic_has_empty_matched_patterns(self):
        result = classify_intent("Tell me about basketball scores")
        assert result.intent == "off_topic"
        assert result.matched_patterns == []

    def test_python_message_not_off_topic(self):
        result = classify_intent("What is a list in Python?")
        assert result.intent != "off_topic"

    def test_off_topic_intent_maps_to_none_agent(self):
        from src.services.agents.triage import get_agent_for_intent
        assert get_agent_for_intent("off_topic") == "none"

    def test_off_topic_in_intent_to_agent_map(self):
        from src.services.agents.triage import INTENT_TO_AGENT
        assert "off_topic" in INTENT_TO_AGENT
        assert INTENT_TO_AGENT["off_topic"] == "none"

    @pytest.mark.parametrize(
        "message,expected_intent",
        [
            ("Write me a poem", "off_topic"),
            ("What is a recipe?", "off_topic"),
            ("Tell me about soccer", "off_topic"),
            ("What is my horoscope?", "off_topic"),
            # Python messages should NOT be off_topic
            ("What is Python?", "concept-explanation"),
            ("Fix this bug in my code", "code-debug"),
        ],
    )
    def test_off_topic_classification_parametrized(self, message, expected_intent):
        result = classify_intent(message)
        assert result.intent == expected_intent, (
            f"'{message}' -> {result.intent} (expected {expected_intent})"
        )


class TestOffTopicPatterns:
    """Tests verifying the OFF_TOPIC_PATTERNS and PYTHON_ANCHOR_PATTERNS constants."""

    def test_off_topic_patterns_is_list(self):
        from src.services.agents.triage import OFF_TOPIC_PATTERNS
        assert isinstance(OFF_TOPIC_PATTERNS, list)
        assert len(OFF_TOPIC_PATTERNS) > 0

    def test_python_anchor_patterns_is_list(self):
        from src.services.agents.triage import PYTHON_ANCHOR_PATTERNS
        assert isinstance(PYTHON_ANCHOR_PATTERNS, list)
        assert len(PYTHON_ANCHOR_PATTERNS) > 0

    def test_all_off_topic_patterns_are_valid_regex(self):
        import re
        from src.services.agents.triage import OFF_TOPIC_PATTERNS
        for pattern in OFF_TOPIC_PATTERNS:
            # Should not raise
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None

    def test_all_python_anchor_patterns_are_valid_regex(self):
        import re
        from src.services.agents.triage import PYTHON_ANCHOR_PATTERNS
        for pattern in PYTHON_ANCHOR_PATTERNS:
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None

    def test_python_anchor_includes_python_keyword(self):
        from src.services.agents.triage import PYTHON_ANCHOR_PATTERNS
        assert any("python" in p.lower() for p in PYTHON_ANCHOR_PATTERNS)

    def test_python_anchor_includes_code_keyword(self):
        from src.services.agents.triage import PYTHON_ANCHOR_PATTERNS
        assert any("code" in p.lower() for p in PYTHON_ANCHOR_PATTERNS)
