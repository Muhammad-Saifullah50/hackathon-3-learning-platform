# Research: Interactive Code Editor (014)

**Phase**: 0 — Research  
**Date**: 2026-05-10  
**Branch**: `014-interactive-code-editor`

---

## 1. Monaco Editor Integration (Next.js 14 App Router)

**Decision**: Use `@monaco-editor/react` v4.x loaded via `next/dynamic` with `ssr: false`.

**Rationale**: The raw `monaco-editor` package requires a custom webpack plugin for web workers that conflicts with Next.js's webpack setup. `@monaco-editor/react` loads Monaco from a CDN by default, bypassing this entirely. The `ssr: false` flag is mandatory — Monaco accesses `window`/`document` at import time and hard-crashes during SSR.

**Alternatives considered**: `monaco-editor` directly — rejected due to webpack worker conflict and extra boilerplate.

**Key patterns**:
- `language="python"` — built-in Python syntax highlighting, no extra config
- `theme="vs-dark"` — matches platform dark theme
- Uncontrolled + `editorRef.current.getValue()` — preferred for performance (avoids re-render on every keystroke)
- Error markers: `monaco.editor.setModelMarkers(model, 'execution', [...])` via `onMount` callback
- Gutter highlight: `editor.deltaDecorations([])` for background coloring of error lines
- Types: `OnMount`, `Monaco`, `editor.IStandaloneCodeEditor` from `@monaco-editor/react`

```tsx
// Page-level
const CodeEditorPanel = dynamic(() => import('@/components/editor/CodeEditorPanel'), {
  ssr: false,
  loading: () => <div>Loading editor...</div>,
})
```

---

## 2. Per-User Daily Rate Limiting

**Decision**: Reuse existing `rate_limit_counters` table with composite string identifier `"{user_id}:{action}:{date}"`. Add `user_daily` to the `IdentifierType` enum.

**Rationale**: No new table or migration required for the counter itself. The existing `identifier` column is `String(255)` with a unique index — sufficient for the key `"abc123:run:2026-05-10"`. The daily reset is implicit: each new calendar date creates a new key.

**Alternatives considered**: Redis-based counters — rejected (adds infrastructure for MVP); new `code_run_limits` table — rejected (unnecessary when existing table handles it); `slowapi` — designed for req/min not req/day, rejected.

**Implementation pattern**:
```python
async def check_daily_limit(db: AsyncSession, user_id: str, action: str, limit: int) -> bool:
    today = date.today().isoformat()
    identifier = f"{user_id}:{action}:{today}"
    # SELECT + increment or INSERT, wrapped in IntegrityError retry
    # Returns True if allowed, False if limit exceeded
```

**Migration needed**: Add `user_daily` to `IdentifierType` enum in `backend/src/auth/models.py` and run Alembic migration.

---

## 3. Code Session Persistence (UPSERT)

**Decision**: New `code_sessions` table with composite PK `(user_id, context_key)`. UPSERT using `sqlalchemy.dialects.postgresql.insert().on_conflict_do_update()`.

**Rationale**: Single-round-trip upsert avoids read-before-write race conditions. No `session.merge()` (requires extra SELECT, subtle async behavior in SQLAlchemy 2.0). The composite PK is the conflict target.

**Alternatives considered**: `session.merge()` — rejected (extra round trip, async quirks); separate SELECT + INSERT/UPDATE — rejected (race condition window).

**Implementation pattern**:
```python
from sqlalchemy.dialects.postgresql import insert as pg_insert

stmt = pg_insert(CodeSession).values(
    user_id=user_id, context_key=context_key, code=code, updated_at=now
).on_conflict_do_update(
    index_elements=["user_id", "context_key"],
    set_={"code": code, "updated_at": now},
)
await db.execute(stmt)
```

**Migration needed**: New Alembic migration for `code_sessions` table.

---

## 4. AI Feedback Integration

**Decision**: Reuse existing `/api/v1/agents/chat` endpoint with `code_snippet` field for "Review with Tutor". The triage agent routes `code_snippet`-bearing messages to the Code Review or Debug agent.

**Rationale**: The existing agent system already handles code review intent classification. No new backend agent endpoint needed; the frontend just sets `code_snippet` in the chat request and the triage agent handles routing.

**General tutor panel**: Also uses `/api/v1/agents/chat` but in a separate session (different `session_id`) with no `code_snippet` — this ensures complete conversation isolation.

---

## 5. Frontend Architecture

**Decision**: New page at `/playground` (route: `frontend/src/app/(student)/playground/page.tsx`). `CodeEditorPanel` component is the shared building block used in both Playground mode and embedded lesson mode.

**Editor modes** controlled by props:
- `mode: "playground"` — no Submit button, context_key = "playground"
- `mode: "exercise"` — Submit button visible, context_key = exercise ID

**Layout**: Three-panel layout:
1. Left: Monaco editor + output panel + code feedback section (collapsible vertically)
2. Right: Collapsible tutor panel (default collapsed on `< 1024px`)

**Auto-save**: `useDebounce` hook triggers localStorage write after 5s of inactivity. Backend save happens on Run/Submit/Review actions.

---

## 6. Rate Limit UX

**Decision**: On HTTP 429, display user-friendly message in the relevant panel (output panel for Run, code feedback section for Review). The respective button remains disabled.

**Button disable rule**: Buttons are disabled while their request is in-flight (not permanently after 429 — user can try next day).
