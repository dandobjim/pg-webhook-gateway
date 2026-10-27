from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.main import app


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def client(session: AsyncMock) -> Iterator[TestClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    # Not used as a context manager, so the lifespan (real engine) never runs.
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_healthz_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_ready_when_database_answers(
    client: TestClient, session: AsyncMock
) -> None:
    response = client.get("/api/v1/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    session.execute.assert_awaited_once()


def test_readyz_returns_503_when_database_is_down(
    client: TestClient, session: AsyncMock
) -> None:
    session.execute.side_effect = OperationalError("SELECT 1", {}, OSError("down"))

    response = client.get("/api/v1/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
