"""Centralized Configuration and Production Validation for Sangram AI.

Loads settings from environment variables or .env file with pydantic-settings.
Enforces strict production security validation.
"""

import json
from functools import lru_cache
from typing import List, Literal, Union
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with strong validation and environment overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Runtime Environment
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False

    # Identity & Routing
    PROJECT_NAME: str = "Sangram AI Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # Server Bindings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security: Secret Key used for session signing and tokens
    SECRET_KEY: str = Field(
        default="dev-insecure-secret-key-change-in-production-min32chars!",
        description="Minimum 32-character secret key for cryptographic signatures.",
    )

    # Authentication & Sessions (Developer 2)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 15
    EMAIL_VERIFICATION_MAX_ATTEMPTS: int = 5
    EMAIL_RESEND_COOLDOWN_SECONDS: int = 60
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    ACCESS_COOKIE_NAME: str = "sangram_session"
    REFRESH_COOKIE_NAME: str = "sangram_refresh"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_DOMAIN: Union[str, None] = None
    FRONTEND_URL: str = "http://localhost:3000"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Email delivery (console = log to stdout in development only)
    EMAIL_BACKEND: Literal["console", "smtp"] = "console"
    EMAIL_FROM: str = "Sangram AI <no-reply@sangram.ai>"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_STARTTLS: bool = True

    # CORS Allowed Origins
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="List of origins permitted to make cross-origin requests.",
    )

    # Database Infrastructure (PostgreSQL with asyncpg driver)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sangram_ai",
        description="SQLAlchemy async connection URL using asyncpg driver.",
    )
    # Provider credentials stay on the server and are never exposed to the browser.
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    XAI_API_KEY: str = ""
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT_SECONDS: float = 3.0
    DB_HEALTH_TIMEOUT_SECONDS: float = 2.0

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Supports comma-separated strings or JSON arrays in environment variables."""
        if isinstance(v, str):
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Ensures that dangerous development defaults are strictly rejected in production."""
        if self.ENVIRONMENT == "production":
            # 1. Debug mode must not be enabled in production
            if self.DEBUG:
                raise ValueError("DEBUG mode must be set to False in production environments.")

            # 2. Secret key must be high-entropy and not the development placeholder
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters long in production.")
            if "insecure" in self.SECRET_KEY.lower() or "dev-" in self.SECRET_KEY.lower():
                raise ValueError(
                    "SECRET_KEY cannot be a development placeholder or contain 'insecure'/'dev-' in production."
                )

            # 3. CORS origins must not be wildcard in production
            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError("Wildcard '*' in ALLOWED_ORIGINS is prohibited in production.")
            if not self.ALLOWED_ORIGINS:
                raise ValueError("At least one explicit origin must be configured in ALLOWED_ORIGINS in production.")

            # 4. Database URL cannot be the unconfigured localhost default
            if "postgres:postgres@localhost" in self.DATABASE_URL:
                raise ValueError(
                    "DATABASE_URL cannot use the default 'postgres:postgres@localhost' credentials in production."
                )

            # 5. Auth cookies must be Secure and email must not go to the console
            if not self.COOKIE_SECURE:
                raise ValueError("COOKIE_SECURE must be true in production.")
            if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
                raise ValueError("SameSite=None requires COOKIE_SECURE=true.")
            if self.EMAIL_BACKEND == "console":
                raise ValueError("EMAIL_BACKEND=console is not allowed in production; configure smtp.")

        return self


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton provider."""
    return Settings()
