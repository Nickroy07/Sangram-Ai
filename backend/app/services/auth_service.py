"""Authentication service (Developer 2) implementing IAuthService.

Security rules enforced here:
- every lookup that returns user data is keyed by the authenticated user id;
- secrets (refresh token, email code, reset token) are stored only as keyed digests;
- login/forgot-password responses do not reveal whether an email exists;
- password change/reset revokes sessions; logout revokes the session server-side.
"""

import hmac
import logging
from datetime import timedelta
from typing import List, Optional

import httpx
import jwt
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import get_settings
from app.core.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.db.auth_models import EmailChange, EmailVerification, PasswordReset, UserSession
from app.proposals.entities import Profile, User
from app.schemas.auth import (
    CurrentPrincipal,
    LoginRequest,
    RegisterRequest,
    SessionInfo,
    TokenResponse,
    UserProfileResponse,
)
from app.services.common import aware, build_profile, get_tier, normalize_email, utcnow
from app.services.email import IEmailSender

logger = logging.getLogger("sangram_ai.auth")

_BAD_LOGIN = "Incorrect email or password."


def validate_password_policy(password: str, email: str, name: str = "") -> None:
    """Length is enforced by the schemas; this adds the content rules."""
    lowered = password.lower()
    problems = []
    if lowered == email.lower() or (name and lowered == name.strip().lower()):
        problems.append("Password must not match your email or name.")
    if password.isdigit():
        problems.append("Password must not be only digits.")
    if len(set(password)) < 4:
        problems.append("Password is too repetitive.")
    if problems:
        raise ValidationError("Password does not meet the policy.", details=problems)


class AuthService:
    def __init__(self, db: AsyncSession, email_sender: IEmailSender) -> None:
        self.db = db
        self.email = email_sender
        self.settings = get_settings()

    # ------------------------------------------------------------------ helpers
    async def _issue_session(
        self, user: User, user_agent: Optional[str], ip_address: Optional[str]
    ) -> TokenResponse:
        s = self.settings
        refresh = security.new_opaque_token()
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=security.digest(refresh, "refresh"),
            user_agent=(user_agent or "")[:512] or None,
            ip_address=(ip_address or "")[:64] or None,
            expires_at=utcnow() + timedelta(days=s.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(session)
        await self.db.flush()  # populates session.id
        access = security.create_access_token(user.id, session.id)
        await self.db.commit()
        return TokenResponse(
            access_token=access,
            token_type="bearer",
            expires_in=s.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh,
        )

    async def _revoke_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> None:
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        if except_session_id:
            stmt = stmt.where(UserSession.id != except_session_id)
        await self.db.execute(stmt)

    async def _send_verification_code(self, user: User) -> None:
        s = self.settings
        # Invalidate older unused codes so only the newest works.
        await self.db.execute(
            update(EmailVerification)
            .where(EmailVerification.user_id == user.id, EmailVerification.used_at.is_(None))
            .values(used_at=utcnow())
        )
        code = security.new_numeric_code(6)
        self.db.add(
            EmailVerification(
                user_id=user.id,
                code_hash=security.digest(f"{user.id}:{code}", "email-code"),
                expires_at=utcnow() + timedelta(minutes=s.EMAIL_VERIFICATION_EXPIRE_MINUTES),
            )
        )
        await self.db.commit()
        await self.email.send(
            user.email,
            "Your Sangram AI verification code",
            f"Your verification code is {code}. It expires in {s.EMAIL_VERIFICATION_EXPIRE_MINUTES} minutes.\n"
            "If you did not create an account, ignore this email.",
        )

    # --------------------------------------------------------------- IAuthService
    async def register(self, payload: RegisterRequest) -> UserProfileResponse:
        email = normalize_email(str(payload.email))
        name = payload.name.strip()
        validate_password_policy(payload.password, email, name)
        if (await self.db.execute(select(User.id).where(User.email == email))).first():
            raise ConflictError("An account with this email already exists.")
        user = User(email=email, password_hash=security.hash_password(payload.password))
        profile = Profile(user_id="", name=name)
        self.db.add(user)
        try:
            await self.db.flush()
            profile.user_id = user.id
            self.db.add(profile)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("An account with this email already exists.")
        await self._send_verification_code(user)
        return build_profile(user, profile, "free")

    async def authenticate(
        self,
        credentials: LoginRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        email = normalize_email(str(credentials.email))
        user = (await self.db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            security.burn_password_check(credentials.password)
            raise AuthenticationError(_BAD_LOGIN)
        if not security.verify_password(credentials.password, user.password_hash):
            raise AuthenticationError(_BAD_LOGIN)
        if not user.is_active:
            raise AuthenticationError("This account is disabled.")
        if security.needs_rehash(user.password_hash):
            user.password_hash = security.hash_password(credentials.password)
        return await self._issue_session(user, user_agent, ip_address)

    async def authenticate_google(
        self,
        credential: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """Verifies Google ID Token via Google's tokeninfo endpoint, creates or resolves user account, and issues session."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": credential.strip()},
                )
                if res.status_code != 200:
                    logger.warning(f"Google tokeninfo validation failed with status {res.status_code}: {res.text}")
                    raise AuthenticationError("Google authentication failed. Invalid or expired token.")
                data = res.json()
        except httpx.RequestError as exc:
            logger.error(f"Network error contacting Google OAuth tokeninfo: {exc}")
            raise AuthenticationError("Could not reach Google authentication services. Please try again.")

        # Validate issuer
        iss = data.get("iss", "")
        if iss not in ("accounts.google.com", "https://accounts.google.com"):
            logger.warning(f"Invalid Google token issuer: {iss}")
            raise AuthenticationError("Invalid Google credential issuer.")

        # Validate audience if GOOGLE_CLIENT_ID is configured and aud is present
        client_id = self.settings.GOOGLE_CLIENT_ID
        if client_id and data.get("aud") and data.get("aud") != client_id:
            logger.warning(f"Google token audience mismatch: {data.get('aud')} != {client_id}")
            raise AuthenticationError("Google credential was not issued for this application.")

        raw_email = data.get("email")
        if not raw_email:
            raise AuthenticationError("Google account does not contain a verified email address.")
        email = normalize_email(raw_email)

        # Lookup or create user
        user = (await self.db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            # Create user and profile
            user = User(
                email=email,
                password_hash=security.hash_password(security.new_opaque_token()),
                role="user",
                is_active=True,
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()

            name = data.get("name") or data.get("given_name") or email.split("@")[0]
            profile = Profile(
                user_id=user.id,
                name=name[:100],
                avatar_url=data.get("picture"),
            )
            self.db.add(profile)
            await self.db.commit()
        else:
            if not user.is_active:
                raise AuthenticationError("This account is disabled.")
            if not user.is_verified:
                user.is_verified = True
                await self.db.commit()

        return await self._issue_session(user, user_agent, ip_address)

    async def verify_token(self, token: str) -> CurrentPrincipal:
        try:
            claims = security.decode_access_token(token)
        except jwt.PyJWTError:
            raise AuthenticationError("Your session is invalid or has expired. Please log in again.")
        row = (
            await self.db.execute(
                select(UserSession, User)
                .join(User, User.id == UserSession.user_id)
                .where(UserSession.id == claims["sid"], UserSession.user_id == claims["sub"])
            )
        ).first()
        if row is None:
            raise AuthenticationError("Your session is invalid or has expired. Please log in again.")
        session, user = row
        if session.revoked_at is not None or aware(session.expires_at) <= utcnow() or not user.is_active:
            raise AuthenticationError("Your session is invalid or has expired. Please log in again.")
        return CurrentPrincipal(
            user_id=user.id,
            email=user.email,
            role=user.role,
            tier=await get_tier(self.db, user.id),
            permissions=[],
            session_id=session.id,
            is_verified=user.is_verified,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        digest = security.digest(refresh_token, "refresh")
        session = (
            await self.db.execute(select(UserSession).where(UserSession.refresh_token_hash == digest))
        ).scalar_one_or_none()
        if session is None or session.revoked_at is not None or aware(session.expires_at) <= utcnow():
            raise AuthenticationError("Refresh token is invalid or expired. Please log in again.")
        user = (await self.db.execute(select(User).where(User.id == session.user_id))).scalar_one_or_none()
        if user is None or not user.is_active:
            raise AuthenticationError("Refresh token is invalid or expired. Please log in again.")
        # Rotate: the old refresh token stops working as soon as this commits.
        new_refresh = security.new_opaque_token()
        session.refresh_token_hash = security.digest(new_refresh, "refresh")
        session.last_used_at = utcnow()
        session.expires_at = utcnow() + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        access = security.create_access_token(user.id, session.id)
        await self.db.commit()
        return TokenResponse(
            access_token=access,
            token_type="bearer",
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_refresh,
        )

    async def logout(self, session_id: str) -> None:
        await self.db.execute(
            update(UserSession)
            .where(UserSession.id == session_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        await self.db.commit()

    async def verify_email(self, user_id: str, code: str) -> bool:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found.")
        if user.is_verified:
            return True
        record = (
            await self.db.execute(
                select(EmailVerification)
                .where(EmailVerification.user_id == user_id, EmailVerification.used_at.is_(None))
                .order_by(EmailVerification.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if record is None or aware(record.expires_at) <= utcnow():
            raise ValidationError("This code has expired. Request a new one.")
        if record.attempts >= self.settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
            raise ValidationError("Too many incorrect attempts. Request a new code.")
        expected = security.digest(f"{user_id}:{code.strip()}", "email-code")
        if not hmac.compare_digest(expected, record.code_hash):
            record.attempts += 1
            await self.db.commit()  # persist the attempt before raising
            raise ValidationError("Incorrect verification code.")
        record.used_at = utcnow()
        user.is_verified = True
        await self.db.commit()
        return True

    async def resend_verification(self, user_id: str) -> bool:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found.")
        if user.is_verified:
            return True
        latest = (
            await self.db.execute(
                select(EmailVerification.created_at)
                .where(EmailVerification.user_id == user_id)
                .order_by(EmailVerification.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        cooldown = timedelta(seconds=self.settings.EMAIL_RESEND_COOLDOWN_SECONDS)
        if latest is not None and utcnow() - aware(latest) < cooldown:
            raise RateLimitError("Please wait a minute before requesting another code.")
        await self._send_verification_code(user)
        return True

    async def change_password(
        self, user_id: str, current_password: str, new_password: str, keep_session_id: Optional[str] = None
    ) -> bool:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found.")
        if not security.verify_password(current_password, user.password_hash):
            # 422, not 401: a 401 would make the frontend treat the session as expired.
            raise ValidationError("Current password is incorrect.", details=[{"loc": ["currentPassword"]}])
        validate_password_policy(new_password, user.email)
        user.password_hash = security.hash_password(new_password)
        await self._revoke_sessions(user_id, except_session_id=keep_session_id)
        await self.db.commit()
        return True

    async def request_email_change(self, user_id: str, new_email: str, password: str) -> bool:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found.")
        if not security.verify_password(password, user.password_hash):
            raise ValidationError("Password is incorrect.", details=[{"loc": ["password"]}])
        new_email = normalize_email(new_email)
        if new_email == user.email:
            raise ValidationError("This is already your email address.")
        if (await self.db.execute(select(User.id).where(User.email == new_email))).first():
            raise ConflictError("An account with this email already exists.")
        latest = (
            await self.db.execute(
                select(EmailChange.created_at)
                .where(EmailChange.user_id == user_id)
                .order_by(EmailChange.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        cooldown = timedelta(seconds=self.settings.EMAIL_RESEND_COOLDOWN_SECONDS)
        if latest is not None and utcnow() - aware(latest) < cooldown:
            raise RateLimitError("Please wait a minute before requesting another code.")
        await self.db.execute(
            update(EmailChange)
            .where(EmailChange.user_id == user_id, EmailChange.used_at.is_(None))
            .values(used_at=utcnow())
        )
        code = security.new_numeric_code(6)
        self.db.add(
            EmailChange(
                user_id=user_id,
                new_email=new_email,
                code_hash=security.digest(f"{user_id}:{new_email}:{code}", "email-change"),
                expires_at=utcnow() + timedelta(minutes=self.settings.EMAIL_VERIFICATION_EXPIRE_MINUTES),
            )
        )
        await self.db.commit()
        await self.email.send(
            new_email,
            "Confirm your new Sangram AI email",
            f"Your confirmation code is {code}. It expires in "
            f"{self.settings.EMAIL_VERIFICATION_EXPIRE_MINUTES} minutes.\n"
            "If you did not request this, ignore this email.",
        )
        return True

    async def confirm_email_change(self, user_id: str, code: str, keep_session_id: Optional[str] = None) -> str:
        record = (
            await self.db.execute(
                select(EmailChange)
                .where(EmailChange.user_id == user_id, EmailChange.used_at.is_(None))
                .order_by(EmailChange.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if record is None or aware(record.expires_at) <= utcnow():
            raise ValidationError("This code has expired. Start the email change again.")
        if record.attempts >= self.settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
            raise ValidationError("Too many incorrect attempts. Start the email change again.")
        expected = security.digest(f"{user_id}:{record.new_email}:{code.strip()}", "email-change")
        if not hmac.compare_digest(expected, record.code_hash):
            record.attempts += 1
            await self.db.commit()  # persist the attempt before raising
            raise ValidationError("Incorrect confirmation code.")
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one()
        if (await self.db.execute(select(User.id).where(User.email == record.new_email))).first():
            raise ConflictError("An account with this email already exists.")
        old_email = user.email
        user.email = record.new_email
        user.is_verified = True  # the code proved ownership of the new address
        record.used_at = utcnow()
        await self._revoke_sessions(user_id, except_session_id=keep_session_id)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("An account with this email already exists.")
        await self.email.send(
            old_email,
            "Your Sangram AI email was changed",
            f"The email on your account was changed to {user.email}. "
            "If this wasn't you, reset your password immediately.",
        )
        return user.email

    async def list_sessions(self, user_id: str, current_session_id: Optional[str] = None) -> List[SessionInfo]:
        rows = (
            await self.db.execute(
                select(UserSession)
                .where(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > utcnow(),
                )
                .order_by(UserSession.last_used_at.desc())
            )
        ).scalars()
        return [
            SessionInfo(
                id=r.id,
                user_agent=r.user_agent,
                ip_address=r.ip_address,
                created_at=aware(r.created_at),
                last_used_at=aware(r.last_used_at),
                is_current=(r.id == current_session_id),
            )
            for r in rows
        ]

    async def revoke_session(self, user_id: str, session_id: str) -> bool:
        result = await self.db.execute(
            update(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,  # ownership check: others' sessions look nonexistent
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
        await self.db.commit()
        if result.rowcount == 0:
            raise NotFoundError("Session not found.")
        return True

    async def forgot_password(self, email: str) -> bool:
        user = (
            await self.db.execute(select(User).where(User.email == normalize_email(email)))
        ).scalar_one_or_none()
        if user is not None and user.is_active:
            await self.db.execute(
                update(PasswordReset)
                .where(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None))
                .values(used_at=utcnow())
            )
            token = security.new_opaque_token()
            self.db.add(
                PasswordReset(
                    user_id=user.id,
                    token_hash=security.digest(token, "password-reset"),
                    expires_at=utcnow() + timedelta(minutes=self.settings.PASSWORD_RESET_EXPIRE_MINUTES),
                )
            )
            await self.db.commit()
            link = f"{self.settings.FRONTEND_URL.rstrip('/')}/auth/reset-password?token={token}"
            await self.email.send(
                user.email,
                "Reset your Sangram AI password",
                f"Use this link to choose a new password (valid {self.settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes):\n"
                f"{link}\nIf you did not request this, ignore this email.",
            )
        return True  # identical response whether or not the account exists

    async def reset_password(self, token: str, new_password: str) -> bool:
        record = (
            await self.db.execute(
                select(PasswordReset).where(PasswordReset.token_hash == security.digest(token, "password-reset"))
            )
        ).scalar_one_or_none()
        if record is None or record.used_at is not None or aware(record.expires_at) <= utcnow():
            raise ValidationError("This reset link is invalid or has expired.")
        user = (await self.db.execute(select(User).where(User.id == record.user_id))).scalar_one()
        validate_password_policy(new_password, user.email)
        user.password_hash = security.hash_password(new_password)
        record.used_at = utcnow()
        await self._revoke_sessions(user.id)
        await self.db.commit()
        return True
