# Data Model: 018-Teacher Dashboard

**Phase**: Phase 1 — Design  
**Date**: 2026-05-18  
**Branch**: `018-teacher-dashboard`

---

## Overview

F18 adds seven new tables to the Neon PostgreSQL database. All use UUID primary keys, `TimestampMixin` (created_at, updated_at), and are added via a single Alembic migration.

---

## Existing Tables Referenced (Read-Only)

| Table | Used For |
|-------|---------|
| `users` | FK target for teacher_id, student_id |
| `exercises_agent` | F07 student exercises — NOT extended; separate teacher table created |

---

## New Entities

### 1. `classes` — Class

Represents a named group of students owned by one teacher.

```
classes
├── id            UUID PK
├── name          VARCHAR(100) NOT NULL
├── teacher_id    UUID FK→users.id ON DELETE CASCADE, NOT NULL, INDEX
├── created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints**:
- `name` length 1–100 characters
- `teacher_id` must reference a user with `role='teacher'` (enforced at service layer)
- No unique constraint on name per teacher (teachers may have similarly-named classes)

**Indexes**: `idx_class_teacher_id` on `teacher_id`

**Relationships**:
- One teacher → many classes
- One class → many `class_memberships`
- One class → many `class_exercises`

---

### 2. `class_memberships` — ClassMembership

Links a student to a class with an invitation status.

```
class_memberships
├── id             UUID PK
├── class_id       UUID FK→classes.id ON DELETE CASCADE, NOT NULL
├── student_id     UUID FK→users.id ON DELETE CASCADE, NOT NULL
├── status         VARCHAR(10) NOT NULL DEFAULT 'pending'  -- pending|accepted|declined
├── invited_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
├── responded_at   TIMESTAMPTZ NULL
├── created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints**:
- `UNIQUE(class_id, student_id)` — prevents duplicate invitations
- `CHECK(status IN ('pending', 'accepted', 'declined'))`

**Indexes**:
- `idx_membership_class_id` on `class_id`
- `idx_membership_student_id` on `student_id`
- `idx_membership_status` on `status`

**State Transitions**:
```
pending → accepted  (student clicks "Accept")
pending → declined  (student clicks "Decline")
```
Accepted and declined states are final (no re-invitation without explicit teacher action — deferred to later feature).

---

### 3. `teacher_generated_exercises` — TeacherGeneratedExercise

Stores multi-question exercises created by teachers via the Exercise Agent.

```
teacher_generated_exercises
├── id               UUID PK
├── title            VARCHAR(200) NOT NULL
├── topic            VARCHAR(100) NOT NULL
├── difficulty       VARCHAR(20) NOT NULL           -- beginner|intermediate|advanced
├── target_module    VARCHAR(100) NOT NULL
├── generation_prompt TEXT NOT NULL                 -- teacher's original prompt (verbatim)
├── questions        JSONB NOT NULL                 -- array of question objects
├── created_by_id    UUID FK→users.id ON DELETE SET NULL, NULL
├── created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**`questions` JSONB Schema**:
```json
[
  {
    "index": 0,
    "description": "Write a function that returns the sum of two numbers.",
    "starter_code": "def add(a, b):\n    pass"
  },
  {
    "index": 1,
    "description": "Use a list comprehension to square each number in a list.",
    "starter_code": "numbers = [1, 2, 3, 4, 5]\nresult = ..."
  }
]
```

**Constraints**:
- `CHECK(difficulty IN ('beginner', 'intermediate', 'advanced'))`
- `questions` must be a non-empty array (enforced at service layer before persist)

**Indexes**:
- `idx_teacher_exercise_created_by` on `created_by_id`
- `idx_teacher_exercise_topic` on `topic`

**Note**: This is NOT the same as `exercises_agent`. That table stores single-question sandbox exercises for student practice (F07). This table stores multi-question teacher-assigned exercises reviewed by AI (not auto-graded via test cases).

---

### 4. `class_exercises` — ClassExercise

Links a teacher-generated exercise to a class (i.e., an assignment).

```
class_exercises
├── id              UUID PK
├── class_id        UUID FK→classes.id ON DELETE CASCADE, NOT NULL
├── exercise_id     UUID FK→teacher_generated_exercises.id ON DELETE CASCADE, NOT NULL
├── assigned_by_id  UUID FK→users.id ON DELETE SET NULL, NULL
├── assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
├── created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints**:
- `UNIQUE(class_id, exercise_id)` — prevents assigning the same exercise to the same class twice

**Indexes**:
- `idx_class_exercise_class_id` on `class_id`
- `idx_class_exercise_exercise_id` on `exercise_id`

---

### 5. `class_exercise_submissions` — ClassExerciseSubmission

Records a student's submission for a class exercise. One row per student per class exercise.

```
class_exercise_submissions
├── id                   UUID PK
├── class_exercise_id    UUID FK→class_exercises.id ON DELETE CASCADE, NOT NULL
├── student_id           UUID FK→users.id ON DELETE CASCADE, NOT NULL
├── overall_score        FLOAT NULL                -- NULL until submitted
├── status               VARCHAR(15) NOT NULL DEFAULT 'in_progress'
├── submitted_at         TIMESTAMPTZ NULL          -- NULL until submitted
├── created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints**:
- `UNIQUE(class_exercise_id, student_id)` — prevents resubmission (enforced at DB level)
- `CHECK(status IN ('in_progress', 'submitted'))`
- `CHECK(overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100))`

**Indexes**:
- `idx_submission_class_exercise_id` on `class_exercise_id`
- `idx_submission_student_id` on `student_id`
- `idx_submission_status` on `status`

**State Transitions**:
```
in_progress → submitted  (student submits after all questions reviewed)
```
Submitted is final — no resubmission.

---

### 6. `question_reviews` — QuestionReview

Stores the AI-generated review and grade for a single question within a submission.

```
question_reviews
├── id                        UUID PK
├── submission_id             UUID FK→class_exercise_submissions.id ON DELETE CASCADE, NOT NULL
├── question_index            INTEGER NOT NULL        -- 0-based index into exercise.questions
├── student_code              TEXT NOT NULL
├── ai_review                 TEXT NOT NULL
├── grade                     FLOAT NOT NULL          -- 0.0–100.0
├── reviewed_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
├── created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints**:
- `UNIQUE(submission_id, question_index)` — one review per question per submission
- `CHECK(grade >= 0 AND grade <= 100)`
- `CHECK(question_index >= 0)`

**Indexes**:
- `idx_question_review_submission_id` on `submission_id`

**Business Rule**: The submit button is enabled only when `COUNT(question_reviews WHERE submission_id=X) = len(exercise.questions)`.

---

### 7. `teacher_notifications` — TeacherNotification

Lightweight notification record created when a student submits an exercise. UI surfaced in F22.

```
teacher_notifications
├── id                        UUID PK
├── teacher_id                UUID FK→users.id ON DELETE SET NULL, NULL
├── student_id                UUID FK→users.id ON DELETE SET NULL, NULL
├── submission_id             UUID FK→class_exercise_submissions.id ON DELETE CASCADE, NOT NULL
├── notification_type         VARCHAR(50) NOT NULL DEFAULT 'exercise_submitted'
├── is_read                   BOOLEAN NOT NULL DEFAULT FALSE
├── created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Indexes**:
- `idx_teacher_notif_teacher_id` on `teacher_id`
- `idx_teacher_notif_is_read` on `is_read`

---

## Entity Relationship Diagram (text)

```
users ──────────────────── classes
  │  (teacher_id FK)          │
  │                           │
  │ (student_id FK)    class_memberships
  │                           │
  │                    class_exercises ──── teacher_generated_exercises
  │                           │                    (created_by_id FK)
  │                    class_exercise_submissions
  │  (student_id FK)          │
  │                    question_reviews
  │
  └─── teacher_notifications (teacher_id, student_id FK)
```

---

## Mastery Impact

F18 exercises are **AI-reviewed** (not auto-graded via test cases). Per the constitution's mastery formula:
- Exercise completion: 40% — F18 submissions DO count as exercise completions
- Code quality ratings: 20% — AI review grade contributes here

Mastery update on submission is **deferred to F19/F20** to keep F18 scope focused. The `overall_score` stored in `class_exercise_submissions` provides the data for future mastery recalculation.

---

## Alembic Migration

**File**: `backend/alembic/versions/20260518_teacher_dashboard.py`  
**Depends on**: `20260518_add_mastery_snapshots` (latest)

Creates all seven tables in dependency order:
1. `classes`
2. `class_memberships`
3. `teacher_generated_exercises`
4. `class_exercises`
5. `class_exercise_submissions`
6. `question_reviews`
7. `teacher_notifications`
