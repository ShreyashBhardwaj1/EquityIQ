"""
Exposes AsyncSession dependencies for FastAPI.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.manager import db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession from the DatabaseManager session factory.
    """
    async with db_manager.session_factory() as session:
        yield session
