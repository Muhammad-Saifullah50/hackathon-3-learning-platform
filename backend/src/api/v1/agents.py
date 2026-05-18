"""Agent routes.

Agent-related API endpoints using the OpenAI Agents SDK.
"""

import json
import logging
import uuid

from agents import InputGuardrailTripwireTriggered, RunConfig, Runner
from src.repositories.quiz_session_repository import QuizSessionRepository
from src.schemas.agent_responses import QuizResponse as QuizResponseSchema
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.config import settings
from src.services.agents.model_provider import get_run_config
from src.dependencies import (
    get_agent_session_repository,
    get_chat_quota_service,
    get_code_session_service,
    get_db,
    get_exercise_repository,
    get_mastery_repository,
    get_progress_repository,
    get_routing_repository,
    get_user_streak_repository,
)
from src.schemas.code_editor import RateLimitErrorResponse
from src.services.chat_quota_service import ChatQuotaService, DAILY_LIMIT
from src.services.code_session_service import CodeSessionService
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
    ChatQuotaStatus,
    ChatSessionDetail,
    ChatSessionListItem,
    CodeReviewRequest,
    ConceptsExplainRequest,
    DebugAnalyzeRequest,
    ExerciseGenerationRequest,
    ExerciseSubmissionRequest,
    HintAdvanceRequest,
)
from src.services.agents.agents import (
    get_code_review_agent,
    get_concepts_agent,
    get_debug_agent,
    get_exercise_agent,
    get_progress_agent,
    get_quiz_agent,
    get_triage_agent,
)
from src.services.agents.exercise import ExerciseService
from src.services.agents.context import LearnFlowContext
from src.services.agents.hooks import LearnFlowHooks
from src.services.agents.triage import classify_intent, get_agent_for_intent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agents"])


async def _sse_result_generator(result, session_id: str | None = None):
    """Emit a completed Runner.run result as SSE (used by non-chat endpoints)."""
    if session_id:
        yield f"event: session\ndata: {session_id}\n\n"
    last_agent_name = getattr(getattr(result, "last_agent", None), "name", None)
    if last_agent_name:
        yield f"event: handoff\ndata: {last_agent_name}\n\n"
    final = result.final_output
    if hasattr(final, "model_dump_json"):
        yield f"event: structured\ndata: {final.model_dump_json()}\n\n"
    else:
        text = final if isinstance(final, str) else str(final)
        if text:
            yield f"data: {text}\n\n"
    yield "data: [DONE]\n\n"



OFF_TOPIC_CANNED = (
    "I'm here to help with Python learning! "
    "Try asking about Python syntax, debugging, or coding exercises."
)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _word_boundary_trim(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    trimmed = text[:max_len]
    space_idx = trimmed.rfind(" ")
    return trimmed[:space_idx] if space_idx > 0 else trimmed


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
        429: {"description": "Daily chat quota exhausted"},
        502: {"model": AgentErrorResponse, "description": "LLM provider error"},
    },
)
async def agent_chat(
    request: AgentChatRequest,
    session_repo: AgentSessionRepository = Depends(get_agent_session_repository),
    routing_repo: RoutingRepository = Depends(get_routing_repository),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    quota_service: ChatQuotaService = Depends(get_chat_quota_service),
):
    """Chat with the agent system. Routes the question to the appropriate specialist."""
    logger.info("Agent chat request from user=%s", current_user.id)
    from datetime import datetime, timedelta, timezone as tz

    # Validate session ownership BEFORE consuming quota so invalid sessions
    # do not burn the user's daily allowance.
    if request.session_id:
        session_obj = await session_repo.get_session(request.session_id)
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
        if str(session_obj.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not your session")
        session_id = session_obj.id
    else:
        session_obj = None

    # Enforce daily chat quota
    allowed, remaining = await quota_service.check_and_get_remaining(db, current_user.id)
    if not allowed:
        retry_after = (datetime.now(tz.utc).date() + timedelta(days=1)).isoformat()
        return JSONResponse(
            status_code=429,
            content=RateLimitErrorResponse(
                message=f"Daily chat quota exhausted ({DAILY_LIMIT} messages/day). Try again tomorrow.",
                retry_after=retry_after,
            ).model_dump(),
        )

    triage_result = classify_intent(request.message)
    agent_name = get_agent_for_intent(triage_result.intent)

    # Create session if not provided
    if session_obj is None:
        session_obj = await session_repo.create_session(user_id=current_user.id)
        session_id = session_obj.id

    # Set session title on first message
    if not session_obj.title:
        title = _word_boundary_trim(request.message)
        await session_repo.update_session(
            str(session_id), title=title, surface=request.surface, active_agent=agent_name
        )
    else:
        await session_repo.update_session(str(session_id), active_agent=agent_name)

    await session_repo.add_message_to_history(str(session_id), "user", request.message)

    # Build context and run agent
    lf_ctx = LearnFlowContext(
        user_id=current_user.id,
        session_id=session_id,
        db=db,
        topic=request.topic,
        code_snippet=request.code_snippet,
        intent=triage_result.intent,
    )

    # For quiz requests, pass the full conversation history so the agent can
    # determine the topic itself rather than relying on a single message heuristic.
    agent_input = request.message
    if agent_name == "quiz" and session_obj is not None:
        history = list(session_obj.conversation_history or [])
        # history already includes the current user message (added above)
        if history:
            convo_lines = []
            for entry in history:
                role = entry.get("role", "user").capitalize()
                content = entry.get("content", "")
                # Truncate very long assistant messages to keep context manageable
                if entry.get("role") == "assistant" and len(content) > 500:
                    content = content[:500] + "…"
                convo_lines.append(f"{role}: {content}")
            convo_text = "\n".join(convo_lines)
            agent_input = (
                f"Conversation so far:\n{convo_text}\n\n"
                f"Student request: {request.message}\n\n"
                "Based on the conversation above, identify the topic being discussed "
                "and generate a quiz on that exact topic."
            )

    _agent_factory_map = {
        "code_review": get_code_review_agent,
        "concepts": get_concepts_agent,
        "debug": get_debug_agent,
        "exercise": get_exercise_agent,
        "progress": get_progress_agent,
        "quiz": get_quiz_agent,
    }
    selected_agent = _agent_factory_map.get(agent_name, get_triage_agent)()
    hooks = LearnFlowHooks(
        session_repo=session_repo,
        routing_repo=routing_repo,
        user_message=request.message,
    )
    run_config = get_run_config()

    streamed = Runner.run_streamed(
        selected_agent,
        input=agent_input,
        context=lf_ctx,
        hooks=hooks,
        run_config=run_config,
    )

    async def _generate():
        # Emit session id and quota immediately so the client can track state.
        yield f"event: session\ndata: {session_id}\n\n"
        yield f"event: quota\ndata: {remaining}\n\n"

        handoff_name: str | None = None
        try:
            async for event in streamed.stream_events():
                if event.type == "agent_updated_stream_event":
                    new_name = getattr(getattr(event, "new_agent", None), "name", None)
                    if new_name:
                        handoff_name = new_name
        except InputGuardrailTripwireTriggered:
            # Persist the canned reply BEFORE yielding [DONE] so the DB write
            # completes while the connection is still active.
            await session_repo.add_message_to_history(
                str(session_id), "assistant", OFF_TOPIC_CANNED, agent_type="none"
            )
            yield "event: handoff\ndata: none\n\n"
            yield f"data: {OFF_TOPIC_CANNED}\n\n"
            yield "data: [DONE]\n\n"
            return

        emit_name = handoff_name or getattr(
            getattr(streamed, "last_agent", None), "name", None
        )
        if emit_name:
            yield f"event: handoff\ndata: {emit_name}\n\n"

        final = streamed.final_output
        if final is not None:
            # If the quiz agent returned a QuizResponse, create a quiz_sessions row
            # and embed the quiz_session_id before emitting to the client.
            if isinstance(final, QuizResponseSchema):
                try:
                    quiz_repo = QuizSessionRepository(db)
                    questions = (
                        [q.model_dump() for q in final.mcq_questions]
                        + [q.model_dump() for q in final.flashcard_questions]
                    )
                    quiz_session = await quiz_repo.create(
                        student_id=current_user.id,
                        chat_session_id=session_id,
                        module_slug=final.module_slug,
                        topic_label=final.topic_label,
                        questions=questions,
                    )
                    final.quiz_session_id = str(quiz_session.id)
                except Exception as exc:
                    logger.warning("Failed to create quiz session: %s", exc)

            content = (
                final.model_dump_json() if hasattr(final, "model_dump_json") else str(final)
            )
            # Persist BEFORE yielding [DONE] so the DB write completes while
            # the SSE connection is still open (avoids dropped writes on disconnect).
            await session_repo.add_message_to_history(
                str(session_id), "assistant", content, agent_type=emit_name
            )
            if hasattr(final, "model_dump_json"):
                yield f"event: structured\ndata: {content}\n\n"
            else:
                yield f"data: {content}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get(
    "/sessions",
    summary="List chat sessions for current user",
    response_model=list[ChatSessionListItem],
    responses={401: {"model": AgentErrorResponse}},
)
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=50),
    session_repo: AgentSessionRepository = Depends(get_agent_session_repository),
    current_user: User = Depends(get_current_user),
):
    """Return the most recent chat sessions for the authenticated user."""
    sessions = await session_repo.list_sessions(current_user.id, limit=limit)
    return [
        ChatSessionListItem(
            id=str(s.id),
            title=s.title or "(Untitled)",
            surface=s.surface,
            message_count=len(s.conversation_history or []),
            last_message_at=s.updated_at,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.get(
    "/quota",
    summary="Get daily chat quota status",
    response_model=ChatQuotaStatus,
    responses={401: {"model": AgentErrorResponse}},
)
async def get_quota(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    quota_service: ChatQuotaService = Depends(get_chat_quota_service),
):
    """Return the current user's daily chat quota status (read-only, no side effects)."""
    status = await quota_service.get_status(db, current_user.id)
    return ChatQuotaStatus(**status)


@router.get(
    "/sessions/{session_id}",
    summary="Get agent session details",
    description=(
        "Return conversation history for a session. "
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
    current_user: User = Depends(get_current_user),
):
    """Get details for an agent session including conversation history."""
    from src.schemas.agents import ConversationMessage as ConvMsg
    session_obj = await session_repo.get_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session_obj.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")

    history = session_obj.conversation_history or []
    return ChatSessionDetail(
        id=str(session_obj.id),
        title=session_obj.title or "(Untitled)",
        surface=session_obj.surface,
        conversation_history=[
            ConvMsg(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", ""),
                agent_type=m.get("agent_type"),
            )
            for m in history
        ],
        created_at=session_obj.created_at,
        updated_at=session_obj.updated_at,
    )


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
        run_config=get_run_config(),
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
    """Submit code for grading against exercise test cases using the sandbox."""
    exercise = await exercise_repo.get_exercise(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    service = ExerciseService(db=db, exercise_repo=exercise_repo)
    result = await service.grade_submission(
        exercise=exercise,
        submitted_code=request.code,
        user_id=current_user.id,
    )
    return result


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


@router.post(
    "/concepts/explain",
    summary="Explain a Python concept",
    description=(
        "Send a concept question directly to the Concepts Agent. "
        "Adapts explanation to the student's level and always includes runnable examples."
    ),
    responses={
        200: {"description": "Streaming explanation via Server-Sent Events"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
        502: {"model": AgentErrorResponse, "description": "LLM provider error"},
    },
)
async def concepts_explain(
    request: ConceptsExplainRequest,
    session_repo: AgentSessionRepository = Depends(get_agent_session_repository),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explain a Python concept via the Concepts Agent."""
    logger.info("Concepts explain request from user=%s", current_user.id)

    if request.session_id:
        session_obj = await session_repo.get_session(request.session_id)
        if not session_obj or str(session_obj.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = session_obj.id
    else:
        session_obj = await session_repo.create_session(user_id=current_user.id)
        session_id = session_obj.id

    await session_repo.add_message_to_history(str(session_id), "user", request.question)

    lf_ctx = LearnFlowContext(
        user_id=current_user.id,
        session_id=session_id,
        db=db,
        topic=request.topic,
        level=request.level or "beginner",
    )
    agent = get_concepts_agent()
    try:
        result = await Runner.run(
            agent,
            input=request.question,
            context=lf_ctx,
            run_config=get_run_config(),
        )
    except Exception as exc:
        logger.exception("Concepts agent error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    await session_repo.add_message_to_history(
        str(session_id), "assistant", result.final_output or ""
    )
    return StreamingResponse(
        _sse_result_generator(result),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/code-review/analyze",
    summary="Analyze code for quality and correctness",
    description=(
        "Submit code directly to the Code Review Agent for PEP 8, "
        "correctness, performance, and readability feedback."
    ),
    responses={
        200: {"description": "Streaming review via Server-Sent Events"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
        502: {"model": AgentErrorResponse, "description": "LLM provider error"},
    },
)
async def code_review_analyze(
    request: CodeReviewRequest,
    session_repo: AgentSessionRepository = Depends(get_agent_session_repository),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review submitted code via the Code Review Agent."""
    logger.info("Code review request from user=%s", current_user.id)

    if request.session_id:
        session_obj = await session_repo.get_session(request.session_id)
        if not session_obj or str(session_obj.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = session_obj.id
    else:
        session_obj = await session_repo.create_session(user_id=current_user.id)
        session_id = session_obj.id

    user_message = request.question or "Please review my code."
    await session_repo.add_message_to_history(str(session_id), "user", user_message)

    lf_ctx = LearnFlowContext(
        user_id=current_user.id,
        session_id=session_id,
        db=db,
        code_snippet=request.code,
    )
    agent = get_code_review_agent()
    try:
        result = await Runner.run(
            agent,
            input=user_message,
            context=lf_ctx,
            run_config=get_run_config(),
        )
    except Exception as exc:
        logger.exception("Code review agent error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    await session_repo.add_message_to_history(
        str(session_id), "assistant", result.final_output or ""
    )
    return StreamingResponse(
        _sse_result_generator(result),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/debug/analyze",
    summary="Debug code errors with progressive hints",
    description=(
        "Submit broken code and optional error message to the Debug Agent. "
        "Returns progressive hints (3 levels) before revealing the full solution."
    ),
    responses={
        200: {"description": "Streaming debug hints via Server-Sent Events"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
        502: {"model": AgentErrorResponse, "description": "LLM provider error"},
    },
)
async def debug_analyze(
    request: DebugAnalyzeRequest,
    session_repo: AgentSessionRepository = Depends(get_agent_session_repository),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze broken code via the Debug Agent with progressive hints."""
    logger.info("Debug analyze request from user=%s", current_user.id)

    if request.session_id:
        session_obj = await session_repo.get_session(request.session_id)
        if not session_obj or str(session_obj.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = session_obj.id
    else:
        session_obj = await session_repo.create_session(user_id=current_user.id)
        session_id = session_obj.id

    parts = [request.question or "Help me debug my code."]
    if request.error_message:
        parts.append(f"Error: {request.error_message}")
    user_message = "\n".join(parts)
    await session_repo.add_message_to_history(str(session_id), "user", user_message)

    lf_ctx = LearnFlowContext(
        user_id=current_user.id,
        session_id=session_id,
        db=db,
        code_snippet=request.code,
    )
    agent = get_debug_agent()
    try:
        result = await Runner.run(
            agent,
            input=user_message,
            context=lf_ctx,
            run_config=get_run_config(),
        )
    except Exception as exc:
        logger.exception("Debug agent error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    await session_repo.add_message_to_history(
        str(session_id), "assistant", result.final_output or ""
    )
    return StreamingResponse(
        _sse_result_generator(result),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get(
    "/progress/summary",
    summary="Get full progress summary for the dashboard",
    responses={
        200: {"description": "Progress summary returned successfully"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
    },
)
async def get_progress_summary(
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    streak_repo: UserStreakRepository = Depends(get_user_streak_repository),
    current_user: User = Depends(get_current_user),
):
    """Return full progress summary including mastery per topic, streak, and recommendations."""
    mastery_records = await mastery_repo.get_user_mastery_records(current_user.id)

    topics = [
        {
            "topic": r.topic,
            "score": r.score,
            "level": r.level,
            "component_breakdown": r.component_breakdown or {},
        }
        for r in mastery_records
    ]

    overall_mastery = (
        round(sum(r.score for r in mastery_records) / len(mastery_records), 2)
        if mastery_records
        else 0.0
    )

    weak_areas = [r.topic for r in mastery_records if r.score < 50]

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

    recommendations: list[str] = []
    if not mastery_records:
        recommendations.append("Start with Python Basics to begin your learning journey!")
    else:
        if weak_areas:
            recommendations.append(f"Focus on improving: {', '.join(weak_areas)}")
        strong_areas = [r.topic for r in mastery_records if r.score >= 71]
        if strong_areas:
            recommendations.append(
                f"Great work on {', '.join(strong_areas[:3])}! Consider advancing to the next topic."
            )
        if streak_data and streak_data["current_streak"] > 0:
            recommendations.append(
                f"You're on a {streak_data['current_streak']}-day streak — keep it up!"
            )

    missing_components: list[str] = []
    if mastery_records:
        all_components = {"exercises", "quizzes", "code_quality", "consistency"}
        seen: set[str] = set()
        for r in mastery_records:
            breakdown = r.component_breakdown or {}
            for comp in all_components:
                if breakdown.get(comp, 0) > 0:
                    seen.add(comp)
        missing_components = list(all_components - seen)
    else:
        missing_components = ["exercises", "quizzes", "code_quality", "consistency"]

    return {
        "overall_mastery": overall_mastery,
        "topics": topics,
        "weak_areas": weak_areas,
        "streak": streak_data,
        "recommendations": recommendations,
        "missing_components": missing_components,
    }


@router.get(
    "/progress/recommendations",
    summary="Get personalized learning recommendations",
    description=(
        "Return personalized recommendations based on weak areas, streak status, "
        "and overall mastery. Derived from the full progress summary."
    ),
    responses={
        200: {"description": "Recommendations returned successfully"},
        401: {"model": AgentErrorResponse, "description": "Unauthorized"},
    },
)
async def get_recommendations(
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    streak_repo: UserStreakRepository = Depends(get_user_streak_repository),
    current_user: User = Depends(get_current_user),
):
    """Get personalized recommendations based on the student's progress."""
    mastery_records = await mastery_repo.get_user_mastery_records(current_user.id)

    weak_areas = [r.topic for r in mastery_records if r.score < 50]
    strong_areas = [r.topic for r in mastery_records if r.score >= 71]

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
        recommendations.append(f"Focus on improving: {', '.join(weak_areas)}")
        recommendations.append(
            f"Try more exercises on {weak_areas[0]} to build mastery."
        )
    if strong_areas:
        recommendations.append(
            f"Great work on {', '.join(strong_areas[:3])}! Consider advancing to the next topic."
        )
    if streak_data and streak_data["current_streak"] > 0:
        recommendations.append(
            f"You're on a {streak_data['current_streak']}-day streak — keep it up!"
        )
    elif streak_data is not None:
        recommendations.append("Log in daily to build your streak and reinforce learning.")
    if not recommendations:
        recommendations.append(
            "Complete exercises and quizzes to unlock personalised recommendations."
        )

    return {
        "recommendations": recommendations,
        "weak_areas": weak_areas,
        "strong_areas": strong_areas,
        "streak": streak_data,
    }
