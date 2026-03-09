"""
LocalWeb AI — Database Engine & Session Factory
Async SQLAlchemy setup — SQLite for local dev, PostgreSQL for production.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


# ── Async Engine ────────────────────────────────────────────
_engine_kwargs = {
    "echo": settings.DEBUG,
}

# PostgreSQL supports connection pooling; SQLite does not
if settings.DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# ── Session Factory ─────────────────────────────────────────
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ──────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ── Dependency for FastAPI ──────────────────────────────────
async def get_db() -> AsyncSession:
    """Yield an async database session for FastAPI dependency injection."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
