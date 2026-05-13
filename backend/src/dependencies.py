"""FastAPI dependencies for database sessions and repositories."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_db
from src.llm.client import LlmClient
from src.llm.service import LlmService
from src.repositories import (
    CacheRepository,
    CurriculumRepository,
    ProgressRepository,
    SubmissionRepository,
    UserProfileRepository,
    UserRepository,
    UserStreakRepository,
)
from src.repositories.agent_session_repository import AgentSessionRepository
from src.repositories.code_session_repository import CodeSessionRepository
from src.repositories.exercise_repository import ExerciseRepository
from src.repositories.mastery_repository import MasteryRepository
from src.repositories.routing_repository import RoutingRepository
from src.services.chat_quota_service import ChatQuotaService
from src.services.code_session_service import CodeSessionService


# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get async database session.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async for session in get_async_db():
        yield session


# Repository dependencies
async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(db)


async def get_user_profile_repository(
    db: AsyncSession = Depends(get_db),
) -> UserProfileRepository:
    """Get UserProfileRepository instance."""
    return UserProfileRepository(db)


async def get_user_streak_repository(
    db: AsyncSession = Depends(get_db),
) -> UserStreakRepository:
    """Get UserStreakRepository instance."""
    return UserStreakRepository(db)


async def get_curriculum_repository(
    db: AsyncSession = Depends(get_db),
) -> CurriculumRepository:
    """Get CurriculumRepository instance."""
    return CurriculumRepository(db)


async def get_progress_repository(
    db: AsyncSession = Depends(get_db),
) -> ProgressRepository:
    """Get ProgressRepository instance."""
    return ProgressRepository(db)


async def get_submission_repository(
    db: AsyncSession = Depends(get_db),
) -> SubmissionRepository:
    """Get SubmissionRepository instance."""
    return SubmissionRepository(db)


async def get_cache_repository(db: AsyncSession = Depends(get_db)) -> CacheRepository:
    """Get CacheRepository instance."""
    return CacheRepository(db)


# LLM service dependency
async def get_llm_service(db: AsyncSession = Depends(get_db)) -> LlmService:
    """
    Get LlmService instance with LiteLLM client and cache repository.

    Args:
        db: Database session for cache repository

    Returns:
        Configured LlmService instance
    """
    client = LlmClient()
    cache_repo = CacheRepository(db)
    return LlmService(client=client, cache_repository=cache_repo)


# Agent repository dependencies
async def get_agent_session_repository(
    db: AsyncSession = Depends(get_db),
) -> AgentSessionRepository:
    """Get AgentSessionRepository instance."""
    return AgentSessionRepository(db)


async def get_routing_repository(
    db: AsyncSession = Depends(get_db),
) -> RoutingRepository:
    """Get RoutingRepository instance."""
    return RoutingRepository(db)


async def get_exercise_repository(
    db: AsyncSession = Depends(get_db),
) -> ExerciseRepository:
    """Get ExerciseRepository instance."""
    return ExerciseRepository(db)


async def get_mastery_repository(
    db: AsyncSession = Depends(get_db),
) -> MasteryRepository:
    """Get MasteryRepository instance."""
    return MasteryRepository(db)


async def get_code_session_repository(
    db: AsyncSession = Depends(get_db),
) -> CodeSessionRepository:
    """Get CodeSessionRepository instance."""
    return CodeSessionRepository(db)


async def get_code_session_service(
    repo: CodeSessionRepository = Depends(get_code_session_repository),
) -> CodeSessionService:
    """Get CodeSessionService instance."""
    return CodeSessionService(repo)


def get_chat_quota_service() -> ChatQuotaService:
    """Get ChatQuotaService instance."""
    return ChatQuotaService()
