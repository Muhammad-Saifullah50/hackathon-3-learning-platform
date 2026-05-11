# Data Model: Interactive Code Editor (014)

**Phase**: 1 — Design  
**Date**: 2026-05-10

---

## New Database Entities

### 1. CodeSession

Persists a student's code for a given editor context (Playground or a specific exercise).

**Table**: `code_sessions`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `user_id` | UUID | FK → `users.id` ON DELETE CASCADE, NOT NULL | Student identity |
| `context_key` | VARCHAR(255) | NOT NULL | `"playground"` or exercise UUID |
| `code` | TEXT | NOT NULL, DEFAULT `""` | Current code content |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Auto-updated on write |

**Primary Key**: `(user_id, context_key)` — composite, enforces uniqueness and is the conflict target for UPSERT.

**Index**: `(user_id, context_key)` (covered by PK).

**Validation rules**:
- `context_key` must be either `"playground"` or a valid UUID string (exercise ID). Enforced at service layer, not DB.
- `code` length is not limited at DB level; service layer caps at 100,000 characters.

---

## Existing Entities (modified)

### 2. IdentifierType Enum (auth/models.py)

Add `user_daily = "user_daily"` to the `IdentifierType` enum to support daily rate limit counters.

**Impact**: Requires Alembic migration to update the PostgreSQL `identifiertype` enum type.

### 3. RateLimitCounter (auth/models.py — no schema change)

Used as-is for daily limits. Identifier format:
- Run limit: `"{user_id}:run:{YYYY-MM-DD}"`
- Review limit: `"{user_id}:review:{YYYY-MM-DD}"`

These keys expire implicitly — each new calendar date creates a new record. Old records can be pruned via a scheduled cleanup (out of scope for MVP).

---

## Existing Entities (read-only)

### 4. CodeSubmission (already exists — F05)

Used by the Submit flow. No schema changes needed. The `exercise_id` field maps to the `context_key` when in embedded graded mode.

### 5. AgentSession (already exists — F07)

Used by both conversation channels:
- **Code feedback channel**: `session_id` derived from `"code-{context_key}-{user_id}"`
- **General tutor panel**: `session_id` derived from `"tutor-{user_id}-{session_uuid}"`

These are distinct session IDs, ensuring complete conversation isolation.

---

## Frontend State Model

### EditorMode
```typescript
type EditorMode = "playground" | "exercise"

interface EditorConfig {
  mode: EditorMode
  contextKey: string          // "playground" or exercise UUID
  starterCode?: string        // lesson-provided; undefined → blank editor
  exerciseId?: string         // present when mode === "exercise"
  isGraded?: boolean          // true → Submit button visible
}
```

### ExecutionResult
```typescript
interface ExecutionResult {
  stdout: string
  stderr: string
  executionTimeMs: number
  timedOut: boolean
  errorLine?: number          // parsed from stderr for line highlighting
  status: "success" | "error" | "timeout"
}
```

### CodeFeedbackMessage
```typescript
interface CodeFeedbackMessage {
  role: "user" | "assistant"
  content: string
  timestamp: string
  codeSnapshot?: string       // code at time of review request
}
```

### TutorPanelMessage
```typescript
interface TutorPanelMessage {
  role: "user" | "assistant"
  content: string
  timestamp: string
}
```

### SubmissionResult
```typescript
interface SubmissionResult {
  passed: boolean
  failingTestCases: Array<{
    input: string
    expected: string
    actual: string
  }>
  message: string
}
```

---

## State Transitions

### Code Session Lifecycle
```
[Editor Opens]
    │
    ├─ Load from localStorage (context_key)
    ├─ If not in localStorage → Load from backend GET /code-sessions/{context_key}
    └─ If no backend record → Use starterCode or blank
    │
[Student Types]
    └─ After 5s inactivity → Save to localStorage (debounced)
    │
[Student Runs / Submits / Reviews]
    └─ Save to backend PUT /code-sessions/{context_key}
    │
[Student Returns]
    └─ Restore from localStorage (fast) or backend (cross-device)
```

### Rate Limit State
```
[Request Initiated]
    │
    ├─ Button disabled (in-flight)
    ├─ Backend checks daily counter
    ├─ Counter < 3 → increment → allow → button re-enabled on response
    └─ Counter ≥ 3 → HTTP 429 → show message → button re-enabled (user can try tomorrow)
```
