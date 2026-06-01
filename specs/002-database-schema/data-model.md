# Data Model: Database Schema & Migrations

**Feature**: 002-database-schema
**Date**: 2026-03-15
**Phase**: 1 (Design & Contracts)

## Overview

This document defines the complete database schema for LearnPyByAI, including all entities, relationships, constraints, and indexes. The schema extends the existing F01 authentication tables and adds curriculum structure, progress tracking, code submissions, and LLM caching.

---

## Entity Relationship Diagram

```
┌─────────────────┐
│     users       │ (from F01, extended)
│─────────────────│
│ id (PK)         │
│ email           │
│ hashed_password │
│ role            │◄──────────┐
│ preferences     │            │
│ created_at      │            │
│ updated_at      │            │
│ deleted_at      │            │
└─────────────────┘            │
         │                     │
         │ 1:1 (optional)      │
         ▼                     │
┌─────────────────┐            │
│ user_profiles   │            │
│─────────────────│            │
│ id (PK)         │            │
│ user_id (FK)    │            │
│ bio             │            │
│ metadata        │            │
└─────────────────┘            │
                               │
         ┌─────────────────────┤
         │                     │
         │ 1:N                 │ 1:N
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  user_streaks   │   │ user_module_    │
│─────────────────│   │    mastery      │
│ id (PK)         │   │─────────────────│
│ user_id (FK)    │   │ id (PK)         │
│ current_streak  │   │ user_id (FK)    │
│ longest_streak  │   │ module_id (FK)  │◄──┐
│ last_activity   │   │ score           │   │
└─────────────────┘   │ version         │   │
                      │ updated_at      │   │
                      └─────────────────┘   │
                                            │
┌─────────────────┐                         │
│    modules      │                         │
│─────────────────│                         │
│ id (PK)         │─────────────────────────┘
│ title           │
│ description     │
│ order           │
│ deleted_at      │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│    lessons      │
│─────────────────│
│ id (PK)         │◄──────────┐
│ module_id (FK)  │           │
│ title           │           │
│ order           │           │
│ content_ref     │           │
│ deleted_at      │           │
└─────────────────┘           │
         │                    │
         │ 1:N                │
         ▼                    │
┌─────────────────┐           │
│   exercises     │           │
│─────────────────│           │
│ id (PK)         │◄──┐       │
│ lesson_id (FK)  │   │       │
│ title           │   │       │
│ order           │   │       │
│ starter_code    │   │       │
│ content_ref     │   │       │
│ deleted_at      │   │       │
└─────────────────┘   │       │
         │            │       │
         │ 1:N        │       │
         ▼            │       │
┌─────────────────┐   │       │
│ user_exercise_  │   │       │
│    progress     │   │       │
│─────────────────│   │       │
│ id (PK)         │   │       │
│ user_id (FK)    │───┘       │
│ exercise_id (FK)│           │
│ status          │           │
│ score           │           │
│ attempts        │           │
│ completed_at    │           │
└─────────────────┘           │
                              │
┌─────────────────┐           │
│     quizzes     │           │
│─────────────────│           │
│ id (PK)         │◄──┐       │
│ lesson_id (FK)  │───┘       │
│ title           │           │
│ questions       │           │
│ deleted_at      │           │
└─────────────────┘           │
         │                    │
         │ 1:N                │
         ▼                    │
┌─────────────────┐           │
│ user_quiz_      │           │
│   attempts      │           │
│─────────────────│           │
│ id (PK)         │           │
│ user_id (FK)    │───────────┘
│ quiz_id (FK)    │
│ score           │
│ answers         │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│ code_submissions│
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │
│ exercise_id (FK)│
│ code_text       │
│ result          │
│ quality_rating  │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│   llm_cache     │
│─────────────────│
│ cache_key_hash  │ (PK)
│ prompt_text     │
│ response_text   │
│ model           │
│ token_count     │
│ created_at      │
│ last_accessed_at│
│ expires_at      │
└─────────────────┘
```

---

## Entity Definitions

### 1. users (Extended from F01)

**Purpose**: Represents platform users with authentication credentials and role-based access.

**Extensions to F01 Schema**:
- Add `role` column (student/teacher/admin)
- Add `preferences` JSONB column
- Add `deleted_at` timestamp for soft deletes

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique user identifier (from F01) |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address (from F01) |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password (from F01) |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'student' | User role: student, teacher, admin |
| preferences | JSONB | NOT NULL, DEFAULT '{}' | User preferences (theme, notifications, etc.) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp (from F01) |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp (from F01) |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp (NULL = active) |

**Indexes**:
- `idx_users_email` (UNIQUE) - from F01
- `idx_users_role` - for role-based queries
- `idx_users_deleted_at` - for filtering active users
- `idx_users_preferences_gin` (GIN) - for JSONB queries

**Validation Rules**:
- `role` must be one of: 'student', 'teacher', 'admin'
- `email` must be valid email format
- `preferences` must be valid JSON object

**State Transitions**:
- Active (deleted_at IS NULL) → Deleted (deleted_at IS NOT NULL)
- On delete: anonymize email to `deleted_{id}@anonymized.local`

---

### 2. user_profiles

**Purpose**: Optional 1:1 extension of users for role-specific metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique profile identifier |
| user_id | INTEGER | FK(users.id), UNIQUE, NOT NULL | Reference to user |
| bio | TEXT | NULL | User biography (teachers) |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | Role-specific data (grade_level, institution, etc.) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Profile creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_user_profiles_user_id` (UNIQUE)
- `idx_user_profiles_metadata_gin` (GIN)

**Validation Rules**:
- `user_id` must reference existing user
- `metadata` structure validated by application layer based on role

---

### 3. modules

**Purpose**: Represents the 8 Python curriculum modules.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique module identifier |
| title | VARCHAR(100) | NOT NULL | Module title (e.g., "Basics", "Control Flow") |
| description | TEXT | NOT NULL | Module description |
| order | INTEGER | NOT NULL, UNIQUE | Display order (1-8) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Module creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Indexes**:
- `idx_modules_order` (UNIQUE)
- `idx_modules_deleted_at`

**Validation Rules**:
- `order` must be between 1 and 8
- `title` must be unique among active modules

**Initial Data** (8 modules):
1. Basics - Variables, Data Types, Input/Output, Operators, Type Conversion
2. Control Flow - Conditionals, For Loops, While Loops, Break/Continue
3. Data Structures - Lists, Tuples, Dictionaries, Sets
4. Functions - Defining Functions, Parameters, Return Values, Scope
5. OOP - Classes & Objects, Attributes & Methods, Inheritance, Encapsulation
6. Files - Reading/Writing Files, CSV Processing, JSON Handling
7. Errors - Try/Except, Exception Types, Custom Exceptions, Debugging
8. Libraries - Installing Packages, Working with APIs, Virtual Environments

---

### 4. lessons

**Purpose**: Represents learning units within modules.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique lesson identifier |
| module_id | INTEGER | FK(modules.id), NOT NULL | Reference to parent module |
| title | VARCHAR(200) | NOT NULL | Lesson title |
| order | INTEGER | NOT NULL | Display order within module |
| content_ref | VARCHAR(500) | NOT NULL | Path to content file or S3 key |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Lesson creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Indexes**:
- `idx_lessons_module_id`
- `idx_lessons_module_order` (module_id, order) - UNIQUE where deleted_at IS NULL
- `idx_lessons_deleted_at`

**Validation Rules**:
- `module_id` must reference existing module
- `order` must be unique within module (among active lessons)
- `content_ref` format validated by application layer

---

### 5. exercises

**Purpose**: Represents coding challenges within lessons.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique exercise identifier |
| lesson_id | INTEGER | FK(lessons.id), NOT NULL | Reference to parent lesson |
| title | VARCHAR(200) | NOT NULL | Exercise title |
| order | INTEGER | NOT NULL | Display order within lesson |
| starter_code | TEXT | NULL | Initial code template for students |
| content_ref | VARCHAR(500) | NOT NULL | Path to exercise description file |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Exercise creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Indexes**:
- `idx_exercises_lesson_id`
- `idx_exercises_lesson_order` (lesson_id, order) - UNIQUE where deleted_at IS NULL
- `idx_exercises_deleted_at`

**Validation Rules**:
- `lesson_id` must reference existing lesson
- `order` must be unique within lesson (among active exercises)

---

### 6. quizzes

**Purpose**: Represents assessments for lessons or modules.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique quiz identifier |
| lesson_id | INTEGER | FK(lessons.id), NULL | Reference to lesson (NULL = module-level quiz) |
| title | VARCHAR(200) | NOT NULL | Quiz title |
| questions | JSONB | NOT NULL | Quiz questions and expected answers |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Quiz creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Indexes**:
- `idx_quizzes_lesson_id`
- `idx_quizzes_deleted_at`

**Validation Rules**:
- `questions` must be valid JSON array with structure:
  ```json
  [
    {
      "question": "What is a variable?",
      "type": "multiple_choice",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A"
    }
  ]
  ```

---

### 7. user_exercise_progress

**Purpose**: Tracks student progress on exercises.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique progress record identifier |
| user_id | INTEGER | FK(users.id), NOT NULL | Reference to student |
| exercise_id | INTEGER | FK(exercises.id), NOT NULL | Reference to exercise |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'not_started' | Progress status |
| score | FLOAT | NULL | Score (0-100) if completed |
| attempts | INTEGER | NOT NULL, DEFAULT 0 | Number of attempts |
| completed_at | TIMESTAMP | NULL | Completion timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | First attempt timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_user_exercise_progress_user_exercise` (user_id, exercise_id) - UNIQUE
- `idx_user_exercise_progress_user_id`
- `idx_user_exercise_progress_status`

**Validation Rules**:
- `status` must be one of: 'not_started', 'in_progress', 'completed'
- `score` must be between 0 and 100 if not NULL
- `completed_at` must be set when status = 'completed'

**State Transitions**:
- not_started → in_progress (on first attempt)
- in_progress → completed (on successful completion)
- completed → in_progress (if retrying for better score)

---

### 8. user_quiz_attempts

**Purpose**: Tracks student quiz submissions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique attempt identifier |
| user_id | INTEGER | FK(users.id), NOT NULL | Reference to student |
| quiz_id | INTEGER | FK(quizzes.id), NOT NULL | Reference to quiz |
| score | FLOAT | NOT NULL | Score (0-100) |
| answers | JSONB | NOT NULL | Student's answers |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Attempt timestamp |

**Indexes**:
- `idx_user_quiz_attempts_user_id`
- `idx_user_quiz_attempts_quiz_id`
- `idx_user_quiz_attempts_user_created` (user_id, created_at DESC)

**Validation Rules**:
- `score` must be between 0 and 100
- `answers` must be valid JSON array matching quiz questions structure

---

### 9. code_submissions

**Purpose**: Stores all student code attempts with execution results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique submission identifier |
| user_id | INTEGER | FK(users.id), NOT NULL | Reference to student |
| exercise_id | INTEGER | FK(exercises.id), NOT NULL | Reference to exercise |
| code_text | TEXT | NOT NULL | Submitted code |
| result | JSONB | NOT NULL | Execution result (stdout, stderr, time) |
| quality_rating | FLOAT | NULL | Code quality score (0-100) from Code Review Agent |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Submission timestamp |

**Indexes**:
- `idx_code_submissions_user_exercise_created` (user_id, exercise_id, created_at DESC)
- `idx_code_submissions_user_id`
- `idx_code_submissions_created_at`

**Validation Rules**:
- `code_text` must not exceed 50KB
- `result` structure:
  ```json
  {
    "stdout": "output text",
    "stderr": "error text",
    "execution_time_ms": 123,
    "success": true
  }
  ```
- `quality_rating` must be between 0 and 100 if not NULL

---

### 10. user_streaks

**Purpose**: Tracks student learning consistency for mastery calculation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique streak record identifier |
| user_id | INTEGER | FK(users.id), UNIQUE, NOT NULL | Reference to student |
| current_streak | INTEGER | NOT NULL, DEFAULT 0 | Current consecutive days |
| longest_streak | INTEGER | NOT NULL, DEFAULT 0 | Longest streak ever achieved |
| last_activity_date | DATE | NOT NULL | Last activity date (for streak calculation) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_user_streaks_user_id` (UNIQUE)
- `idx_user_streaks_last_activity`

**Validation Rules**:
- `current_streak` >= 0
- `longest_streak` >= `current_streak`
- `last_activity_date` <= today

**Business Logic**:
- Increment `current_streak` if activity today and last_activity_date = yesterday
- Reset `current_streak` to 1 if activity today and last_activity_date < yesterday
- Update `longest_streak` if `current_streak` > `longest_streak`

---

### 11. user_module_mastery

**Purpose**: Stores computed mastery scores for user-module combinations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique mastery record identifier |
| user_id | INTEGER | FK(users.id), NOT NULL | Reference to student |
| module_id | INTEGER | FK(modules.id), NOT NULL | Reference to module |
| score | FLOAT | NOT NULL, DEFAULT 0 | Mastery score (0-100) |
| version | INTEGER | NOT NULL, DEFAULT 1 | Optimistic locking version |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last calculation timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation timestamp |

**Indexes**:
- `idx_user_module_mastery_user_module` (user_id, module_id) - UNIQUE
- `idx_user_module_mastery_user_id`
- `idx_user_module_mastery_updated_at`

**Validation Rules**:
- `score` must be between 0 and 100
- `version` incremented on each update (optimistic locking)

**Calculation Formula** (from constitution):
- Exercise completion: 40%
- Quiz scores: 30%
- Code quality ratings: 20%
- Consistency (streak): 10%

**Mastery Levels**:
- 0-40%: Beginner (Red)
- 41-70%: Learning (Yellow)
- 71-90%: Proficient (Green)
- 91-100%: Mastered (Blue)

---

### 12. llm_cache

**Purpose**: Caches LLM responses to reduce API costs and improve response times.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| cache_key_hash | VARCHAR(64) | PK | SHA-256 hash of normalized prompt + params |
| prompt_text | TEXT | NOT NULL | Original prompt (for debugging) |
| response_text | TEXT | NOT NULL | Cached LLM response |
| model | VARCHAR(100) | NOT NULL | LLM model identifier |
| token_count | INTEGER | NOT NULL | Total tokens (prompt + response) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Cache entry creation timestamp |
| last_accessed_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last cache hit timestamp |
| expires_at | TIMESTAMP | NULL | Expiration timestamp (NULL = indefinite) |

**Indexes**:
- `idx_llm_cache_key` (cache_key_hash) - PRIMARY KEY
- `idx_llm_cache_last_accessed` - for TTL-based purging
- `idx_llm_cache_expires_at` - for expiration queries

**Validation Rules**:
- `cache_key_hash` must be 64-character hex string (SHA-256)
- `response_text` must not exceed 50KB
- `token_count` > 0

**TTL Strategy** (from spec):
- Curriculum content: indefinite (expires_at = NULL)
- Generated exercises: 7-30 days
- Student-specific feedback: no caching
- Purge entries not accessed in 60+ days

---

## Relationships Summary

| Parent | Child | Type | Cascade |
|--------|-------|------|---------|
| users | user_profiles | 1:1 | CASCADE |
| users | user_streaks | 1:1 | CASCADE |
| users | user_module_mastery | 1:N | CASCADE |
| users | user_exercise_progress | 1:N | CASCADE |
| users | user_quiz_attempts | 1:N | CASCADE |
| users | code_submissions | 1:N | CASCADE |
| modules | lessons | 1:N | RESTRICT |
| modules | user_module_mastery | 1:N | RESTRICT |
| lessons | exercises | 1:N | RESTRICT |
| lessons | quizzes | 1:N | RESTRICT |
| exercises | user_exercise_progress | 1:N | RESTRICT |
| exercises | code_submissions | 1:N | RESTRICT |
| quizzes | user_quiz_attempts | 1:N | RESTRICT |

**Cascade Rules**:
- CASCADE: Delete child records when parent is deleted (user data)
- RESTRICT: Prevent deletion if child records exist (curriculum integrity)

---

## Constraints & Invariants

### Database-Level Constraints

1. **Foreign Key Integrity**: All FK relationships enforced at database level
2. **Unique Constraints**:
   - users.email (from F01)
   - user_profiles.user_id
   - user_streaks.user_id
   - (user_id, module_id) on user_module_mastery
   - (user_id, exercise_id) on user_exercise_progress
   - modules.order
   - (module_id, order) on lessons where deleted_at IS NULL
   - (lesson_id, order) on exercises where deleted_at IS NULL
3. **Check Constraints**:
   - users.role IN ('student', 'teacher', 'admin')
   - user_exercise_progress.status IN ('not_started', 'in_progress', 'completed')
   - user_exercise_progress.score BETWEEN 0 AND 100
   - user_quiz_attempts.score BETWEEN 0 AND 100
   - code_submissions.quality_rating BETWEEN 0 AND 100
   - user_module_mastery.score BETWEEN 0 AND 100
   - user_streaks.current_streak >= 0
   - user_streaks.longest_streak >= current_streak

### Application-Level Invariants

1. **Soft Delete Consistency**: Queries must filter `deleted_at IS NULL` by default
2. **Mastery Recalculation**: Trigger recalculation when:
   - Exercise completed
   - Quiz submitted
   - Code quality rating assigned
   - Streak updated
3. **Streak Update Logic**: Update streak on any learning activity (exercise, quiz, code submission)
4. **Cache Key Uniqueness**: SHA-256 collision probability is negligible but handle gracefully
5. **GDPR Compliance**: On user deletion, anonymize email and set deleted_at

---

## Performance Considerations

### Query Patterns & Indexes

1. **Student Dashboard** (most frequent):
   ```sql
   -- Get all mastery scores for a student
   SELECT * FROM user_module_mastery WHERE user_id = ? AND deleted_at IS NULL;
   -- Index: idx_user_module_mastery_user_module
   ```

2. **Exercise History**:
   ```sql
   -- Get recent submissions for an exercise
   SELECT * FROM code_submissions
   WHERE user_id = ? AND exercise_id = ?
   ORDER BY created_at DESC LIMIT 10;
   -- Index: idx_code_submissions_user_exercise_created
   ```

3. **LLM Cache Lookup**:
   ```sql
   -- Check cache before API call
   SELECT response_text FROM llm_cache
   WHERE cache_key_hash = ? AND (expires_at IS NULL OR expires_at > NOW());
   -- Index: PRIMARY KEY on cache_key_hash
   ```

4. **Struggle Detection**:
   ```sql
   -- Find students with 3+ failed attempts
   SELECT user_id, COUNT(*) as failures
   FROM code_submissions
   WHERE exercise_id = ? AND result->>'success' = 'false'
   GROUP BY user_id
   HAVING COUNT(*) >= 3;
   -- Index: idx_code_submissions_user_exercise_created
   ```

### Estimated Row Counts (10K students)

| Table | Estimated Rows | Growth Rate |
|-------|----------------|-------------|
| users | 10,000 | Linear with signups |
| user_profiles | 10,000 | 1:1 with users |
| modules | 8 | Static |
| lessons | 80 | Slow growth |
| exercises | 400 | Slow growth |
| quizzes | 80 | Slow growth |
| user_exercise_progress | 4M | 10K users × 400 exercises |
| user_quiz_attempts | 800K | 10K users × 80 quizzes × avg 1 attempt |
| code_submissions | 10M+ | High volume (multiple attempts per exercise) |
| user_streaks | 10,000 | 1:1 with students |
| user_module_mastery | 80,000 | 10K users × 8 modules |
| llm_cache | 100K+ | Grows with unique prompts |

### Storage Estimates

- **Total DB size**: ~5-10 GB for 10K students with 1 year of data
- **Largest tables**: code_submissions (text-heavy), llm_cache (text-heavy)
- **Backup strategy**: Daily full backups, point-in-time recovery via Neon

---

## Migration Strategy

### Phase 1: Core Schema (F02-001)
- Extend users table with role, preferences, deleted_at
- Create modules, lessons, exercises, quizzes tables
- Create user_profiles, user_streaks tables
- Add indexes for curriculum queries

### Phase 2: Progress Tracking (F02-002)
- Create user_exercise_progress, user_quiz_attempts tables
- Create user_module_mastery table with optimistic locking
- Add composite indexes for progress queries

### Phase 3: Code Submissions (F02-003)
- Create code_submissions table
- Add indexes for submission history queries

### Phase 4: LLM Cache (F02-004)
- Create llm_cache table
- Add indexes for cache lookups and TTL management

### Rollback Strategy
- Each migration has corresponding `downgrade()` function
- Test rollback on staging before production deployment
- Alembic tracks applied migrations in `alembic_version` table

---

## Next Steps

1. Generate `contracts/models.yaml` with SQLAlchemy model specifications
2. Generate `contracts/migrations.yaml` with Alembic migration sequence
3. Create `quickstart.md` with database setup instructions
