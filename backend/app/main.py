"""
EquityIQ FastAPI Application Entry Point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.company import router as company_router
from app.api.v1.document import router as document_router
from app.api.v1.financial_statement import router as financial_statement_router
from app.api.v1.health import router as health_router
from app.api.v1.workspace import router as workspace_router
from app.core.config import settings
from app.infrastructure.db.manager import db_manager
from app.infrastructure.logging.logger import setup_logging
from app.infrastructure.logging.middleware import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
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
app.include_router(auth_router, tags=["Authentication"])
app.include_router(workspace_router)
app.include_router(company_router)
app.include_router(document_router)
app.include_router(financial_statement_router)
