"""FastAPI dependencies for authentication and authorization."""

from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.jwt import verify_token
from src.database import get_async_db
from src.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    token = credentials.credentials

    try:
        payload = verify_token(token, expected_type="access")
        user_id: str = payload.get("sub")
        session_id: Optional[str] = payload.get("session_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if session_id:
        from src.auth.models import Session as SessionModel

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        session_result = await db.execute(
            select(SessionModel).where(SessionModel.id == session_uuid)
        )
        session = session_result.scalar_one_or_none()
        if session and session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user._session_id = session_id

    return user


def require_role(allowed_roles: list[str]):
    """
    Dependency factory to require specific user roles.

    Args:
        allowed_roles: List of allowed role strings (e.g., ['teacher', 'admin'])

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin", dependencies=[Depends(require_role(['admin']))])
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


def require_verified_email(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require verified email for teachers and admins.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if email is verified (or user is student)

    Raises:
        HTTPException: 403 if email is not verified for teacher/admin
    """
    # Students don't require email verification
    if current_user.role == "student":
        return current_user

    # Teachers and admins require email verification
    if current_user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
        )

    return current_user
