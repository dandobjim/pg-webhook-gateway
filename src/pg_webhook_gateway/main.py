"""FastAPI application entrypoint for the webhook gateway."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a welcome message.

    Returns:
        A JSON object with a greeting message.
    """
    return {"message": "Welcome to the PG Webhook Gateway!"}
