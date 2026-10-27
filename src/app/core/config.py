"""Application settings loaded from environment variables and ``.env``."""

from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the gateway.

    Values are read from environment variables (case-insensitive) and, as a
    fallback, from a ``.env`` file in the working directory.

    Attributes:
        database_url: Async SQLAlchemy URL, e.g.
            ``postgresql+asyncpg://user:pass@localhost:5432/db``.
        database_pool_size: Connections kept open in the pool.
        database_max_overflow: Extra connections allowed above the pool size.
        database_echo: Log every SQL statement emitted by SQLAlchemy.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: PostgresDsn
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings.

    Returns:
        The settings instance, built once per process.
    """
    return Settings()  # type: ignore[call-arg]  # fields come from the env
