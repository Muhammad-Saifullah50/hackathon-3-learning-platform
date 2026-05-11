# Quickstart: Interactive Code Editor (014)

**Branch**: `014-interactive-code-editor`  
**Date**: 2026-05-10

---

## Prerequisites

- Features 001–007 and 013 complete and running (auth, sandbox, agents, frontend foundation)
- Neon PostgreSQL connection string in `backend/.env`
- Backend running at `http://localhost:8000`
- Frontend running at `http://localhost:3000`

---

## 1. Install Frontend Dependency

```bash
cd frontend
npm install @monaco-editor/react
```

---

## 2. Apply Backend Migrations

Two Alembic migrations are needed:

```bash
cd backend

# Migration 1: Add user_daily to IdentifierType enum
alembic revision --autogenerate -m "add_user_daily_identifier_type"
# Verify: adds 'user_daily' to identifiertype enum

# Migration 2: Create code_sessions table
alembic revision --autogenerate -m "create_code_sessions_table"
# Verify: creates code_sessions with PK (user_id, context_key)

alembic upgrade head
```

---

## 3. New Backend Files

```
backend/src/
├── models/
│   └── code_session.py          # CodeSession SQLAlchemy model (NEW)
├── repositories/
│   └── code_session_repository.py  # UPSERT + GET operations (NEW)
├── schemas/
│   └── code_editor.py           # SaveCodeRequest, CodeSessionResponse (NEW)
├── services/
│   └── code_session_service.py  # Business logic + daily rate limit check (NEW)
└── api/v1/
    └── code_editor.py           # GET/PUT /code-sessions/{context_key} (NEW)
```

Modify:
- `backend/src/auth/models.py` — add `user_daily = "user_daily"` to `IdentifierType`
- `backend/src/api/v1/code_execution.py` — add daily rate limit check before execution
- `backend/src/api/v1/agents.py` — add daily review rate limit check when `code_snippet` present
- `backend/src/main.py` — register `code_editor` router

---

## 4. New Frontend Files

```
frontend/src/
├── app/(student)/playground/
│   └── page.tsx                 # Playground page (standalone mode) (NEW)
├── components/editor/
│   ├── CodeEditorPanel.tsx      # Main editor component (Monaco, output, feedback) (NEW)
│   ├── OutputPanel.tsx          # Stdout/stderr/timing display (NEW)
│   ├── CodeFeedbackSection.tsx  # AI code review conversation below editor (NEW)
│   └── TutorPanel.tsx           # Collapsible right general chat panel (NEW)
├── hooks/
│   ├── useCodeSession.ts        # Load/save code persistence logic (NEW)
│   ├── useCodeExecution.ts      # Run button logic + rate limit handling (NEW)
│   └── useCodeFeedback.ts       # Review with Tutor conversation state (NEW)
└── lib/
    └── code-editor-api.ts       # Typed API calls for code-sessions endpoints (NEW)
```

Modify:
- `frontend/src/components/layout/student-sidebar.tsx` — add Playground nav item
- `frontend/src/app/(student)/layout.tsx` — ensure Playground page is within student shell

---

## 5. Verify the Happy Path

1. Start backend: `cd backend && uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Log in as a student
4. Click "Playground" in sidebar → editor loads blank
5. Type `print("hello world")`, click Run → output panel shows `hello world`
6. Click "Review with Tutor" → loading indicator → AI feedback appears below editor
7. Open right tutor panel → ask "what is a list?" → general answer appears
8. Close browser → reopen → navigate to Playground → code restored

---

## 6. Environment Variables

No new environment variables are needed. The feature uses:
- `NEXT_PUBLIC_BACKEND_URL` (already set)
- `DATABASE_URL` (already set in backend)
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` (already set)

---

## 7. Rate Limit Behaviour (Testing)

To test rate limits locally, manually insert counter records:

```sql
-- Simulate 3 run requests for a user today
INSERT INTO rate_limit_counters (identifier, identifier_type, attempt_count, last_attempt_at)
VALUES ('{user_id}:run:2026-05-10', 'user_daily', 3, NOW());
```

Click Run → expect 429 with message in output panel.
