# Implementation Plan: Chat Interface with AI Tutor

**Branch**: `015-ai-tutor-chat` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-ai-tutor-chat/spec.md`

---

## Summary

Build a real-time AI tutor chat available as both a standalone `/chat` page and an upgraded embedded panel inside the code editor. Every student message is classified by the existing Triage Agent and routed to a specialist (Concepts, Debug, Code Review, Exercise, or Progress). Responses stream token-by-token via SSE. The system enforces a 5-messages-per-day quota, persists full conversation history per session, and supports multiple named sessions per student. The embedded panel automatically injects the current editor code (≤4 KB) and last execution output as context. Off-topic messages are declined by the Triage Agent without invoking any specialist.

---

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5+ / React 19 (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.115+, OpenAI Agents SDK (Runner), SQLAlchemy 2.0+, Pydantic 2.0+, asyncpg, Alembic
- Frontend: Next.js 14+, React Query (TanStack Query), `react-markdown` + `react-syntax-highlighter`, EventSource / fetch + ReadableStream
**Storage**: Neon PostgreSQL — existing `agent_sessions`, `routing_decisions`, `rate_limit_counters` tables + two new columns on `agent_sessions` via Alembic migration
**Testing**: pytest + httpx (backend), Vitest + Testing Library (frontend), Playwright (E2E)
**Target Platform**: Linux server (Railway/Render backend) + Vercel (Next.js frontend)
**Project Type**: Web application — existing `backend/` + `frontend/` monorepo
**Performance Goals**:
- First SSE token ≤ 3 s (SC-001); constitution AI first-token budget ≤ 1.2 s
- Page load ≤ 800 ms SSR; FastAPI non-AI routes ≤ 150 ms p95
**Constraints**:
- 2000-character message input cap (FR-018)
- 15 messages/student/day quota (FR-020) enforced server-side
- Code context ≤ 4 KB per message (FR-013)
- Conversation history window: last 5 messages (FR-012)
- OpenAI Agents SDK streaming bug (#601) was present in v0.12 but **fixed in v0.13**. Upgrade `openai-agents` to `>=0.13` as part of this feature. Use `Runner.run_streamed` for true per-token SSE.
**Scale/Scope**: 50+ concurrent sessions without degradation (SC-007); session list per student (unbounded, paginated)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Repository pattern — DB access only through repos | ✅ PASS | New `ChatQuotaRepository` + extensions to `AgentSessionRepository` |
| LLM Provider Abstraction — `_ConfiguredLitellmProvider` | ✅ PASS | Reuse existing provider; no hardcoded API keys |
| Stream all AI responses (`StreamingResponse`) | ✅ PASS | True per-token SSE via `Runner.run_streamed` (openai-agents v0.13 fixes #601) |
| Auth required on all routes | ✅ PASS | `get_current_user` dependency on every new endpoint |
| Rate limiting (`slowapi` or `RateLimitCounter`) | ✅ PASS | Chat quota via `RateLimitCounter` pattern (same as code review) |
| Alembic migrations only — no direct schema changes | ✅ PASS | New migration for `agent_sessions.title` + `agent_sessions.surface` |
| No business logic in route handlers | ✅ PASS | Chat quota + session logic in service layer |
| Pydantic v2 for all request/response schemas | ✅ PASS | New schemas in `src/schemas/agents.py` |
| Test coverage targets (FastAPI 80%, repos 85%) | ⚠️ TARGET | TDD for quota enforcement and session listing; test-after for UI |
| No `exec()`/`eval()` on user code | ✅ PASS | Not applicable to chat feature |
| ARIA accessibility | ✅ PASS | FR-021 mandates ARIA labels and `aria-live` region |
| Bundle size ≤ 200 KB gzipped | ⚠️ WATCH | `react-syntax-highlighter` is heavy; use dynamic import + only Python grammar |

**Gate result**: PASS with two items to watch during Phase 1 (test coverage targets and bundle size).

---

## Project Structure

### Documentation (this feature)

```text
specs/015-ai-tutor-chat/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── chat-api.yaml    ← Phase 1 OpenAPI contract
└── tasks.md             ← Phase 2 output (sp.tasks command)
```

### Source Code

```text
backend/
├── alembic/versions/
│   └── 20260511_XXXX_add_chat_session_title_surface.py   ← new migration
├── src/
│   ├── models/
│   │   └── agent_session.py        ← add `title` + `surface` columns
│   ├── repositories/
│   │   └── agent_session_repository.py  ← add list_sessions(), get_session_with_messages()
│   ├── schemas/
│   │   └── agents.py               ← add ChatSessionListItem, ChatSessionDetail, ChatQuotaStatus
│   ├── services/
│   │   └── chat_quota_service.py   ← NEW: 15 msg/day enforcement via RateLimitCounter
│   ├── dependencies.py             ← add get_chat_quota_service()
│   └── api/v1/
│       └── agents.py               ← add GET /sessions, GET /sessions/{id} endpoints;
│                                      upgrade POST /chat with quota, title, surface, context injection

frontend/
├── src/
│   ├── app/(student)/chat/
│   │   ├── page.tsx                ← replace coming-soon with full chat page
│   │   └── [sessionId]/
│   │       └── page.tsx            ← (optional) deep-link to a specific session
│   ├── components/
│   │   ├── chat/                   ← NEW directory
│   │   │   ├── ChatWindow.tsx      ← message list + SSE streaming display
│   │   │   ├── ChatInput.tsx       ← textarea, char counter, send button, quota badge
│   │   │   ├── ChatMessage.tsx     ← per-message bubble with markdown + code highlighting
│   │   │   ├── SessionSidebar.tsx  ← session list with New Chat button
│   │   │   └── TypingIndicator.tsx ← animated dots while waiting for first token
│   │   └── editor/
│   │       └── TutorPanel.tsx      ← upgrade: add code/output context, quota, session persistence
│   ├── hooks/
│   │   ├── useChatSessions.ts      ← React Query: list + create sessions
│   │   ├── useStreamChat.ts        ← SSE streaming hook (shared by /chat and TutorPanel)
│   │   └── useChatQuota.ts         ← fetch remaining daily quota
│   └── lib/
│       └── api/
│           └── chat.ts             ← typed fetch helpers for chat endpoints
```

**Structure Decision**: Web application (existing backend/ + frontend/). No new top-level projects. All changes are additive to the existing FastAPI service and Next.js app.

---

## Complexity Tracking

> No constitution violations requiring justification. All additions follow existing patterns.
