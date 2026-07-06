"""
Centralized dependency injection providers for FastAPI.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.infrastructure.db.manager import DatabaseManager, db_manager
from app.infrastructure.db.repositories.company_repo import (
    SQLAlchemyCompanyRepository,
)
from app.infrastructure.db.repositories.document_repo import (
    SQLAlchemyDocumentRepository,
)
from app.infrastructure.db.repositories.statement_repo import (
    SQLAlchemyFinancialStatementRepository,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.health.database_health import DatabaseHealth
from app.infrastructure.health.health_service import HealthService
from app.infrastructure.health.redis_health import RedisHealth


def get_settings() -> Settings:
    """
    Dependency provider yielding application configuration.
    """
    return settings


def get_db_manager() -> DatabaseManager:
    """
    Dependency provider yielding the global DatabaseManager.
    """
    return db_manager


def get_company_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyCompanyRepository:
    """
    Dependency provider yielding Company repository.
    """
    return SQLAlchemyCompanyRepository(session)


def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyDocumentRepository:
    """
    Dependency provider yielding Document repository.
    """
    return SQLAlchemyDocumentRepository(session)


def get_statement_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyFinancialStatementRepository:
    """
    Dependency provider yielding FinancialStatement repository.
    """
    return SQLAlchemyFinancialStatementRepository(session)


def get_health_service(
    session: AsyncSession = Depends(get_db_session),
) -> HealthService:
    """
    Dependency provider yielding the HealthService orchestrator.
    """
    db_health = DatabaseHealth(session)
    redis_health = RedisHealth(settings.REDIS_URL)
    return HealthService(db_health, redis_health)
