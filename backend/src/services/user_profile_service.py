"""User profile service - business logic for profile management."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import bcrypt
from sqlalchemy import cast, delete, func, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserProfile
from src.repositories.user_repository import UserProfileRepository, UserRepository
from src.schemas.user_profile import (
    AdminUserListItem,
    AdminUserListResponse,
    PreferencesUpdateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)


class UserProfileService:
    """Service for user profile management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = UserProfileRepository(db)

    async def get_profile(self, user_id: UUID) -> Optional[ProfileResponse]:
        """
        Get user profile with combined User and UserProfile data.

        Args:
            user_id: User ID

        Returns:
            ProfileResponse or None if user not found
        """
        user = await self.user_repo.get_by_id(str(user_id))
        if not user:
            return None

        # Get profile (may not exist)
        profile = await self.profile_repo.get_by_user_id(str(user_id))

        return ProfileResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            bio=profile.bio if profile else None,
            preferences=user.preferences or {},
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def update_profile(
        self, user_id: UUID, update_data: ProfileUpdateRequest
    ) -> ProfileResponse:
        """
        Update user profile with display name and bio.

        Business rules:
        - If display_name is empty/whitespace, fallback to email
        - Bio max length: 500 characters (validated in schema)
        - Create UserProfile if it doesn't exist

        Args:
            user_id: User ID
            update_data: Profile update data

        Returns:
            Updated ProfileResponse

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repo.get_by_id(str(user_id))
        if not user:
            raise ValueError("User not found")

        # Update display_name with fallback to email
        if update_data.display_name is not None:
            display_name = update_data.display_name.strip()
            if not display_name:
                # Fallback to email if empty
                user.display_name = user.email
            else:
                user.display_name = display_name
            user.updated_at = datetime.utcnow()

        # Update bio in UserProfile
        if update_data.bio is not None:
            profile = await self.profile_repo.get_by_user_id(str(user_id))
            if profile:
                profile.bio = update_data.bio
                profile.updated_at = datetime.utcnow()
            else:
                # Create profile if it doesn't exist
                profile = UserProfile(
                    user_id=user.id,
                    bio=update_data.bio,
                    profile_metadata={},
                )
                await self.profile_repo.create(profile)

        await self.db.commit()
        await self.db.refresh(user)

        return await self.get_profile(user_id)

    async def update_preferences(
        self, user_id: UUID, preferences_data: PreferencesUpdateRequest
    ) -> ProfileResponse:
        """
        Update user learning preferences.

        Args:
            user_id: User ID
            preferences_data: Preferences update data

        Returns:
            Updated ProfileResponse

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repo.get_by_id(str(user_id))
        if not user:
            raise ValueError("User not found")

        # Get current preferences
        current_prefs = user.preferences or {}

        # Update only provided fields
        if preferences_data.learning_pace is not None:
            current_prefs["learning_pace"] = preferences_data.learning_pace.value
        if preferences_data.difficulty_level is not None:
            current_prefs["difficulty_level"] = preferences_data.difficulty_level.value
        if preferences_data.theme is not None:
            current_prefs["theme"] = preferences_data.theme.value

        # Update user preferences
        user.preferences = current_prefs
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return await self.get_profile(user_id)

    async def hard_delete_account(self, user_id: UUID, password: str) -> bool:
        """
        Permanently delete user account with password confirmation.

        GDPR compliance: Hard delete removes all user data permanently.
        CASCADE delete configured in models removes all related data:
        - UserProfile
        - UserStreak
        - UserExerciseProgress
        - UserQuizAttempt
        - UserModuleMastery
        - CodeSubmission
        - Sessions

        Args:
            user_id: User ID
            password: Password for confirmation

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If user not found or password incorrect
        """
        user = await self.user_repo.get_by_id(str(user_id))
        if not user:
            raise ValueError("User not found")

        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            raise ValueError("Incorrect password")

        # Hard delete user (CASCADE to all related tables)
        stmt = delete(User).where(User.id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()

        return True

    async def list_users(
        self, page: int = 1, page_size: int = 50, role: Optional[str] = None
    ) -> AdminUserListResponse:
        """
        List all users with pagination and optional role filtering (admin only).

        Args:
            page: Page number (1-indexed)
            page_size: Number of users per page (default: 50)
            role: Optional role filter (student, teacher, admin)

        Returns:
            AdminUserListResponse with paginated user list
        """
        # Build query
        query = select(User).where(User.deleted_at.is_(None))
        if role:
            query = query.where(cast(User.role, String) == role)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).limit(page_size).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()

        # Convert to response items
        user_items = [
            AdminUserListItem(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                email_verified_at=user.email_verified_at,
                created_at=user.created_at,
            )
            for user in users
        ]

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size

        return AdminUserListResponse(
            users=user_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
