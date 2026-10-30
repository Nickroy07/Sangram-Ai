"""FastAPI Dependency Injection Providers.

Provides dependencies for:
1. Async database session (get_db_session)
2. Fail-closed authentication (get_current_principal)
3. Module service interfaces (IAuthService, IBattleService, etc.)
"""

import logging
from typing import AsyncGenerator, Optional
from fastapi import Cookie, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppException, AuthenticationError, ModuleNotImplementedError
from app.db.session import get_db
from app.interfaces.auth import IAuthService, IUserService
from app.interfaces.battles import (
    IBattleService,
    IBattleStreamService,
    ISavedAnswerService,
    IShareService,
)
from app.interfaces.billing import IBillingService, IUsageService
from app.interfaces.model_gateway import IModelGatewayService
from app.schemas.auth import CurrentPrincipal
from app.services.auth_service import AuthService
from app.services.email import IEmailSender, build_email_sender
from app.services.user_service import UserService
from app.services.model_gateway import ModelGatewayService
from app.services.battle_service import BattleService
from app.services.saved_service import SavedAnswerService
from app.services.battle_stream_service import BattleStreamService
from app.services.billing_service import BillingService
from app.services.usage_service import UsageService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an active async database session for the request scope."""
    async for session in get_db():
        yield session


def get_email_sender() -> IEmailSender:
    """Email delivery backend (console in dev, SMTP in production)."""
    return build_email_sender()


def get_auth_service(
    db: AsyncSession = Depends(get_db_session),
    email_sender: IEmailSender = Depends(get_email_sender),
) -> IAuthService:
    """Developer 2: authentication & sessions."""
    return AuthService(db, email_sender)


def get_user_service(db: AsyncSession = Depends(get_db_session)) -> IUserService:
    """Developer 2: user profile, preferences, account lifecycle."""
    return UserService(db)


def extract_token(
    authorization: Optional[str],
    session_cookie: Optional[str],
    query_token: Optional[str] = None,
) -> Optional[str]:
    """Bearer header wins; then query parameter; otherwise the HttpOnly session cookie."""
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    if query_token and query_token.strip():
        return query_token.strip()
    return session_cookie or None


async def get_current_principal(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    session_cookie: Optional[str] = Cookie(None, alias="sangram_session"),
    query_token: Optional[str] = Query(None, alias="token"),
    auth_service: IAuthService = Depends(get_auth_service),
) -> CurrentPrincipal:
    """Authenticates caller identity (fails closed).

    Verifies the JWT signature/expiry, then checks that its session row exists, is not
    revoked/expired and that the user is active. Any failure is a 401 AUTH_FAILED.
    Tests inject principals via app.dependency_overrides[get_current_principal].
    """
    token = extract_token(authorization, session_cookie, query_token)
    if not token:
        raise AuthenticationError(
            message="Authentication credentials were not provided. Please log in.",
            details={"required_schemes": ["Bearer <jwt>", "Cookie: sangram_session"]},
        )
    try:
        return await auth_service.verify_token(token)
    except AppException:
        raise
    except Exception:
        logging.getLogger("sangram_ai.auth").exception("Unexpected error while verifying token")
        raise AuthenticationError(message="Authentication could not be verified. Please log in again.")


async def get_optional_principal(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    session_cookie: Optional[str] = Cookie(None, alias="sangram_session"),
    auth_service: IAuthService = Depends(get_auth_service),
) -> Optional[CurrentPrincipal]:
    """Returns authenticated principal if valid, or None for public endpoints."""
    try:
        return await get_current_principal(authorization, session_cookie, auth_service)
    except AuthenticationError:
        return None


# ------------------------------------------------------------------------------
# Module Service Dependencies (Overridden when modules are implemented)
# ------------------------------------------------------------------------------

def get_model_gateway_service() -> IModelGatewayService:
    """Provider gateway; it fails clearly when a selected provider is not configured."""
    return ModelGatewayService()


def get_battle_service(db: AsyncSession = Depends(get_db_session)) -> IBattleService:
    """Persists and orchestrates real provider-backed battles."""
    return BattleService(db)


def get_battle_stream_service() -> IBattleStreamService:
    """Streams persisted battle progress using the contract SSE event vocabulary."""
    return BattleStreamService()


def get_share_service() -> IShareService:
    """Returns IShareService implementation or raises 501."""
    raise ModuleNotImplementedError(module_name="Share Links", owner="Developer 4")


def get_saved_answer_service(db: AsyncSession = Depends(get_db_session)) -> ISavedAnswerService:
    """Returns the database-backed saved-answer library."""
    return SavedAnswerService(db)


def get_billing_service(db: AsyncSession = Depends(get_db_session)) -> IBillingService:
    """Returns the database-backed billing service."""
    return BillingService(db)


def get_usage_service(db: AsyncSession = Depends(get_db_session)) -> IUsageService:
    """Returns the database-backed usage tracking service."""
    return UsageService(db)
