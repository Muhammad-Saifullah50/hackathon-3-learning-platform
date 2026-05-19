"""SDK-native guardrails for the LearnFlow platform.

Includes:
- off_topic_guardrail: SDK @input_guardrail for chat agents
- teacher_exercise_guardrail: standalone function for teacher prompt validation

The off_topic_guardrail uses an LLM-based classifier agent decorated with
@input_guardrail. The SDK runs it in parallel with the first specialist
agent call; if the tripwire fires, InputGuardrailTripwireTriggered is
raised before the specialist produces any output.
"""

from typing import Optional
from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    ModelSettings,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

from src.services.agents.model_provider import get_run_config


class OffTopicCheck(BaseModel):
    is_off_topic: bool
    reasoning: str


_off_topic_classifier = Agent(
    name="off-topic-classifier",
    instructions=(
        "You are a content classifier for a Python programming learning platform. "
        "Decide whether the user's message is off-topic for this platform.\n\n"
        "OFF-TOPIC (is_off_topic=true): poems, creative writing, cooking recipes, "
        "sports scores, weather, geography, history, politics, music lyrics, "
        "jokes, horoscopes, personal advice unrelated to programming.\n\n"
        "ON-TOPIC (is_off_topic=false): Python syntax, debugging, algorithms, "
        "data structures, OOP, libraries, code review, software engineering concepts, "
        "computer science theory, programming exercises, coding best practices.\n\n"
        "When in doubt, return is_off_topic=false — it is better to let a borderline "
        "question through than to incorrectly block a learning question."
    ),
    output_type=OffTopicCheck,
    model_settings=ModelSettings(temperature=0.0),
)


@input_guardrail
async def off_topic_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Raise InputGuardrailTripwireTriggered for clearly non-Python messages."""
    result = await Runner.run(
        _off_topic_classifier,
        input,
        context=ctx.context,
        run_config=get_run_config(),
    )
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


# --- Teacher exercise prompt guardrail ---

class TeacherPromptCheck(BaseModel):
    is_valid: bool
    missing: list[str]
    message: str
    code: str  # "OK" | "PROMPT_INVALID" | "NOT_PYTHON_TOPIC"


_teacher_prompt_classifier = Agent(
    name="teacher-prompt-classifier",
    instructions=(
        "You validate teacher prompts for Python exercise generation on LearnFlow.\n\n"
        "A valid prompt MUST:\n"
        "1. Be about a Python programming topic (not cooking, history, sports, etc.)\n"
        "2. Specify a difficulty level (beginner, intermediate, or advanced)\n"
        "3. Specify a topic or concept (e.g. loops, functions, OOP)\n"
        "4. Request coding exercises (not just theory questions)\n\n"
        "Return:\n"
        "- is_valid=true, code='OK', missing=[], message='' if all conditions are met\n"
        "- is_valid=false, code='NOT_PYTHON_TOPIC', missing=[], message='...' if not Python\n"
        "- is_valid=false, code='PROMPT_INVALID', missing=[list of missing items], message='...' "
        "if it is Python but requirements are incomplete\n\n"
        "Be lenient — if difficulty/topic can be reasonably inferred, treat them as present."
    ),
    output_type=TeacherPromptCheck,
    model_settings=ModelSettings(temperature=0.0),
)


async def teacher_exercise_guardrail(prompt: str) -> TeacherPromptCheck:
    """Validate a teacher's exercise generation prompt. Returns structured validation result."""
    result = await Runner.run(
        _teacher_prompt_classifier,
        prompt,
        run_config=get_run_config(),
    )
    return result.final_output
