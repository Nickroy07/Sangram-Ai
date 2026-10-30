"""Authentication and User Service Interfaces (Developer 2 Boundary).

Defines the typed protocol Developer 2 must implement for user authentication,
sessions, and profile persistence.
"""

from typing import List, Optional, Protocol, runtime_checkable
from app.schemas.auth import (
    CurrentPrincipal,
    LoginRequest,
    OnboardingRequest,
    RegisterRequest,
    SessionInfo,
    TokenResponse,
    UserPreferences,
    UserProfileResponse,
)


@runtime_checkable
class IAuthService(Protocol):
    """Contract for user identity, JWT issuing, password management, and email verification."""

    async def authenticate(
        self,
        credentials: LoginRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """Validates credentials and returns signed JWT access + refresh tokens.
        
        Raises:
            AuthenticationError: If credentials do not match.
        """
        ...

    async def authenticate_google(
        self,
        credential: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """Verifies Google ID token and returns signed application session tokens.

        Raises:
            AuthenticationError: If token is invalid or verification fails.
        """
        ...

    async def register(self, payload: RegisterRequest) -> UserProfileResponse:
        """Registers a new user account, creates default profile, sends verification code.
        
        Raises:
            ConflictError: If email is already registered.
            ValidationError: If password policy is violated.
        """
        ...

    async def verify_token(self, token: str) -> CurrentPrincipal:
        """Decodes and validates JWT bearer token, returning CurrentPrincipal.
        
        Raises:
            AuthenticationError: If token is expired, invalid, or revoked.
        """
        ...

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Exchanges a valid refresh token for a fresh access token."""
        ...

    async def verify_email(self, user_id: str, code: str) -> bool:
        """Validates a 6-digit confirmation code and marks user as verified."""
        ...

    async def logout(self, session_id: str) -> None:
        """Revokes one session; its access and refresh tokens stop working immediately."""
        ...

    async def resend_verification(self, user_id: str) -> bool:
        """Sends a fresh 6-digit code (cool-down enforced)."""
        ...

    async def change_password(
        self, user_id: str, current_password: str, new_password: str, keep_session_id: Optional[str] = None
    ) -> bool:
        """Changes the password and revokes every other session."""
        ...

    async def request_email_change(self, user_id: str, new_email: str, password: str) -> bool:
        """Sends a code to the NEW address; the email only changes after confirmation.

        Raises:
            ValidationError: Wrong password, or new email equals the current one.
            ConflictError: The new email is already registered.
        """
        ...

    async def confirm_email_change(self, user_id: str, code: str, keep_session_id: Optional[str] = None) -> str:
        """Applies the pending change, marks the email verified, signs out other sessions.
        Returns the new email."""
        ...

    async def list_sessions(self, user_id: str, current_session_id: Optional[str] = None) -> List[SessionInfo]:
        """Lists the user's active sessions."""
        ...

    async def revoke_session(self, user_id: str, session_id: str) -> bool:
        """Revokes one of the user's own sessions.

        Raises:
            NotFoundError: If the session does not exist or belongs to someone else.
        """
        ...

    async def forgot_password(self, email: str) -> bool:
        """Generates a secure password reset token and dispatches reset instructions."""
        ...

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Consumes a reset token and updates the user's password hash."""
        ...


@runtime_checkable
class IUserService(Protocol):
    """Contract for user profile and preference retrieval/mutation."""

    async def get_profile(self, user_id: str) -> UserProfileResponse:
        """Retrieves user profile by ID.
        
        Raises:
            NotFoundError: If user does not exist.
        """
        ...

    async def update_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        occupation: Optional[str] = None,
    ) -> UserProfileResponse:
        """Updates display name, avatar or occupation (role)."""
        ...

    async def get_preferences(self, user_id: str) -> UserPreferences:
        """Retrieves user UI/motion preferences."""
        ...

    async def update_preferences(self, user_id: str, preferences: UserPreferences) -> UserPreferences:
        """Persists updated preferences."""
        ...

    async def complete_onboarding(self, user_id: str, payload: OnboardingRequest) -> UserProfileResponse:
        """Stores onboarding answers and marks onboarding as completed."""
        ...

    async def delete_account(self, user_id: str, password: str) -> bool:
        """Hard-deletes the account after password confirmation; database cascades remove owned data.

        Raises:
            ValidationError: If the password is wrong.
        """
        ...
