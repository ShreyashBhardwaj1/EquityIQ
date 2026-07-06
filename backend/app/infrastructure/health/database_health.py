"""
Database connection health check.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("equityiq.health")


class DatabaseHealth:
    """
    Checks the connectivity of the PostgreSQL database using an active session.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the DatabaseHealth checker.

        Args:
            session: SQLAlchemy AsyncSession.
        """
        self.session = session

    async def check_health(self) -> bool:
        """
        Executes a simple query ping to verify SQL connectivity.

        Returns:
            True if connection is healthy, otherwise False.
        """
        try:
            await self.session.execute(select(1))
            return True
        except Exception as exc:
            logger.error(f"Database health check failed: {exc}")
            return False
        # Do not close or commit the session here; session lifecycle is handled externally
