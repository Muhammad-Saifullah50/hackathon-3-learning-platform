"""LearnFlow agent definitions using the OpenAI Agents SDK.

Builds 6 agents (Triage, Concepts, Debug, CodeReview, Exercise, Progress)
using SDK primitives: Agent, function_tool, handoff, ModelSettings.
"""

import uuid
from typing import Optional

from agents import Agent, ModelSettings, RunContextWrapper, Runner, function_tool, handoff

from src.services.agents.guardrails import off_topic_guardrail

from src.llm.prompts import (
    get_code_review_agent_prompt,
    get_concept_agent_prompt,
    get_debug_agent_prompt,
    get_exercise_agent_prompt,
    get_module_detail_prompt,
    get_progress_agent_prompt,
    get_recommendations_prompt,
)
from src.repositories.exercise_repository import ExerciseRepository
from src.repositories.mastery_repository import MasteryRepository
from src.repositories.progress_repository import ProgressRepository
from src.repositories.user_repository import UserStreakRepository
from src.schemas.agent_responses import (
    CodeReviewResponse,
    ConceptResponse,
    DebugResponse,
    ExerciseAgentResponse,
    ProgressAgentResponse,
    QuizResponse,
)
from src.services.agents.context import LearnFlowContext
from src.services.agents.triage import classify_intent


def _build_level_instructions(level: Optional[str]) -> str:
    """Return level-specific additions to the system prompt."""
    if level == "beginner":
        return (
            " The student is a BEGINNER. Use simple analogies, avoid jargon, "
            "explain step-by-step, and include a basic runnable code example."
        )
    if level == "intermediate":
        return (
            " The student is at an INTERMEDIATE level. Provide moderate depth "
            "with some technical terms and a practical code example."
        )
    if level == "advanced":
        return (
            " The student is ADVANCED. Provide technical depth, implementation "
            "details, performance considerations, and sophisticated code examples."
        )
    return ""


@function_tool
def get_exercise(ctx: RunContextWrapper[LearnFlowContext], topic: str, difficulty: str) -> str:
    """Generate a coding exercise on a given topic and difficulty level."""
    return (
        f"Generate a {difficulty}-level Python exercise on '{topic}'. "
        f"Include: problem description, starter code, test cases as JSON, "
        f"and a reference solution."
    )


@function_tool
def get_progress_summary(ctx: RunContextWrapper[LearnFlowContext]) -> str:
    """Fetch the student's current mastery scores and streak data."""
    lf_ctx = ctx.context
    return (
        f"Fetch progress data for user {lf_ctx.user_id}. "
        f"Calculate mastery using the 40/30/20/10 formula "
        f"(exercises/quizzes/code_quality/streak). "
        f"Identify weak areas (score < 50%) and provide recommendations."
    )


@function_tool
def run_static_analysis(ctx: RunContextWrapper[LearnFlowContext], code: str) -> str:
    """Run PEP 8 static analysis on the provided Python code."""
    import subprocess
    import tempfile

    violations = []
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        filepath = f.name

    for checker in ["ruff", "pycodestyle"]:
        try:
            result = subprocess.run(
                [checker, filepath],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.stdout:
                violations.extend(result.stdout.strip().split("\n"))
            break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if violations:
        return "PEP 8 violations:\n" + "\n".join(violations[:10])
    return "No PEP 8 violations found."


def get_triage_agent() -> Agent[LearnFlowContext]:
    """Triage agent that routes student queries to specialist agents via handoffs."""
    concepts = get_concepts_agent()
    debug = get_debug_agent()
    code_review = get_code_review_agent()
    exercise = get_exercise_agent()
    progress = get_progress_agent()

    return Agent(
        name="triage",
        instructions=(
            "You are a triage agent that routes student queries to the appropriate specialist. "
            "Analyze the student's question and determine which specialist can best help: "
            "If they want a concept explained, hand off to concepts. "
            "If they have code that's broken or has errors, hand off to debug. "
            "If they want their code reviewed for quality, hand off to code_review. "
            "If they want practice exercises or challenges, hand off to exercise. "
            "If they want to know about their learning progress, hand off to progress. "
            "If unsure, answer the question yourself as a general tutor."
        ),
        handoffs=[
            handoff(concepts),
            handoff(debug),
            handoff(code_review),
            handoff(exercise),
            handoff(progress),
        ],
        input_guardrails=[off_topic_guardrail],
        model_settings=ModelSettings(temperature=0.3),
    )


def get_concepts_agent() -> Agent[LearnFlowContext]:
    """Concepts agent that explains Python concepts at the right level."""

    def dynamic_instructions(
        context: RunContextWrapper[LearnFlowContext], agent: Agent[LearnFlowContext]
    ) -> str:
        lf_ctx = context.context
        base = get_concept_agent_prompt()
        level_text = _build_level_instructions(lf_ctx.level)
        topic_context = f"\n\nThe student is asking about: {lf_ctx.topic}" if lf_ctx.topic else ""
        return f"{base}{level_text}{topic_context} Always include a runnable code example. After your explanation, ask 2-3 follow-up questions."

    return Agent(
        name="concepts",
        instructions=dynamic_instructions,
        output_type=ConceptResponse,
        input_guardrails=[off_topic_guardrail],
        model_settings=ModelSettings(temperature=0.7),
    )


def get_debug_agent() -> Agent[LearnFlowContext]:
    """Debug agent that provides progressive hints for broken code."""

    def dynamic_instructions(
        context: RunContextWrapper[LearnFlowContext], agent: Agent[LearnFlowContext]
    ) -> str:
        base = get_debug_agent_prompt()
        code_context = ""
        if context.context.code_snippet:
            code_context = f"\n\nStudent's code:\n```python\n{context.context.code_snippet}\n```"
        return f"{base} Follow the progressive hint system: Level 1 = high-level error category, Level 2 = specific location and cause, Level 3 = concrete fix. Never reveal the full solution unless explicitly requested.{code_context}"

    return Agent(
        name="debug",
        instructions=dynamic_instructions,
        output_type=DebugResponse,
        input_guardrails=[off_topic_guardrail],
        model_settings=ModelSettings(temperature=0.5),
    )


def get_code_review_agent() -> Agent[LearnFlowContext]:
    """Code review agent that analyzes code for correctness, style, and efficiency."""

    def dynamic_instructions(
        context: RunContextWrapper[LearnFlowContext], agent: Agent[LearnFlowContext]
    ) -> str:
        base = get_code_review_agent_prompt()
        code_context = ""
        if context.context.code_snippet:
            code_context = f"\n\nCode to review:\n```python\n{context.context.code_snippet}\n```"
        question_context = ""
        if context.context.question_description:
            question_context = f"\n\nExercise question: {context.context.question_description}"
        return (
            f"{base}{question_context}{code_context}\n\n"
            "INSTRUCTIONS:\n"
            "1. Call run_static_analysis with the code to get PEP 8 violations.\n"
            "2. After receiving tool results, evaluate the code for correctness, style, efficiency, and readability.\n"
            "3. Assign a realistic score: 90-100 = excellent; 70-89 = good with minor issues; "
            "50-69 = works but needs improvement; 20-49 = significant issues; 0-19 = non-functional.\n"
            "4. Write a concise summary (2-4 sentences) covering what the code does well and what to improve.\n"
            "5. NEVER set score=0 unless the code is completely non-functional or empty.\n"
            "6. Always start with positive reinforcement."
        )

    return Agent(
        name="code_review",
        instructions=dynamic_instructions,
        output_type=CodeReviewResponse,
        tools=[run_static_analysis],
        input_guardrails=[off_topic_guardrail],
        model_settings=ModelSettings(temperature=0.5),
    )


def get_exercise_agent() -> Agent[LearnFlowContext]:
    """Exercise agent that generates coding challenges and grades submissions."""

    def dynamic_instructions(
        context: RunContextWrapper[LearnFlowContext], agent: Agent[LearnFlowContext]
    ) -> str:
        base = get_exercise_agent_prompt()
        topic_context = ""
        if context.context.topic:
            topic_context = f"\n\nTopic: {context.context.topic}"
        difficulty = context.context.level or "beginner"
        return (
            f"{base}{topic_context}\n\n"
            f"Generate a {difficulty}-level Python exercise. "
            "Your JSON response MUST include: title (string), description (string), "
            f"difficulty='{difficulty}', starter_code={{code: '...', language: 'python'}}, "
            "expected_concepts (list), send_to_editor (null or CodeBlock). "
            "Do NOT omit title, difficulty, or starter_code."
        )

    return Agent(
        name="exercise",
        instructions=dynamic_instructions,
        output_type=ExerciseAgentResponse,
        tools=[get_exercise],
        input_guardrails=[off_topic_guardrail],
        model_settings=ModelSettings(temperature=0.1),
    )


def get_quiz_agent() -> Agent[LearnFlowContext]:
    """Quiz agent that generates a 6-card quiz (3 MCQ + 3 flashcard) on a Python topic."""

    def dynamic_instructions(
        context: RunContextWrapper[LearnFlowContext], agent: Agent[LearnFlowContext]
    ) -> str:
        topic_hint = f" The topic is explicitly: {context.context.topic}." if context.context.topic else (
            " Read the full conversation provided in the input and identify what Python topic "
            "the student was learning about. Quiz them on THAT topic — do not default to "
            "unrelated curriculum topics."
        )
        return (
            "You are a Python quiz generator. Generate a quiz with exactly 3 multiple-choice "
            "questions followed by exactly 3 flashcard questions.\n\n"
            "Rules:\n"
            "- module_slug MUST be one of: basics, control_flow, data_structures, functions, "
            "oop, files, errors, libraries\n"
            "- topic_label is a short human-readable label (e.g. 'For Loops', 'Starlette')\n"
            "- Each MCQ has exactly 4 options and a correct_index (0-3)\n"
            "- Each flashcard has a term and a definition\n"
            "- mcq_questions must have exactly 3 items\n"
            "- flashcard_questions must have exactly 3 items\n"
            "- quiz_session_id must be null (set server-side)\n"
            "- IMPORTANT: Any Python code, expressions, or identifiers in question text or "
            "options MUST be wrapped in backticks (e.g. `if x > 3: print('Yes')`, `list.append()`, "
            "`True`). Multi-line code snippets must use fenced code blocks (```python ... ```).\n"
            f"{topic_hint}"
        )

    return Agent(
        name="quiz",
        instructions=dynamic_instructions,
        output_type=QuizResponse,
        input_guardrails=[off_topic_guardrail],
        model_settings=ModelSettings(temperature=0.5),
    )


def get_progress_agent() -> Agent[LearnFlowContext]:
    """Progress agent that summarizes learning progress, mastery, and recommendations."""

    def dynamic_instructions(
        context: RunContextWrapper[LearnFlowContext], agent: Agent[LearnFlowContext]
    ) -> str:
        lf_ctx = context.context
        mastery_ctx = lf_ctx.mastery_context or ""

        if lf_ctx.agent_mode == "recommendations":
            return get_recommendations_prompt(mastery_ctx)

        if lf_ctx.agent_mode == "module_detail" and lf_ctx.module_slug:
            return get_module_detail_prompt(lf_ctx.module_slug, mastery_ctx)

        base = get_progress_agent_prompt()
        user_context = (
            f"Student user_id: {lf_ctx.user_id}. "
            "Mastery formula: exercises 40%, quizzes 30%, code quality 20%, streak 10%. "
            "Mastery levels: 0-40% Beginner, 41-70% Learning, 71-90% Proficient, 91-100% Mastered. "
            "If no data is available, encourage the student and suggest starting with Module 1 (Basics)."
        )
        return f"{base} {user_context} Use an encouraging tone."

    return Agent(
        name="progress",
        instructions=dynamic_instructions,
        output_type=ProgressAgentResponse,
        tools=[get_progress_summary],
        input_guardrails=[off_topic_guardrail],
        model_settings=ModelSettings(temperature=0.7),
    )
