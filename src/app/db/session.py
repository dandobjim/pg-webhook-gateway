"""Async SQLAlchemy engine factory and the per-request session dependency."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Build the async engine (and its connection pool) from the settings.

    Args:
        settings: Application settings holding the database URL and pool size.

    Returns:
        A lazily-connecting async engine; no connection is opened until used.
    """
    return create_async_engine(
        str(settings.database_url),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        echo=settings.database_echo,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build the session factory bound to ``engine``.

    Args:
        engine: Engine the sessions will draw connections from.

    Returns:
        A factory producing ``AsyncSession`` objects.
    """
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a session for the duration of one request.

    The factory is created in the app lifespan and stored in ``app.state``.

    Args:
        request: Incoming request, used to reach the application state.

    Yields:
        An ``AsyncSession`` closed automatically after the response.
    """
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.session_factory
    )
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
