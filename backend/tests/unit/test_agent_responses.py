"""Tests for structured agent response schemas (src/schemas/agent_responses.py).

These schemas are used as output_type for specialist agents so the OpenAI
Agents SDK can coerce LLM output into typed Pydantic models.
"""

import pytest
from pydantic import ValidationError

from src.schemas.agent_responses import (
    CodeBlock,
    CodeReviewResponse,
    ConceptResponse,
    DebugResponse,
    ExerciseAgentResponse,
    IssueItem,
    ProgressAgentResponse,
    TutorResponse,
)


class TestCodeBlock:
    """Tests for CodeBlock model."""

    def test_minimal_valid(self):
        block = CodeBlock(code="print('hello')")
        assert block.code == "print('hello')"
        assert block.language == "python"
        assert block.caption is None

    def test_custom_language(self):
        block = CodeBlock(code="console.log('hi')", language="javascript")
        assert block.language == "javascript"

    def test_with_caption(self):
        block = CodeBlock(code="x = 1", caption="Assign x")
        assert block.caption == "Assign x"

    def test_empty_code_allowed(self):
        block = CodeBlock(code="")
        assert block.code == ""

    def test_missing_code_raises(self):
        with pytest.raises(ValidationError):
            CodeBlock()

    def test_multiline_code(self):
        code = "def foo():\n    return 42\n"
        block = CodeBlock(code=code, caption="Example function")
        assert block.code == code


class TestIssueItem:
    """Tests for IssueItem model."""

    def test_error_severity(self):
        issue = IssueItem(severity="error", message="Undefined variable 'x'")
        assert issue.severity == "error"
        assert issue.message == "Undefined variable 'x'"
        assert issue.line_ref is None

    def test_warning_severity(self):
        issue = IssueItem(severity="warning", message="Unused import os")
        assert issue.severity == "warning"

    def test_suggestion_severity(self):
        issue = IssueItem(severity="suggestion", message="Consider using list comprehension")
        assert issue.severity == "suggestion"

    def test_with_line_ref(self):
        issue = IssueItem(severity="error", message="SyntaxError", line_ref="line 5")
        assert issue.line_ref == "line 5"

    def test_invalid_severity_raises(self):
        with pytest.raises(ValidationError):
            IssueItem(severity="critical", message="Oops")

    def test_missing_severity_raises(self):
        with pytest.raises(ValidationError):
            IssueItem(message="Missing severity field")

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            IssueItem(severity="error")


class TestConceptResponse:
    """Tests for ConceptResponse model."""

    def test_minimal_valid(self):
        resp = ConceptResponse(explanation="A list stores items in order.")
        assert resp.response_type == "concept"
        assert resp.explanation == "A list stores items in order."
        assert resp.code_blocks == []
        assert resp.key_points == []
        assert resp.related_topics == []
        assert resp.send_to_editor is None

    def test_response_type_literal(self):
        resp = ConceptResponse(explanation="test")
        assert resp.response_type == "concept"

    def test_response_type_cannot_be_changed(self):
        with pytest.raises(ValidationError):
            ConceptResponse(explanation="test", response_type="other")

    def test_with_code_blocks(self):
        block = CodeBlock(code="x = [1, 2, 3]", caption="List example")
        resp = ConceptResponse(explanation="Lists store items.", code_blocks=[block])
        assert len(resp.code_blocks) == 1
        assert resp.code_blocks[0].code == "x = [1, 2, 3]"

    def test_with_key_points(self):
        resp = ConceptResponse(
            explanation="Loops repeat code.",
            key_points=["Use for loops for iteration", "Use while for conditions"],
        )
        assert len(resp.key_points) == 2

    def test_with_related_topics(self):
        resp = ConceptResponse(
            explanation="Lists in Python.",
            related_topics=["tuples", "dictionaries"],
        )
        assert "tuples" in resp.related_topics

    def test_with_send_to_editor(self):
        editor_block = CodeBlock(code="my_list = []")
        resp = ConceptResponse(explanation="Empty list.", send_to_editor=editor_block)
        assert resp.send_to_editor.code == "my_list = []"

    def test_missing_explanation_raises(self):
        with pytest.raises(ValidationError):
            ConceptResponse()

    def test_serializable_to_json(self):
        resp = ConceptResponse(explanation="Lists are ordered.")
        json_str = resp.model_dump_json()
        assert '"response_type":"concept"' in json_str
        assert '"explanation"' in json_str


class TestDebugResponse:
    """Tests for DebugResponse model."""

    def test_minimal_valid(self):
        resp = DebugResponse(
            error_identified="NameError: name 'x' is not defined",
            explanation="You used 'x' before assigning it.",
            hint="Assign x a value first.",
        )
        assert resp.response_type == "debug"
        assert resp.error_identified == "NameError: name 'x' is not defined"
        assert resp.fix_code is None
        assert resp.send_to_editor is None

    def test_response_type_literal(self):
        resp = DebugResponse(
            error_identified="error",
            explanation="explanation",
            hint="hint",
        )
        assert resp.response_type == "debug"

    def test_response_type_cannot_be_overridden(self):
        with pytest.raises(ValidationError):
            DebugResponse(
                error_identified="e",
                explanation="e",
                hint="h",
                response_type="other",
            )

    def test_with_fix_code(self):
        fix = CodeBlock(code="x = 5\nprint(x)")
        resp = DebugResponse(
            error_identified="NameError",
            explanation="x was undefined",
            hint="Define x first",
            fix_code=fix,
        )
        assert resp.fix_code.code == "x = 5\nprint(x)"

    def test_with_send_to_editor(self):
        editor = CodeBlock(code="x = 5")
        resp = DebugResponse(
            error_identified="NameError",
            explanation="x undefined",
            hint="Define x",
            send_to_editor=editor,
        )
        assert resp.send_to_editor.code == "x = 5"

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            DebugResponse(error_identified="e")

    def test_serializable_to_json(self):
        resp = DebugResponse(
            error_identified="TypeError",
            explanation="Wrong type",
            hint="Use str()",
        )
        json_str = resp.model_dump_json()
        assert '"response_type":"debug"' in json_str


class TestExerciseAgentResponse:
    """Tests for ExerciseAgentResponse model."""

    def _starter(self):
        return CodeBlock(code="def solution():\n    pass", language="python")

    def test_minimal_valid(self):
        resp = ExerciseAgentResponse(
            title="Print Hello World",
            description="Write a function that prints hello world.",
            difficulty="beginner",
            starter_code=self._starter(),
        )
        assert resp.response_type == "exercise"
        assert resp.title == "Print Hello World"
        assert resp.difficulty == "beginner"
        assert resp.expected_concepts == []
        assert resp.send_to_editor is None

    def test_response_type_literal(self):
        resp = ExerciseAgentResponse(
            title="t",
            description="d",
            difficulty="intermediate",
            starter_code=self._starter(),
        )
        assert resp.response_type == "exercise"

    def test_beginner_difficulty(self):
        resp = ExerciseAgentResponse(
            title="t", description="d", difficulty="beginner", starter_code=self._starter()
        )
        assert resp.difficulty == "beginner"

    def test_intermediate_difficulty(self):
        resp = ExerciseAgentResponse(
            title="t", description="d", difficulty="intermediate", starter_code=self._starter()
        )
        assert resp.difficulty == "intermediate"

    def test_advanced_difficulty(self):
        resp = ExerciseAgentResponse(
            title="t", description="d", difficulty="advanced", starter_code=self._starter()
        )
        assert resp.difficulty == "advanced"

    def test_invalid_difficulty_raises(self):
        with pytest.raises(ValidationError):
            ExerciseAgentResponse(
                title="t",
                description="d",
                difficulty="expert",
                starter_code=self._starter(),
            )

    def test_with_expected_concepts(self):
        resp = ExerciseAgentResponse(
            title="Loop exercise",
            description="Use a for loop",
            difficulty="beginner",
            starter_code=self._starter(),
            expected_concepts=["for loops", "iteration"],
        )
        assert "for loops" in resp.expected_concepts

    def test_missing_starter_code_raises(self):
        with pytest.raises(ValidationError):
            ExerciseAgentResponse(
                title="t",
                description="d",
                difficulty="beginner",
            )

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            ExerciseAgentResponse(
                description="d",
                difficulty="beginner",
                starter_code=self._starter(),
            )

    def test_serializable_to_json(self):
        resp = ExerciseAgentResponse(
            title="t",
            description="d",
            difficulty="beginner",
            starter_code=self._starter(),
        )
        json_str = resp.model_dump_json()
        assert '"response_type":"exercise"' in json_str
        assert '"difficulty":"beginner"' in json_str


class TestCodeReviewResponse:
    """Tests for CodeReviewResponse model."""

    def test_minimal_valid(self):
        resp = CodeReviewResponse(summary="Code looks good overall.", score=85)
        assert resp.response_type == "code_review"
        assert resp.summary == "Code looks good overall."
        assert resp.score == 85
        assert resp.issues == []
        assert resp.improved_code is None
        assert resp.send_to_editor is None

    def test_response_type_literal(self):
        resp = CodeReviewResponse(summary="s", score=50)
        assert resp.response_type == "code_review"

    def test_score_zero(self):
        resp = CodeReviewResponse(summary="Very poor code.", score=0)
        assert resp.score == 0

    def test_score_hundred(self):
        resp = CodeReviewResponse(summary="Perfect code.", score=100)
        assert resp.score == 100

    def test_score_below_zero_raises(self):
        with pytest.raises(ValidationError):
            CodeReviewResponse(summary="s", score=-1)

    def test_score_above_hundred_raises(self):
        with pytest.raises(ValidationError):
            CodeReviewResponse(summary="s", score=101)

    def test_with_issues(self):
        issue = IssueItem(severity="warning", message="Line too long")
        resp = CodeReviewResponse(summary="Minor issues.", score=70, issues=[issue])
        assert len(resp.issues) == 1
        assert resp.issues[0].severity == "warning"

    def test_with_improved_code(self):
        improved = CodeBlock(code="def foo(x):\n    return x * 2")
        resp = CodeReviewResponse(summary="Fixed.", score=90, improved_code=improved)
        assert resp.improved_code.code == "def foo(x):\n    return x * 2"

    def test_missing_score_raises(self):
        with pytest.raises(ValidationError):
            CodeReviewResponse(summary="Good.")

    def test_serializable_to_json(self):
        resp = CodeReviewResponse(summary="All good.", score=95)
        json_str = resp.model_dump_json()
        assert '"response_type":"code_review"' in json_str
        assert '"score":95' in json_str


class TestProgressAgentResponse:
    """Tests for ProgressAgentResponse model."""

    def test_minimal_valid(self):
        resp = ProgressAgentResponse(summary="You're making great progress!")
        assert resp.response_type == "progress"
        assert resp.summary == "You're making great progress!"
        assert resp.streak_days == 0
        assert resp.next_recommended_topic is None
        assert resp.modules == []
        assert resp.send_to_editor is None

    def test_response_type_literal(self):
        resp = ProgressAgentResponse(summary="s")
        assert resp.response_type == "progress"

    def test_with_streak_days(self):
        resp = ProgressAgentResponse(summary="Keep it up!", streak_days=7)
        assert resp.streak_days == 7

    def test_with_recommended_topic(self):
        resp = ProgressAgentResponse(
            summary="Review functions.",
            next_recommended_topic="Functions",
        )
        assert resp.next_recommended_topic == "Functions"

    def test_with_modules(self):
        resp = ProgressAgentResponse(
            summary="Progress summary",
            modules=[{"name": "Basics", "mastery": 80}],
        )
        assert len(resp.modules) == 1
        assert resp.modules[0]["name"] == "Basics"

    def test_send_to_editor_always_none(self):
        resp = ProgressAgentResponse(summary="Good progress.")
        assert resp.send_to_editor is None

    def test_missing_summary_raises(self):
        with pytest.raises(ValidationError):
            ProgressAgentResponse()

    def test_serializable_to_json(self):
        resp = ProgressAgentResponse(summary="Doing well.", streak_days=3)
        json_str = resp.model_dump_json()
        assert '"response_type":"progress"' in json_str
        assert '"streak_days":3' in json_str


class TestTutorResponseUnion:
    """Tests for the TutorResponse Union type."""

    def test_concept_response_in_union(self):
        resp = ConceptResponse(explanation="A loop repeats code.")
        assert isinstance(resp, ConceptResponse)

    def test_debug_response_in_union(self):
        resp = DebugResponse(
            error_identified="err", explanation="exp", hint="hint"
        )
        assert isinstance(resp, DebugResponse)

    def test_exercise_response_in_union(self):
        resp = ExerciseAgentResponse(
            title="t",
            description="d",
            difficulty="beginner",
            starter_code=CodeBlock(code="pass"),
        )
        assert isinstance(resp, ExerciseAgentResponse)

    def test_code_review_response_in_union(self):
        resp = CodeReviewResponse(summary="OK", score=80)
        assert isinstance(resp, CodeReviewResponse)

    def test_progress_response_in_union(self):
        resp = ProgressAgentResponse(summary="Good!")
        assert isinstance(resp, ProgressAgentResponse)

    def test_tutor_response_annotation_is_union(self):
        import typing
        # TutorResponse should be a Union type
        assert hasattr(TutorResponse, "__args__"), "TutorResponse should be a Union"
        args = TutorResponse.__args__
        assert ConceptResponse in args
        assert DebugResponse in args
        assert ExerciseAgentResponse in args
        assert CodeReviewResponse in args
        assert ProgressAgentResponse in args