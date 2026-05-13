# Data Model: Chat Interface with AI Tutor (F15)

**Date**: 2026-05-11 | **Branch**: `015-ai-tutor-chat`

---

## 1. Modified Entities

### 1.1 `AgentSession` (existing — modified)

**Table**: `agent_sessions`

Two new nullable columns added via Alembic migration:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `title` | `TEXT` | YES | NULL | Human-readable session title (first 60 chars of first message, set on first message save) |
| `surface` | `VARCHAR(20)` | YES | NULL | `'standalone'` or `'embedded'`; NULL for legacy sessions from F07 |

**Existing columns preserved** (no changes):
- `id UUID PK`
- `user_id UUID FK → users.id`
- `status VARCHAR(20)` — `active | completed | abandoned`
- `conversation_history JSONB` — `[{role, content, timestamp, agent_type?}]`
- `active_agent VARCHAR(30)`
- `created_at TIMESTAMP`
- `updated_at TIMESTAMP`

**New indexes**:
- `idx_agent_session_title_updated` — `(user_id, updated_at DESC)` — used by session list query

**Validation rules**:
- `surface` CHECK: `surface IN ('standalone', 'embedded') OR surface IS NULL`
- `title` max length enforced in service layer (60 chars, word-boundary trim)

**State transitions** (status field):
```
active → completed  (student explicitly closes or session replaced by new one)
active → abandoned  (system cleanup after 7 days of inactivity — future, not F15)
```

---

## 2. New Entities (via existing `RateLimitCounter` — no new table)

### 2.1 Chat Quota Tracking

**Table**: `rate_limit_counters` (existing, reused)

The `ChatQuotaService` uses the existing `RateLimitCounter` model with a namespaced identifier:

```
identifier = "{user_id}:chat:{UTC_date}"  
# e.g., "550e8400-e29b-41d4-a716-446655440000:chat:2026-05-11"
```

| Column | Role in Chat Quota |
|--------|--------------------|
| `identifier` | `{user_id}:chat:{date}` |
| `identifier_type` | `USER_DAILY` |
| `attempt_count` | messages sent today (0–5) |
| `last_attempt_at` | timestamp of last message |
| `created_at` | when first message of the day was sent |

**Quota rules**:
- Limit: 5 messages per UTC calendar day
- Reset: identifier changes naturally at UTC midnight (new date → new row)
- Check: `attempt_count < 5` → allowed; increment atomically via `ON CONFLICT DO UPDATE`
- Remaining: `max(0, 5 - attempt_count)` after last increment

---

## 3. Conversation History Schema (JSONB)

`agent_sessions.conversation_history` is a JSONB array. Each element:

```json
{
  "role": "user | assistant",
  "content": "message text (max 2000 chars for user; unbounded for AI)",
  "timestamp": "2026-05-11T14:30:00Z",
  "agent_type": "triage | concepts | debug | code_review | exercise | progress | null"
}
```

- `agent_type` is NULL for user messages; set to the specialist agent name for AI messages.
- Context injection (code snippet, execution output) is prepended to the user message before it is sent to the AI but is **not stored** in `conversation_history` — only the raw user text is stored. This keeps history clean and avoids unbounded JSONB growth.
- Context is stored in a separate `context_snapshot` field only if `code_snippet` was provided (optional; for debugging purposes).

**History window rule**: Only the last 5 entries (combined user + AI) are sent as context to the LLM on each request (FR-012). Full history is stored in DB for display but not all sent to LLM.

---

## 4. Structured Agent Output Schemas

These Pydantic models are used as `output_type` in each specialist agent's `Runner.run_streamed` call. They are serialised to JSON and emitted as `event: structured` SSE before `[DONE]`.

### 4.1 Shared Sub-types

```python
class CodeBlock(BaseModel):
    code: str
    language: str = "python"
    caption: Optional[str] = None

class IssueItem(BaseModel):
    line_ref: Optional[str] = None   # e.g. "line 12" or "lines 5-8"
    severity: Literal["error", "warning", "suggestion"]
    message: str
```

### 4.2 Agent Response Types

```python
class ConceptResponse(BaseModel):
    response_type: Literal["concept"] = "concept"
    explanation: str
    code_blocks: list[CodeBlock] = []          # 0-3 inline examples
    key_points: list[str] = []                 # bullet takeaways
    related_topics: list[str] = []             # follow-up topic names
    send_to_editor: Optional[CodeBlock] = None # primary runnable example

class DebugResponse(BaseModel):
    response_type: Literal["debug"] = "debug"
    error_identified: str          # e.g. "NameError: name 'x' is not defined"
    explanation: str               # why it happened
    hint: str                      # progressive hint (always shown)
    fix_code: Optional[CodeBlock] = None       # corrected snippet (after hint)
    send_to_editor: Optional[CodeBlock] = None # same as fix_code when present

class ExerciseResponse(BaseModel):
    response_type: Literal["exercise"] = "exercise"
    title: str
    description: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    starter_code: CodeBlock
    expected_concepts: list[str] = []          # Python topics this covers
    send_to_editor: Optional[CodeBlock] = None # always set to starter_code

class CodeReviewResponse(BaseModel):
    response_type: Literal["code_review"] = "code_review"
    summary: str
    score: int = Field(ge=0, le=100)
    issues: list[IssueItem] = []
    improved_code: Optional[CodeBlock] = None
    send_to_editor: Optional[CodeBlock] = None # same as improved_code when present

class ProgressResponse(BaseModel):
    response_type: Literal["progress"] = "progress"
    summary: str
    streak_days: int = 0
    next_recommended_topic: Optional[str] = None
    modules: list[dict] = []  # [{name, mastery_percent, level}]
    send_to_editor: None = None  # progress has no code to load

# Union type used on the frontend side for type narrowing
TutorResponse = Union[
    ConceptResponse, DebugResponse, ExerciseResponse,
    CodeReviewResponse, ProgressResponse
]
```

### 4.3 Storage

The `conversation_history` JSONB array stores the serialised structured response for AI turns. The `content` field stores the `response_type` + full JSON dump so history can be re-rendered with full fidelity on reload.

```json
{
  "role": "assistant",
  "content": "{\"response_type\":\"exercise\",\"title\":\"List Comprehension...\", ...}",
  "timestamp": "2026-05-11T14:30:00Z",
  "agent_type": "exercise"
}
```

The frontend detects AI message `content` starting with `{"response_type":` and parses it as structured; otherwise falls back to plain text rendering (for legacy messages from F07).

---

## 5. API Response Shapes

### 4.1 Session List Item

```python
class ChatSessionListItem(BaseModel):
    id: str  # UUID
    title: str
    surface: Optional[str]  # 'standalone' | 'embedded' | None
    message_count: int
    last_message_at: datetime
    created_at: datetime
```

### 4.2 Session Detail (with messages)

```python
class ChatSessionDetail(BaseModel):
    id: str
    title: str
    surface: Optional[str]
    conversation_history: list[ConversationMessage]  # existing schema
    created_at: datetime
    updated_at: datetime
```

### 4.3 Chat Quota Status

```python
class ChatQuotaStatus(BaseModel):
    messages_sent_today: int
    daily_limit: int  # always 5
    remaining: int    # max(0, 5 - messages_sent_today)
    quota_reset_at: datetime  # next UTC midnight
```

### 4.4 Enhanced Chat Request

```python
class AgentChatRequest(BaseModel):  # extends existing
    message: str = Field(..., min_length=1, max_length=2000)
    topic: Optional[str] = None
    session_id: Optional[str] = None
    code_snippet: Optional[str] = Field(None, max_length=4096)  # 4 KB cap
    execution_output: Optional[str] = Field(None, max_length=2000)
    surface: Optional[Literal['standalone', 'embedded']] = None
```

---

## 6. Relationship Diagram

```
users (existing)
  │
  ├──< agent_sessions (existing + title/surface columns)
  │       │
  │       └──< routing_decisions (existing)
  │       └──< hint_progressions (existing)
  │
  └──< rate_limit_counters (existing — chat quota via identifier pattern)
```

---

## 7. Migration Plan

**Migration file**: `alembic/versions/20260511_XXXX_add_chat_session_title_surface.py`

```python
# Up
op.add_column('agent_sessions', sa.Column('title', sa.Text(), nullable=True))
op.add_column('agent_sessions', sa.Column('surface', sa.String(20), nullable=True))
op.create_check_constraint(
    'check_session_surface',
    'agent_sessions',
    "surface IN ('standalone', 'embedded') OR surface IS NULL"
)
op.create_index(
    'idx_agent_session_user_updated',
    'agent_sessions',
    ['user_id', sa.text('updated_at DESC')]
)

# Down
op.drop_index('idx_agent_session_user_updated', 'agent_sessions')
op.drop_constraint('check_session_surface', 'agent_sessions')
op.drop_column('agent_sessions', 'surface')
op.drop_column('agent_sessions', 'title')
```

**No data migration required** — existing sessions get `title=NULL`, `surface=NULL` which is valid.
