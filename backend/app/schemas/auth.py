"""Authentication, Authorization, and User Account Schemas.

Defines the CurrentPrincipal context and user/auth contracts owned by Developer 2.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema


class CurrentPrincipal(BaseSchema):
    """Authenticated caller identity injected into route handlers.
    
    Contains authorization context, role, and subscription tier.
    """

    user_id: str = Field(..., description="Unique immutable user identifier (UUID or stable id)")
    email: EmailStr = Field(..., description="Normalized user email address")
    role: str = Field("user", description="Authorization role: 'user', 'admin', 'moderator'")
    tier: str = Field("free", description="Subscription tier: 'free', 'pro', 'power', 'team'")
    permissions: List[str] = Field(default_factory=list, description="Explicit fine-grained permissions")
    is_authenticated: bool = Field(True, description="Always true for authenticated principal")
    session_id: Optional[str] = Field(None, description="Current login session id (used for logout / revoke-others)")
    is_verified: bool = Field(False, description="True once the email address has been confirmed")


class LoginRequest(BaseSchema):
    """User login credential payload."""

    email: EmailStr = Field(..., description="Registered account email")
    password: str = Field(..., min_length=1, description="Account password")


class RegisterRequest(BaseSchema):
    """User registration payload."""

    name: str = Field(..., min_length=2, max_length=100, description="Full name or display handle")
    email: EmailStr = Field(..., description="Valid contact email")
    password: str = Field(..., min_length=8, max_length=128, description="Secure password")


class TokenResponse(BaseSchema):
    """Token response emitted upon successful login or token refresh."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field("bearer", description="Token scheme identifier")
    expires_in: int = Field(..., description="Access token lifespan in seconds")
    refresh_token: Optional[str] = Field(None, description="Optional refresh token")


class UserPreferences(BaseSchema):
    """User UI preferences (Obsidian theme, reduced motion, etc.)."""

    theme: str = Field("obsidian", description="'obsidian' or 'navy'")
    motion: str = Field("full", description="'full' or 'reduced'")
    default_models: List[str] = Field(default_factory=list, description="Preferred combatant model ids (onboarding)")
    default_archetype: Optional[str] = Field(None, description="Preferred cognitive lens id (onboarding)")


class UserProfileResponse(BaseSchema):
    """User profile data matching frontend mockUser shape."""

    id: str = Field(..., description="User unique identifier")
    name: str = Field(..., description="Display name")
    email: EmailStr = Field(..., description="Primary email")
    role: str = Field(..., description="Account role")
    tier: str = Field(..., description="Current subscription tier")
    avatar: Optional[str] = Field(None, description="Avatar image URL")
    occupation: Optional[str] = Field(None, description="Role chosen during onboarding")
    email_verified: bool = Field(False, description="Whether the email has been confirmed")
    onboarding_completed: bool = Field(False, description="Whether onboarding has been finished")
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerifyEmailRequest(BaseSchema):
    """Email verification payload."""

    code: str = Field(..., min_length=4, max_length=12, description="Verification token/code")


class ForgotPasswordRequest(BaseSchema):
    """Password recovery trigger request."""

    email: EmailStr = Field(..., description="Email address associated with account")


class ResetPasswordRequest(BaseSchema):
    """Password reset completion request."""

    token: str = Field(..., description="One-time password reset token")
    newPassword: str = Field(..., min_length=8, max_length=128, description="New secure password")


class ChangePasswordRequest(BaseSchema):
    """Authenticated password change."""

    currentPassword: str = Field(..., min_length=1, max_length=128)
    newPassword: str = Field(..., min_length=8, max_length=128)


class SessionInfo(BaseSchema):
    """An active login session shown in Settings > Security."""

    id: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_used_at: datetime
    is_current: bool = False


class DeleteAccountRequest(BaseSchema):
    """Account deletion requires re-entering the password."""

    password: str = Field(..., min_length=1, max_length=128)


class OnboardingRequest(BaseSchema):
    """Onboarding answers: role, combatant models, cognitive lens."""

    occupation: Optional[str] = Field(None, max_length=64)
    models: List[str] = Field(default_factory=list, max_length=6)
    archetype: Optional[str] = Field(None, max_length=64)


class ChangeEmailRequest(BaseSchema):
    """Start an email change; requires the current password."""

    newEmail: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ConfirmEmailChangeRequest(BaseSchema):
    """Confirm with the code sent to the new address."""

    code: str = Field(..., min_length=4, max_length=12)


class GoogleLoginRequest(BaseSchema):
    """Google Sign-In credential issued by Google Identity Services."""

    credential: str = Field(..., min_length=10, description="Google ID Token (JWT)")
