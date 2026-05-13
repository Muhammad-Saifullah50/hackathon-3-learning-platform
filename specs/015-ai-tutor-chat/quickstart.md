# Quickstart: Chat Interface with AI Tutor (F15)

**Branch**: `015-ai-tutor-chat` | **Date**: 2026-05-11

---

## Prerequisites

- Python 3.11+, Node.js 18+
- Neon PostgreSQL connection string (same as F07 — reuse `.env`)
- LLM provider credentials (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`) — same as F07

---

## 1. Backend Setup

### 1.1 Apply the new migration

```bash
cd backend
source .venv/bin/activate  # or: uv run
alembic upgrade head
```

This applies the `20260511_XXXX_add_chat_session_title_surface` migration, adding `title` and `surface` columns to `agent_sessions`.

### 1.2 Verify migration

```sql
-- Run in Neon SQL console or psql:
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'agent_sessions'
  AND column_name IN ('title', 'surface');
```

Expected: two rows with `character varying` / `text` and `YES` nullable.

### 1.3 Start the backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### 1.4 Verify new endpoints

```bash
# List sessions (requires auth cookie — use browser after login, or httpie/curl with cookie)
curl -s http://localhost:8000/api/v1/agents/sessions \
  -H "Cookie: better-auth.session_token=<your_token>" | python -m json.tool

# Check quota
curl -s http://localhost:8000/api/v1/agents/quota \
  -H "Cookie: better-auth.session_token=<your_token>" | python -m json.tool
```

---

## 2. Frontend Setup

### 2.1 Install new dependencies

```bash
cd frontend
npm install react-markdown react-syntax-highlighter
npm install --save-dev @types/react-syntax-highlighter
```

### 2.2 Verify environment variables

Ensure `frontend/.env.local` has:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 2.3 Start the frontend

```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:3000/chat` — the chat page should load (no longer "Coming Soon").

---

## 3. Manual Smoke Tests

### 3.1 Standalone chat — first message

1. Log in as a student
2. Go to `/chat`
3. Verify the quota badge shows "5 messages remaining"
4. Send "What is a Python list comprehension?"
5. Verify: typing indicator appears → text streams in → code block is highlighted → message count drops to 4

### 3.2 Session persistence

1. After step 3.1, reload the page
2. Verify the previous message and response are displayed
3. Verify the session appears in the session sidebar

### 3.3 Embedded panel

1. Go to `/playground` (the code editor)
2. Enter a code snippet with a `TypeError`
3. Run the code
4. Click the chat toggle (left side of tutor panel)
5. Send "What's wrong with my code?"
6. Verify the AI response references the specific error

### 3.4 Quota enforcement

1. Send 5 messages in one session
2. On the 5th response, verify "0 messages remaining" is shown
3. Try to send a 6th message — verify the send button is disabled and the quota message is shown

### 3.5 Off-topic guardrail

1. Send "Write me a poem about the ocean"
2. Verify the response politely declines and redirects to Python topics

---

## 4. Running Tests

### Backend

```bash
cd backend
pytest tests/test_chat/ -v
# Specifically for quota logic:
pytest tests/test_chat/test_chat_quota.py -v
# For session listing:
pytest tests/test_chat/test_session_api.py -v
```

### Frontend

```bash
cd frontend
npm run test -- --watch src/components/chat/
npm run test -- --watch src/hooks/
```

---

## 5. Key Files Reference

| File | Purpose |
|------|---------|
| `backend/alembic/versions/20260511_*_add_chat_session_title_surface.py` | DB migration |
| `backend/src/models/agent_session.py` | `title` + `surface` columns |
| `backend/src/services/chat_quota_service.py` | 5 msg/day enforcement |
| `backend/src/api/v1/agents.py` | `/chat`, `/sessions`, `/sessions/{id}`, `/quota` |
| `frontend/src/app/(student)/chat/page.tsx` | Standalone chat page |
| `frontend/src/components/chat/ChatWindow.tsx` | Message list + SSE streaming |
| `frontend/src/components/chat/ChatInput.tsx` | Input with char counter + quota badge |
| `frontend/src/components/chat/SessionSidebar.tsx` | Session list + New Chat |
| `frontend/src/components/editor/TutorPanel.tsx` | Upgraded embedded panel |
| `frontend/src/hooks/useStreamChat.ts` | SSE streaming hook (shared) |
| `frontend/src/hooks/useChatSessions.ts` | Session list (React Query) |
| `frontend/src/hooks/useChatQuota.ts` | Quota status (React Query) |

---

## 6. Common Issues

**"Session not found" on first load after migration**  
→ Existing F07 sessions have `title=NULL` — this is valid. The session list will show auto-generated titles for them. No action needed.

**Chat quota not resetting**  
→ The `RateLimitCounter` row key includes the UTC date. If the server clock is not UTC, reset may be off. Verify `TZ=UTC` in backend env.

**`react-syntax-highlighter` bundle size warning**  
→ Ensure the dynamic import uses `import('react-syntax-highlighter/dist/esm/light')` not the full build. See `ChatMessage.tsx` implementation.

**Tutor panel not showing code context**  
→ Verify `CodeEditorPanel` passes `code` and `lastOutput` props to `TutorPanel`. Check browser DevTools Network tab — the `/chat` request body should include `code_snippet`.
