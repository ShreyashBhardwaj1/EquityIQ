"""
DatabaseManager for engine lifecycle and session factory management.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger("equityiq.db")


class DatabaseManager:
    """
    Manages SQLAlchemy engine initialization, session factory creation, and graceful shutdown.
    """

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """
        Initializes the DatabaseManager setup variables.

        Args:
            database_url: Connection string for database.
            echo: Set to True to enable raw SQL logging.
        """
        self.database_url = database_url
        self.echo = echo
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self) -> None:
        """
        Creates the async engine and session factory with connection pooling options.
        """
        if self._engine is not None:
            logger.warning(
                "DatabaseManager already initialized; initialization skipped."
            )
            return

        logger.info("Initializing async database engine and connection pool.")

        # Dialect-agnostic keyword arguments
        engine_kwargs: dict[str, Any] = {
            "echo": self.echo,
            "pool_pre_ping": True,
        }

        # SQLite dialect doesn't support pool_size and max_overflow parameters
        if "sqlite" not in self.database_url:
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20

        self._engine = create_async_engine(self.database_url, **engine_kwargs)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Keep state active after transaction commits
        )

    async def shutdown(self) -> None:
        """
        Disposes connection pools and gracefully closes the engine.
        """
        if self._engine is None:
            logger.warning("DatabaseManager engine not initialized; shutdown skipped.")
            return

        logger.info("Closing async database connection pool.")
        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Retrieves the session factory.

        Returns:
            The async sessionmaker factory.

        Raises:
            RuntimeError: If initialize has not been called.
        """
        if self._session_factory is None:
            raise RuntimeError(
                "DatabaseManager has not been initialized. Call initialize() first."
            )
        return self._session_factory

    @property
    def engine(self) -> AsyncEngine:
        """
        Retrieves the DB engine.

        Returns:
            The async engine instance.

        Raises:
            RuntimeError: If initialize has not been called.
        """
        if self._engine is None:
            raise RuntimeError(
                "DatabaseManager has not been initialized. Call initialize() first."
            )
        return self._engine


# Global DatabaseManager instance initialized with settings
db_manager = DatabaseManager(
    settings.DATABASE_URL, echo=(settings.ENV == "development")
)
