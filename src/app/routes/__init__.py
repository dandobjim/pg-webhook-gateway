"""Routes for the application."""
from fastapi import APIRouter

from .health_routes import router as health_router

routers = APIRouter(prefix="/api/v1" )

routers.include_router(health_router, tags=["Health Check"])
