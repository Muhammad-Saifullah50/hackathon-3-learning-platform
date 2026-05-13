"""Agent schemas package.

Pydantic schemas for agent request/response validation.
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request schema for agent chat endpoint."""

    message: str = Field(..., min_length=1, max_length=2000)
    topic: Optional[str] = None
    session_id: Optional[str] = None
    code_snippet: Optional[str] = Field(None, max_length=4096)
    execution_output: Optional[str] = Field(None, max_length=2000)
    surface: Optional[Literal["standalone", "embedded"]] = None


class ConversationMessage(BaseModel):
    """A single message in a conversation."""

    role: str
    content: str
    timestamp: datetime


class RoutingDecisionRecord(BaseModel):
    """Record of a routing decision."""

    intent: str
    confidence: float
    target_agent: str
    message: str
    created_at: datetime


class AgentSessionResponse(BaseModel):
    """Response schema for agent session."""

    id: str
    status: str
    active_agent: Optional[str]
    conversation_history: list[ConversationMessage]
    routing_decisions: list[RoutingDecisionRecord]
    created_at: datetime
    updated_at: datetime


class AgentChatResponse(BaseModel):
    """Response schema for agent chat (non-streaming metadata)."""

    session_id: str
    agent: str
    intent: str
    confidence: float


class ExerciseGenerationRequest(BaseModel):
    """Request schema for exercise generation."""

    topic: str = Field(..., min_length=1, max_length=100)
    difficulty: str = Field(..., pattern="^(beginner|intermediate|advanced)$")


class TestCase(BaseModel):
    """A single test case for an exercise."""

    input: str
    expected_output: str
    assert_statement: str


class ExerciseResponse(BaseModel):
    """Response schema for a generated exercise."""

    id: str
    topic: str
    difficulty: str
    description: str
    starter_code: Optional[str]
    test_cases: list[TestCase]
    created_at: datetime


class ExerciseSubmissionRequest(BaseModel):
    """Request schema for exercise submission."""

    code: str = Field(..., min_length=1)


class TestResult(BaseModel):
    """Result of a single test case execution."""

    test_index: int
    passed: bool
    error_message: Optional[str] = None


class ExerciseSubmissionResponse(BaseModel):
    """Response schema for exercise submission grading."""

    exercise_id: str
    score: float
    test_results: list[TestResult]
    feedback: Optional[str]
    execution_time_ms: Optional[int]


class TopicMastery(BaseModel):
    """Mastery breakdown for a single topic."""

    topic: str
    score: float
    level: str
    component_breakdown: dict[str, Any]


class StreakInfo(BaseModel):
    """User streak information."""

    current_streak: int
    longest_streak: int


class ProgressSummaryResponse(BaseModel):
    """Response schema for progress summary."""

    overall_mastery: float
    topics: list[TopicMastery]
    weak_areas: list[str]
    streak: Optional[StreakInfo]
    recommendations: list[str]
    missing_components: list[str]


class HintAdvanceRequest(BaseModel):
    """Request schema for advancing hint level."""

    session_id: str
    request_solution: bool = False


class HintResponse(BaseModel):
    """Response schema for hint advancement."""

    hint_text: str
    hint_level: int
    hints_remaining: int
    solution_available: bool


class ConceptsExplainRequest(BaseModel):
    """Request schema for the concepts explain endpoint."""

    question: str = Field(..., min_length=1, max_length=2000)
    topic: Optional[str] = None
    level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    session_id: Optional[str] = None


class CodeReviewRequest(BaseModel):
    """Request schema for the code review analyze endpoint."""

    code: str = Field(..., min_length=1)
    question: Optional[str] = None
    session_id: Optional[str] = None


class DebugAnalyzeRequest(BaseModel):
    """Request schema for the debug analyze endpoint."""

    code: str = Field(..., min_length=1)
    error_message: Optional[str] = None
    question: Optional[str] = None
    session_id: Optional[str] = None


class AgentErrorResponse(BaseModel):
    """Standard error response for agent endpoints."""

    error: str
    message: str
    detail: Optional[str] = None


class ChatSessionListItem(BaseModel):
    """Summary of a chat session for the session list."""

    id: str
    title: str
    surface: Optional[str]
    message_count: int
    last_message_at: datetime
    created_at: datetime


class ChatSessionDetail(BaseModel):
    """Full chat session with conversation history."""

    id: str
    title: str
    surface: Optional[str]
    conversation_history: list[ConversationMessage]
    created_at: datetime
    updated_at: datetime


class ChatQuotaStatus(BaseModel):
    """Daily chat quota status for the current user."""

    messages_sent_today: int
    daily_limit: int
    remaining: int
    quota_reset_at: datetime
