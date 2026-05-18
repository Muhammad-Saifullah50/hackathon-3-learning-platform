# Quickstart: Enhanced Student Dashboard & Module Progress Detail

**Branch**: `017-enhanced-dashboard` | **Date**: 2026-05-18

---

## Prerequisites

- Python 3.11+ with existing virtualenv activated (`backend/`)
- Node.js 18+ with `pnpm` or `npm` (`frontend/`)
- Neon PostgreSQL connection string in `backend/.env` (`DATABASE_URL`)
- LLM API key configured (`GEMINI_API_KEY` or equivalent in `.env`)

---

## Backend Setup

### 1. Run the new migration

```bash
cd backend
alembic upgrade head
```

This applies `20260518_add_mastery_snapshots.py`, creating the `mastery_snapshots` table with appropriate indexes.

### 2. Verify the new table exists

```bash
psql $DATABASE_URL -c "\d mastery_snapshots"
```

### 3. Start the backend

```bash
uvicorn src.main:app --reload --port 8000
```

### 4. Verify new endpoints appear in Swagger

Open `http://localhost:8000/docs` and confirm:
- `GET /api/v1/dashboard/mastery-history`
- `GET /api/v1/dashboard/recommendations/stream`
- `GET /api/v1/module/{moduleId}/progress/stream`

---

## Frontend Setup

### 1. Install dependencies (none new — recharts already present)

```bash
cd frontend
npm install
```

### 2. Start the dev server

```bash
npm run dev
```

### 3. Verify chart rendering

1. Log in as a student with existing mastery records
2. Navigate to `/dashboard`
3. Confirm "Mastery Over Time" line chart renders (or shows empty state)
4. Confirm "Module Mastery" bar chart renders all 8 modules
5. Confirm "Recommended Next" card shows loading state then updates with AI content

### 4. Verify module progress page

1. Click "View Progress" on any module card
2. Confirm navigation to `/module/{slug}/progress`
3. Confirm loading skeleton appears then is replaced by topic breakdown

### 5. Verify /progress removal

1. Navigate to `/progress` — expect 404
2. Confirm sidebar has no "Progress" link

---

## New Files Added

### Backend

| File | Purpose |
|---|---|
| `backend/alembic/versions/20260518_add_mastery_snapshots.py` | DB migration — new table |
| `backend/src/api/v1/dashboard.py` | New router: mastery-history + 2 SSE endpoints |
| `backend/src/schemas/dashboard.py` | Pydantic: MasterySnapshotResponse, RecommendationItem, TopicProgressItem |
| `backend/src/repositories/mastery_snapshot_repository.py` | Query mastery_snapshots table |

### Frontend

| File | Purpose |
|---|---|
| `frontend/src/app/(student)/module/[moduleId]/progress/page.tsx` | New module progress detail page |
| `frontend/src/components/dashboard/mastery-timeline-chart.tsx` | Recharts LineChart (Mastery Over Time) |
| `frontend/src/components/dashboard/module-mastery-chart.tsx` | Recharts BarChart (Module Mastery) |
| `frontend/src/components/module-progress/topic-list.tsx` | SSE-driven topic breakdown |
| `frontend/src/components/module-progress/topic-skeleton.tsx` | Loading skeleton for topic list |
| `frontend/src/hooks/use-recommendations-stream.ts` | SSE hook for recommendations card |
| `frontend/src/hooks/use-module-progress-stream.ts` | SSE hook for module detail page |
| `frontend/src/lib/api/dashboard.ts` | Fetch helpers: mastery history, SSE URLs |

---

## Files Modified

### Backend

| File | Change |
|---|---|
| `backend/src/services/agents/context.py` | Add `agent_mode`, `module_slug` fields |
| `backend/src/services/agents/agents.py` | Extend `get_progress_agent()` with mode branching |
| `backend/src/llm/prompts.py` | Add `get_recommendations_prompt()`, `get_module_detail_prompt()` |
| `backend/src/repositories/progress_repository.py` | Insert into `mastery_snapshots` on mastery update |
| `backend/src/dependencies.py` | Register `get_mastery_snapshot_repository` |
| `backend/src/main.py` | Mount new `dashboard` router |

### Frontend

| File | Change |
|---|---|
| `frontend/src/components/layout/nav-links.tsx` | Remove `Progress` nav item |
| `frontend/src/components/dashboard/module-card.tsx` | Replace "Start Lesson" with "View Progress" |
| `frontend/src/components/dashboard/recommendations-panel.tsx` | Accept SSE stream instead of static `string[]` |
| `frontend/src/components/dashboard/dashboard-client.tsx` | Add chart section; pass SSE hook to recommendations |
| `frontend/src/types/index.ts` | Add `MasterySnapshot`, `TopicProgressItem`, `Recommendation` |

### Removed

| File | Reason |
|---|---|
| `frontend/src/app/(student)/progress/page.tsx` | FR-016: standalone /progress removed |

---

## Environment Variables

No new environment variables required. The new SSE endpoints use the same auth JWT flow as existing agent endpoints.

---

## Testing

```bash
# Backend unit + integration
cd backend
pytest tests/ -x -q

# Frontend component tests
cd frontend
npm run test

# Manual SSE test (replace TOKEN)
curl -N -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/dashboard/recommendations/stream

curl -N -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/module/control-flow/progress/stream
```
