"""
HealthService coordinating multiple infrastructure pings.
"""

from typing import Any

from app.infrastructure.health.database_health import DatabaseHealth
from app.infrastructure.health.redis_health import RedisHealth


class HealthService:
    """
    Coordinates and aggregates connection checks for PostgreSQL and Redis.
    """

    def __init__(self, db_health: DatabaseHealth, redis_health: RedisHealth) -> None:
        """
        Initializes the HealthService.

        Args:
            db_health: DatabaseHealth check instance.
            redis_health: RedisHealth check instance.
        """
        self.db_health = db_health
        self.redis_health = redis_health

    async def check_ready(self) -> dict[str, Any]:
        """
        Checks the connectivity status of all backing services.

        Returns:
            A dictionary stating overall status and sub-services states.
        """
        db_ok = await self.db_health.check_health()
        redis_ok = await self.redis_health.check_health()

        overall_status = "healthy" if (db_ok and redis_ok) else "unhealthy"
        return {
            "status": overall_status,
            "services": {
                "database": "up" if db_ok else "down",
                "redis": "up" if redis_ok else "down",
            },
        }
