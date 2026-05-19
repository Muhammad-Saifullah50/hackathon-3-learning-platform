"""SDK context object for LearnFlow agent runs.

Carries user identity, session tracking, database access, and request
parameters into every SDK agent, tool, and handoff call.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class LearnFlowContext:
    """Context passed to all SDK agents via Runner.run().

    Attributes:
        user_id: Authenticated user UUID
        session_id: Agent session UUID (for conversation persistence)
        db: Async SQLAlchemy session for database operations
        topic: Optional curriculum topic context
        code_snippet: Optional code provided by the student
        level: Optional student level (beginner/intermediate/advanced)
        intent: Classified intent (set by triage before handoff)
        extra: Arbitrary additional data for tool functions
    """

    user_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    db: Optional[AsyncSession] = None
    topic: Optional[str] = None
    code_snippet: Optional[str] = None
    level: Optional[str] = None
    intent: Optional[str] = None
    agent_mode: Optional[Literal["recommendations", "module_detail"]] = None
    module_slug: Optional[str] = None
    mastery_context: Optional[str] = None
    question_description: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
