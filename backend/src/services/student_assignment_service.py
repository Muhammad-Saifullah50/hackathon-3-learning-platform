"""StudentAssignmentService — student exercise completion with AI review."""

import uuid
from typing import Any, Optional

from agents import Runner
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.class_exercise_repository import ClassExerciseRepository
from src.repositories.class_membership_repository import ClassMembershipRepository
from src.repositories.class_repository import ClassRepository
from src.repositories.teacher_exercise_repository import (
    ClassExerciseSubmissionRepository,
    QuestionReviewRepository,
    TeacherExerciseRepository,
    TeacherNotificationRepository,
)
from src.schemas.student_classes import (
    AssignedExerciseDetail,
    AssignedExerciseSummary,
    QuestionDetail,
    QuestionReviewResult,
    SubmitResponse,
)
from src.services.agents.context import LearnFlowContext
from src.services.agents.model_provider import get_run_config


class StudentAssignmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._class_exercise_repo = ClassExerciseRepository(session)
        self._membership_repo = ClassMembershipRepository(session)
        self._class_repo = ClassRepository(session)
        self._teacher_exercise_repo = TeacherExerciseRepository(session)
        self._submission_repo = ClassExerciseSubmissionRepository(session)
        self._review_repo = QuestionReviewRepository(session)
        self._notification_repo = TeacherNotificationRepository(session)

    async def list_assigned_exercises(self, student_id: uuid.UUID) -> list[AssignedExerciseSummary]:
        class_exercises = await self._class_exercise_repo.list_assigned_to_student(student_id)
        result = []
        for ce in class_exercises:
            exercise = await self._teacher_exercise_repo.get_by_id(ce.exercise_id)
            class_ = await self._class_repo.get_by_id(ce.class_id)
            if not exercise or not class_:
                continue
            submission = await self._submission_repo.get_by_class_exercise_and_student(ce.id, student_id)
            status = submission.status if submission else "in_progress"
            result.append(AssignedExerciseSummary(
                class_exercise_id=ce.id,
                exercise_id=exercise.id,
                title=exercise.title,
                topic=exercise.topic,
                difficulty=exercise.difficulty,
                class_name=class_.name,
                status=status,
            ))
        return result

    async def get_exercise_detail(
        self, class_exercise_id: uuid.UUID, student_id: uuid.UUID
    ) -> Optional[AssignedExerciseDetail]:
        ce = await self._class_exercise_repo.get_by_id(class_exercise_id)
        if not ce:
            return None

        # Verify student is an accepted member of the class
        membership = await self._membership_repo.get_by_class_and_student(ce.class_id, student_id)
        if not membership or membership.status != "accepted":
            return None

        exercise = await self._teacher_exercise_repo.get_by_id(ce.exercise_id)
        class_ = await self._class_repo.get_by_id(ce.class_id)
        if not exercise or not class_:
            return None

        submission = await self._submission_repo.get_by_class_exercise_and_student(ce.id, student_id)
        reviews = []
        if submission:
            raw_reviews = await self._review_repo.list_by_submission(submission.id)
            reviews = [
                QuestionReviewResult(
                    question_index=r.question_index,
                    student_code=r.student_code,
                    ai_review=r.ai_review,
                    grade=r.grade,
                )
                for r in raw_reviews
            ]

        questions = [
            QuestionDetail(
                index=q["index"],
                description=q["description"],
                starter_code=q["starter_code"],
            )
            for q in exercise.questions
        ]

        return AssignedExerciseDetail(
            class_exercise_id=ce.id,
            exercise_id=exercise.id,
            title=exercise.title,
            topic=exercise.topic,
            difficulty=exercise.difficulty,
            class_name=class_.name,
            questions=questions,
            reviews=reviews,
            status=submission.status if submission else "in_progress",
            overall_score=submission.overall_score if submission else None,
        )

    async def review_question(
        self,
        class_exercise_id: uuid.UUID,
        student_id: uuid.UUID,
        question_index: int,
        student_code: str,
    ) -> dict[str, Any]:
        ce = await self._class_exercise_repo.get_by_id(class_exercise_id)
        if not ce:
            return {"error": "not_found", "detail": "Exercise not found."}

        # Verify membership
        membership = await self._membership_repo.get_by_class_and_student(ce.class_id, student_id)
        if not membership or membership.status != "accepted":
            return {"error": "forbidden", "detail": "Access denied."}

        exercise = await self._teacher_exercise_repo.get_by_id(ce.exercise_id)
        if not exercise:
            return {"error": "not_found", "detail": "Exercise not found."}

        # Check question exists
        if question_index < 0 or question_index >= len(exercise.questions):
            return {"error": "bad_request", "detail": "Invalid question index."}

        # Get or create submission
        submission = await self._submission_repo.get_or_create(ce.id, student_id)
        if submission.status == "submitted":
            return {"error": "conflict", "detail": "Exercise already submitted."}

        # Call Code Review Agent
        from src.services.agents.agents import get_code_review_agent
        question_desc = exercise.questions[question_index].get("description", "") if exercise.questions else ""
        ctx = LearnFlowContext(
            user_id=student_id,
            code_snippet=student_code,
            question_description=question_desc,
        )
        agent = get_code_review_agent()
        run_result = await Runner.run(
            agent,
            f"Review this Python solution for the exercise question: \"{question_desc}\"\n\nStudent code:\n```python\n{student_code}\n```",
            context=ctx,
            run_config=get_run_config(),
        )
        review_data = run_result.final_output

        # Persist review (upsert)
        review = await self._review_repo.upsert(
            submission_id=submission.id,
            question_index=question_index,
            student_code=student_code,
            ai_review=review_data.summary,
            grade=float(review_data.score),
        )

        return {
            "question_index": review.question_index,
            "ai_review": review.ai_review,
            "grade": review.grade,
        }

    async def submit_exercise(self, class_exercise_id: uuid.UUID, student_id: uuid.UUID) -> dict[str, Any]:
        ce = await self._class_exercise_repo.get_by_id(class_exercise_id)
        if not ce:
            return {"error": "not_found", "detail": "Exercise not found."}

        exercise = await self._teacher_exercise_repo.get_by_id(ce.exercise_id)
        if not exercise:
            return {"error": "not_found", "detail": "Exercise not found."}

        submission = await self._submission_repo.get_by_class_exercise_and_student(ce.id, student_id)
        if not submission:
            return {"error": "not_ready", "detail": "No reviews submitted yet."}
        if submission.status == "submitted":
            return {"error": "conflict", "detail": "Exercise already submitted."}

        reviews = await self._review_repo.list_by_submission(submission.id)
        total_questions = len(exercise.questions)

        if len(reviews) < total_questions:
            return {
                "error": "not_ready",
                "detail": f"All {total_questions} questions must be reviewed before submitting.",
            }

        # Calculate overall score
        overall_score = sum(r.grade for r in reviews) / len(reviews) if reviews else 0.0

        updated = await self._submission_repo.mark_submitted(submission, overall_score)

        # Determine teacher for notification
        class_ = await self._class_repo.get_by_id(ce.class_id)
        if class_:
            await self._notification_repo.create(
                teacher_id=class_.teacher_id,
                student_id=student_id,
                submission_id=updated.id,
            )

        return SubmitResponse(
            submission_id=updated.id,
            overall_score=overall_score,
            submitted_at=str(updated.submitted_at),
        )
