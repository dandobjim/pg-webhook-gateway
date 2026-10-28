import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import dependencies
from app.auth.dependencies import ApiKeyDep
from app.auth.utils import KEY_RE, generate_key, hash_key
from app.db.repositories.api_keys import ApiKey, get_active_api_key
from app.db.session import get_session

FULL_KEY, PREFIX, KEY_HASH = generate_key()
STORED = ApiKey(
    id=uuid4(), tenant_id=uuid4(), scopes=("events:write",), key_hash=KEY_HASH
)


@pytest.fixture
def lookup(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock(return_value=STORED)
    monkeypatch.setattr(dependencies, "get_active_api_key", mock)
    return mock


@pytest.fixture
def client(lookup: AsyncMock) -> TestClient:
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(api_key: ApiKeyDep) -> dict[str, str]:
        return {"tenant_id": str(api_key.tenant_id)}

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield AsyncMock(spec=AsyncSession)

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


@pytest.mark.parametrize("env", ["live", "test"])
def test_generate_key_matches_regex_and_hash(env: str) -> None:
    full_key, prefix, key_hash = generate_key(env)

    match = KEY_RE.fullmatch(full_key)
    assert match is not None
    assert match["prefix"] == prefix
    assert prefix.startswith(f"pwg_{env}_")
    assert key_hash == hash_key(full_key)
    assert len(key_hash) == 32


def test_valid_key_is_accepted(client: TestClient, lookup: AsyncMock) -> None:
    response = client.get("/whoami", headers={"Authorization": f"Bearer {FULL_KEY}"})

    assert response.status_code == 200
    assert response.json() == {"tenant_id": str(STORED.tenant_id)}
    assert lookup.await_args is not None
    assert lookup.await_args.args[1] == PREFIX


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": f"Basic {FULL_KEY}"},
        {"Authorization": "Bearer not-a-key"},
        {"Authorization": f"Bearer {PREFIX}_{'x' * 40}"},
    ],
    ids=["missing", "wrong-scheme", "malformed", "wrong-secret"],
)
def test_bad_credentials_are_rejected(
    client: TestClient, headers: dict[str, str]
) -> None:
    response = client.get("/whoami", headers=headers)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_unknown_key_is_rejected(client: TestClient, lookup: AsyncMock) -> None:
    lookup.return_value = None

    response = client.get("/whoami", headers={"Authorization": f"Bearer {FULL_KEY}"})

    assert response.status_code == 401


def test_get_active_api_key_maps_row() -> None:
    row = MagicMock(
        id=STORED.id,
        tenant_id=STORED.tenant_id,
        scopes=["events:write"],
        key_hash=KEY_HASH,
    )
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value.one_or_none = MagicMock(return_value=row)

    assert asyncio.run(get_active_api_key(session, PREFIX)) == STORED


def test_get_active_api_key_returns_none_when_missing() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value.one_or_none = MagicMock(return_value=None)

    assert asyncio.run(get_active_api_key(session, PREFIX)) is None
