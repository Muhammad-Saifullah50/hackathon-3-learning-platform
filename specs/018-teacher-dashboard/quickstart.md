# Developer Quickstart: 018-Teacher Dashboard

**Branch**: `018-teacher-dashboard`  
**Date**: 2026-05-18

---

## Prerequisites

- Python 3.13 with virtualenv at `backend/.venv`
- Node.js 20+ with pnpm
- Neon PostgreSQL connection string in `backend/.env` as `DATABASE_URL`
- Gemini API key in `backend/.env` as `GEMINI_API_KEY` (used by agents)

---

## 1. Run Database Migration

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

This applies `20260518_teacher_dashboard.py` which creates all 7 new tables:
`classes`, `class_memberships`, `teacher_generated_exercises`, `class_exercises`,
`class_exercise_submissions`, `question_reviews`, `teacher_notifications`.

Verify:
```bash
alembic current  # should show: 20260518_teacher_dashboard (head)
```

---

## 2. Register Test Users

Use the updated signup form (with role selector) or POST directly to the auth endpoint:

**Teacher account:**
```bash
curl -X POST http://localhost:8000/api/auth/sign-up/email \
  -H "Content-Type: application/json" \
  -d '{"email":"teacher@test.com","password":"Teacher@123","name":"Ms Smith","role":"teacher"}'
```

**Student account:**
```bash
curl -X POST http://localhost:8000/api/auth/sign-up/email \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student@123","name":"Alice Jones","role":"student"}'
```

---

## 3. Start Backend

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

Verify new routes are registered:
```bash
curl http://localhost:8000/openapi.json | python -m json.tool | grep "/api/v1/teacher"
```

---

## 4. Start Frontend

```bash
cd frontend
pnpm dev
```

Routes to verify after startup:
- `http://localhost:3000/register` — should show role selector (Student/Teacher)
- `http://localhost:3000/teacher/dashboard` — accessible after teacher login, redirects students
- `http://localhost:3000/dashboard` — students see Assigned + Invitations tabs in sidebar

---

## 5. End-to-End Smoke Test Flow

### Step A: Teacher creates class and invites student

1. Log in as teacher → navigate to `/teacher/dashboard`
2. Click "Create Class" → enter name "Python Basics" → confirm
3. Click the class → click "Add Student" → search "Alice" → click "Add to class"
4. Verify: Alice appears in member list with status "Pending"

### Step B: Student accepts invitation

1. Log in as student → navigate to `/dashboard`
2. Click "Invitations" tab in sidebar
3. Verify: invitation from "Ms Smith" appears
4. Click "Accept"
5. Verify: Invitations tab clears; class appears on dashboard with teacher name

### Step C: Teacher generates and assigns exercise

1. Log in as teacher → navigate to `/teacher/exercises/generate`
2. Enter incomplete prompt: "Create some exercises" → submit
3. Verify: inline error listing missing items (topic, difficulty, module)
4. Enter valid prompt: "Create 2 beginner Python for-loop exercises targeting Module 2 (Control Flow)"
5. Verify: exercise preview appears with 2 questions
6. Click "Assign to Class" → select "Python Basics" → confirm
7. Verify: success message; assigned_to_count = 1

### Step D: Student completes exercise

1. Log in as student → click "Assigned" tab in sidebar
2. Verify: exercise appears labelled "Python Basics"
3. Open exercise → verify 2 questions with descriptions
4. Write code for Question 1 → click "Get AI Review"
5. Verify: AI review and grade appear; submit button still disabled
6. Write code for Question 2 → click "Get AI Review"
7. Verify: submit button now enabled
8. Click "Submit" → verify score displayed
9. Navigate back to exercise → verify read-only state; resubmit button absent

---

## 6. Running Tests

```bash
# Backend unit + integration tests
cd backend
source .venv/bin/activate
pytest tests/unit/test_class_service.py -v
pytest tests/integration/test_teacher_api.py -v
pytest tests/integration/test_student_classes_api.py -v

# Frontend component tests
cd frontend
pnpm test -- --run
```

---

## 7. Key File Locations

| What | Where |
|------|-------|
| New DB models | `backend/src/models/teacher_classes.py` |
| Migration | `backend/alembic/versions/20260518_teacher_dashboard.py` |
| Teacher API router | `backend/src/api/v1/teacher.py` |
| Student classes router | `backend/src/api/v1/student_classes.py` |
| Teacher exercise service | `backend/src/services/teacher_exercise_service.py` |
| Teacher guardrail | `backend/src/services/agents/guardrails.py` (extended) |
| Teacher layout | `frontend/src/app/(teacher)/layout.tsx` |
| Teacher dashboard page | `frontend/src/app/(teacher)/teacher/dashboard/page.tsx` |
| Exercise generate page | `frontend/src/app/(teacher)/teacher/exercises/generate/page.tsx` |
| Student exercise view | `frontend/src/app/(student)/exercises/[id]/page.tsx` |
| Register form (with role) | `frontend/src/components/auth/register-form.tsx` |

---

## 8. Environment Variables (no new vars required)

F18 reuses all existing env vars. No new secrets needed. The Exercise Agent and Code Review Agent already use `GEMINI_API_KEY` / `OPENAI_API_KEY` via `LlmClient`.

---

## 9. Known Constraints

- Exercise generation may take up to 10 seconds — frontend shows a loading state
- Per-question AI review calls Code Review Agent — no timeout below 30s constitution limit
- Teacher cannot remove a student from a class in F18 (deferred)
- Class analytics are deferred to F19
