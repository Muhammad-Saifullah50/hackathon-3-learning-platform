# Implementation Plan: Database Schema & Migrations

**Branch**: `002-database-schema` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-database-schema/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Design and implement the complete PostgreSQL schema for LearnPyByAI's core data model including users, curriculum structure (8 Python modules with lessons and exercises), student progress tracking, code submissions, quiz attempts, mastery calculations, and LLM response caching. This feature extends the existing F01 authentication schema with role-based user profiles and creates the foundational data layer for all AI tutoring agents to track student learning journeys.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: SQLAlchemy 2.0+, Alembic 1.13+, asyncpg (PostgreSQL async driver), Pydantic 2.0+ (validation)
**Storage**: Neon PostgreSQL 12+ (serverless PostgreSQL with connection pooling)
**Testing**: pytest with pytest-asyncio for async database tests, pytest-postgresql for test database fixtures
**Target Platform**: Linux server (FastAPI backend)
**Project Type**: Web (backend database layer)
**Performance Goals**:
  - Single student mastery query: <200ms (P95)
  - Curriculum structure query (8 modules): <100ms
  - Code submission history (100+ records): <500ms
  - LLM cache lookup: <50ms
  - Concurrent agent updates: support 10+ simultaneous writes without deadlocks
**Constraints**:
  - Must extend F01 schema without modifying existing migrations
  - Soft deletes required for GDPR compliance
  - Composite indexes mandatory for progress queries
  - Foreign key constraints enforced for referential integrity
  - JSON fields for flexible user preferences
**Scale/Scope**:
  - 10,000+ students (MVP target)
  - 8 modules × ~10 lessons × ~5 exercises = ~400 curriculum items
  - 100,000+ LLM cache entries
  - 1M+ code submissions over time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Code Quality Standards
- ✅ **Naming Conventions**: Database columns use `snake_case` per constitution
- ✅ **Documentation**: SQLAlchemy models will have docstrings, Alembic migrations will have descriptive revision messages

### Testing Principles
- ✅ **Coverage Targets**: Database repositories require 85% coverage (constitution mandate)
- ✅ **Test Types**: Integration tests against real test DB using pytest + asyncpg
- ✅ **TDD Approach**: Strict TDD for progress tracking and mastery calculation logic (critical business logic)

### Performance Standards
- ✅ **Latency Budgets**: PostgreSQL queries <40ms (hard limit 150ms) - aligns with constitution
- ✅ **Optimization Rules**: Composite indexes on `user_id`, `lesson_id`, `created_at` from day one (constitution requirement)
- ⚠️ **EXPLAIN ANALYZE**: Must run before any new query goes to production (constitution mandate)

### Security Constraints
- ✅ **Data Handling**: Soft deletes + PII anonymization for GDPR compliance (constitution requirement)
- ✅ **Secrets Management**: Database credentials in `.env` (gitignored), production uses Neon secret manager

### Architecture Patterns
- ✅ **Repository Pattern**: All DB access through repository classes, never raw queries in routes (constitution mandate)
- ✅ **Anti-Patterns Avoided**: No business logic in models, no skipping Alembic migrations (constitution)

### Business Logic Integrity
- ✅ **Mastery Calculation**: Formula encoded in database schema design (40% exercises, 30% quizzes, 20% code quality, 10% streak)
- ✅ **Mastery Levels**: Thresholds will be queryable via database views or application logic
- ✅ **Struggle Detection**: Schema supports tracking error patterns, time-on-task, and failure counts

### Multi-Agent Architecture Standards
- ✅ **Agent Communication**: Schema designed for concurrent agent access with proper locking
- ✅ **Agent Responses**: Progress tracking tables support all 6 agent types (Triage, Concepts, Code Review, Debug, Exercise, Progress)

### Development Workflow
- ✅ **Branching Strategy**: Feature branch `002-database-schema` follows GitHub Flow
- ✅ **Commit Conventions**: Will use `feat:` prefix for schema additions, `chore:` for migration updates

**GATE STATUS**: ✅ PASS - No constitution violations detected. All requirements align with established principles.

## Project Structure

### Documentation (this feature)

```text
specs/002-database-schema/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── models.yaml      # SQLAlchemy model contracts
│   └── migrations.yaml  # Alembic migration sequence
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User, UserProfile (extends F01)
│   │   ├── curriculum.py        # Module, Lesson, Exercise, Quiz
│   │   ├── progress.py          # UserExerciseProgress, UserQuizAttempt, UserStreak, UserModuleMastery
│   │   ├── submission.py        # CodeSubmission
│   │   └── cache.py             # LLMCache
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── curriculum_repository.py
│   │   ├── progress_repository.py
│   │   ├── submission_repository.py
│   │   └── cache_repository.py
│   └── database.py              # SQLAlchemy engine, session factory
├── alembic/
│   ├── versions/
│   │   ├── [F01_migrations]     # Existing from 001-auth
│   │   └── [F02_migrations]     # New migrations for this feature
│   ├── env.py
│   └── alembic.ini
└── tests/
    ├── integration/
    │   ├── test_user_repository.py
    │   ├── test_curriculum_repository.py
    │   ├── test_progress_repository.py
    │   ├── test_submission_repository.py
    │   └── test_cache_repository.py
    └── fixtures/
        └── database.py          # pytest-postgresql fixtures
```

**Structure Decision**: Web application structure (backend focus). This feature implements the database layer only. Frontend integration will be handled in subsequent features. The repository pattern is used per constitution mandate to isolate database access from business logic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected** - All design decisions align with constitution principles.

---

## Phase Summary

### Phase 0: Research (Completed)

**Artifacts Generated**:
- [research.md](research.md) - Technical decisions and best practices

**Key Decisions**:
1. **SQLAlchemy 2.0+ Async**: Use async/await patterns with asyncpg for FastAPI compatibility
2. **Alembic Dependencies**: Chain migrations using down_revision to F01's latest migration
3. **Composite Indexes**: Optimize for student-centric queries (user_id first in all indexes)
4. **Soft Deletes**: Use deleted_at timestamp with PII anonymization for GDPR compliance
5. **JSONB Storage**: Use PostgreSQL JSONB with GIN indexes for flexible user preferences
6. **Optimistic Locking**: Use version column to handle concurrent agent updates
7. **Cache Keys**: SHA-256 hash of normalized prompt + model + parameters
8. **Testing**: pytest-asyncio + pytest-postgresql for async integration tests

### Phase 1: Design & Contracts (Completed)

**Artifacts Generated**:
- [data-model.md](data-model.md) - Complete entity definitions with relationships
- [contracts/models.yaml](contracts/models.yaml) - SQLAlchemy model specifications
- [contracts/migrations.yaml](contracts/migrations.yaml) - Alembic migration sequence
- [quickstart.md](quickstart.md) - Database setup and deployment guide

**Schema Overview**:
- **12 entities**: User (extended), UserProfile, Module, Lesson, Exercise, Quiz, UserExerciseProgress, UserQuizAttempt, UserStreak, UserModuleMastery, CodeSubmission, LLMCache
- **7 migrations**: Extend users, create profiles/streaks, curriculum structure, progress tracking, code submissions, LLM cache, seed data
- **15+ indexes**: Composite indexes optimized for query patterns
- **8 seeded modules**: Basics, Control Flow, Data Structures, Functions, OOP, Files, Errors, Libraries

**Constitution Re-Check**: ✅ PASS - All design decisions comply with constitution principles.

### Agent Context Update (Completed)

Updated [CLAUDE.md](../../CLAUDE.md) with:
- Python 3.11+ (backend language)
- SQLAlchemy 2.0+, Alembic 1.13+, asyncpg, Pydantic 2.0+ (frameworks)
- Neon PostgreSQL 12+ (database)

---

## Next Steps

### Phase 2: Task Generation (Not part of /sp.plan)

Run `/sp.tasks` to generate actionable tasks from this plan. Expected task categories:
1. **Database Setup**: Configure Alembic, create migration files
2. **Model Implementation**: Implement SQLAlchemy models with relationships
3. **Repository Layer**: Create repository classes for each entity
4. **Migration Execution**: Apply migrations and seed data
5. **Testing**: Write integration tests for repositories (85% coverage target)
6. **Documentation**: Update API documentation with database schema

### Implementation Readiness

✅ **Ready for Implementation**:
- All technical unknowns resolved
- Data model fully specified
- Migration sequence defined
- Testing strategy established
- Performance considerations documented

⚠️ **Pending Dependencies**:
- F01 final migration revision ID (placeholder: 001z)
- Neon PostgreSQL connection string (to be provided in .env)
- Curriculum content files (lessons, exercises) - out of scope for F02

---

## Architectural Decisions Detected

The following architecturally significant decisions were made during planning:

1. **Database Schema Design**: Choice of normalized relational schema vs. denormalized for performance
2. **Soft Delete Strategy**: Timestamp-based soft deletes with PII anonymization for GDPR
3. **Optimistic Locking**: Version-based concurrency control for multi-agent updates
4. **LLM Cache Architecture**: SHA-256 key generation with differentiated TTL strategies
5. **Index Strategy**: Composite indexes optimized for student-centric query patterns

📋 **Recommendation**: Document these decisions with ADRs after implementation begins. Run `/sp.adr <decision-title>` for each significant decision above.
