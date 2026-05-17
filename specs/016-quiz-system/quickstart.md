# Quickstart: Quiz System (F16)

**Branch**: `016-quiz-system` | **Date**: 2026-05-17

This guide covers how to set up, verify, and manually test the quiz system end-to-end.

---

## Prerequisites

- Backend running (`uvicorn src.main:app --reload` in `backend/`)
- Frontend running (`npm run dev` in `frontend/`)
- Neon PostgreSQL connection active (`DATABASE_URL` set in `backend/.env`)
- Valid JWT for a student user (via existing `/api/v1/auth/login`)
- `GEMINI_API_KEY` or equivalent LLM provider key set in `backend/.env`

---

## Step 1: Apply the Migration

```bash
cd backend
alembic upgrade head
```

Verify:
```bash
psql $DATABASE_URL -c "\d quiz_sessions"
# Should show all columns including questions (jsonb), student_answers (jsonb), grades (jsonb)
```

---

## Step 2: Verify Backend Routes

Start the backend and check Swagger UI at `http://localhost:8000/docs`:

- `GET /api/v1/quiz/{session_id}` — Quiz Session State
- `POST /api/v1/quiz/{session_id}/grade-flashcard` — Grade Flashcard
- `POST /api/v1/quiz/{session_id}/submit` — Submit Quiz

All 3 require `Authorization: Bearer <token>`.

---

## Step 3: Trigger Quiz Generation (Chat Route)

```bash
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "give me a quiz on for loops", "session_id": null}' \
  --no-buffer
```

Expected SSE stream:
```
event: session
data: <session_uuid>

event: quota
data: 14

event: handoff
data: quiz

event: structured
data: {"response_type":"quiz","module_slug":"control_flow","topic_label":"For Loops","mcq_questions":[...],"flashcard_questions":[...],"quiz_session_id":"<quiz_session_uuid>"}

data: [DONE]
```

Note the `quiz_session_id` from the structured event — all subsequent quiz calls use this ID.

---

## Step 4: Get Quiz State (Resume Flow)

```bash
curl http://localhost:8000/api/v1/quiz/<quiz_session_id> \
  -H "Authorization: Bearer <token>"
```

Expected: full session state with `status: "generated"`, `student_answers: {}`, `grades: {}`.

---

## Step 5: Grade a Flashcard

```bash
curl -X POST http://localhost:8000/api/v1/quiz/<quiz_session_id>/grade-flashcard \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"card_index": 3, "student_answer": "a way to loop over a range of numbers"}'
```

Expected:
```json
{
  "card_index": 3,
  "grade": "Partial",
  "feedback": "Correct about iteration, but for loops work over any iterable, not just ranges.",
  "session_status": "in_progress"
}
```

---

## Step 6: Submit the Quiz

```bash
curl -X POST http://localhost:8000/api/v1/quiz/<quiz_session_id>/submit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "mcq_answers": [
      {"card_index": 0, "selected_index": 1, "is_correct": true},
      {"card_index": 1, "selected_index": 0, "is_correct": false},
      {"card_index": 2, "selected_index": 2, "is_correct": true}
    ]
  }'
```

Expected:
```json
{
  "session_id": "<quiz_session_id>",
  "score": 66.7,
  "score_out_of_6": 4.0,
  "per_card_results": [...],
  "mastery_updated": true,
  "module_slug": "control_flow",
  "struggle_flagged": false
}
```

Verify mastery update:
```bash
curl http://localhost:8000/api/v1/agents/progress \
  -H "Authorization: Bearer <token>"
# Should show control_flow with updated quiz component in component_breakdown
```

---

## Step 7: Frontend Smoke Test

1. Open `http://localhost:3000/chat`
2. Start a new chat and type: **"give me a quiz on for loops"**
3. Confirm:
   - `TypingIndicator` appears while quiz generates
   - `QuizCard` replaces it inline in the chat feed (no page navigation)
   - 3 MCQ cards render with 4 options each
   - Selecting an MCQ option locks it and highlights correct (green) / wrong (red) immediately
   - After MCQ 3, flashcard 1 appears with a term and input field
   - "Check" button is disabled until at least 1 character typed
   - Clicking "Check" triggers grading → card flips to reveal definition + grade badge
   - After all 6 cards: QuizSummary shows score (X/6) with per-card breakdown
   - "Continue Learning" button returns focus to chat input

4. Refresh page mid-quiz, return to same chat session — confirm incomplete `QuizCard` re-renders with answered cards locked.

---

## Triage Keyword Test

Run the unit test to confirm intent classification:
```bash
cd backend
pytest tests/unit/test_quiz_triage.py -v
```

Expected: "give me a quiz", "quiz me", "quick quiz", "test my knowledge" → `quiz-generation` intent.

---

## Environment Variables

No new env vars required. Reuses:
- `DATABASE_URL` — Neon PostgreSQL connection
- `GEMINI_API_KEY` (or `OPENAI_API_KEY`) — LLM provider for quiz generation + flashcard grading
- `JWT_SECRET` — Authentication (unchanged)

---

## Rollback

```bash
cd backend
alembic downgrade -1
# Drops quiz_sessions table; mastery_records unchanged
```
