# Data Model: Quiz System (F16)

**Branch**: `016-quiz-system` | **Date**: 2026-05-17

---

## Entities

### 1. QuizSession (NEW)

**Table**: `quiz_sessions`
**Purpose**: Stores a single student quiz attempt — generated questions, student answers, AI grades, and final score.

#### Fields

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID (PK) | NO | uuid4 | Primary key |
| `student_id` | UUID (FK → users.id) | NO | — | Ownership; 403 on mismatch |
| `chat_session_id` | UUID (FK → agent_sessions.id) | NO | — | Which chat session triggered this quiz |
| `module_slug` | VARCHAR(50) | NO | — | One of 8 curriculum slugs (constrained) |
| `topic_label` | VARCHAR(200) | NO | — | Human-readable topic for display |
| `status` | VARCHAR(20) | NO | `'generated'` | `generated` → `in_progress` → `completed` |
| `score` | FLOAT | YES | NULL | 0.0–100.0; NULL until completed |
| `questions` | JSONB | NO | — | 6-card array (3 MCQ + 3 flashcard) |
| `student_answers` | JSONB | NO | `{}` | Keyed by card index (0–5) |
| `grades` | JSONB | NO | `{}` | Keyed by card index (0–5) |
| `completed_at` | TIMESTAMP WITH TZ | YES | NULL | Set on submit |
| `created_at` | TIMESTAMP WITH TZ | NO | now() | From TimestampMixin |
| `updated_at` | TIMESTAMP WITH TZ | NO | now() | From TimestampMixin |

#### Indexes

```sql
CREATE INDEX idx_quiz_sessions_student_id   ON quiz_sessions (student_id);
CREATE INDEX idx_quiz_sessions_chat_session ON quiz_sessions (chat_session_id);
CREATE INDEX idx_quiz_sessions_status       ON quiz_sessions (status);
CREATE INDEX idx_quiz_sessions_module_slug  ON quiz_sessions (module_slug);
CREATE INDEX idx_quiz_sessions_created_at   ON quiz_sessions (created_at DESC);
```

#### Constraints

```sql
CHECK (status IN ('generated', 'in_progress', 'completed'))
CHECK (score IS NULL OR (score >= 0 AND score <= 100))
CHECK (module_slug IN ('basics', 'control_flow', 'data_structures', 'functions', 'oop', 'files', 'errors', 'libraries'))
FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
FOREIGN KEY (chat_session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
```

#### JSONB Shape: `questions`

```json
[
  {
    "type": "mcq",
    "question": "What does the `range(5)` function return?",
    "options": [
      "A list [0, 1, 2, 3, 4]",
      "A range object from 0 to 4",
      "A list [1, 2, 3, 4, 5]",
      "An iterator from 1 to 5"
    ],
    "correct_index": 1
  },
  {
    "type": "mcq",
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_index": 0
  },
  {
    "type": "mcq",
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_index": 2
  },
  {
    "type": "flashcard",
    "term": "list comprehension",
    "definition": "A concise syntax to create a new list by applying an expression to each item in an iterable, optionally filtering items."
  },
  {
    "type": "flashcard",
    "term": "for loop",
    "definition": "A control flow statement that iterates over a sequence or iterable, executing a block of code for each element."
  },
  {
    "type": "flashcard",
    "term": "break statement",
    "definition": "A statement that immediately exits the nearest enclosing loop."
  }
]
```

#### JSONB Shape: `student_answers`

```json
{
  "0": 1,
  "1": 0,
  "2": null,
  "3": "a shorthand way to create lists by iterating",
  "4": null,
  "5": null
}
```
- MCQ: integer (selected option index, 0-3) or null
- Flashcard: string (typed answer) or null

#### JSONB Shape: `grades`

```json
{
  "0": "correct",
  "1": "wrong",
  "2": null,
  "3": "Partial",
  "4": null,
  "5": null
}
```
- MCQ grades: `"correct"` or `"wrong"` (computed client-side, submitted in POST /submit body)
- Flashcard grades: `"Correct"` | `"Partial"` | `"Wrong"` (from AI grader)

---

### 2. MasteryRecord (EXISTING — modified behaviour only)

**Table**: `mastery_records` (no schema change)

The quiz submit endpoint reads the existing record for the student + module_slug pair, updates `component_breakdown.quizzes` to the most-recent quiz score (0–100), recomputes the total, and calls `MasteryRepository.update_mastery()`.

No migration needed for this table.

---

### 3. AgentSession (EXISTING — no schema change)

The chat session detail response will embed `quiz_session_id` when the assistant message `content` parses to a `QuizResponse`. The `quiz_session_id` is stored as part of the message content JSON. No new columns required.

---

## State Machine: Quiz Session

```
┌───────────┐    first answer    ┌─────────────┐    all answered + submit    ┌───────────┐
│ generated │ ─────────────────► │ in_progress │ ─────────────────────────► │ completed │
└───────────┘                    └─────────────┘                             └───────────┘
     │                                  │
     │  (student never returns)         │  (student leaves mid-quiz)
     ▼                                  ▼
 [partial session retained; no score]  [partial session retained; resumes on return]
```

**Transition rules**:
- `generated → in_progress`: triggered by first flashcard grading call (`POST /grade-flashcard`). MCQ client-side answers do not trigger a server state change until submit.
- `in_progress → completed`: triggered by `POST /submit` only when all 6 cards are answered (validated server-side).
- No reverse transitions. Retakes create a new `quiz_sessions` row.

---

## Alembic Migration

**File**: `backend/alembic/versions/20260517_create_quiz_sessions_table.py`

```python
"""Create quiz_sessions table

Revision ID: 20260517_quiz_sessions
Revises: 20260511_add_chat_session_title_surface
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260517_quiz_sessions"
down_revision = "20260511_add_chat_session_title_surface"
branch_labels = None
depends_on = None

VALID_SLUGS = "('basics','control_flow','data_structures','functions','oop','files','errors','libraries')"
VALID_STATUS = "('generated','in_progress','completed')"


def upgrade() -> None:
    op.create_table(
        "quiz_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_session_id", UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_slug", sa.String(50), nullable=False),
        sa.Column("topic_label", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("questions", JSONB, nullable=False),
        sa.Column("student_answers", JSONB, nullable=False, server_default="'{}'"),
        sa.Column("grades", JSONB, nullable=False, server_default="'{}'"),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_check_constraint("ck_quiz_status", "quiz_sessions", f"status IN {VALID_STATUS}")
    op.create_check_constraint("ck_quiz_score", "quiz_sessions", "score IS NULL OR (score >= 0 AND score <= 100)")
    op.create_check_constraint("ck_quiz_module_slug", "quiz_sessions", f"module_slug IN {VALID_SLUGS}")

    op.create_index("idx_quiz_sessions_student_id",   "quiz_sessions", ["student_id"])
    op.create_index("idx_quiz_sessions_chat_session",  "quiz_sessions", ["chat_session_id"])
    op.create_index("idx_quiz_sessions_status",        "quiz_sessions", ["status"])
    op.create_index("idx_quiz_sessions_module_slug",   "quiz_sessions", ["module_slug"])
    op.create_index("idx_quiz_sessions_created_at",    "quiz_sessions", ["created_at"])


def downgrade() -> None:
    op.drop_table("quiz_sessions")
```

---

## SQLAlchemy Model

**File**: `backend/src/models/quiz_session.py`

```python
"""Quiz session model."""
import uuid
from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.base import TimestampMixin

CURRICULUM_SLUGS = (
    "basics", "control_flow", "data_structures", "functions",
    "oop", "files", "errors", "libraries",
)

class QuizSession(Base, TimestampMixin):
    """A single student quiz attempt."""
    __tablename__ = "quiz_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    module_slug = Column(String(50), nullable=False, index=True)
    topic_label = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="generated")
    score = Column(Float, nullable=True)
    questions = Column(JSONB, nullable=False)
    student_answers = Column(JSONB, nullable=False, default=dict)
    grades = Column(JSONB, nullable=False, default=dict)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('generated','in_progress','completed')", name="ck_quiz_status"),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_quiz_score"),
        CheckConstraint(
            f"module_slug IN {tuple(CURRICULUM_SLUGS)!r}".replace("(", "(", 1),
            name="ck_quiz_module_slug",
        ),
        Index("idx_quiz_sessions_student_id",  "student_id"),
        Index("idx_quiz_sessions_chat_session", "chat_session_id"),
        Index("idx_quiz_sessions_status",       "status"),
        Index("idx_quiz_sessions_module_slug",  "module_slug"),
        Index("idx_quiz_sessions_created_at",   "created_at"),
    )
```

---

## Scoring Formula

| Card type | Grade | Points |
|-----------|-------|--------|
| MCQ | Correct | 1.0 |
| MCQ | Wrong | 0.0 |
| Flashcard | Correct | 1.0 |
| Flashcard | Partial | 0.5 |
| Flashcard | Wrong | 0.0 |

**Raw score** = Σ(points) / 6 (max = 6 cards)
**Quiz component (0–100)** = raw_score × 100

**Mastery recompute** (unchanged formula):
```
total_mastery = exercises×0.4 + quizzes×0.3 + code_quality×0.2 + streak×0.1
```

**Level thresholds** (unchanged):
| Score | Level |
|-------|-------|
| 0–40 | Beginner |
| 41–70 | Learning |
| 71–90 | Proficient |
| 91–100 | Mastered |

**Struggle trigger**: if `quiz_component < 50` after submit, flag for struggle detection.
