"""Alembic migration environment running on async SQLAlchemy with asyncpg."""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set to the declarative Base metadata (pg_webhook_gateway.db) once models exist,
# so `alembic revision --autogenerate` can diff against it.
target_metadata = None


def get_database_url() -> str:
    """Return the database URL from the ``DATABASE_URL`` environment variable.

    Returns:
        The async SQLAlchemy URL, e.g.
        ``postgresql+asyncpg://user:pass@localhost:5432/db``.

    Raises:
        RuntimeError: If ``DATABASE_URL`` is not set.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = (
            "DATABASE_URL is not set. Copy .env.example to .env and run "
            "`uv run --env-file .env alembic ...`."
        )
        raise RuntimeError(msg)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode, emitting SQL to the script output."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations on a synchronous connection proxied by the async engine.

    Args:
        connection: Connection handed over by ``AsyncConnection.run_sync``.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through it."""
    connectable = create_async_engine(get_database_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
