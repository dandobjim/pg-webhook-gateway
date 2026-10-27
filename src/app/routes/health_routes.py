"""Liveness and readiness probes."""

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..db.session import SessionDep

router = APIRouter()


@router.get(
    "/healthz",
    tags=["Health Check"],
    summary="Health Check Endpoint",
    status_code=status.HTTP_200_OK,
)
async def healthz(response: Response) -> dict[str, str]:
    """Report that the process is alive, without touching dependencies.

    Args:
        response: Outgoing response.

    Returns:
        ``{"status": "ok"}``.
    """
    response.status_code = status.HTTP_200_OK
    return {"status": "ok"}


@router.get(
    "/readyz",
    tags=["Health Check"],
    summary="Readiness Check Endpoint",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unreachable"}
    },
)
async def readyz(session: SessionDep, response: Response) -> dict[str, str]:
    """Report whether the service can reach its database.

    Args:
        session: Request-scoped database session.
        response: Outgoing response, used to set 503 when not ready.

    Returns:
        ``{"status": "ready"}`` when ``SELECT 1`` succeeds, otherwise
        ``{"status": "unavailable"}`` with HTTP 503.
    """
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError, OSError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ready"}
