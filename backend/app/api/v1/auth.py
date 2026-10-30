"""Authentication Endpoints (Developer 2).

Registration, login, logout, token refresh, email verification, password reset/change
and session management. Tokens travel in HttpOnly cookies:
  sangram_session  -> short-lived access JWT (path /)
  sangram_refresh  -> rotating refresh token (path /api/auth only)
The refresh token is never returned in a response body.
"""

from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response, status

from app.api.deps import get_auth_service, get_current_principal
from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.interfaces.auth import IAuthService
from app.schemas.auth import (
    ChangeEmailRequest,
    ChangePasswordRequest,
    ConfirmEmailChangeRequest,
    CurrentPrincipal,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionInfo,
    TokenResponse,
    UserProfileResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


def _client_meta(request: Request) -> dict:
    ip = request.client.host if request.client else None
    return {"user_agent": request.headers.get("user-agent"), "ip_address": ip}


def _set_auth_cookies(response: Response, tokens: TokenResponse) -> TokenResponse:
    s = get_settings()
    is_test = s.ENVIRONMENT == "test"
    common = dict(
        httponly=True,
        secure=False if is_test else s.COOKIE_SECURE,
        samesite="lax" if is_test else s.COOKIE_SAMESITE,
        domain=s.COOKIE_DOMAIN,
    )
    response.set_cookie(
        s.ACCESS_COOKIE_NAME, tokens.access_token, max_age=tokens.expires_in, path="/", **common
    )
    if tokens.refresh_token:
        response.set_cookie(
            s.REFRESH_COOKIE_NAME,
            tokens.refresh_token,
            max_age=s.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path=f"{s.API_V1_PREFIX}/auth",
            **common,
        )
    # Never echo the refresh token in the body.
    return tokens.model_copy(update={"refresh_token": None})


def _clear_auth_cookies(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(s.ACCESS_COOKIE_NAME, path="/", domain=s.COOKIE_DOMAIN)
    response.delete_cookie(s.REFRESH_COOKIE_NAME, path=f"{s.API_V1_PREFIX}/auth", domain=s.COOKIE_DOMAIN)


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: IAuthService = Depends(get_auth_service),
) -> UserProfileResponse:
    """Creates the account, emails a 6-digit code, and signs the user in (unverified)
    so the verify-email and onboarding screens can call authenticated endpoints."""
    profile = await auth_service.register(payload)
    tokens = await auth_service.authenticate(
        LoginRequest(email=payload.email, password=payload.password), **_client_meta(request)
    )
    _set_auth_cookies(response, tokens)
    return profile


@router.post("/login", response_model=TokenResponse, summary="User Login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    auth_service: IAuthService = Depends(get_auth_service),
) -> TokenResponse:
    tokens = await auth_service.authenticate(payload, **_client_meta(request))
    return _set_auth_cookies(response, tokens)


@router.post("/google", response_model=TokenResponse, summary="Google Sign-In")
async def google_login(
    payload: GoogleLoginRequest,
    request: Request,
    response: Response,
    auth_service: IAuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Verifies Google Identity Services ID token and establishes application session."""
    tokens = await auth_service.authenticate_google(payload.credential, **_client_meta(request))
    return _set_auth_cookies(response, tokens)


@router.post("/logout", summary="User Logout")
async def logout(
    response: Response,
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    """Revokes this session server-side and clears the cookies."""
    if principal.session_id:
        await auth_service.logout(principal.session_id)
    _clear_auth_cookies(response)
    return {"success": True, "message": "Successfully logged out."}


@router.get("/me", response_model=CurrentPrincipal, summary="Get Current Authenticated Principal")
async def get_me(principal: CurrentPrincipal = Depends(get_current_principal)) -> CurrentPrincipal:
    return principal


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
async def refresh_tokens(
    response: Response,
    x_refresh_token: Optional[str] = Header(None, alias="X-Refresh-Token"),
    refresh_cookie: Optional[str] = Cookie(None, alias="sangram_refresh"),
    auth_service: IAuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Rotates the refresh token (cookie, or X-Refresh-Token header for non-browser clients)."""
    token = refresh_cookie or x_refresh_token
    if not token:
        raise AuthenticationError("No refresh token provided. Please log in.")
    try:
        tokens = await auth_service.refresh_tokens(token)
    except AuthenticationError:
        _clear_auth_cookies(response)
        raise
    return _set_auth_cookies(response, tokens)


@router.post("/verify-email", summary="Verify Email Address")
async def verify_email(
    payload: VerifyEmailRequest,
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    verified = await auth_service.verify_email(user_id=principal.user_id, code=payload.code)
    return {"verified": verified}


@router.post("/resend-verification", summary="Resend Email Verification Code")
async def resend_verification(
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    sent = await auth_service.resend_verification(user_id=principal.user_id)
    return {"success": sent}


@router.post("/forgot-password", summary="Request Password Reset")
async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    sent = await auth_service.forgot_password(email=str(payload.email))
    return {"success": sent, "message": "If an account exists, a reset link has been dispatched."}


@router.post("/reset-password", summary="Confirm Password Reset")
async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    success = await auth_service.reset_password(token=payload.token, new_password=payload.newPassword)
    return {"success": success, "message": "Password has been successfully updated."}


@router.post("/change-password", summary="Change Password (authenticated)")
async def change_password(
    payload: ChangePasswordRequest,
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    """Changes the password and signs out every other device."""
    await auth_service.change_password(
        user_id=principal.user_id,
        current_password=payload.currentPassword,
        new_password=payload.newPassword,
        keep_session_id=principal.session_id,
    )
    return {"success": True, "message": "Password updated. Other sessions were signed out."}


@router.post("/change-email", summary="Start Email Change (code sent to new address)")
async def change_email(
    payload: ChangeEmailRequest,
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    await auth_service.request_email_change(
        user_id=principal.user_id, new_email=str(payload.newEmail), password=payload.password
    )
    return {"success": True, "message": "A confirmation code was sent to the new address."}


@router.post("/confirm-email-change", summary="Confirm Email Change")
async def confirm_email_change(
    payload: ConfirmEmailChangeRequest,
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    """Applies the change, marks the email verified, and signs out other devices."""
    new_email = await auth_service.confirm_email_change(
        user_id=principal.user_id, code=payload.code, keep_session_id=principal.session_id
    )
    return {"success": True, "email": new_email}


@router.get("/sessions", response_model=List[SessionInfo], summary="List Active Sessions")
async def list_sessions(
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> List[SessionInfo]:
    return await auth_service.list_sessions(principal.user_id, principal.session_id)


@router.delete("/sessions/{session_id}", summary="Revoke a Session")
async def revoke_session(
    session_id: str,
    principal: CurrentPrincipal = Depends(get_current_principal),
    auth_service: IAuthService = Depends(get_auth_service),
) -> dict:
    await auth_service.revoke_session(user_id=principal.user_id, session_id=session_id)
    return {"revoked": True}
