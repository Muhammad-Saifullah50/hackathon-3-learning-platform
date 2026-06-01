# Research: Database Schema & Migrations

**Feature**: 002-database-schema
**Date**: 2026-03-15
**Phase**: 0 (Research & Technical Decisions)

## Overview

This document captures all technical research and decisions for implementing the LearnPyByAI database schema. Each section resolves a "NEEDS CLARIFICATION" item from the Technical Context or addresses a key implementation question.

---

## 1. SQLAlchemy 2.0+ Async Patterns

### Decision
Use SQLAlchemy 2.0+ with async/await patterns via `asyncpg` driver and `AsyncSession` for all database operations.

### Rationale
- FastAPI is async-first, so async database operations prevent blocking the event loop
- SQLAlchemy 2.0 has mature async support with `AsyncEngine` and `AsyncSession`
- `asyncpg` is the fastest PostgreSQL driver for Python
- Neon PostgreSQL supports connection pooling natively, reducing overhead

### Alternatives Considered
- **Sync SQLAlchemy with thread pools**: Rejected because it adds complexity and doesn't leverage FastAPI's async nature
- **Raw asyncpg without ORM**: Rejected because we lose type safety, migrations, and relationship management
- **Tortoise ORM**: Rejected because SQLAlchemy has better ecosystem support and Alembic integration

### Implementation Notes
```python
# Engine setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True  # Verify connections before use
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency injection for FastAPI
async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
```

**Key Patterns**:
- Use `async with` for session management
- Set `expire_on_commit=False` to avoid lazy-loading issues after commit
- Enable `pool_pre_ping=True` for Neon's serverless connection handling

---

## 2. Alembic Migration Dependencies

### Decision
Create new migrations with `down_revision` pointing to the latest F01 migration. Use Alembic's revision identifier system to establish dependency chain.

### Rationale
- Alembic's revision system is designed for linear migration chains
- Setting `down_revision` to F01's latest migration ensures proper ordering
- Never modify existing migrations (immutability principle)
- Allows independent development of features while maintaining schema consistency

### Alternatives Considered
- **Branch merging**: Rejected because it adds complexity for linear schema evolution
- **Separate Alembic environments**: Rejected because it fragments schema history
- **Manual SQL scripts**: Rejected because we lose rollback capability and version tracking

### Implementation Notes
```bash
# Find the latest F01 migration revision
alembic history

# Create new migration depending on F01
alembic revision --autogenerate -m "Add curriculum and progress tables" \
  --head <F01_latest_revision_id>
```

**Migration File Structure**:
```python
# alembic/versions/002_add_curriculum_tables.py
revision = '002a'
down_revision = '001z'  # Last F01 migration
branch_labels = None
depends_on = None

def upgrade():
    # Add new tables without modifying existing ones
    pass

def downgrade():
    # Drop only tables created in this migration
    pass
```

**Key Patterns**:
- Use descriptive revision messages
- Test both `upgrade()` and `downgrade()` paths
- Never use `ALTER TABLE` on F01 tables in F02 migrations
- Use `op.execute()` for complex SQL like creating indexes concurrently

---

## 3. Composite Index Strategies

### Decision
Create composite indexes in the following order based on query patterns:

1. `(user_id, module_id)` on `user_module_mastery`
2. `(user_id, exercise_id, created_at DESC)` on `code_submissions`
3. `(user_id, lesson_id)` on `user_exercise_progress`
4. `(cache_key_hash)` unique index on `llm_cache`
5. `(user_id, created_at DESC)` on `user_quiz_attempts`

### Rationale
- PostgreSQL uses leftmost prefix matching for composite indexes
- Most queries filter by `user_id` first (student-centric queries)
- Adding `created_at DESC` enables efficient "latest submission" queries
- Hash indexes for cache lookups provide O(1) lookup time
- Unique constraint on `cache_key_hash` prevents duplicate cache entries

### Alternatives Considered
- **Separate single-column indexes**: Rejected because PostgreSQL can't efficiently combine them for multi-column queries
- **Covering indexes with INCLUDE**: Considered but deferred to optimization phase (adds storage overhead)
- **Partial indexes for soft deletes**: Rejected because filtering `deleted_at IS NULL` is fast enough with full index

### Implementation Notes
```python
# In SQLAlchemy models
class UserModuleMastery(Base):
    __tablename__ = "user_module_mastery"

    __table_args__ = (
        Index('idx_user_module_mastery', 'user_id', 'module_id'),
        Index('idx_mastery_updated', 'updated_at'),
    )

# In Alembic migration for concurrent index creation (production)
def upgrade():
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_user_module_mastery
        ON user_module_mastery (user_id, module_id)
    """)
```

**Key Patterns**:
- Use `CREATE INDEX CONCURRENTLY` in production to avoid table locks
- Name indexes descriptively: `idx_<table>_<columns>`
- Monitor index usage with `pg_stat_user_indexes`
- Add indexes incrementally based on query patterns (don't over-index)

---

## 4. Soft Delete Patterns

### Decision
Implement soft deletes using a `deleted_at` timestamp column with SQLAlchemy query filters and a custom base class.

### Rationale
- Preserves referential integrity (foreign keys remain valid)
- Enables GDPR "right to be forgotten" by anonymizing PII when `deleted_at` is set
- Allows data recovery if deletion was accidental
- Maintains audit trail for compliance

### Alternatives Considered
- **Hard deletes with archive tables**: Rejected because it complicates foreign key relationships
- **Boolean `is_deleted` flag**: Rejected because timestamp provides more information (when deleted)
- **Separate deleted records table**: Rejected because it fragments data and complicates queries

### Implementation Notes
```python
# Base model with soft delete support
class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    @declared_attr
    def __mapper_args__(cls):
        return {
            "polymorphic_on": None,
            "with_polymorphic": "*",
        }

# Custom query class that filters deleted records by default
class SoftDeleteQuery(Query):
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj._with_deleted = False
        return obj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._with_deleted = False

    def with_deleted(self):
        self._with_deleted = True
        return self

    def _filter_deleted(self):
        if not self._with_deleted:
            return self.filter(self._mapper_zero().class_.deleted_at.is_(None))
        return self

# GDPR anonymization
async def anonymize_user_pii(user_id: int, session: AsyncSession):
    user = await session.get(User, user_id)
    user.email = f"deleted_{user_id}@anonymized.local"
    user.deleted_at = datetime.utcnow()
    await session.commit()
```

**Key Patterns**:
- Always filter `deleted_at IS NULL` in queries unless explicitly requesting deleted records
- Anonymize PII fields when setting `deleted_at`
- Use `with_deleted()` method for admin queries that need to see deleted records
- Index `deleted_at` for efficient filtering

---

## 5. JSON Field Usage

### Decision
Use PostgreSQL `JSONB` (not `JSON`) for user preferences with GIN indexes for nested key queries.

### Rationale
- `JSONB` stores data in binary format, enabling efficient indexing and querying
- GIN indexes support containment queries (`@>`, `?`, `?&`, `?|` operators)
- Flexible schema for user preferences without migrations
- Native PostgreSQL support for JSON operations

### Alternatives Considered
- **Separate preferences table with key-value pairs**: Rejected because it requires joins and is harder to query
- **JSON (text-based)**: Rejected because it's slower and doesn't support indexing
- **Serialized Python dict as TEXT**: Rejected because it loses query capability

### Implementation Notes
```python
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = "users"

    preferences = Column(JSONB, nullable=False, default=dict, server_default='{}')

    __table_args__ = (
        # GIN index for containment queries
        Index('idx_user_preferences_gin', 'preferences', postgresql_using='gin'),
    )

# Query examples
# Find users with dark mode enabled
stmt = select(User).where(User.preferences['theme'].astext == 'dark')

# Find users with notification preferences set
stmt = select(User).where(User.preferences.has_key('notifications'))
```

**Key Patterns**:
- Always provide `default=dict` and `server_default='{}'` to avoid NULL issues
- Use GIN indexes for queries on nested keys
- Validate JSONB structure with Pydantic schemas before insertion
- Keep JSONB documents small (<10KB) for performance

---

## 6. Concurrent Update Handling

### Decision
Use SQLAlchemy's optimistic locking with a `version` column and retry logic for concurrent updates.

### Rationale
- Multiple AI agents may update the same user's progress simultaneously
- Optimistic locking prevents lost updates without pessimistic locks
- Retry logic handles transient conflicts gracefully
- Better performance than row-level locks for read-heavy workloads

### Alternatives Considered
- **Pessimistic locking (SELECT FOR UPDATE)**: Rejected because it reduces concurrency and can cause deadlocks
- **Last-write-wins**: Rejected because it can lose progress updates
- **Event sourcing**: Rejected as over-engineering for MVP

### Implementation Notes
```python
class UserModuleMastery(Base):
    __tablename__ = "user_module_mastery"

    version = Column(Integer, nullable=False, default=1, server_default='1')

    __mapper_args__ = {
        "version_id_col": version
    }

# Repository method with retry logic
async def update_mastery_score(
    user_id: int,
    module_id: int,
    new_score: float,
    session: AsyncSession,
    max_retries: int = 3
):
    for attempt in range(max_retries):
        try:
            stmt = select(UserModuleMastery).where(
                UserModuleMastery.user_id == user_id,
                UserModuleMastery.module_id == module_id
            )
            mastery = await session.scalar(stmt)
            mastery.score = new_score
            await session.commit()
            return mastery
        except StaleDataError:
            await session.rollback()
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
```

**Key Patterns**:
- Add `version` column to tables with concurrent updates
- Use `version_id_col` in `__mapper_args__`
- Implement exponential backoff for retries
- Log conflicts for monitoring

---

## 7. LLM Cache Key Generation

### Decision
Generate cache keys using SHA-256 hash of normalized prompt + model + temperature + max_tokens.

### Rationale
- SHA-256 provides collision resistance for cache lookups
- Normalizing prompts (strip whitespace, lowercase) increases cache hit rate
- Including model and parameters ensures cache correctness
- Fixed-length hash enables efficient indexing

### Alternatives Considered
- **MD5 hash**: Rejected due to collision vulnerabilities
- **Full prompt as key**: Rejected because variable-length keys are inefficient for indexing
- **Semantic similarity matching**: Rejected as too complex for MVP (requires embeddings)

### Implementation Notes
```python
import hashlib
import json

def generate_cache_key(
    prompt: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 600
) -> str:
    # Normalize prompt
    normalized_prompt = " ".join(prompt.lower().split())

    # Create stable JSON representation
    cache_input = {
        "prompt": normalized_prompt,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    # Generate SHA-256 hash
    cache_str = json.dumps(cache_input, sort_keys=True)
    return hashlib.sha256(cache_str.encode()).hexdigest()

# SQLAlchemy model
class LLMCache(Base):
    __tablename__ = "llm_cache"

    cache_key_hash = Column(String(64), primary_key=True, index=True)
    prompt_text = Column(Text, nullable=False)  # Store original for debugging
    response_text = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL = indefinite
```

**Key Patterns**:
- Normalize prompts before hashing (whitespace, case)
- Include all parameters that affect response in hash
- Store original prompt for debugging
- Use `cache_key_hash` as primary key for O(1) lookups
- Update `last_accessed_at` on cache hits for TTL management

---

## 8. Database Testing with pytest

### Decision
Use `pytest-asyncio` for async test support and `pytest-postgresql` for test database fixtures with transaction rollback per test.

### Rationale
- `pytest-asyncio` enables testing async repository methods
- `pytest-postgresql` provides isolated test databases
- Transaction rollback ensures test isolation without slow database recreation
- Fixtures enable reusable test data setup

### Alternatives Considered
- **Docker containers per test**: Rejected as too slow (seconds per test)
- **In-memory SQLite**: Rejected because PostgreSQL-specific features (JSONB, indexes) won't work
- **Shared test database**: Rejected because parallel tests would conflict

### Implementation Notes
```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

@pytest.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_learnpybyai",
        poolclass=NullPool,  # Disable pooling for tests
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()

# Test example
@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(email="test@example.com", role="student")
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.created_at is not None
```

**Key Patterns**:
- Use `scope="function"` for test isolation
- Disable connection pooling in tests (`NullPool`)
- Rollback transactions after each test
- Use `pytest.mark.asyncio` for async tests
- Create reusable fixtures for common test data (sample users, modules, etc.)

---

## Summary of Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **ORM** | SQLAlchemy 2.0+ async | FastAPI async compatibility, mature ecosystem |
| **Driver** | asyncpg | Fastest PostgreSQL driver for Python |
| **Migrations** | Alembic with down_revision chain | Immutable migration history, proper dependency tracking |
| **Indexes** | Composite indexes on (user_id, ...) | Optimize student-centric queries |
| **Soft Deletes** | deleted_at timestamp + PII anonymization | GDPR compliance, referential integrity |
| **JSON Storage** | JSONB with GIN indexes | Flexible schema, efficient querying |
| **Concurrency** | Optimistic locking with version column | Prevent lost updates from multiple agents |
| **Cache Keys** | SHA-256 hash of normalized prompt | Collision resistance, efficient indexing |
| **Testing** | pytest-asyncio + pytest-postgresql | Async support, isolated test databases |

---

## Next Steps (Phase 1)

1. Generate `data-model.md` with detailed entity schemas
2. Create `contracts/models.yaml` with SQLAlchemy model specifications
3. Create `contracts/migrations.yaml` with Alembic migration sequence
4. Generate `quickstart.md` with setup instructions
5. Update agent context with new technologies
