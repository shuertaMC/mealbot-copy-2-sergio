"""
Database connection and session management for Mealbot.

This module provides SQLAlchemy async engine, session factory, and
dependency injection for FastAPI routes.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import get_settings

# Declarative base for all ORM models
Base = declarative_base()

# Global engine and session factory (initialized on first import)
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the global SQLAlchemy async engine.

    The engine is configured to use asyncpg as the PostgreSQL driver.
    Connection URLs are automatically converted from postgres:// to postgresql+asyncpg://
    for Heroku compatibility.

    Returns:
        AsyncEngine: The SQLAlchemy async engine instance
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url

        # Convert postgres:// to postgresql+asyncpg:// for Heroku compatibility
        # Heroku uses postgres:// but asyncpg requires postgresql+asyncpg://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        _engine = create_async_engine(
            database_url,
            echo=settings.debug,  # Log SQL queries in debug mode
            pool_size=5,  # Number of connections to maintain in the pool
            max_overflow=10,  # Maximum additional connections beyond pool_size
            pool_pre_ping=True,  # Verify connections before using them
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the global async session factory.

    Returns:
        async_sessionmaker: Factory for creating AsyncSession instances
    """
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False,
        )

    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    This is an async generator that yields an AsyncSession and ensures
    proper cleanup (closing the session) even if an exception occurs.

    Usage in FastAPI route:
        @router.get("/example")
        async def example_route(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass

    Yields:
        AsyncSession: An async database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
