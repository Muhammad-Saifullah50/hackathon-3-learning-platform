# Implementation Plan: Interactive Code Editor

**Branch**: `014-interactive-code-editor` | **Date**: 2026-05-10 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/014-interactive-code-editor/spec.md`

## Summary

Build a Monaco Editor-based Python coding environment with two modes (standalone Playground, embedded lesson), real-time code execution via the existing sandbox (F05), AI code review via the existing agent layer (F07), a collapsible general tutor panel, graded exercise submission, auto-save persistence using a new `code_sessions` table, and per-user daily rate limiting (3 runs/day, 3 reviews/day) enforced at the FastAPI layer.

---

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5+ / React 19 (frontend)  
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0 async, `sqlalchemy.dialects.postgresql.insert` (UPSERT), Pydantic 2.0, existing `RateLimitCounter` model
- Frontend: Next.js 14+ (App Router), `@monaco-editor/react` v4.x (loaded via `next/dynamic` with `ssr: false`), Tailwind CSS, Shadcn/ui

**Storage**: Neon PostgreSQL (new `code_sessions` table), browser localStorage (auto-save fallback)  
**Testing**: pytest + httpx (backend), vitest + @testing-library/react (frontend), Playwright (E2E)  
**Target Platform**: Linux server (backend), browser (frontend, min 1024px supported width)  
**Performance Goals**:
- Code execution result visible within 5s of Run click (SC-001)
- AI feedback visible within 10s in 90% of cases (SC-003)
- Auto-save with zero typing interruption (SC-007)
- Monaco loaded via `next/dynamic` — excluded from initial JS bundle (constitution §III)

**Constraints**:
- Monaco must load with `ssr: false` (crashes on SSR)
- Code execution sandbox: 5s timeout, 50MB memory, stdlib-only (enforced by F05, unchanged)
- Rate limit: 3 run/day + 3 review/day per student, HTTP 429 on excess
- Playground and lesson code persist independently — never overwrite each other
- General tutor panel collapsed by default on viewports < 1024px (FR-020)
- No streaming for agent chat (known upstream SDK bug, non-streaming path used, F07 decision)

**Scale/Scope**: MVP — single institution, ~100 concurrent students; no cross-tab sync UI required (last-write-wins)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| Monaco via `next/dynamic` (constitution §III) | ✅ PASS | `ssr: false`, excluded from initial bundle |
| Repository Pattern — DB access via repos only | ✅ PASS | `CodeSessionRepository` wraps all DB access; no raw queries in routes |
| No `exec()`/`eval()` on server | ✅ PASS | Sandbox is Docker-isolated (F05); this feature only calls the sandbox API |
| Rate limiting via existing infrastructure | ✅ PASS | Reuses `rate_limit_counters` table; no new infra |
| Auth required on all routes | ✅ PASS | `get_current_user` dependency on all new endpoints |
| No secrets hardcoded | ✅ PASS | All config via env vars |
| Smallest viable diff | ✅ PASS | Reuses F05 sandbox, F07 agents, F13 frontend shell; only adds what's new |
| Alembic for schema changes | ✅ PASS | Two migrations planned (enum + new table) |
| TDD for business logic | ✅ PASS | Rate limit service and code session service require tests-first |
| LLM calls non-synchronous | ⚠️ NOTE | Agent chat uses non-streaming Runner.run (F07 decision due to SDK bug); SSE wrapper still used at transport layer |

**Gate result**: PASS — no violations requiring justification.

---

## Project Structure

### Documentation (this feature)

```text
specs/014-interactive-code-editor/
├── plan.md              # This file
├── research.md          # Phase 0 output ✅
├── data-model.md        # Phase 1 output ✅
├── quickstart.md        # Phase 1 output ✅
├── contracts/
│   └── openapi.yaml     # Phase 1 output ✅
└── tasks.md             # Phase 2 output (sp.tasks — not yet created)
```

### Source Code (repository root)

```text
backend/src/
├── models/
│   └── code_session.py              # NEW: CodeSession model (composite PK)
├── repositories/
│   └── code_session_repository.py   # NEW: UPSERT + GET
├── schemas/
│   └── code_editor.py               # NEW: SaveCodeRequest, CodeSessionResponse
├── services/
│   └── code_session_service.py      # NEW: save/load + daily rate limit logic
└── api/v1/
    └── code_editor.py               # NEW: GET/PUT /api/v1/code-sessions/{context_key}

# Modified files:
# backend/src/auth/models.py          — add user_daily to IdentifierType enum
# backend/src/api/v1/code_execution.py — add daily run rate limit
# backend/src/api/v1/agents.py        — add daily review rate limit (when code_snippet present)
# backend/src/main.py                 — register code_editor router
# backend/src/dependencies.py         — add get_code_session_repository

frontend/src/
├── app/(student)/playground/
│   └── page.tsx                     # NEW: Playground route
├── components/editor/
│   ├── CodeEditorPanel.tsx          # NEW: Top-level editor component (Monaco + output + feedback)
│   ├── OutputPanel.tsx              # NEW: Stdout/stderr/timing display
│   ├── CodeFeedbackSection.tsx      # NEW: AI review conversation below editor
│   └── TutorPanel.tsx              # NEW: Right collapsible general chat panel
├── hooks/
│   ├── useCodeSession.ts            # NEW: localStorage + backend persistence
│   ├── useCodeExecution.ts          # NEW: Run action + rate limit handling
│   └── useCodeFeedback.ts           # NEW: Review with Tutor conversation
└── lib/
    └── code-editor-api.ts           # NEW: Typed calls to /code-sessions endpoints

# Modified files:
# frontend/src/components/layout/student-sidebar.tsx — add Playground nav item
```

**Structure Decision**: Web application (Option 2) — existing `backend/` + `frontend/` layout. All new files placed within established directory conventions. No new top-level directories.

---

## Phase 0: Research Summary

All NEEDS CLARIFICATION items resolved. See [research.md](research.md).

| Question | Resolution |
|---|---|
| Monaco integration in Next.js 14 | `@monaco-editor/react` + `next/dynamic(ssr: false)` |
| Error line highlighting | `monaco.editor.setModelMarkers` + `deltaDecorations` via `onMount` ref |
| Daily rate limiting approach | Reuse `rate_limit_counters` table with `user_daily` identifier type |
| Code session persistence UPSERT | `pg_insert().on_conflict_do_update()` on composite PK |
| AI feedback channel reuse | Existing `/api/v1/agents/chat` with `code_snippet` field |
| Conversation isolation | Distinct `session_id` per channel — no shared state |

---

## Phase 1: Design Decisions

### 1. Editor Modes (FR-005)

`CodeEditorPanel` accepts an `EditorConfig` prop:
```typescript
interface EditorConfig {
  mode: "playground" | "exercise"
  contextKey: string      // "playground" | exercise UUID
  starterCode?: string    // lesson-provided; undefined → blank
  exerciseId?: string
  isGraded?: boolean      // true → Submit button appears
}
```

The Playground page passes `{ mode: "playground", contextKey: "playground" }`. Lesson pages embed the component with exercise context.

### 2. Monaco Error Line Highlighting (FR-004)

Backend response includes `error_line: number | null` parsed from stderr. Frontend uses `monaco.editor.setModelMarkers` (squiggly underline) and `editor.deltaDecorations` (whole-line background tint) to mark the error line. Both are cleared on the next Run click.

Line number parsing logic lives in a utility function:
```python
def parse_error_line(stderr: str) -> int | None:
    # Matches patterns like: File "...", line 4 or SyntaxError: line 4
    match = re.search(r'line (\d+)', stderr)
    return int(match.group(1)) if match else None
```

### 3. Auto-Save Strategy (FR-007, FR-008, FR-009)

Two-tier persistence:
1. **localStorage** (fast, local): debounced 5s after last keystroke — key: `learnflow:code:{userId}:{contextKey}`
2. **Backend** (cross-device): on every Run/Submit/Review action — PUT `/api/v1/code-sessions/{contextKey}`

On editor load:
1. Check localStorage → restore immediately if found
2. Simultaneously fetch backend — if newer (by `updated_at`), replace localStorage and display

### 4. Rate Limiting Architecture (FR-025, FR-026)

Daily limit enforced at service layer (not middleware) to allow context-aware 429 responses:

```python
# In CodeSessionService
async def check_and_increment_daily_limit(
    db: AsyncSession, user_id: str, action: str, limit: int = 3
) -> bool:
    today = date.today().isoformat()
    identifier = f"{user_id}:{action}:{today}"
    # SELECT + compare + INSERT/INCREMENT with IntegrityError retry
```

The `/api/v1/agents/chat` endpoint checks the rate limit **only when `code_snippet` is present** in the request (= Review with Tutor action). General tutor panel messages without `code_snippet` are not rate limited by the daily counter.

### 5. Conversation Isolation (FR-018)

Two completely separate `session_id` namespaces:
- **Code feedback**: `f"code-{context_key}-{user_id}"` — stable per editor context
- **General tutor**: new UUID generated per browser session — resets on page refresh (simpler for MVP; cross-session persistence is out of scope)

### 6. Graded Submission (FR-021–FR-024)

Submit button visible only when `isGraded === true`. On click:
1. Save code to backend (PUT code-sessions)
2. POST to existing `/api/v1/agents/exercise-submit` with `{ exercise_id, code }`
3. Display pass/fail + failing test case details in output panel
4. Submit button re-enabled after response (regardless of pass/fail)

### 7. Tutor Panel Responsive Behaviour (FR-020)

Panel default state determined by `window.innerWidth < 1024` on mount. State persists via `useState` for the session (not localStorage — refreshing resets it, which is acceptable per spec).

---

## Complexity Tracking

No constitution violations requiring justification.

---

## Risks & Follow-ups

1. **Monaco bundle size**: `@monaco-editor/react` adds ~2MB (CDN-loaded, not in bundle). Verify CDN availability in student environments; consider self-hosting if CDN is blocked.
2. **Rate limit counter cleanup**: Old `rate_limit_counters` records (one per user per day per action type) accumulate indefinitely. A scheduled cleanup job is out of scope for MVP but should be tracked as tech debt.
3. **Agent chat rate limit granularity**: The daily review limit (3/day) applies to code-snippet-bearing requests via the main `/chat` endpoint. If the triage agent's routing changes in a future sprint, verify the rate limit check point remains correct.
