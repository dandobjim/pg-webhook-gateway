"""FastAPI dependencies that authenticate requests with an API key."""

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..db.repositories.api_keys import ApiKey, get_active_api_key
from ..db.session import SessionDep
from .utils import KEY_RE, hash_key

# auto_error=False so a missing header gets the same 401 as a wrong key.
bearer = HTTPBearer(bearerFormat="pwg_<env>_<id>_<secret>", auto_error=False)


def _unauthorized() -> HTTPException:
    """Build the single 401 returned for every authentication failure."""
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_api_key(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: SessionDep,
) -> ApiKey:
    """Authenticate the request from its ``Authorization: Bearer`` header.

    The key is looked up by its public prefix and the hash is compared in constant
    time. Every failure yields the same response so callers cannot tell a
    malformed, unknown, revoked or expired key apart.

    Args:
        creds: Bearer credentials, or ``None`` if the header is missing or uses
            another scheme.
        session: Request-scoped database session.

    Returns:
        The authenticated key.

    Raises:
        HTTPException: 401 if the key is missing, malformed or not usable.
    """
    if creds is None or (match := KEY_RE.fullmatch(creds.credentials)) is None:
        raise _unauthorized()
    api_key = await get_active_api_key(session, match["prefix"])
    if api_key is None or not hmac.compare_digest(
        api_key.key_hash, hash_key(creds.credentials)
    ):
        raise _unauthorized()
    return api_key


ApiKeyDep = Annotated[ApiKey, Depends(require_api_key)]
