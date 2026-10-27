"""FastAPI application entrypoint for the webhook gateway."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import get_settings
from .db.session import create_engine, create_session_factory
from .routes import routers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the database engine on startup and dispose of it on shutdown.

    Args:
        app: The application whose state receives the engine and session factory.

    Yields:
        Control to the running application.
    """
    engine = create_engine(get_settings())
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(routers)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a welcome message.

    Returns:
        A JSON object with a greeting message.
    """
    return {"message": "Welcome to the PG Webhook Gateway!"}
