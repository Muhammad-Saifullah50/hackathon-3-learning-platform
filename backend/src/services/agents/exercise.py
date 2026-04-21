import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent_exercise import AgentExerciseSubmission
from src.repositories.exercise_repository import ExerciseRepository
from src.services.sandbox.docker_sandbox import DockerSandbox


class ExerciseService:
    """Service to manage exercise generation and grading."""

    def __init__(self, db: AsyncSession, exercise_repo: ExerciseRepository):
        self.db = db
        self.exercise_repo = exercise_repo
        self.sandbox = DockerSandbox()

    async def generate_exercise(
        self,
        topic: str,
        difficulty: str,
        description: str,
        test_cases: List[dict],
        starter_code: Optional[str] = None,
        solution_code: Optional[str] = None,
        creator: str = "system",
        created_by_user_id: Optional[uuid.UUID] = None,
    ):
        """Persist a generated exercise into the database.

        The actual prompt/LLM generation is handled by the agent layer elsewhere;
        this service accepts structured exercise data and persists it.
        """
        exercise = await self.exercise_repo.create_exercise(
            topic=topic,
            difficulty=difficulty,
            description=description,
            test_cases=test_cases,
            starter_code=starter_code,
            solution_code=solution_code,
            creator=creator,
            created_by_user_id=created_by_user_id,
        )
        return exercise

    async def grade_submission(
        self, exercise, submitted_code: str, user_id: uuid.UUID, timeout_s: int = 5
    ):
        """Run the submitted code against exercise test cases using the sandbox.

        Returns a dict with score, per-test results, feedback and execution time.
        """
        test_cases = exercise.test_cases
        # Run tests in sandbox
        results = await self.sandbox.run_test_cases(submitted_code, test_cases, timeout=timeout_s)

        passed = sum(1 for r in results if r.get("passed"))
        total = len(results) if results else 0
        score = round(100.0 * passed / total, 2) if total > 0 else 0.0

        # Simple feedback aggregation
        failed_msgs = [r.get("error") for r in results if not r.get("passed")]
        feedback = (
            "All tests passed. Great job!"
            if passed == total and total > 0
            else "\n".join([m for m in failed_msgs if m]) or "Some tests failed."
        )

        # Persisting submission record could be done here if repository exists for submissions.
        submission_payload = {
            "score": score,
            "test_results": results,
            "feedback": feedback,
            "execution_time_ms": None,
        }

        return submission_payload
