# Quickstart: Database Schema & Migrations

**Feature**: 002-database-schema
**Date**: 2026-03-15
**Audience**: Developers setting up the LearnPyByAI database

## Overview

This guide walks you through setting up the LearnPyByAI PostgreSQL database schema, running migrations, and verifying the installation. The schema includes user management, curriculum structure, progress tracking, code submissions, and LLM caching.

---

## Prerequisites

- Python 3.11+ installed
- PostgreSQL 12+ (or Neon PostgreSQL account)
- F01 (Authentication & Authorization) feature completed
- Git repository cloned locally

---

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Key packages installed**:
- `sqlalchemy[asyncio]>=2.0.0` - ORM with async support
- `alembic>=1.13.0` - Database migrations
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `pydantic>=2.0.0` - Data validation

### 2. Configure Database Connection

Create or update `backend/.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/learnpybyai

# For Neon PostgreSQL (recommended)
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.us-east-2.aws.neon.tech/learnpybyai?sslmode=require

# For local PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/learnpybyai_dev
```

**Security Note**: Never commit `.env` to version control. It's already in `.gitignore`.

### 3. Verify F01 Migrations

Check that F01 authentication migrations are applied:

```bash
cd backend
alembic current
```

**Expected output**:
```
001z (head)  # Or whatever the last F01 migration is
```

If no migrations are applied, run F01 migrations first:
```bash
alembic upgrade head
```

### 4. Run F02 Migrations

Apply all F02 database schema migrations:

```bash
alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Running upgrade 001z -> 002a_extend_users
INFO  [alembic.runtime.migration] Running upgrade 002a -> 002b_user_profiles_streaks
INFO  [alembic.runtime.migration] Running upgrade 002b -> 002c_curriculum_structure
INFO  [alembic.runtime.migration] Running upgrade 002c -> 002d_progress_tracking
INFO  [alembic.runtime.migration] Running upgrade 002d -> 002e_code_submissions
INFO  [alembic.runtime.migration] Running upgrade 002e -> 002f_llm_cache
INFO  [alembic.runtime.migration] Running upgrade 002f -> 002g_seed_curriculum
```

### 5. Verify Schema

Connect to the database and verify tables exist:

```bash
# Using psql
psql $DATABASE_URL -c "\dt"

# Or using Python
python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('postgresql://user:pass@host/db')
inspector = inspect(engine)
print('Tables:', inspector.get_table_names())
"
```

**Expected tables** (17 total):
- `users` (extended from F01)
- `user_profiles`
- `user_streaks`
- `modules`
- `lessons`
- `exercises`
- `quizzes`
- `user_exercise_progress`
- `user_quiz_attempts`
- `user_module_mastery`
- `code_submissions`
- `llm_cache`
- `alembic_version` (Alembic metadata)

### 6. Verify Seed Data

Check that the 8 Python modules were seeded:

```bash
psql $DATABASE_URL -c "SELECT id, title, \"order\" FROM modules ORDER BY \"order\";"
```

**Expected output**:
```
 id |      title       | order
----+------------------+-------
  1 | Basics           |     1
  2 | Control Flow     |     2
  3 | Data Structures  |     3
  4 | Functions        |     4
  5 | OOP              |     5
  6 | Files            |     6
  7 | Errors           |     7
  8 | Libraries        |     8
```

---

## Development Workflow

### Creating New Migrations

When you modify SQLAlchemy models, generate a new migration:

```bash
cd backend
alembic revision --autogenerate -m "Add new field to exercises table"
```

**Review the generated migration** in `backend/alembic/versions/` before applying:
- Check that only intended changes are included
- Verify foreign key constraints
- Add any custom SQL if needed (e.g., data migrations)

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade 002c_curriculum_structure

# Apply one migration at a time
alembic upgrade +1
```

### Rolling Back Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 002b_user_profiles_streaks

# Rollback all F02 migrations (back to F01)
alembic downgrade 001z
```

### Viewing Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

---

## Testing the Schema

### 1. Run Integration Tests

```bash
cd backend
pytest tests/integration/test_*_repository.py -v
```

**Expected output**:
```
tests/integration/test_user_repository.py::test_create_user PASSED
tests/integration/test_curriculum_repository.py::test_get_modules PASSED
tests/integration/test_progress_repository.py::test_update_mastery PASSED
...
```

### 2. Manual Testing with Python

Create a test script `backend/test_schema.py`:

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.models import User, Module, UserModuleMastery

async def test_schema():
    engine = create_async_engine("postgresql+asyncpg://...")
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        # Test 1: Query modules
        from sqlalchemy import select
        stmt = select(Module).order_by(Module.order)
        result = await session.execute(stmt)
        modules = result.scalars().all()
        print(f"✓ Found {len(modules)} modules")

        # Test 2: Create test user
        user = User(email="test@example.com", role="student")
        session.add(user)
        await session.commit()
        print(f"✓ Created user with ID {user.id}")

        # Test 3: Create mastery record
        mastery = UserModuleMastery(
            user_id=user.id,
            module_id=modules[0].id,
            score=75.0
        )
        session.add(mastery)
        await session.commit()
        print(f"✓ Created mastery record with score {mastery.score}")

    await engine.dispose()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_schema())
```

Run the test:
```bash
python backend/test_schema.py
```

---

## Common Issues & Solutions

### Issue 1: "relation already exists" error

**Cause**: Migration was partially applied or run multiple times.

**Solution**:
```bash
# Check current revision
alembic current

# If stuck, manually set revision
alembic stamp head

# Or rollback and reapply
alembic downgrade -1
alembic upgrade +1
```

### Issue 2: Foreign key constraint violation

**Cause**: Trying to delete a module/lesson that has dependent records.

**Solution**:
- Use soft deletes (set `deleted_at` timestamp) instead of hard deletes
- Or cascade delete dependent records first

```python
# Soft delete (recommended)
module.deleted_at = datetime.utcnow()
await session.commit()

# Hard delete (only if no dependencies)
await session.delete(module)
await session.commit()
```

### Issue 3: "asyncpg.exceptions.UndefinedTableError"

**Cause**: Migrations not applied or wrong database URL.

**Solution**:
```bash
# Verify DATABASE_URL is correct
echo $DATABASE_URL

# Apply migrations
alembic upgrade head

# Check tables exist
psql $DATABASE_URL -c "\dt"
```

### Issue 4: Slow queries on progress tables

**Cause**: Missing indexes or large dataset.

**Solution**:
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;

-- Analyze query performance
EXPLAIN ANALYZE
SELECT * FROM user_module_mastery WHERE user_id = 123;
```

If indexes are missing, create them:
```bash
alembic revision -m "Add missing indexes"
# Edit migration file to add indexes
alembic upgrade head
```

### Issue 5: Optimistic locking conflicts

**Cause**: Multiple agents updating the same mastery record simultaneously.

**Solution**: The repository layer handles retries automatically. If conflicts persist:

```python
# Increase retry attempts in repository
async def update_mastery_score(
    user_id: int,
    module_id: int,
    new_score: float,
    session: AsyncSession,
    max_retries: int = 5  # Increase from default 3
):
    # ... retry logic
```

---

## Performance Optimization

### 1. Connection Pooling

Configure connection pool in `backend/src/database.py`:

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Max connections in pool
    max_overflow=10,     # Additional connections if pool exhausted
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

### 2. Query Optimization

Use `EXPLAIN ANALYZE` to identify slow queries:

```sql
EXPLAIN ANALYZE
SELECT u.id, u.email, m.score
FROM users u
JOIN user_module_mastery m ON u.id = m.user_id
WHERE u.role = 'student' AND m.module_id = 1;
```

Look for:
- Sequential scans (should use indexes)
- High execution time (>100ms)
- Large row counts

### 3. Index Maintenance

Periodically analyze tables to update statistics:

```sql
-- Analyze all tables
ANALYZE;

-- Analyze specific table
ANALYZE user_module_mastery;

-- Reindex if needed
REINDEX TABLE user_module_mastery;
```

### 4. Cache Purging

Set up a cron job to purge old LLM cache entries:

```python
# backend/src/tasks/cache_cleanup.py
async def purge_old_cache_entries(session: AsyncSession):
    """Delete cache entries not accessed in 60+ days"""
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from src.models import LLMCache

    cutoff_date = datetime.utcnow() - timedelta(days=60)
    stmt = delete(LLMCache).where(LLMCache.last_accessed_at < cutoff_date)
    result = await session.execute(stmt)
    await session.commit()
    print(f"Purged {result.rowcount} cache entries")
```

Run daily via cron or task scheduler.

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Backup production database
- [ ] Test migrations on staging with production-like data
- [ ] Verify all foreign key constraints
- [ ] Check index creation time on large tables
- [ ] Review migration SQL for any destructive operations
- [ ] Prepare rollback plan

### Deployment Steps

1. **Backup Database**:
   ```bash
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Apply Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Verify Schema**:
   ```bash
   psql $DATABASE_URL -c "\dt"
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM modules;"
   ```

4. **Run Smoke Tests**:
   ```bash
   pytest tests/integration/ -v --maxfail=1
   ```

5. **Monitor Performance**:
   ```sql
   -- Check for long-running queries
   SELECT pid, now() - query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - query_start > interval '5 seconds';
   ```

### Rollback Procedure

If issues occur:

```bash
# Rollback to previous revision
alembic downgrade -1

# Or rollback all F02 migrations
alembic downgrade 001z

# Restore from backup if needed
psql $DATABASE_URL < backup_20260315_062752.sql
```

---

## Next Steps

After completing database setup:

1. **Implement Repository Layer**: Create repository classes in `backend/src/repositories/`
2. **Add Business Logic**: Implement mastery calculation, streak updates, struggle detection
3. **Create API Endpoints**: Build FastAPI routes that use the repositories
4. **Add Validation**: Use Pydantic schemas to validate input/output
5. **Write Tests**: Achieve 85% coverage on repositories (constitution requirement)

---

## Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Neon PostgreSQL Docs](https://neon.tech/docs)

---

## Support

For issues or questions:
- Check `specs/002-database-schema/data-model.md` for entity details
- Review `specs/002-database-schema/research.md` for technical decisions
- Consult `CLAUDE.md` for constitution principles
- Open a GitHub issue with the `database` label
