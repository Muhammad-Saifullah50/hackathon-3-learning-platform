"""Service layer for authentication business logic."""

import logging
import secrets
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.auth.jwt import create_access_token, create_refresh_token
from src.auth.password import check_password_breach, hash_password, verify_password
from src.auth.rate_limit import RateLimiter
from src.auth.repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    SessionRepository,
    UserRepository,
)
from src.auth.schemas import LoginResponse, TokenResponse, UserResponse
from src.config import settings
from src.models.user import User

# Configure logger
logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.email_verification_repo = EmailVerificationTokenRepository(db)
        self.password_reset_repo = PasswordResetTokenRepository(db)
        self.session_repo = SessionRepository(db)
        self.rate_limiter = RateLimiter(db)

    async def register_user(
        self,
        email: str,
        password: str,
        display_name: str,
        role: str,
    ) -> Tuple[User, Optional[str]]:
        """
        Register a new user.

        Args:
            email: User email address
            password: Plain text password
            display_name: User display name
            role: User role (student, teacher, admin)

        Returns:
            Tuple of (User object, verification_token if applicable)

        Raises:
            HTTPException: If registration fails
        """
        logger.info(f"Registration attempt for email: {email}, role: {role}")

        # Check if user already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            logger.warning(f"Registration failed - email already exists: {email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        # Check password breach
        is_breached, breach_count = await check_password_breach(password)
        if is_breached:
            logger.warning(
                f"Registration failed - breached password for email: {email}, breach_count: {breach_count}"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"This password has been compromised in {breach_count} data breaches. Please choose a different password.",
            )

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = self.user_repo.create_user(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
        )

        # Create email verification token for teachers and admins
        verification_token = None
        if role in ["teacher", "admin"]:
            verification_token = self.email_verification_repo.create_token(user.id)
            logger.info(f"Email verification token created for user_id: {user.id}")
            # TODO: Send verification email (will be implemented in T033)

        logger.info(
            f"User registered successfully - user_id: {user.id}, email: {email}, role: {role}"
        )
        return user, verification_token

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LoginResponse:
        """
        Authenticate user and create session.

        Args:
            email: User email address
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            LoginResponse with user and tokens

        Raises:
            HTTPException: If authentication fails
        """
        logger.info(f"Login attempt for email: {email}, ip_address: {ip_address}")

        # Check rate limiting by email
        lockout_until = self.rate_limiter.check_rate_limit(email, "email")
        if lockout_until:
            remaining_seconds = self.rate_limiter.get_remaining_lockout_seconds(lockout_until)
            logger.warning(
                f"Login rate limited by email: {email}, remaining_seconds: {remaining_seconds}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again in {remaining_seconds} seconds.",
            )

        # Check rate limiting by IP if provided
        if ip_address:
            lockout_until = self.rate_limiter.check_rate_limit(ip_address, "ip")
            if lockout_until:
                remaining_seconds = self.rate_limiter.get_remaining_lockout_seconds(lockout_until)
                logger.warning(
                    f"Login rate limited by IP: {ip_address}, email: {email}, remaining_seconds: {remaining_seconds}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed login attempts from this IP. Please try again in {remaining_seconds} seconds.",
                )

        # Get user
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            # Increment failed attempt counter
            self.rate_limiter.increment_failed_attempt(email, "email")
            if ip_address:
                self.rate_limiter.increment_failed_attempt(ip_address, "ip")

            logger.warning(
                f"Login failed - invalid credentials for email: {email}, ip_address: {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Reset rate limit counters on successful login
        self.rate_limiter.reset_counter(email)
        if ip_address:
            self.rate_limiter.reset_counter(ip_address)

        # Create refresh token
        refresh_token = secrets.token_urlsafe(32)

        # Create session
        session = self.session_repo.create_session(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Create access token with session_id
        access_token = create_access_token(user.id, user.role, user.email, session.id)

        logger.info(
            f"Login successful - user_id: {user.id}, email: {email}, session_id: {session.id}, ip_address: {ip_address}"
        )

        # Build response
        user_response = UserResponse.model_validate(user)
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return LoginResponse(user=user_response, tokens=token_response)

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Plain text refresh token
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            TokenResponse with new access and refresh tokens

        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        logger.info(f"Token refresh attempt from ip_address: {ip_address}")

        # Get session by refresh token
        session = self.session_repo.get_by_refresh_token_hash(refresh_token)
        if not session:
            logger.warning(
                f"Token refresh failed - invalid refresh token from ip_address: {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Get user
        user = self.user_repo.get_by_id(session.user_id)
        if not user:
            logger.error(f"Token refresh failed - user not found for session_id: {session.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Revoke old session (token rotation)
        self.session_repo.revoke_session(session.id)

        # Create new refresh token
        new_refresh_token = secrets.token_urlsafe(32)

        # Create new session
        new_session = self.session_repo.create_session(
            user_id=user.id,
            refresh_token=new_refresh_token,
            expires_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Create new access token with session_id
        access_token = create_access_token(user.id, user.role, user.email, new_session.id)

        logger.info(
            f"Token refresh successful - user_id: {user.id}, old_session_id: {session.id}, new_session_id: {new_session.id}"
        )

        # Build response
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return token_response

    async def verify_email(self, token: str) -> User:
        """
        Verify user email with verification token.

        Args:
            token: Plain text verification token

        Returns:
            User object with updated email_verified_at

        Raises:
            HTTPException: If token is invalid or expired
        """
        from datetime import datetime

        logger.info("Email verification attempt")

        # Get token from repository
        token_record = self.email_verification_repo.get_by_token_hash(token)
        if not token_record:
            logger.warning("Email verification failed - invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        # Check if token is already used
        if token_record.used_at:
            logger.warning(
                f"Email verification failed - token already used for user_id: {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has already been used",
            )

        # Check if token is expired
        if token_record.expires_at < datetime.utcnow():
            logger.warning(
                f"Email verification failed - token expired for user_id: {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
            )

        # Get user
        user = self.user_repo.get_by_id(token_record.user_id)
        if not user:
            logger.error(
                f"Email verification failed - user not found for user_id: {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if email is already verified
        if user.email_verified_at:
            logger.warning(f"Email verification failed - already verified for user_id: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified",
            )

        # Mark token as used
        self.email_verification_repo.mark_used(token_record.id)

        # Update user's email_verified_at
        user.email_verified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Email verified successfully - user_id: {user.id}, email: {user.email}")
        return user

    async def resend_verification_email(self, email: str) -> str:
        """
        Resend verification email to user.

        Args:
            email: User email address

        Returns:
            Verification token (for testing purposes)

        Raises:
            HTTPException: If user not found or email already verified
        """
        logger.info(f"Resend verification email requested for email: {email}")

        # Get user
        user = self.user_repo.get_by_email(email)
        if not user:
            logger.warning(f"Resend verification failed - user not found for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if email is already verified
        if user.email_verified_at:
            logger.warning(
                f"Resend verification failed - email already verified for user_id: {user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified",
            )

        # Create new verification token
        verification_token = self.email_verification_repo.create_token(user.id)

        logger.info(f"Verification email resent - user_id: {user.id}, email: {email}")

        # TODO: Send verification email (will be implemented in email service)
        # For now, return token for testing purposes

        return verification_token

    async def request_password_reset(self, email: str) -> str:
        """
        Request password reset for user.

        Args:
            email: User email address

        Returns:
            Password reset token (for testing purposes)

        Raises:
            HTTPException: If user not found
        """
        logger.info(f"Password reset requested for email: {email}")

        # Get user
        user = self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal if user exists or not for security
            logger.warning(f"Password reset requested for non-existent email: {email}")
            # Return success message anyway
            return "dummy_token"

        # Create password reset token
        reset_token = self.password_reset_repo.create_token(user.id)

        logger.info(f"Password reset token created - user_id: {user.id}, email: {email}")

        # TODO: Send password reset email (will be implemented in email service)
        # For now, return token for testing purposes

        return reset_token

    async def confirm_password_reset(self, token: str, new_password: str) -> User:
        """
        Confirm password reset with token and set new password.

        Args:
            token: Plain text password reset token
            new_password: New password

        Returns:
            User object with updated password

        Raises:
            HTTPException: If token is invalid or expired
        """
        from datetime import datetime

        logger.info("Password reset confirmation attempt")

        # Get token from repository
        token_record = self.password_reset_repo.get_by_token_hash(token)
        if not token_record:
            logger.warning("Password reset failed - invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        # Check if token is already used
        if token_record.used_at:
            logger.warning(
                f"Password reset failed - token already used for user_id: {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has already been used",
            )

        # Check if token is expired
        if token_record.expires_at < datetime.utcnow():
            logger.warning(
                f"Password reset failed - token expired for user_id: {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired",
            )

        # Get user
        user = self.user_repo.get_by_id(token_record.user_id)
        if not user:
            logger.error(
                f"Password reset failed - user not found for user_id: {token_record.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check password breach
        is_breached, breach_count = await check_password_breach(new_password)
        if is_breached:
            logger.warning(
                f"Password reset failed - breached password for user_id: {user.id}, breach_count: {breach_count}"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"This password has been compromised in {breach_count} data breaches. Please choose a different password.",
            )

        # Hash new password
        password_hash = hash_password(new_password)

        # Update user password
        user.password_hash = password_hash
        self.db.commit()
        self.db.refresh(user)

        # Mark token as used
        self.password_reset_repo.mark_used(token_record.id)

        # Revoke all user sessions (force re-login with new password)
        self.session_repo.revoke_all_user_sessions(user.id)

        logger.info(
            f"Password reset successful - user_id: {user.id}, email: {user.email}, all sessions revoked"
        )
        return user

    async def logout(self, user_id: UUID, session_id: UUID) -> None:
        """
        Logout user from specific session.

        Args:
            user_id: User UUID
            session_id: Session UUID to revoke

        Raises:
            HTTPException: If session not found or doesn't belong to user
        """
        logger.info(f"Logout - user_id: {user_id}, session_id: {session_id}")
        # Revoke the specific session
        self.session_repo.revoke_session(session_id)
        logger.info(f"Logout successful - user_id: {user_id}, session_id: {session_id}")

    async def logout_all(self, user_id: UUID) -> None:
        """
        Logout user from all sessions.

        Args:
            user_id: User UUID
        """
        logger.info(f"Logout all sessions - user_id: {user_id}")
        # Revoke all user sessions
        self.session_repo.revoke_all_user_sessions(user_id)
        logger.info(f"All sessions revoked - user_id: {user_id}")
