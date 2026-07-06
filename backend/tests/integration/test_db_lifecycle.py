"""
Integration tests for DatabaseManager lifecycle.
"""

import pytest

from app.infrastructure.db.manager import DatabaseManager
from app.infrastructure.health.database_health import DatabaseHealth


@pytest.mark.asyncio
async def test_database_manager_lifecycle() -> None:
    """
    Verifies that the DatabaseManager correctly starts, validates health, and shuts down.
    """
    db_url = "sqlite+aiosqlite:///:memory:"
    manager = DatabaseManager(db_url)

    # Initialize manager engine and sessionmaker
    manager.initialize()
    assert manager.engine is not None
    assert manager.session_factory is not None

    # Test database connectivity health
    async with manager.session_factory() as session:
        health_checker = DatabaseHealth(session)
        is_healthy = await health_checker.check_health()
        assert is_healthy is True

    # Shutdown manager and release resources
    await manager.shutdown()

    # Ensure engine access raises error after dispose
    with pytest.raises(RuntimeError):
        _ = manager.engine
