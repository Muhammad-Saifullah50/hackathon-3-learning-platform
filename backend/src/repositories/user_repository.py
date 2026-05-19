"""User repository - CRUD operations for User, UserProfile, UserStreak."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import cast, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserProfile, UserStreak


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_role(self, role: str) -> List[User]:
        """Get all users with a specific role."""
        stmt = select(User).where(cast(User.role, String) == role, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_preferences(self, user_id: str, preferences: dict) -> Optional[User]:
        """Update user preferences."""
        user = await self.get_by_id(user_id)
        if user:
            user.preferences = preferences
            user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def soft_delete(self, user_id: str, anonymize: bool = True) -> Optional[User]:
        """
        Soft delete user with optional PII anonymization for GDPR compliance.

        Args:
            user_id: User ID to delete
            anonymize: If True, anonymize email (GDPR requirement)
        """
        user = await self.get_by_id(user_id)
        if user:
            user.deleted_at = datetime.utcnow()
            if anonymize:
                user.email = f"deleted_{user_id}@anonymized.local"
            await self.session.commit()
            await self.session.refresh(user)
        return user


class UserProfileRepository:
    """Repository for UserProfile model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, profile: UserProfile) -> UserProfile:
        """Create a new user profile."""
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update_metadata(self, user_id: str, metadata: dict) -> Optional[UserProfile]:
        """Update user profile metadata."""
        profile = await self.get_by_user_id(user_id)
        if profile:
            profile.profile_metadata = metadata
            profile.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(profile)
        return profile


class UserStreakRepository:
    """Repository for UserStreak model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: str) -> Optional[UserStreak]:
        """Get user streak by user ID."""
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_streak(self, user_id: str, activity_date: datetime.date) -> UserStreak:
        """
        Update user streak based on activity date.

        Business logic:
        - Increment if activity today and last_activity_date = yesterday
        - Reset to 1 if activity today and last_activity_date < yesterday
        - Update longest_streak if current_streak > longest_streak
        """
        from datetime import timedelta

        streak = await self.get_by_user_id(user_id)

        if not streak:
            # Create new streak record
            streak = UserStreak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_activity_date=activity_date
            )
            self.session.add(streak)
        else:
            yesterday = activity_date - timedelta(days=1)

            if streak.last_activity_date == yesterday:
                # Consecutive day - increment streak
                streak.current_streak += 1
            elif streak.last_activity_date < yesterday:
                # Gap in activity - reset streak
                streak.current_streak = 1
            # If same day, don't change streak

            # Update longest streak if needed
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak

            streak.last_activity_date = activity_date
            streak.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(streak)
        return streak
