"""Database Engine and Session Lifecycle Management.

Configures SQLAlchemy 2 async connection pool with asyncpg.
Provides bounded health check probe for readiness endpoint.
"""

import asyncio
import logging
import time
from typing import AsyncGenerator, Optional, Tuple
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

logger = logging.getLogger("sangram_ai.db")

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Returns or lazily creates the async SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        kwargs = {
            "echo": settings.DEBUG,
            "pool_pre_ping": True,
        }
        is_sqlite = "sqlite" in settings.DATABASE_URL
        if is_sqlite:
            kwargs["connect_args"] = {"timeout": 30.0}
        else:
            kwargs["pool_size"] = settings.DB_POOL_SIZE
            kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
            kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT_SECONDS

        _engine = create_async_engine(settings.DATABASE_URL, **kwargs)

        if is_sqlite:
            @event.listens_for(_engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=30000")
                cursor.close()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Returns or lazily creates the async sessionmaker."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


async def close_db_engine() -> None:
    """Gracefully closes all pooled connections on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        logger.info("Closing database engine and connection pool...")
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> Tuple[bool, Optional[float], Optional[str]]:
    """Performs a bounded PostgreSQL connectivity check (SELECT 1).
    
    Returns:
        (is_healthy, response_time_ms, error_message)
    """
    settings = get_settings()
    timeout = settings.DB_HEALTH_TIMEOUT_SECONDS
    start = time.perf_counter()

    try:
        engine = get_engine()

        async def _ping() -> None:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_ping(), timeout=timeout)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        return True, duration_ms, None
    except asyncio.TimeoutError:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        err = f"Database health check timed out after {timeout}s"
        logger.warning(err)
        return False, duration_ms, err
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        err = f"Database connection error: {exc.__class__.__name__}"
        logger.warning(err)
        return False, duration_ms, err
