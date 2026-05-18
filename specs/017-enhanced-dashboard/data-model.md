# Data Model: Enhanced Student Dashboard & Module Progress Detail

**Branch**: `017-enhanced-dashboard` | **Date**: 2026-05-18

---

## Existing Tables (read-only for charts)

### `user_module_mastery`
Stores the **current** mastery score per student per module.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users.id | CASCADE DELETE |
| module_id | INT FK → modules.id | |
| score | FLOAT | 0–100 |
| version | INT | Optimistic lock |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Unique index: `(user_id, module_id)` — **one row per student per module**.  
Used by: "Module Mastery" bar chart (current scores), Progress Agent context.

---

## New Table

### `mastery_snapshots`
Append-only log of mastery scores over time. One row per mastery update event.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID PK | NO | uuid_generate_v4() | |
| user_id | UUID FK → users.id | NO | — | CASCADE DELETE |
| module_id | INT FK → modules.id | NO | — | |
| score | FLOAT | NO | — | 0–100 |
| recorded_at | TIMESTAMPTZ | NO | NOW() | Indexed |

**Indexes**:
- `idx_mastery_snapshots_user_recorded` on `(user_id, recorded_at DESC)` — dashboard time-series query
- `idx_mastery_snapshots_user_module` on `(user_id, module_id)` — module progress query

**Write pattern**: Every call to `ProgressRepository.update_mastery_score()` inserts one row here in addition to updating `user_module_mastery`.

**Query for "Mastery Over Time" chart**:
```sql
SELECT
  DATE(recorded_at) AS day,
  AVG(score) AS avg_score
FROM mastery_snapshots
WHERE user_id = :user_id
GROUP BY DATE(recorded_at)
ORDER BY day ASC;
```

---

## Ephemeral Entities (not persisted)

### `TopicProgressItem`
Agent-generated assessment of a single topic for a student. Returned in SSE stream, never stored.

```python
class TopicProgressItem(BaseModel):
    topic: str              # e.g., "ternary shorthand"
    status: Literal["covered", "partial", "remaining"]
    note: str | None        # optional detail, e.g. "understands basics but not edge cases"
```

### `Recommendation`
Agent-generated next-action suggestion. Returned in SSE stream, never stored.

```python
class Recommendation(BaseModel):
    text: str               # e.g., "Take a quiz on Control Flow to push past 70%"
    module_slug: str | None # associated module, if applicable
```

---

## Static Module Slug Map (backend constant)

```python
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

Used by `GET /api/v1/module/{moduleId}/progress/stream` to resolve slug → module DB ID.

---

## LearnFlowContext Extension

Two new optional fields added to `src/services/agents/context.py`:

```python
agent_mode: Literal["recommendations", "module_detail"] | None = None
module_slug: str | None = None
```

---

## Frontend Type Additions (`frontend/src/types/index.ts`)

```typescript
export interface MasterySnapshot {
  day: string           // ISO date "YYYY-MM-DD"
  avg_score: number     // 0–100
}

export type TopicStatus = 'covered' | 'partial' | 'remaining'

export interface TopicProgressItem {
  topic: string
  status: TopicStatus
  note?: string
}

export interface Recommendation {
  text: string
  module_slug?: string
}
```

---

## Schema Summary (no breaking changes to existing tables)

| Change | Type | Impact |
|---|---|---|
| Add `mastery_snapshots` | New table | Requires Alembic migration |
| Extend `LearnFlowContext` | Backend dataclass | Non-breaking, optional fields |
| Add `agent_mode`, `module_slug` | New fields | Backward-compatible |
| Add frontend types | TS interfaces | Non-breaking |
