"""Pytest configuration and fixtures for testing."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.models import UserRole
from src.auth.password import hash_password
from src.database import Base, get_db
from src.main import app
from src.models.user import User


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    return "VARCHAR(36)"


# Test database URL (use in-memory SQLite for tests with StaticPool to share across connections)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with StaticPool to share in-memory database across connections
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def setup_test_database():
    """Create tables once for the entire test session.

    Note: This fixture is NOT auto-use. Tests that need database access
    must explicitly request it. This prevents pure unit tests from
    failing due to PostgreSQL-specific types (JSONB, UUID) that SQLite
    cannot create.
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db(setup_test_database) -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.

    Yields:
        Database session for testing
    """
    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Clean up all data after each test
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.

    Args:
        db: Test database session

    Yields:
        FastAPI test client
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """
    Create a test user in the database.

    Args:
        db: Test database session

    Returns:
        Test User object
    """
    user = User(
        email="test@example.com",
        password_hash=hash_password("Test@1234"),
        role=UserRole.STUDENT,
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_teacher(db: Session) -> User:
    """
    Create a test teacher in the database.

    Args:
        db: Test database session

    Returns:
        Test Teacher object
    """
    teacher = User(
        email="teacher@example.com",
        password_hash=hash_password("Teacher@1234"),
        role=UserRole.TEACHER,
        display_name="Test Teacher",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@pytest.fixture
def test_admin(db: Session) -> User:
    """
    Create a test admin in the database.

    Args:
        db: Test database session

    Returns:
        Test Admin object
    """
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("Admin@1234"),
        role=UserRole.ADMIN,
        display_name="Test Admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture(autouse=True)
def cleanup_test_db():
    """
    Cleanup fixture (not needed for in-memory DB with StaticPool).
    """
    yield
