"""FastAPI routes for authentication endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from src.auth.dependencies import get_current_user, require_role
from src.auth.schemas import (
    EmailVerificationRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserResponse,
)
from src.auth.service import AuthService
from src.database import get_db
from src.models.user import User

router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    - **email**: Valid email address
    - **password**: At least 8 characters with one non-alphanumeric character
    - **display_name**: User's display name (1-100 characters)
    - **role**: User role (student, teacher, or admin)

    Returns user object and success message.
    """
    service = AuthService(db)

    user, verification_token = await service.register_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        role=request.role,
    )

    user_response = UserResponse.model_validate(user)

    # Build response message
    if verification_token:
        message = (
            "Registration successful! A verification email has been sent to your email address. "
            "Please verify your email before logging in."
        )
    else:
        message = "Registration successful! You can now log in."

    return {
        "user": user_response.model_dump(),
        "message": message,
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    request_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and receive JWT tokens.

    - **email**: User email address
    - **password**: User password

    Returns user object and JWT tokens (access + refresh).
    """
    service = AuthService(db)

    # Extract client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    response = await service.login(
        email=request_data.email,
        password=request_data.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access and refresh tokens (token rotation).
    """
    service = AuthService(db)

    # Extract client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    response = await service.refresh_token(
        refresh_token=request_data.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return response


@router.post("/stateless-token")
async def create_stateless_token(
    current_user: User = Depends(get_current_user),
):
    """
    Create an access token for the Better Auth session storage layer.

    This token is intended to be called once during the login proxy flow so that
    Better Auth can store a FastAPI-compatible JWT alongside its own session.
    The token is RS256-signed and expires in JWT_ACCESS_TOKEN_EXPIRE_MINUTES.
    It must only be invoked from the server-side login proxy, not from client code.
    """
    from src.auth.jwt import create_access_token
    token = create_access_token(current_user.id, current_user.role, current_user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.

    Requires valid JWT access token in Authorization header.

    Returns user profile information.
    """
    return UserResponse.model_validate(current_user)


@router.get("/teacher-only", response_model=MessageResponse)
async def teacher_only_endpoint(
    current_user: User = Depends(require_role(["teacher", "admin"])),
):
    """
    Test endpoint for teacher-only access (teachers and admins allowed).

    Requires valid JWT access token with teacher or admin role.

    Returns success message.
    """
    return MessageResponse(
        message=f"Welcome, {current_user.display_name}! You have teacher/admin access."
    )


@router.get("/admin-only", response_model=MessageResponse)
async def admin_only_endpoint(
    current_user: User = Depends(require_role(["admin"])),
):
    """
    Test endpoint for admin-only access.

    Requires valid JWT access token with admin role.

    Returns success message.
    """
    return MessageResponse(
        message=f"Welcome, {current_user.display_name}! You have admin access."
    )


@router.post("/email-verification/verify", response_model=MessageResponse)
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    """
    Verify user email with verification token.

    - **token**: Email verification token from email

    Returns success message.
    """
    service = AuthService(db)
    user = await service.verify_email(request.token)

    return MessageResponse(message=f"Email verified successfully! You can now log in.")


@router.post("/email-verification/send", response_model=MessageResponse)
async def resend_verification_email(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """
    Resend verification email to user.

    - **email**: User email address

    Returns success message.
    """
    service = AuthService(db)
    await service.resend_verification_email(request.email)

    return MessageResponse(
        message="Verification email sent successfully! Please check your inbox."
    )


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request password reset for user.

    - **email**: User email address

    Returns success message.
    """
    service = AuthService(db)
    await service.request_password_reset(request.email)

    return MessageResponse(
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Confirm password reset with token and new password.

    - **token**: Password reset token from email
    - **new_password**: New password (at least 8 characters with one non-alphanumeric character)

    Returns success message.
    """
    service = AuthService(db)
    await service.confirm_password_reset(request.token, request.new_password)

    return MessageResponse(
        message="Password reset successfully! You can now log in with your new password."
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout from current session.

    Requires valid JWT access token in Authorization header.
    Revokes the current session associated with the token.

    Returns success message.
    """
    from uuid import UUID

    service = AuthService(db)

    # Extract session_id from user object (set by get_current_user dependency)
    session_id = getattr(current_user, "_session_id", None)

    if session_id:
        await service.logout(current_user.id, UUID(session_id))
    else:
        # If no session_id in token (old tokens), revoke all sessions as fallback
        await service.logout_all(current_user.id)

    return MessageResponse(message="Logged out successfully.")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout from all sessions.

    Requires valid JWT access token in Authorization header.
    Revokes all sessions for the current user.

    Returns success message.
    """
    service = AuthService(db)
    await service.logout_all(current_user.id)

    return MessageResponse(message="Logged out from all sessions successfully.")


@router.get("/public-key")
async def get_public_key():
    """
    Get RSA public key for JWT verification.

    This endpoint is used by Kong API Gateway and other services
    to verify JWT tokens signed by this authentication service.

    Returns the public key in PEM format.
    """
    from src.config import settings

    try:
        public_key = settings.get_public_key()
        return {
            "public_key": public_key,
            "algorithm": settings.JWT_ALGORITHM,
            "key_type": "RSA",
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Public key not found: {str(e)}",
        )
