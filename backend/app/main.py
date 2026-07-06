"""
EquityIQ FastAPI Application Entry Point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import settings
from app.infrastructure.db.manager import db_manager
from app.infrastructure.logging.logger import setup_logging
from app.infrastructure.logging.middleware import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifespan context manager handling startup and shutdown hooks.
    """
    # Startup lifecycle hooks
    setup_logging(env=settings.ENV)
    logger = logging.getLogger("equityiq.main")
    logger.info("FastAPI Application starting up...")
    db_manager.initialize()

    yield

    # Shutdown lifecycle hooks
    logger.info("FastAPI Application shutting down...")
    await db_manager.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    description="Investment Analysis and Research Platform Core API",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Register structured request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include core system routers
app.include_router(health_router, tags=["Health"])
