"""Structured output schemas for specialist AI agents.

Each specialist agent uses one of these as its output_type so the
OpenAI Agents SDK coerces the LLM output into a typed Pydantic model.
The models are serialised to JSON and emitted as `event: structured` SSE.
"""

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class CodeBlock(BaseModel):
    code: str
    language: str = "python"
    caption: Optional[str] = None


class IssueItem(BaseModel):
    line_ref: Optional[str] = None
    severity: Literal["error", "warning", "suggestion"]
    message: str


class ConceptResponse(BaseModel):
    response_type: Literal["concept"] = "concept"
    explanation: str
    code_blocks: list[CodeBlock] = []
    key_points: list[str] = []
    related_topics: list[str] = []
    send_to_editor: Optional[CodeBlock] = None


class DebugResponse(BaseModel):
    response_type: Literal["debug"] = "debug"
    error_identified: str
    explanation: str
    hint: str
    fix_code: Optional[CodeBlock] = None
    send_to_editor: Optional[CodeBlock] = None


class ExerciseAgentResponse(BaseModel):
    response_type: Literal["exercise"] = "exercise"
    title: str
    description: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    starter_code: CodeBlock
    expected_concepts: list[str] = []
    send_to_editor: Optional[CodeBlock] = None


class CodeReviewResponse(BaseModel):
    response_type: Literal["code_review"] = "code_review"
    summary: str
    score: int = Field(ge=0, le=100)
    issues: list[IssueItem] = []
    improved_code: Optional[CodeBlock] = None
    send_to_editor: Optional[CodeBlock] = None


class ProgressAgentResponse(BaseModel):
    response_type: Literal["progress"] = "progress"
    summary: str
    streak_days: int = 0
    next_recommended_topic: Optional[str] = None
    modules: list[dict] = []
    send_to_editor: None = None


TutorResponse = Union[
    ConceptResponse,
    DebugResponse,
    ExerciseAgentResponse,
    CodeReviewResponse,
    ProgressAgentResponse,
]
