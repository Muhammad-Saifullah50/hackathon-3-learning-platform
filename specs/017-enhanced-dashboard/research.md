# Research: Enhanced Student Dashboard & Module Progress Detail

**Branch**: `017-enhanced-dashboard` | **Date**: 2026-05-18 | **Phase**: 0

---

## 1. Mastery History Gap

### Finding
The spec assumes "timestamped mastery records already exist" for the Mastery Over Time chart. In reality, `user_module_mastery` has a **unique index on (user_id, module_id)**, meaning one row per student per module — not a historical log. The `updated_at` column only reflects the most-recent update, not past values.

### Decision
Add a lightweight `mastery_snapshots` table that appends one row every time `user_module_mastery` is written. The dashboard chart reads from this table, grouped by calendar date (average per day when multiple snapshots exist).

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK | CASCADE DELETE |
| module_id | INT FK | |
| score | FLOAT | 0–100 |
| recorded_at | TIMESTAMPTZ | server default NOW() |

**Alternatives considered**:
- Use `user_quiz_attempts.created_at` as proxy — rejected: quiz scores are not the same as mastery scores.
- Reuse `user_module_mastery.updated_at` — rejected: only gives one data point per module, not a time series.
- No chart (empty state only) — rejected: SC-002 requires correct data when records exist.

---

## 2. Recharts Integration

### Finding
`recharts@^2.15.0` is already listed in `frontend/package.json`. No install step required.

### Decision
Use `<LineChart>` for "Mastery Over Time" and `<BarChart layout="vertical">` for "Module Mastery". Both are server-component-safe when loaded with `next/dynamic` and `{ ssr: false }` (Recharts uses browser APIs).

**Rationale**: Recharts is declarative, React-native, tree-shakeable, and avoids canvas complexity.

---

## 3. SSE Pattern Reuse

### Finding
`agents.py` already defines `_sse_result_generator` and uses `StreamingResponse` with `media_type="text/event-stream"`. The pattern: call `Runner.run(...)` (or `Runner.run_streamed`) then yield SSE events.

### Decision
Create two **new dedicated routers** (`dashboard.py`):
- `GET /api/v1/dashboard/recommendations/stream` — calls Progress Agent, emits `event: recommendation` then `event: done`
- `GET /api/v1/module/{moduleId}/progress/stream` — calls Progress Agent in module-detail mode, emits `event: topic` events then `event: done`

**Alternatives considered**:
- Extend existing chat endpoint with a `mode` param — rejected: chat applies quota logic, off-topic guardrails, and session persistence that are irrelevant here.
- Use WebSockets — rejected: SSE is simpler for one-way server→client push; existing F15 pattern already validated.

---

## 4. Module Slug Mapping

### Finding
Modules are seeded by title (not slug). Module IDs are auto-assigned integers by PostgreSQL. The spec uses human-readable slugs (e.g., `control-flow`) in URLs.

### Decision
Hardcode a slug set in the backend for **URL validation only** (confirming the slug is a known module). The integer values in the original mapping are unused — do not rely on them for DB lookups, as auto-assigned IDs are not guaranteed to be stable across environments or re-seeds.

```python
# Keys are the valid URL slugs. Integer values are unused — only the key set matters.
MODULE_SLUG_MAP: dict[str, int] = {
    "basics": 1,
    "control-flow": 2,
    "data-structures": 3,
    "functions": 4,
    "oop": 5,
    "files": 6,
    "errors": 7,
    "libraries": 8,
}
```

If a module_id is needed for a DB query, resolve it via `SELECT id FROM modules WHERE title = :title` or a `modules.slug` column — never via a hardcoded integer. The dashboard SSE endpoints pass the slug string directly to the Progress Agent context; no module_id DB resolution is required.

The frontend `ModuleCard` receives `id` (currently the module slug). The `module-grid` will derive slugs from existing module data. The "View Progress" button href becomes `/module/{module.id}/progress`.

---

## 5. Progress Agent Extension Strategy

### Finding
`get_progress_agent()` in `agents.py` uses a single `dynamic_instructions` function that reads `LearnFlowContext`. The context currently has: `user_id`, `level`, `topic`, `code_snippet`, `surface`.

### Decision
Add two new fields to `LearnFlowContext`:
- `agent_mode: Literal["recommendations", "module_detail"] | None` — selects the agent's task
- `module_slug: str | None` — set for `module_detail` mode

The progress agent `dynamic_instructions` branches on `agent_mode`:
- `recommendations` → produce 1–3 JSON recommendations based on mastery scores
- `module_detail` → produce topic breakdown for the given module (covered/partial/remaining)

**Rationale**: Reusing the existing agent avoids a new agent factory and keeps routing logic minimal. The Progress Agent already has topic-level knowledge of the curriculum from its system prompt.

---

## 6. Dashboard Rendering Strategy (SSR vs Client)

### Finding
`/dashboard/page.tsx` currently performs a **blocking SSR fetch** to `/api/v1/agents/progress/summary` before rendering. The Recommended Next card is populated from the same synchronous call (`data.recommendations`).

### Decision
Keep the existing SSR fetch for charts and module cards (these come from DB, not agent). Move recommendations to an **SSE client hook** (`useRecommendationsStream`) that fires after mount. This satisfies FR-005 (non-blocking) and SC-001 (< 2s to interactive).

The `DashboardClient` receives `initialProgress` (with empty `recommendations: []`) from SSR, then the SSE hook replaces it asynchronously.

---

## 7. Frontend Route for Module Progress

### Finding
No `module/[moduleId]/progress` page exists yet. The Next.js app uses `(student)` route group for authenticated student pages.

### Decision
Create `frontend/src/app/(student)/module/[moduleId]/progress/page.tsx`. The `moduleId` param is the human-readable slug. Auth guard is inherited from the route group layout.

---

## 8. Removing /progress

### Finding
`/progress/page.tsx` renders `<ComingSoonPanel>` — it's trivially removable (delete the file, Next.js returns 404). The sidebar `nav-links.tsx` lists `{ label: 'Progress', href: '/progress' }` which must be removed.

### Decision
- Delete `frontend/src/app/(student)/progress/page.tsx`
- Remove the `Progress` entry from `NAV_ITEMS` in `nav-links.tsx`
- No redirect needed (404 is acceptable per FR-016)
