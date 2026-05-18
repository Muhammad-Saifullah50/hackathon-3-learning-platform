"""Dashboard service — agent orchestration and output transformation for dashboard SSE streams."""
import asyncio
import json
import logging
from typing import AsyncGenerator

from src.models import User
from src.repositories.mastery_repository import MasteryRepository

logger = logging.getLogger(__name__)

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


def build_mastery_context(mastery_records) -> str:
    if not mastery_records:
        return "No mastery data available — student is new."
    lines = []
    for r in mastery_records:
        topic = getattr(r, "topic", "unknown")
        score = getattr(r, "score", 0)
        level = getattr(r, "level", "Beginner")
        lines.append(f"- {topic}: {score:.0f}% ({level})")
    return "Student mastery scores:\n" + "\n".join(lines)


async def recommendations_generator(
    current_user: User,
    mastery_repo: MasteryRepository,
    db,
) -> AsyncGenerator[str, None]:
    try:
        from agents import Runner
        from src.services.agents.agents import get_progress_agent
        from src.services.agents.context import LearnFlowContext
        from src.services.agents.model_provider import get_run_config
        from src.schemas.dashboard import RecommendationItem

        mastery_records = await mastery_repo.get_user_mastery_records(current_user.id)
        mastery_context = build_mastery_context(mastery_records)

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
        yield 'event: error\ndata: {"detail": "An internal error occurred"}\n\n'


async def module_progress_generator(
    module_id: str,
    current_user: User,
    mastery_repo: MasteryRepository,
    db,
) -> AsyncGenerator[str, None]:
    try:
        from src.schemas.dashboard import TopicProgressItem

        mastery_records = await mastery_repo.get_user_mastery_records(current_user.id)

        # No mastery data → skip LLM, mark all topics as remaining
        if not mastery_records:
            for t in MODULE_TOPICS.get(module_id, []):
                item = TopicProgressItem(topic=t, status="remaining", note="Complete exercises or a quiz to track your progress here.")
                yield f"event: topic\ndata: {item.model_dump_json()}\n\n"
            yield "event: done\ndata: {}\n\n"
            return

        from agents import Runner
        from src.services.agents.agents import get_progress_agent
        from src.services.agents.context import LearnFlowContext
        from src.services.agents.model_provider import get_run_config

        mastery_context = build_mastery_context(mastery_records)

        ctx = LearnFlowContext(
            user_id=current_user.id,
            db=db,
            agent_mode="module_detail",
            module_slug=module_id,
            mastery_context=mastery_context,
        )

        agent = get_progress_agent()
        run_config = get_run_config()

        result = await asyncio.wait_for(
            Runner.run(
                agent,
                input=f"Assess the student's progress in the '{module_id}' module topic by topic.",
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
                    parsed = json.loads(rec) if isinstance(rec, str) else rec
                    if isinstance(parsed, dict) and "topic" in parsed and "status" in parsed:
                        topics.append(TopicProgressItem(**parsed))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as parse_err:
                    logger.debug("Failed to parse topic item from agent output: %s", parse_err)

        # If agent returned nothing parseable, fall back to all-remaining
        if not topics:
            for t in MODULE_TOPICS.get(module_id, []):
                topics.append(TopicProgressItem(topic=t, status="remaining"))

        for topic in topics:
            yield f"event: topic\ndata: {topic.model_dump_json()}\n\n"

        yield "event: done\ndata: {}\n\n"

    except asyncio.TimeoutError:
        yield 'event: error\ndata: {"detail": "Agent timed out"}\n\n'
    except Exception as exc:
        logger.exception("Module progress stream error: %s", exc)
        yield 'event: error\ndata: {"detail": "An internal error occurred"}\n\n'
