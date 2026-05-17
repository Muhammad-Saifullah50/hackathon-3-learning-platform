"""Quiz endpoints.

GET  /api/v1/quiz                          → list quiz sessions for authenticated student
GET  /api/v1/quiz/{session_id}             → full quiz session state
POST /api/v1/quiz/{session_id}/grade-flashcard → AI grade a single flashcard answer
POST /api/v1/quiz/{session_id}/submit      → submit all answers, compute score, update mastery
"""

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.dependencies import get_db, get_mastery_repository
from src.llm.client import LlmClient
from src.models import User
from src.repositories.mastery_repository import MasteryRepository
from src.repositories.quiz_session_repository import QuizSessionRepository
from src.schemas.quiz import (
    GradeFlashcardRequest,
    GradeFlashcardResponse,
    QuizListItem,
    QuizSessionState,
    PerCardResult,
    SubmitQuizRequest,
    SubmitQuizResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


async def get_quiz_repo(db: AsyncSession = Depends(get_db)) -> QuizSessionRepository:
    return QuizSessionRepository(db)


def _ownership_check(quiz, current_user: User):
    if str(quiz.student_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your quiz session")


def _mastery_level(score: float) -> str:
    if score <= 40:
        return "Beginner"
    if score <= 70:
        return "Learning"
    if score <= 90:
        return "Proficient"
    return "Mastered"


# ── GET /api/v1/quiz ──────────────────────────────────────────────────────────

@router.get("", response_model=list[QuizListItem])
async def list_quiz_sessions(
    quiz_repo: QuizSessionRepository = Depends(get_quiz_repo),
    current_user: User = Depends(get_current_user),
):
    """Return all quiz sessions for the authenticated student."""
    sessions = await quiz_repo.list_by_student(current_user.id)
    return [
        QuizListItem(
            quiz_session_id=s.id,
            agent_session_id=s.chat_session_id,
            module_slug=s.module_slug,
            topic_label=s.topic_label,
            score=s.score,
            status=s.status,
            created_at=s.created_at,
        )
        for s in sessions
    ]


# ── GET /api/v1/quiz/{session_id} ─────────────────────────────────────────────

@router.get("/{session_id}", response_model=QuizSessionState)
async def get_quiz_session(
    session_id: str,
    quiz_repo: QuizSessionRepository = Depends(get_quiz_repo),
    current_user: User = Depends(get_current_user),
):
    """Return full quiz session state."""
    try:
        quiz_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    quiz = await quiz_repo.get_by_id(quiz_uuid)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    _ownership_check(quiz, current_user)

    return QuizSessionState(
        quiz_session_id=quiz.id,
        agent_session_id=quiz.chat_session_id,
        module_slug=quiz.module_slug,
        topic_label=quiz.topic_label,
        status=quiz.status,
        score=quiz.score,
        questions=quiz.questions,
        student_answers=quiz.student_answers or {},
        grades=quiz.grades or {},
        completed_at=quiz.completed_at,
        created_at=quiz.created_at,
    )


# ── POST /api/v1/quiz/{session_id}/grade-flashcard ───────────────────────────

@router.post("/{session_id}/grade-flashcard", response_model=GradeFlashcardResponse)
async def grade_flashcard(
    session_id: str,
    request: GradeFlashcardRequest,
    quiz_repo: QuizSessionRepository = Depends(get_quiz_repo),
    current_user: User = Depends(get_current_user),
):
    """AI-grade a single flashcard answer."""
    try:
        quiz_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    quiz = await quiz_repo.get_by_id(quiz_uuid)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    _ownership_check(quiz, current_user)

    card_index = request.card_index
    if card_index < 3 or card_index > 5:
        raise HTTPException(status_code=400, detail="card_index must be 3–5 for flashcards")

    questions = quiz.questions or []
    if card_index >= len(questions):
        raise HTTPException(status_code=400, detail="Card index out of range")

    card = questions[card_index]
    if card.get("type") != "flashcard":
        raise HTTPException(status_code=400, detail="Card at index is not a flashcard")

    definition = card.get("definition", "")
    student_answer = request.student_answer

    grading_prompt = (
        f"You are grading a Python flashcard answer.\n\n"
        f"Term: {card.get('term', '')}\n"
        f"Correct definition: {definition}\n"
        f"Student answer: {student_answer}\n\n"
        "Grade the student's answer as one of: Correct, Partial, or Wrong.\n"
        "Respond in JSON: {{\"grade\": \"Correct|Partial|Wrong\", \"feedback\": \"one-line feedback\"}}"
    )

    llm = LlmClient()
    grade_result: dict = {"grade": "Wrong", "feedback": "Could not grade."}
    try:
        chunks = []
        async for text, _ in llm.stream_completion(
            messages=[{"role": "user", "content": grading_prompt}],
            max_tokens=100,
            temperature=0.0,
        ):
            chunks.append(text)
        raw = "".join(chunks).strip()
        # Extract JSON from possible markdown code block
        if "```" in raw:
            raw = raw.split("```")[1].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        grade_result = json.loads(raw)
    except Exception as exc:
        logger.warning("Flashcard grading LLM error: %s", exc)

    grade = grade_result.get("grade", "Wrong")
    if grade not in ("Correct", "Partial", "Wrong"):
        grade = "Wrong"
    feedback = grade_result.get("feedback", "")

    new_status = "in_progress" if quiz.status == "generated" else quiz.status
    await quiz_repo.update_answers_and_grades(
        quiz_uuid,
        card_index=card_index,
        student_answer=student_answer,
        grade=grade,
        new_status=new_status,
    )

    return GradeFlashcardResponse(
        card_index=card_index,
        grade=grade,
        feedback=feedback,
        session_status=new_status,
    )


# ── POST /api/v1/quiz/{session_id}/submit ─────────────────────────────────────

@router.post("/{session_id}/submit", response_model=SubmitQuizResponse)
async def submit_quiz(
    session_id: str,
    request: SubmitQuizRequest,
    quiz_repo: QuizSessionRepository = Depends(get_quiz_repo),
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    current_user: User = Depends(get_current_user),
):
    """Submit all MCQ answers, compute score, update mastery."""
    try:
        quiz_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    quiz = await quiz_repo.get_by_id(quiz_uuid)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    _ownership_check(quiz, current_user)

    if quiz.status == "completed":
        raise HTTPException(status_code=400, detail="Quiz already completed")

    if len(request.mcq_answers) != 3:
        raise HTTPException(status_code=400, detail="All 3 MCQ answers are required")

    # Build MCQ answer/grade maps
    mcq_answer_map: dict[str, int] = {}
    mcq_grade_map: dict[str, str] = {}
    for item in request.mcq_answers:
        key = str(item.card_index)
        mcq_answer_map[key] = item.selected_index
        mcq_grade_map[key] = "correct" if item.is_correct else "wrong"

    # Compute score
    per_card_results: list[PerCardResult] = []
    raw_points = 0.0
    flashcard_grades = quiz.grades or {}

    for idx in range(3):
        is_correct = request.mcq_answers[idx].is_correct
        pts = 1.0 if is_correct else 0.0
        raw_points += pts
        per_card_results.append(
            PerCardResult(card_index=idx, card_type="mcq", grade="correct" if is_correct else "wrong", points=pts)
        )

    for idx in range(3, 6):
        flashcard_grade = flashcard_grades.get(str(idx), "Wrong")
        grade_lower = flashcard_grade.lower() if isinstance(flashcard_grade, str) else "wrong"
        if grade_lower == "correct":
            pts = 1.0
        elif grade_lower == "partial":
            pts = 0.5
        else:
            pts = 0.0
        raw_points += pts
        per_card_results.append(
            PerCardResult(card_index=idx, card_type="flashcard", grade=flashcard_grade, points=pts)
        )

    score_out_of_6 = raw_points
    final_score = round((raw_points / 6.0) * 100, 2)

    await quiz_repo.mark_completed(
        quiz_uuid,
        mcq_answers=mcq_answer_map,
        mcq_grades=mcq_grade_map,
        final_score=final_score,
    )

    # Update mastery record
    mastery_updated = False
    struggle_flagged = False
    try:
        record = await mastery_repo.get_or_create_mastery(current_user.id, quiz.module_slug)
        breakdown = dict(record.component_breakdown or {})
        breakdown["quizzes"] = final_score
        breakdown.pop("missing_components", None)

        exercises = breakdown.get("exercises", 0.0)
        quizzes = breakdown.get("quizzes", 0.0)
        code_quality = breakdown.get("code_quality", 0.0)
        streak = breakdown.get("streak", 0.0)
        total = exercises * 0.4 + quizzes * 0.3 + code_quality * 0.2 + streak * 0.1

        await mastery_repo.update_mastery(
            user_id=current_user.id,
            topic=quiz.module_slug,
            score=round(total, 2),
            level=_mastery_level(total),
            component_breakdown=breakdown,
        )
        mastery_updated = True
        if final_score < 50:
            struggle_flagged = True
            logger.info(
                "Struggle detected: user=%s module=%s score=%.1f",
                current_user.id, quiz.module_slug, final_score,
            )
    except Exception as exc:
        logger.warning("Mastery update failed: %s", exc)

    return SubmitQuizResponse(
        session_id=quiz_uuid,
        score=final_score,
        score_out_of_6=score_out_of_6,
        per_card_results=per_card_results,
        mastery_updated=mastery_updated,
        module_slug=quiz.module_slug,
        struggle_flagged=struggle_flagged,
    )
