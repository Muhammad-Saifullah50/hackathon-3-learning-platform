"""SDK lifecycle hooks for LearnPyByAI agents.

RunHooks that persist conversation history to AgentSession and log
routing decisions whenever a handoff occurs.
"""

import logging
from typing import Any

from agents import Agent, RunContextWrapper, RunHooks

from src.repositories.agent_session_repository import AgentSessionRepository
from src.repositories.routing_repository import RoutingRepository
from src.services.agents.context import LearnPyByAIContext

logger = logging.getLogger(__name__)


class LearnPyByAIHooks(RunHooks):
    """Hooks that persist agent runs to the database."""

    def __init__(
        self,
        session_repo: AgentSessionRepository,
        routing_repo: RoutingRepository,
        user_message: str = "",
    ):
        """
        Args:
            session_repo: Repository for agent session persistence
            routing_repo: Repository for routing decision logging
            user_message: The original user message for routing logs
        """
        self.session_repo = session_repo
        self.routing_repo = routing_repo
        self.user_message = user_message

    async def on_agent_start(
        self,
        context: RunContextWrapper[LearnPyByAIContext],
        agent: Agent[LearnPyByAIContext],
    ) -> None:
        """Log which agent is starting to handle the request."""
        lf_ctx = context.context
        logger.info(
            "Agent %s starting for user=%s session=%s",
            agent.name,
            lf_ctx.user_id,
            lf_ctx.session_id,
        )

    async def on_handoff(
        self,
        context: RunContextWrapper[LearnPyByAIContext],
        from_agent: Agent[LearnPyByAIContext],
        to_agent: Agent[LearnPyByAIContext],
    ) -> None:
        """Log a routing decision when control transfers between agents."""
        lf_ctx = context.context
        if lf_ctx.session_id and lf_ctx.db:
            try:
                await self.routing_repo.log_routing_decision(
                    session_id=lf_ctx.session_id,
                    user_id=lf_ctx.user_id,
                    message=self.user_message,
                    intent=lf_ctx.intent or "general",
                    confidence=1.0,
                    target_agent=to_agent.name,
                )
                await self.session_repo.update_session(
                    str(lf_ctx.session_id), active_agent=to_agent.name
                )
            except Exception:
                logger.exception("Failed to log routing decision")

    async def on_agent_end(
        self,
        context: RunContextWrapper[LearnPyByAIContext],
        agent: Agent[LearnPyByAIContext],
        output: Any,
    ) -> None:
        """Called when the agent produces its final output.

        Persistence is handled by the streaming endpoint (_generate) which saves
        the JSON-serialised response immediately before yielding [DONE], ensuring
        the DB write completes while the SSE connection is still open.
        """
