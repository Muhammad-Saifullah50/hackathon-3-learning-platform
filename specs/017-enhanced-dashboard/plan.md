# Implementation Plan: Enhanced Student Dashboard & Module Progress Detail

**Branch**: `017-enhanced-dashboard` | **Date**: 2026-05-18 | **Spec**: `specs/017-enhanced-dashboard/spec.md`  
**Input**: Feature specification from `/specs/017-enhanced-dashboard/spec.md`

---

## Summary

Upgrade the student dashboard with Recharts visualisations (Mastery Over Time line chart + Module Mastery bar chart), an async SSE-based "Recommended Next" card powered by the Progress Agent, and a new `/module/[moduleId]/progress` page that streams a topic-level breakdown via SSE. Remove the standalone `/progress` page and its sidebar link. A new `mastery_snapshots` append-only table is required to support the time-series chart.

---

## Technical Context

**Language/Version**: Python 3.11+ (backend) · TypeScript 5+ / React 19 (frontend)  
**Primary Dependencies**:
- Backend: FastAPI, openai-agents ≥0.13, SQLAlchemy 2.0+, Alembic 1.13+, Pydantic 2.0+, asyncpg
- Frontend: Next.js 14+, Recharts ^2.15.0 (already installed), Tailwind CSS, React Query
**Storage**: Neon PostgreSQL — new `mastery_snapshots` table; all other reads from existing `user_module_mastery`, `modules`
**Testing**: pytest + httpx (backend), vitest + @testing-library/react (frontend), Playwright (E2E)
**Target Platform**: Linux server (backend) · Next.js 14 SSR/Client (frontend)
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: Dashboard interactive in < 2s (SC-001); SSE agent responses < 15s p95 (SC-003, SC-004)  
**Constraints**: 30s agent timeout; no new LLM provider; no chart data stored (ephemeral); mastery snapshots append-only (no UPDATE/DELETE)  
**Scale/Scope**: Per-student queries; 8 modules; up to ~365 snapshot rows per student per year

---

## Constitution Check

*GATE: Must pass before implementation begins.*

| Gate | Status | Notes |
|---|---|---|
| Repository pattern for DB access | PASS | New `MasterySnapshotRepository` + extend `ProgressRepository` |
| No business logic in route handlers | PASS | Agent calls delegated to service layer |
| All routes require auth | PASS | `get_current_user` dependency on all new endpoints |
| Stream all AI responses | PASS | SSE via `StreamingResponse` |
| Cache LLM responses where applicable | CONDITIONAL | Recommendations are user-specific; caching skipped. Module detail is per-user per-module — same skip. No violation since the rule targets identical prompt+lesson pairs. |
| Recharts loaded with `next/dynamic` | REQUIRED | Recharts uses browser APIs; must be dynamically imported with `ssr: false` |
| `mastery_snapshots` migration via Alembic | REQUIRED | No direct schema changes |
| Smallest viable diff | PASS | No refactors outside feature scope |

---

## Project Structure

### Documentation (this feature)

```text
specs/017-enhanced-dashboard/
├── plan.md              ← this file
├── research.md          ← Phase 0 (done)
├── data-model.md        ← Phase 1 (done)
├── quickstart.md        ← Phase 1 (done)
├── contracts/
│   └── openapi.yaml     ← Phase 1 (done)
└── tasks.md             ← Phase 2 (/sp.tasks — not yet)
```

### Source Code Layout

```text
backend/
├── alembic/versions/
│   └── YYYYMMDD_add_mastery_snapshots.py   [NEW] migration
├── src/
│   ├── api/v1/
│   │   └── dashboard.py                    [NEW] 3 endpoints
│   ├── repositories/
│   │   ├── progress_repository.py          [MOD] insert snapshot on update
│   │   └── mastery_snapshot_repository.py  [NEW] time-series queries
│   ├── schemas/
│   │   └── dashboard.py                    [NEW] Pydantic schemas
│   ├── services/agents/
│   │   ├── agents.py                       [MOD] progress agent mode branching
│   │   └── context.py                      [MOD] +agent_mode, +module_slug
│   ├── llm/
│   │   └── prompts.py                      [MOD] +2 prompt getters
│   ├── dependencies.py                     [MOD] register snapshot repo
│   └── main.py                             [MOD] mount dashboard router

frontend/src/
├── app/(student)/
│   ├── module/[moduleId]/progress/
│   │   └── page.tsx                        [NEW] module progress page
│   └── progress/
│       └── page.tsx                        [DELETE] FR-016
├── components/
│   ├── dashboard/
│   │   ├── mastery-timeline-chart.tsx      [NEW] LineChart (Mastery Over Time)
│   │   ├── module-mastery-chart.tsx        [NEW] BarChart (Module Mastery)
│   │   ├── dashboard-client.tsx            [MOD] add charts + SSE recommendations
│   │   ├── recommendations-panel.tsx       [MOD] SSE stream instead of static props
│   │   └── module-card.tsx                 [MOD] "View Progress" button
│   ├── module-progress/                    [NEW dir]
│   │   ├── topic-list.tsx                  [NEW] SSE-driven topic breakdown
│   │   └── topic-skeleton.tsx              [NEW] loading skeleton
│   └── layout/
│       └── nav-links.tsx                   [MOD] remove Progress nav item
├── hooks/
│   ├── use-recommendations-stream.ts       [NEW] SSE hook
│   └── use-module-progress-stream.ts       [NEW] SSE hook
├── lib/api/
│   └── dashboard.ts                        [NEW] fetch helpers
└── types/
    └── index.ts                            [MOD] +MasterySnapshot, TopicProgressItem, Recommendation
```

---

## Architecture Decisions

### AD-1: `mastery_snapshots` table instead of deriving from `user_quiz_attempts`

**Context**: `user_module_mastery` is a single row per (user, module) — it cannot produce a time series. Quiz attempts give partial signal but not composite mastery.

**Decision**: New append-only `mastery_snapshots` table. Written by `ProgressRepository.update_mastery_score()` as a side-effect (no new surface API).

**Trade-off**: Adds a table and migration; rows grow over time. Mitigated by the fact that mastery is updated infrequently (per quiz submission / exercise completion).

📋 Architectural decision detected: Append-only mastery_snapshots for time-series charting — Document reasoning and tradeoffs? Run `/sp.adr mastery-snapshots-time-series`

---

### AD-2: Dedicated dashboard router (not extending agents router)

**Context**: The existing `/api/v1/agents/chat` endpoint applies chat quota, session persistence, off-topic guardrails — none of which apply here.

**Decision**: New `backend/src/api/v1/dashboard.py` router with stateless read-only SSE endpoints.

**Trade-off**: One more file; but keeps separation of concerns clean and avoids entangling dashboard SSE with chat quota logic.

---

### AD-3: Progress Agent mode switching via `LearnFlowContext`

**Context**: The Progress Agent already understands student mastery. Two new tasks (recommendations + module detail) can be served by the same agent with different system prompts.

**Decision**: Add `agent_mode: Literal["recommendations", "module_detail"] | None` to `LearnFlowContext`. Progress Agent `dynamic_instructions` branches on this field.

**Trade-off**: Makes the Progress Agent more complex but avoids introducing a new agent type. Both modes share the same output validation and error handling.

---

## Phase-by-Phase Plan

### Phase 1 — DB & Backend Foundations

1. **Migration**: Create `mastery_snapshots` table + indexes (`idx_mastery_snapshots_user_recorded`, `idx_mastery_snapshots_user_module`)
2. **Snapshot write**: Extend `ProgressRepository.update_mastery_score()` to insert a snapshot row after each mastery update
3. **Snapshot read**: Create `MasterySnapshotRepository` with `get_daily_averages(user_id)` query
4. **Pydantic schemas**: `MasteryHistoryResponse`, `RecommendationItem`, `TopicProgressItem` in `src/schemas/dashboard.py`
5. **Prompts**: Add `get_recommendations_prompt(mastery_context)` and `get_module_detail_prompt(module_slug, mastery_context)` to `src/llm/prompts.py`
6. **Context extension**: Add `agent_mode`, `module_slug` to `LearnFlowContext`
7. **Agent extension**: Branch `get_progress_agent().dynamic_instructions` on `agent_mode`

### Phase 2 — New Dashboard Endpoints

8. **`GET /api/v1/dashboard/mastery-history`**: Query `MasterySnapshotRepository`, return `MasteryHistoryResponse`
9. **`GET /api/v1/dashboard/recommendations/stream`**: Build `LearnFlowContext(agent_mode="recommendations")`, run Progress Agent, stream SSE
10. **`GET /api/v1/module/{moduleId}/progress/stream`**: Validate slug, build `LearnFlowContext(agent_mode="module_detail", module_slug=...)`, run Progress Agent, stream SSE; return 404 for unknown slug
11. **Router registration**: Mount `dashboard.router` in `src/main.py`
12. **Dependency**: Register `get_mastery_snapshot_repository` in `src/dependencies.py`

### Phase 3 — Frontend Charts

13. **Types**: Add `MasterySnapshot`, `TopicProgressItem`, `Recommendation` to `types/index.ts`
14. **`dashboard.ts`**: Fetch helpers — `fetchMasteryHistory()`, `recommendationsStreamUrl()`, `moduleProgressStreamUrl(moduleId)`
15. **`mastery-timeline-chart.tsx`**: Recharts `<LineChart>` loaded via `next/dynamic({ ssr: false })`; x-axis = date, y-axis = avg_score; empty state when `snapshots.length === 0`
16. **`module-mastery-chart.tsx`**: Recharts `<BarChart layout="vertical">`; one bar per module; colour-coded by mastery band; empty state when all scores are 0

### Phase 4 — Frontend SSE Hooks

17. **`use-recommendations-stream.ts`**: Opens `EventSource` on mount; parses `recommendation` events; handles `error` and `done`; 30s client-side timeout fallback
18. **`use-module-progress-stream.ts`**: Same pattern; parses `topic` events; sorts covered first, then remaining/partial alphabetically within each group

### Phase 5 — Dashboard UI Integration

19. **`recommendations-panel.tsx`**: Accept `{ streamUrl: string }` instead of `recommendations: string[]`; use `useRecommendationsStream`; show loading state / fallback
20. **`dashboard-client.tsx`**: Add `MasteryTimelineChart` + `ModuleMasteryChart` sections; pass SSE URL to `RecommendationsPanel`; fetch mastery history with React Query
21. **`module-card.tsx`**: Replace "Start Lesson" button with "View Progress" linking to `/module/{module.id}/progress`

### Phase 6 — Module Progress Detail Page

22. **`topic-skeleton.tsx`**: Shimmer skeleton matching topic list layout
23. **`topic-list.tsx`**: Renders sorted topic list; uses `useModuleProgressStream`; shows skeleton while loading; fallback + retry button on error
24. **`/module/[moduleId]/progress/page.tsx`**: SSR auth check; render module name header + `TopicList`; validate slug (redirect to `/dashboard` on unknown)

### Phase 7 — Removals & Nav

25. **Delete** `frontend/src/app/(student)/progress/page.tsx`
26. **Remove** `Progress` entry from `NAV_ITEMS` in `nav-links.tsx`

### Phase 8 — Tests

27. Backend: unit tests for `MasterySnapshotRepository`, SSE endpoint integration tests (mock agent)
28. Frontend: component tests for `MasteryTimelineChart` (empty + data), `ModuleMasteryChart`, `TopicList` (loading/loaded/error states)
29. E2E (Playwright): verify `/progress` → 404; verify "View Progress" navigation; verify recommendations card lifecycle

---

## Risk Analysis

| Risk | Blast Radius | Mitigation |
|---|---|---|
| Progress Agent produces malformed topic JSON | Module progress page shows fallback | Pydantic validation on SSE parse; structured `output_type` on agent |
| `mastery_snapshots` grows unbounded over years | Query performance degrades | Index on `(user_id, recorded_at DESC)`; 365 rows/user/year is manageable for MVP |
| Recharts SSR crash (uses browser APIs) | Dashboard white screen | Enforce `next/dynamic({ ssr: false })` wrapper; add error boundary |

---

## Acceptance Checklist

- [ ] `mastery_snapshots` table exists in DB post-migration
- [ ] `GET /api/v1/dashboard/mastery-history` returns `{ snapshots: [] }` for new student
- [ ] `GET /api/v1/dashboard/recommendations/stream` emits `recommendation` events then `done`
- [ ] `GET /api/v1/module/bad-slug/progress/stream` returns 404
- [ ] Dashboard charts render without blocking page interactivity
- [ ] "Recommended Next" card shows loading state then updates in-place
- [ ] "View Progress" button navigates to `/module/{slug}/progress`
- [ ] Module progress page shows skeleton then agent-generated topic list
- [ ] `/progress` URL returns 404
- [ ] Sidebar has no "Progress" link
- [ ] No student can access another student's data via URL manipulation
