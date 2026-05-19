"""TeacherExerciseService — generate and assign multi-question exercises."""

import uuid
from typing import Any, Literal

from agents import Agent, ModelSettings, Runner
from pydantic import BaseModel, field_validator

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.class_exercise_repository import ClassExerciseRepository
from src.repositories.class_membership_repository import ClassMembershipRepository
from src.repositories.class_repository import ClassRepository
from src.repositories.teacher_exercise_repository import TeacherExerciseRepository
from src.services.agents.guardrails import teacher_exercise_guardrail
from src.services.agents.model_provider import get_run_config

_VALID_DIFFICULTIES = ('beginner', 'intermediate', 'advanced')
_VALID_MODULES = ('basics', 'control_flow', 'data_structures', 'functions', 'oop', 'files', 'errors', 'libraries')


class TeacherExerciseQuestion(BaseModel):
    index: int
    description: str
    starter_code: str


class TeacherMultiExerciseResponse(BaseModel):
    title: str
    topic: str
    difficulty: Literal['beginner', 'intermediate', 'advanced']
    target_module: Literal['basics', 'control_flow', 'data_structures', 'functions', 'oop', 'files', 'errors', 'libraries']
    questions: list[TeacherExerciseQuestion]

    @field_validator('title', 'topic', mode='after')
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or v.strip() in ('', ':'):
            raise ValueError('Field must not be empty or a placeholder')
        return v

    @field_validator('questions', mode='after')
    @classmethod
    def has_questions(cls, v: list) -> list:
        if not v:
            raise ValueError('questions list must not be empty')
        return v


_EXERCISE_EXAMPLE = '''{
  "title": "Python Lists Practice Set",
  "topic": "Python Lists",
  "difficulty": "beginner",
  "target_module": "data_structures",
  "questions": [
    {
      "index": 0,
      "description": "Write a function that returns the first element of a list.",
      "starter_code": "def first_element(items):\\n    # TODO: return the first item\\n    pass"
    },
    {
      "index": 1,
      "description": "Write a function that appends a value to a list and returns it.",
      "starter_code": "def append_item(items, value):\\n    # TODO: append value and return the list\\n    pass"
    },
    {
      "index": 2,
      "description": "Write a function that returns the length of a list.",
      "starter_code": "def list_length(items):\\n    # TODO: return the number of items\\n    pass"
    }
  ]
}'''

_teacher_exercise_agent = Agent(
    name="teacher-exercise-generator",
    instructions=(
        "You are an expert Python exercise generator for teachers on LearnFlow.\n\n"
        "Given a teacher's prompt, generate a multi-question coding exercise set.\n\n"
        "Rules:\n"
        "- Generate exactly 3 coding questions (no more, no less)\n"
        "- Each question must have a clear description and starter Python code\n"
        "- difficulty MUST be exactly one of: 'beginner', 'intermediate', 'advanced'\n"
        "- target_module MUST be exactly one of: 'basics', 'control_flow', 'data_structures', 'functions', 'oop', 'files', 'errors', 'libraries'\n"
        "- title: a short descriptive name like 'Python Lists Practice Set' — NEVER just ':' or empty\n"
        "- topic: the specific concept covered like 'Python Lists' — NEVER just ':' or empty\n"
        "- Questions should be progressive (easier first)\n"
        "- starter_code must be valid Python with a function signature or scaffold\n\n"
        "EXAMPLE OUTPUT (follow this exact JSON structure):\n"
        f"{_EXERCISE_EXAMPLE}\n\n"
        "IMPORTANT: Output ONLY valid JSON matching the structure above. "
        "The title and topic fields MUST contain real descriptive text based on the teacher's request."
    ),
    output_type=TeacherMultiExerciseResponse,
    model_settings=ModelSettings(temperature=0.3),
)


class TeacherExerciseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repo = TeacherExerciseRepository(session)
        self._class_repo = ClassRepository(session)
        self._class_exercise_repo = ClassExerciseRepository(session)
        self._membership_repo = ClassMembershipRepository(session)

    async def generate(self, prompt: str, teacher_id: uuid.UUID) -> dict[str, Any]:
        # 1. Run guardrail
        validation = await teacher_exercise_guardrail(prompt)
        if not validation.is_valid:
            return {
                "error": "guardrail",
                "code": validation.code,
                "missing": validation.missing,
                "message": validation.message,
            }

        # 2. Call the teacher exercise agent (retry once on validation failure)
        exercise_data: TeacherMultiExerciseResponse | None = None
        last_exc: Exception | None = None
        for attempt, agent_prompt in enumerate([
            prompt,
            (
                f"{prompt}\n\n"
                "REMINDER: The 'title' field must be a real exercise name (e.g. 'Python Lists Practice Set'). "
                "The 'topic' field must be the concept name (e.g. 'Python Lists'). "
                "Do NOT output ':' or empty strings for any field."
            ),
        ]):
            try:
                result = await Runner.run(
                    _teacher_exercise_agent,
                    agent_prompt,
                    run_config=get_run_config(),
                )
                exercise_data = result.final_output
                break
            except Exception as exc:
                last_exc = exc
                if attempt == 0:
                    continue
        if exercise_data is None:
            return {
                "error": "generation_failed",
                "detail": f"Exercise generation failed: {last_exc}",
            }

        # Sanity-check parsed output before touching the DB
        if (
            not exercise_data
            or not exercise_data.questions
            or exercise_data.difficulty not in _VALID_DIFFICULTIES
            or exercise_data.target_module not in _VALID_MODULES
            or not exercise_data.title.strip()
        ):
            return {
                "error": "generation_failed",
                "detail": "The AI returned an incomplete exercise. Please try again with a more specific prompt.",
            }

        # 3. Persist
        questions_json = [q.model_dump() for q in exercise_data.questions]
        exercise = await self._repo.create(
            title=exercise_data.title,
            topic=exercise_data.topic,
            difficulty=exercise_data.difficulty,
            target_module=exercise_data.target_module,
            generation_prompt=prompt,
            questions=questions_json,
            created_by_id=teacher_id,
        )

        return {
            "id": str(exercise.id),
            "title": exercise.title,
            "topic": exercise.topic,
            "difficulty": exercise.difficulty,
            "target_module": exercise.target_module,
            "questions": questions_json,
        }

    async def assign(self, exercise_id: uuid.UUID, class_id: uuid.UUID, teacher_id: uuid.UUID) -> dict[str, Any]:
        # Verify exercise exists
        exercise = await self._repo.get_by_id(exercise_id)
        if not exercise:
            return {"error": "not_found", "detail": "Exercise not found."}

        # Verify class ownership
        class_ = await self._class_repo.get_by_id(class_id)
        if not class_ or class_.teacher_id != teacher_id:
            return {"error": "not_found", "detail": "Class not found."}

        # Check for duplicate assignment
        existing = await self._class_exercise_repo.get_by_class_and_exercise(class_id, exercise_id)
        if existing:
            return {"error": "conflict", "detail": "Exercise already assigned to this class."}

        # Create class exercise
        class_exercise = await self._class_exercise_repo.create(
            class_id=class_id,
            exercise_id=exercise_id,
            assigned_by_id=teacher_id,
        )

        # Count accepted members
        accepted_members = await self._membership_repo.list_accepted_by_class(class_id)
        count = len(accepted_members)

        warning = None
        if count == 0:
            warning = "No accepted members in this class yet. Exercise will be visible once students accept their invitations."

        return {
            "class_exercise_id": str(class_exercise.id),
            "assigned_to_count": count,
            "warning": warning,
        }
