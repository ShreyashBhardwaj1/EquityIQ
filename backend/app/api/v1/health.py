"""
Health and Version API routes.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.dependencies import get_health_service, get_settings
from app.infrastructure.health.health_service import HealthService

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Shallow health check indicating the API is running.
    """
    return {"status": "healthy"}


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe indicating the container is alive.
    """
    return {"status": "live"}


@router.get("/ready")
async def readiness_check(
    health_service: HealthService = Depends(get_health_service),
) -> JSONResponse:
    """
    Readiness probe executing backing services pings (Database, Redis).
    """
    report = await health_service.check_ready()
    status_code = (
        status.HTTP_200_OK
        if report["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(content=report, status_code=status_code)


@router.get("/version")
async def version_check(
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """
    Version endpoint exposing system release tag information.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "release_tag": settings.RELEASE_TAG,
    }
