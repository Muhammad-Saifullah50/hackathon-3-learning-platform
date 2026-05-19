# Data Model: 019-class-analytics

**Phase**: 1 — Design  
**Date**: 2026-05-19

---

## New Tables

**None.** All analytics are computed from existing tables.

---

## Existing Tables Used

### `users`
| Column | Type | Usage |
|--------|------|-------|
| `id` | UUID | Join key |
| `role` | VARCHAR(20) | Filter `role = 'student'` for total count |
| `display_name` | VARCHAR(100) | Shown in struggling students list |

**Query pattern**: `SELECT COUNT(*) FROM users WHERE role = 'student' AND deleted_at IS NULL`

---

### `user_module_mastery`
| Column | Type | Usage |
|--------|------|-------|
| `user_id` | UUID | Group by (ignored — we aggregate across all students) |
| `module_id` | Integer | JOIN with `modules` |
| `score` | Float | AVG per module; global AVG for summary stat |

**Query pattern — avg mastery summary**:
```sql
SELECT AVG(score) AS avg_mastery
FROM user_module_mastery
```

**Query pattern — per-module breakdown**:
```sql
SELECT m.slug, m.name, COALESCE(AVG(umm.score), 0) AS avg_score
FROM modules m
LEFT JOIN user_module_mastery umm ON umm.module_id = m.id
GROUP BY m.id, m.slug, m.name
ORDER BY m.id
```

Modules with no mastery records return 0 (via COALESCE) — satisfies edge case in US2.

---

### `quiz_sessions`
| Column | Type | Usage |
|--------|------|-------|
| `student_id` | UUID | GROUP BY to get latest quiz per student |
| `status` | VARCHAR(20) | Filter `status = 'completed'` |
| `score` | Float | Filter `score < 50`, show in UI |
| `module_slug` | VARCHAR(50) | Shown as context in UI |
| `topic_label` | VARCHAR(200) | Shown as context in UI |
| `completed_at` | TIMESTAMP | ORDER BY to find most recent |

**Query pattern — struggling students** (most recent completed quiz per student, score < 50):
```sql
WITH latest_quiz AS (
  SELECT DISTINCT ON (student_id)
    student_id,
    score,
    module_slug,
    topic_label,
    completed_at
  FROM quiz_sessions
  WHERE status = 'completed'
    AND score IS NOT NULL
  ORDER BY student_id, completed_at DESC
)
SELECT u.id AS student_id, u.display_name, lq.score, lq.module_slug, lq.topic_label
FROM latest_quiz lq
JOIN users u ON u.id = lq.student_id
WHERE lq.score < 50
ORDER BY lq.score ASC
```

**Query pattern — low quiz count** (for stat card):
```sql
SELECT COUNT(*) FROM (
  SELECT DISTINCT ON (student_id) student_id, score
  FROM quiz_sessions
  WHERE status = 'completed' AND score IS NOT NULL
  ORDER BY student_id, completed_at DESC
) sub
WHERE score < 50
```

---

### `modules` (reference, read-only)
| Column | Type | Usage |
|--------|------|-------|
| `id` | Integer | JOIN key |
| `slug` | VARCHAR | Returned in API response |
| `name` | VARCHAR | Human-readable label for chart |

8 rows, seeded. Never mutated by this feature.

---

## API Response Shape

```
TeacherAnalyticsResponse
├── total_students: int           # COUNT(users WHERE role='student')
├── avg_mastery: float | None     # AVG(user_module_mastery.score), null if no records
├── low_quiz_count: int           # students w/ latest completed quiz score < 50
├── module_mastery: List[ModuleMasteryItem]
│   ├── module_slug: str
│   ├── module_name: str
│   └── avg_score: float          # 0.0 if no records
└── struggling_students: List[StrugglingStudent]
    ├── student_id: str (UUID)
    ├── display_name: str
    ├── score: float
    ├── module_slug: str
    └── topic_label: str
```

---

## Indexes Already Available

| Table | Index | Used By |
|-------|-------|---------|
| `quiz_sessions` | `idx_quiz_sessions_student_id` | DISTINCT ON (student_id) |
| `quiz_sessions` | `idx_quiz_sessions_status` | WHERE status='completed' |
| `quiz_sessions` | `idx_quiz_sessions_created_at` | ORDER BY completed_at |
| `users` | implicit on `role` (index from F02) | WHERE role='student' |

No new indexes required for the expected data volumes (≤100 students per SC-001).

---

## Validation Rules

- `avg_mastery` is `None` (null) when `user_module_mastery` is empty; frontend renders "N/A" or "0%".
- `avg_score` per module is always `float` (COALESCE to 0.0), never null.
- `score` in `StrugglingStudent` is always `< 50` by construction.
- Students with no completed quizzes never appear in `struggling_students`.
