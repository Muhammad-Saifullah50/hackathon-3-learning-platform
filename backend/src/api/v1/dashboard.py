"""Dashboard API endpoints (F017).

Stateless read-only endpoints for mastery history charts and SSE agent streams.
These endpoints do NOT consume chat quota and do NOT persist sessions.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.auth.dependencies import get_current_user
from src.dependencies import get_db, get_mastery_repository
from src.models import User
from src.repositories.mastery_repository import MasteryRepository
from src.repositories.mastery_snapshot_repository import MasterySnapshotRepository
from src.schemas.dashboard import MasteryHistoryResponse, MasterySnapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Separate router for /module/{moduleId}/progress/stream (no /dashboard prefix)
module_router = APIRouter(prefix="/module", tags=["Dashboard"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

MODULE_SLUG_MAP: dict[str, int] = {
    "basics": 1,
    "control-flow": 2,
    "data-structures": 3,
    "functions": 4,
    "oop": 5,
    "files": 6,
    "errors": 7,
    "libraries": 8,
}


async def get_mastery_snapshot_repository(
    db=Depends(get_db),
) -> MasterySnapshotRepository:
    return MasterySnapshotRepository(db)


@router.get(
    "/mastery-history",
    response_model=MasteryHistoryResponse,
    summary="Get student mastery history (daily averages)",
)
async def get_mastery_history(
    current_user: User = Depends(get_current_user),
    snapshot_repo: MasterySnapshotRepository = Depends(get_mastery_snapshot_repository),
) -> MasteryHistoryResponse:
    """Return daily average mastery scores for the authenticated student."""
    rows = await snapshot_repo.get_daily_averages(str(current_user.id))
    snapshots = [MasterySnapshot(day=str(row["day"]), avg_score=round(row["avg_score"], 2)) for row in rows]
    return MasteryHistoryResponse(snapshots=snapshots)


@router.get(
    "/recommendations/stream",
    summary="Stream AI-generated recommendations via SSE",
)
async def stream_recommendations(
    current_user: User = Depends(get_current_user),
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    db=Depends(get_db),
) -> StreamingResponse:
    """Run the Progress Agent in recommendations mode and stream results as SSE."""

    async def generate() -> AsyncGenerator[str, None]:
        try:
            from agents import Runner
            from src.services.agents.agents import get_progress_agent
            from src.services.agents.context import LearnFlowContext
            from src.services.agents.model_provider import get_run_config
            from src.schemas.dashboard import RecommendationItem

            mastery_records = await mastery_repo.get_user_mastery_records(current_user.id)
            mastery_context = _build_mastery_context(mastery_records)

            ctx = LearnFlowContext(
                user_id=current_user.id,
                db=db,
                agent_mode="recommendations",
                mastery_context=mastery_context,
            )

            agent = get_progress_agent()
            run_config = get_run_config()

            result = await asyncio.wait_for(
                Runner.run(
                    agent,
                    input="Generate 1-3 personalised learning recommendations for this student based on their mastery scores.",
                    context=ctx,
                    run_config=run_config,
                ),
                timeout=30.0,
            )

            output = result.final_output
            recs: list[RecommendationItem] = []

            if hasattr(output, "recommendations") and output.recommendations:
                for rec_text in output.recommendations:
                    recs.append(RecommendationItem(text=str(rec_text)))
            elif hasattr(output, "model_dump"):
                data = output.model_dump()
                for k, v in data.items():
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                recs.append(RecommendationItem(text=item))
                            elif isinstance(item, dict) and "text" in item:
                                recs.append(RecommendationItem(**item))
                        if recs:
                            break
            elif isinstance(output, str):
                recs.append(RecommendationItem(text=output))

            if not recs:
                recs.append(RecommendationItem(text="Keep practising — complete exercises to unlock personalised recommendations."))

            for rec in recs:
                yield f"event: recommendation\ndata: {rec.model_dump_json()}\n\n"

            yield "event: done\ndata: {}\n\n"

        except asyncio.TimeoutError:
            yield 'event: error\ndata: {"detail": "Agent timed out"}\n\n'
        except Exception as exc:
            logger.exception("Recommendations stream error: %s", exc)
            yield f'event: error\ndata: {json.dumps({"detail": str(exc)})}\n\n'

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@module_router.get(
    "/{moduleId}/progress/stream",
    summary="Stream agent-generated module topic breakdown via SSE",
)
async def stream_module_progress(
    moduleId: str,
    current_user: User = Depends(get_current_user),
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    db=Depends(get_db),
) -> StreamingResponse:
    """Run the Progress Agent in module_detail mode and stream topic SSE events."""
    if moduleId not in MODULE_SLUG_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown module: '{moduleId}'")

    async def generate() -> AsyncGenerator[str, None]:
        try:
            from src.schemas.dashboard import TopicProgressItem

            MODULE_TOPICS: dict[str, list[str]] = {
                "basics": ["Variables", "Data Types", "Input/Output", "Operators", "Type Conversion"],
                "control-flow": ["Conditionals (if/elif/else)", "For Loops", "While Loops", "Break/Continue"],
                "data-structures": ["Lists", "Tuples", "Dictionaries", "Sets"],
                "functions": ["Defining Functions", "Parameters", "Return Values", "Scope"],
                "oop": ["Classes & Objects", "Attributes & Methods", "Inheritance", "Encapsulation"],
                "files": ["Reading/Writing Files", "CSV Processing", "JSON Handling"],
                "errors": ["Try/Except", "Exception Types", "Custom Exceptions", "Debugging"],
                "libraries": ["Installing Packages", "Working with APIs", "Virtual Environments"],
            }

            mastery_records = await mastery_repo.get_user_mastery_records(current_user.id)

            # No mastery data → skip LLM, mark all topics as remaining
            if not mastery_records:
                for t in MODULE_TOPICS.get(moduleId, []):
                    item = TopicProgressItem(topic=t, status="remaining", note="Complete exercises or a quiz to track your progress here.")
                    yield f"event: topic\ndata: {item.model_dump_json()}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            from agents import Runner
            from src.services.agents.agents import get_progress_agent
            from src.services.agents.context import LearnFlowContext
            from src.services.agents.model_provider import get_run_config

            mastery_context = _build_mastery_context(mastery_records)

            ctx = LearnFlowContext(
                user_id=current_user.id,
                db=db,
                agent_mode="module_detail",
                module_slug=moduleId,
                mastery_context=mastery_context,
            )

            agent = get_progress_agent()
            run_config = get_run_config()

            result = await asyncio.wait_for(
                Runner.run(
                    agent,
                    input=f"Assess the student's progress in the '{moduleId}' module topic by topic.",
                    context=ctx,
                    run_config=run_config,
                ),
                timeout=30.0,
            )

            output = result.final_output
            topics: list[TopicProgressItem] = []

            if hasattr(output, "recommendations") and output.recommendations:
                for rec in output.recommendations:
                    try:
                        import json as _json
                        parsed = _json.loads(rec) if isinstance(rec, str) else rec
                        if isinstance(parsed, dict) and "topic" in parsed and "status" in parsed:
                            topics.append(TopicProgressItem(**parsed))
                    except Exception:
                        pass

            # If agent returned nothing parseable, fall back to all-remaining
            if not topics:
                for t in MODULE_TOPICS.get(moduleId, []):
                    topics.append(TopicProgressItem(topic=t, status="remaining"))

            for topic in topics:
                yield f"event: topic\ndata: {topic.model_dump_json()}\n\n"

            yield "event: done\ndata: {}\n\n"

        except asyncio.TimeoutError:
            yield 'event: error\ndata: {"detail": "Agent timed out"}\n\n'
        except Exception as exc:
            logger.exception("Module progress stream error: %s", exc)
            yield f'event: error\ndata: {json.dumps({"detail": str(exc)})}\n\n'

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


def _build_mastery_context(mastery_records) -> str:
    if not mastery_records:
        return "No mastery data available — student is new."
    lines = []
    for r in mastery_records:
        topic = getattr(r, "topic", "unknown")
        score = getattr(r, "score", 0)
        level = getattr(r, "level", "Beginner")
        lines.append(f"- {topic}: {score:.0f}% ({level})")
    return "Student mastery scores:\n" + "\n".join(lines)
