"""SDK-native input guardrail for off-topic message detection.

The off_topic_guardrail uses an LLM-based classifier agent decorated with
@input_guardrail. The SDK runs it in parallel with the first specialist
agent call; if the tripwire fires, InputGuardrailTripwireTriggered is
raised before the specialist produces any output.
"""

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
