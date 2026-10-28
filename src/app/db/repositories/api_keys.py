"""Queries over the ``api_keys`` table."""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SELECT_ACTIVE_BY_PREFIX = text(
    """
    SELECT k.id, k.tenant_id, k.scopes, k.key_hash
    FROM api_keys AS k
    JOIN tenants AS t ON t.id = k.tenant_id
    WHERE k.prefix = :prefix
      AND k.revoked_at IS NULL
      AND (k.expires_at IS NULL OR k.expires_at > now())
      AND t.status = 'active'
    """
)


@dataclass(frozen=True, slots=True)
class ApiKey:
    """An API key that is usable right now.

    Attributes:
        id: Primary key of the ``api_keys`` row.
        tenant_id: Tenant the key belongs to.
        scopes: Permissions granted to the key, e.g. ``events:write``.
        key_hash: SHA-256 digest of the full key; excluded from ``repr``.
    """

    id: UUID
    tenant_id: UUID
    scopes: tuple[str, ...]
    key_hash: bytes = field(repr=False)


async def get_active_api_key(session: AsyncSession, prefix: str) -> ApiKey | None:
    """Fetch the key with ``prefix`` if it is neither revoked nor expired.

    Keys whose tenant is not ``active`` are treated as missing.

    Args:
        session: Request-scoped database session.
        prefix: Public part of the key, ``pwg_<env>_<key_id>``.

    Returns:
        The key, or ``None`` if no usable key has that prefix.
    """
    result = await session.execute(_SELECT_ACTIVE_BY_PREFIX, {"prefix": prefix})
    row = result.one_or_none()
    if row is None:
        return None
    return ApiKey(
        id=row.id,
        tenant_id=row.tenant_id,
        scopes=tuple(row.scopes),
        key_hash=bytes(row.key_hash),
    )
