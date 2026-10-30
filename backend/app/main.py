"""Sangram AI Backend — Application Factory and Entrypoint.

Configures lifespan, CORS, middleware, central exception handlers,
and OpenAPI schema generation.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.errors import AppErrorCode, AppException
from app.core.logging import request_id_ctx_var, setup_logging
from app.core.middleware import (
    AccessLoggingMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from app.db.session import close_db_engine

logger = logging.getLogger("sangram_ai.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and graceful resource cleanup."""
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL, use_json=settings.LOG_JSON)
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} "
        f"[env={settings.ENVIRONMENT}, debug={settings.DEBUG}]"
    )

    # Note: External AI model providers, payment gateways, and email services
    # are NEVER contacted at startup to allow zero-dependency booting.

    yield

    logger.info("Initiating graceful backend shutdown...")
    await close_db_engine()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Application factory building the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Sangram AI Backend — Dialectic Multi-Model Arena Platform.\n\n"
            "Provides REST API contracts and Server-Sent Events (SSE) for multi-model "
            "adversarial debates, claim cross-examinations, and synthesis verdicts."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # --------------------------------------------------------------------------
    # Middleware Stack (Execution order is bottom-to-top on request)
    # --------------------------------------------------------------------------

    # 1. CORS Configuration (Explicit origins + FRONTEND_URL)
    allowed_origins = list(settings.ALLOWED_ORIGINS)
    if settings.FRONTEND_URL and settings.FRONTEND_URL not in allowed_origins:
        allowed_origins.append(settings.FRONTEND_URL)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-Refresh-Token",
            "Last-Event-ID",
            "Accept",
        ],
        expose_headers=["X-Request-ID"],
    )

    # 2. Access logging with latency tracking (sanitizes sensitive data)
    app.add_middleware(AccessLoggingMiddleware)

    # 3. Request-ID generation and propagation (X-Request-ID)
    app.add_middleware(RequestIDMiddleware)

    # 4. Security response headers (outermost so every response is covered)
    app.add_middleware(SecurityHeadersMiddleware)

    # --------------------------------------------------------------------------
    # Central Exception Handlers (Standardized error envelope)
    # --------------------------------------------------------------------------

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx_var.get() or "unknown"
        return JSONResponse(
            status_code=exc.status_code,
            headers={"X-Request-ID": req_id},
            content={
                "code": exc.code.value if hasattr(exc.code, "value") else str(exc.code),
                "message": exc.message,
                "retryable": exc.retryable,
                "requestId": req_id,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx_var.get() or "unknown"
        formatted_details = []
        for error in exc.errors():
            formatted_details.append(
                {
                    "loc": [str(loc) for loc in error.get("loc", [])],
                    "msg": error.get("msg", "Invalid value"),
                    "type": error.get("type", "value_error"),
                }
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers={"X-Request-ID": req_id},
            content={
                "code": AppErrorCode.VALIDATION_ERROR.value,
                "message": "The request payload failed structural validation.",
                "retryable": False,
                "requestId": req_id,
                "details": formatted_details,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx_var.get() or "unknown"

        # Map HTTP status code to appropriate AppErrorCode
        code_map = {
            400: AppErrorCode.API_FAILURE,
            401: AppErrorCode.AUTH_FAILED,
            403: AppErrorCode.FORBIDDEN,
            404: AppErrorCode.NOT_FOUND,
            409: AppErrorCode.CONFLICT,
            422: AppErrorCode.VALIDATION_ERROR,
            429: AppErrorCode.RATE_LIMIT,
            501: AppErrorCode.MODULE_NOT_IMPLEMENTED,
            503: AppErrorCode.SERVICE_UNAVAILABLE,
        }
        error_code = code_map.get(exc.status_code, AppErrorCode.INTERNAL_SERVER_ERROR)

        return JSONResponse(
            status_code=exc.status_code,
            headers={"X-Request-ID": req_id},
            content={
                "code": error_code.value,
                "message": str(exc.detail),
                "retryable": exc.status_code in (429, 503),
                "requestId": req_id,
                "details": None,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None) or request_id_ctx_var.get() or "unknown"
        # Log stack trace internally with request ID for investigation
        logger.error(
            f"Unhandled server error on {request.method} {request.url.path} [requestId={req_id}]: {exc}",
            exc_info=exc,
            extra={"request_id": req_id},
        )
        # Never expose internal exceptions or stack traces to clients
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers={"X-Request-ID": req_id},
            content={
                "code": AppErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": "An unexpected error occurred while processing your request. Please try again later.",
                "retryable": True,
                "requestId": req_id,
                "details": None,
            },
        )

    # --------------------------------------------------------------------------
    # Route Registration
    # --------------------------------------------------------------------------
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
