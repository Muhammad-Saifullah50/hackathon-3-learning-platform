"""Agent routes.

Agent-related API endpoints using the OpenAI Agents SDK.
"""

import logging
import uuid

from agents import RunConfig, Runner
from agents.extensions.models.litellm_model import LitellmModel
from agents.models.interface import Model, ModelProvider
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.config import settings
from src.dependencies import (
    get_agent_session_repository,
    get_db,
    get_exercise_repository,
    get_mastery_repository,
    get_progress_repository,
    get_routing_repository,
    get_user_streak_repository,
)
from src.models import User
from src.models.agent_session import HintProgression
from src.repositories.agent_session_repository import AgentSessionRepository
from src.repositories.exercise_repository import ExerciseRepository
from src.repositories.mastery_repository import MasteryRepository
from src.repositories.progress_repository import ProgressRepository
from src.repositories.routing_repository import RoutingRepository
from src.repositories.user_repository import UserStreakRepository
from src.schemas.agents import (
    AgentChatRequest,
    AgentErrorResponse,
    ExerciseGenerationRequest,
    ExerciseSubmissionRequest,
    HintAdvanceRequest,
)
from src.services.agents.agents import get_exercise_agent, get_triage_agent
from src.services.agents.context import LearnFlowContext
from src.services.agents.hooks import LearnFlowHooks
from src.services.agents.triage import classify_intent, get_agent_for_intent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agents"])


class _ConfiguredLitellmProvider(ModelProvider):
    """LitellmProvider wired to project LLM settings (api_key, base_url, model)."""

    def get_model(self, model_name: str | None) -> Model:
        return LitellmModel(
            model=model_name or settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL or None,
            api_key=settings.LLM_API_KEY or None,
        )


async def _sse_result_generator(result):
    """Convert a non-streaming Runner.run result into a single-chunk SSE stream.

    The OpenAI Agents SDK + LitellmModel streaming path is currently broken
    (openai/openai-agents-python#601), so we run the agent to completion and
    emit the final output as one SSE event followed by [DONE].
    """
    last_agent_name = getattr(getattr(result, "last_agent", None), "name", None)
    if last_agent_name:
        yield f"event: handoff\ndata: {last_agent_name}\n\n"
    text = result.final_output if isinstance(result.final_output, str) else str(result.final_output)
    if text:
        yield f"data: {text}\n\n"
    yield "data: [DONE]\n\n"


@router.post(
    "/chat",
    summary="Send a question to the agent system",
    description=(
        "Student sends a natural language question. The Triage Agent classifies the intent, "
        "routes to the appropriate specialist agent via handoffs, and returns a streaming response."
    ),
    responses={
        200: {
            "description": "Streaming response via Server-Sent Events",
            "content": {"text/event-stream": {}},
        },
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
        404: {"model": AgentErrorResponse, "description": "Session not found"},
        502: {"model": AgentErrorResponse, "description": "LLM provider error"},
    },
)
async def agent_chat(
    request: AgentChatRequest,
    session_repo: AgentSessionRepository = Depends(get_agent_session_repository),
    routing_repo: RoutingRepository = Depends(get_routing_repository),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat with the agent system. Routes the question to the appropriate specialist."""
    logger.info("Agent chat request from user=%s", current_user.id)

    triage_result = classify_intent(request.message)
    agent_name = get_agent_for_intent(triage_result.intent)

    if request.session_id:
        session_obj = await session_repo.get_session(request.session_id)
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
        if str(session_obj.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not your session")
        session_id = session_obj.id
    else:
        session_obj = await session_repo.create_session(user_id=current_user.id)
        session_id = session_obj.id

    await session_repo.add_message_to_history(str(session_id), "user", request.message)
    await session_repo.update_session(str(session_id), active_agent=agent_name)

    lf_ctx = LearnFlowContext(
        user_id=current_user.id,
        session_id=session_id,
        db=db,
        topic=request.topic,
        code_snippet=request.code_snippet,
        intent=triage_result.intent,
    )

    triage_agent = get_triage_agent()
    hooks = LearnFlowHooks(
        session_repo=session_repo,
        routing_repo=routing_repo,
        user_message=request.message,
    )

    run_config = RunConfig(model_provider=_ConfiguredLitellmProvider())

    result = await Runner.run(
        triage_agent,
        input=request.message,
        context=lf_ctx,
        hooks=hooks,
        run_config=run_config,
    )

    if result.final_output:
        await session_repo.add_message_to_history(
            str(session_id), "assistant", str(result.final_output)
        )

    return StreamingResponse(
        _sse_result_generator(result),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/sessions/{session_id}",
    summary="Get agent session details",
    description=(
        "Return conversation history and routing decisions for a session. "
        "Verifies user ownership."
    ),
    responses={
        200: {"description": "Session details returned successfully"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
        404: {"model": AgentErrorResponse, "description": "Session not found"},
    },
)
async def get_session(
    session_id: str,
    session_repo: AgentSessionRepository = Depends(get_agent_session_repository),
    routing_repo: RoutingRepository = Depends(get_routing_repository),
    current_user: User = Depends(get_current_user),
):
    """Get details for an agent session including conversation history."""
    session_obj = await session_repo.get_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session_obj.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")

    routing_decisions = await routing_repo.get_session_routing_decisions(uuid.UUID(session_id))

    return {
        "id": str(session_obj.id),
        "status": session_obj.status,
        "active_agent": session_obj.active_agent,
        "conversation_history": session_obj.conversation_history,
        "routing_decisions": [
            {
                "intent": rd.intent,
                "confidence": rd.confidence,
                "target_agent": rd.target_agent,
                "message": rd.message,
                "created_at": rd.created_at,
            }
            for rd in routing_decisions
        ],
        "created_at": session_obj.created_at,
        "updated_at": session_obj.updated_at,
    }


@router.post(
    "/exercises",
    summary="Generate a coding exercise",
    description="Request a coding exercise on a specific topic and difficulty level.",
    responses={
        200: {"description": "Exercise generated successfully"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
    },
)
async def generate_exercise(
    request: ExerciseGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a coding exercise."""
    lf_ctx = LearnFlowContext(
        user_id=current_user.id,
        db=db,
        topic=request.topic,
    )

    exercise_agent = get_exercise_agent()
    result = await Runner.run(
        exercise_agent,
        input=f"Generate a {request.difficulty}-level Python exercise on '{request.topic}'.",
        context=lf_ctx,
        run_config=RunConfig(model_provider=_ConfiguredLitellmProvider()),
    )

    return {
        "topic": request.topic,
        "difficulty": request.difficulty,
        "content": result.final_output,
    }


@router.post(
    "/exercises/{exercise_id}/submit",
    summary="Submit an exercise solution for grading",
    description="Submit code for an exercise. The system grades it against test cases.",
    responses={
        200: {"description": "Submission graded successfully"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
        404: {"model": AgentErrorResponse, "description": "Exercise not found"},
    },
)
async def submit_exercise(
    exercise_id: str,
    request: ExerciseSubmissionRequest,
    exercise_repo: ExerciseRepository = Depends(get_exercise_repository),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit code for grading."""
    exercise = await exercise_repo.get_exercise(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    test_cases = exercise.test_cases
    test_results = []
    for i, tc in enumerate(test_cases):
        test_results.append(
            {
                "test_index": i,
                "passed": False,
                "error_message": "Sandbox execution not yet integrated.",
            }
        )

    score = 0.0
    return {
        "score": score,
        "test_results": test_results,
        "feedback": "Sandbox integration pending. Review your code manually.",
        "execution_time_ms": None,
    }


@router.post(
    "/hints/advance",
    summary="Advance debugging hint level",
    description="Advance to the next hint level or request the full solution.",
    responses={
        200: {"description": "Hint advanced successfully"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
    },
)
async def advance_hint(
    request: HintAdvanceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Advance the hint level or request solution."""
    stmt = select(HintProgression).where(
        HintProgression.session_id == uuid.UUID(request.session_id),
        HintProgression.user_id == current_user.id,
        HintProgression.resolved == 0,
    )
    result = await db.execute(stmt)
    hint_progress = result.scalar_one_or_none()

    if not hint_progress:
        return {
            "hint_level": 1,
            "hints_remaining": 3,
            "solution_available": True,
        }

    current_level = hint_progress.hint_level
    if request.request_solution:
        hint_progress.solution_revealed = 1
        new_level = 4
    elif current_level < 3:
        new_level = current_level + 1
        hint_progress.hint_level = new_level
    else:
        new_level = 4

    await db.commit()
    hints_remaining = max(0, 3 - new_level) if new_level <= 3 else 0

    return {
        "hint_level": min(new_level, 3),
        "hints_remaining": hints_remaining,
        "solution_available": True,
    }


@router.get(
    "/progress",
    summary="Get learning progress summary",
    description=(
        "Return a comprehensive progress summary including mastery scores per topic, "
        "weak areas, streak information, and personalized recommendations."
    ),
    responses={
        200: {"description": "Progress summary returned successfully"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
    },
)
async def get_progress(
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    progress_repo: ProgressRepository = Depends(get_progress_repository),
    streak_repo: UserStreakRepository = Depends(get_user_streak_repository),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get learning progress summary."""
    mastery_records = await mastery_repo.get_user_mastery_records(current_user.id)

    if not mastery_records:
        return {
            "overall_mastery": 0.0,
            "topics": [],
            "weak_areas": [],
            "streak": None,
            "recommendations": [
                "Start by completing your first exercise to begin tracking progress!",
                "Try exploring the curriculum and asking questions about Python concepts.",
            ],
            "missing_components": ["exercises", "quizzes", "code_quality", "streak"],
        }

    topics = []
    weak_areas = []
    total_score = 0.0
    all_missing = set()

    for record in mastery_records:
        topics.append(
            {
                "topic": record.topic,
                "score": record.score,
                "level": record.level,
                "component_breakdown": record.component_breakdown,
            }
        )
        if record.score < 50:
            weak_areas.append(record.topic)
        total_score += record.score
        all_missing.update(record.component_breakdown.get("missing_components", []))

    overall = round(total_score / len(mastery_records), 2)

    streak_data = None
    try:
        streak = await streak_repo.get_by_user_id(current_user.id)
        if streak:
            streak_data = {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
            }
    except Exception:
        pass

    recommendations = []
    if weak_areas:
        recommendations.append(f"Focus on these weak areas: {', '.join(weak_areas)}")
    if streak_data and streak_data["current_streak"] > 0:
        recommendations.append(
            f"Keep it up! You have a {streak_data['current_streak']}-day streak going!"
        )
    if not recommendations:
        recommendations.append("Keep practicing to improve your skills!")

    return {
        "overall_mastery": overall,
        "topics": topics,
        "weak_areas": weak_areas,
        "streak": streak_data,
        "recommendations": recommendations,
        "missing_components": list(all_missing),
    }
