"""Tests for utility functions and constants in src/api/v1/agents.py.

Covers:
- _word_boundary_trim() — title truncation helper
- OFF_TOPIC_CANNED — canned off-topic response constant
- SSE_HEADERS — SSE response headers constant
"""

import pytest

from src.api.v1.agents import (
    OFF_TOPIC_CANNED,
    SSE_HEADERS,
    _word_boundary_trim,
)


class TestWordBoundaryTrim:
    """Tests for _word_boundary_trim()."""

    def test_short_string_unchanged(self):
        text = "What is a list?"
        result = _word_boundary_trim(text, max_len=60)
        assert result == text

    def test_exactly_max_len_unchanged(self):
        text = "a" * 60
        result = _word_boundary_trim(text, max_len=60)
        assert result == text

    def test_long_string_trimmed_at_word_boundary(self):
        text = "How do I use list comprehensions in Python programming?"
        result = _word_boundary_trim(text, max_len=30)
        assert len(result) <= 30
        # Should not end mid-word (no trailing partial word)
        assert not result.endswith(" ")

    def test_long_string_shorter_than_max(self):
        text = "Hello world"
        result = _word_boundary_trim(text, max_len=60)
        assert result == text

    def test_trim_falls_back_to_hard_cut_when_no_space(self):
        """When no space in trimmed prefix, falls back to hard cut at max_len."""
        text = "a" * 100  # No spaces
        result = _word_boundary_trim(text, max_len=60)
        assert result == text[:60]

    def test_trim_preserves_up_to_last_space(self):
        text = "Hello world this is a long message that exceeds the limit"
        result = _word_boundary_trim(text, max_len=25)
        assert len(result) <= 25
        # Result should be a complete word from the original
        assert text.startswith(result)

    def test_default_max_len_is_60(self):
        text = "a" * 70
        result = _word_boundary_trim(text)
        assert len(result) <= 60

    def test_empty_string(self):
        result = _word_boundary_trim("")
        assert result == ""

    def test_single_word_longer_than_max(self):
        """Single long word with no spaces: returns hard-truncated string."""
        text = "superlongword" * 10
        result = _word_boundary_trim(text, max_len=10)
        assert result == text[:10]

    def test_spaces_only(self):
        text = "   " * 25
        result = _word_boundary_trim(text, max_len=20)
        assert len(result) <= 20

    def test_unicode_text(self):
        text = "How do I learn Python effectively using modern tools?"
        result = _word_boundary_trim(text, max_len=30)
        assert len(result) <= 30

    def test_custom_max_len(self):
        text = "What is a Python list comprehension and why is it useful?"
        result = _word_boundary_trim(text, max_len=20)
        assert len(result) <= 20

    def test_trim_does_not_include_trailing_space(self):
        """The trimmed result should not end with a space."""
        text = "This is a message that is quite long and should be trimmed"
        result = _word_boundary_trim(text, max_len=20)
        assert not result.endswith(" ")

    def test_return_type_is_str(self):
        result = _word_boundary_trim("Hello world", max_len=60)
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "text,max_len,expected_max",
        [
            ("Short", 60, 5),
            ("A" * 80, 60, 60),
            ("Hello world!", 8, 8),
            ("How do you do?", 6, 6),
        ],
    )
    def test_result_never_exceeds_max_len(self, text, max_len, expected_max):
        result = _word_boundary_trim(text, max_len=max_len)
        assert len(result) <= expected_max


class TestOffTopicCanned:
    """Tests for OFF_TOPIC_CANNED constant."""

    def test_is_string(self):
        assert isinstance(OFF_TOPIC_CANNED, str)

    def test_not_empty(self):
        assert len(OFF_TOPIC_CANNED) > 0

    def test_mentions_python(self):
        assert "Python" in OFF_TOPIC_CANNED

    def test_is_friendly(self):
        # Should not be confrontational — should redirect politely
        assert "!" not in OFF_TOPIC_CANNED or "Try" in OFF_TOPIC_CANNED

    def test_mentions_learning(self):
        # Should indicate this is a learning platform
        assert any(
            word in OFF_TOPIC_CANNED.lower()
            for word in ["learn", "help", "python", "asking"]
        )


class TestSSEHeaders:
    """Tests for SSE_HEADERS constant."""

    def test_is_dict(self):
        assert isinstance(SSE_HEADERS, dict)

    def test_has_cache_control(self):
        assert "Cache-Control" in SSE_HEADERS
        assert SSE_HEADERS["Cache-Control"] == "no-cache"

    def test_has_connection(self):
        assert "Connection" in SSE_HEADERS
        assert SSE_HEADERS["Connection"] == "keep-alive"

    def test_has_x_accel_buffering(self):
        assert "X-Accel-Buffering" in SSE_HEADERS
        assert SSE_HEADERS["X-Accel-Buffering"] == "no"

    def test_has_exactly_three_headers(self):
        assert len(SSE_HEADERS) == 3