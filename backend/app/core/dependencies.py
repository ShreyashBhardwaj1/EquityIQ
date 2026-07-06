"""
Centralized dependency injection providers for FastAPI.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.manager import DatabaseManager, db_manager
from app.infrastructure.db.repositories.company_repo import (
    SQLAlchemyCompanyRepository,
)
from app.infrastructure.db.repositories.document_repo import (
    SQLAlchemyDocumentRepository,
)
from app.infrastructure.db.repositories.refresh_token_repo import (
    SQLAlchemyRefreshTokenRepository,
)
from app.infrastructure.db.repositories.statement_repo import (
    SQLAlchemyFinancialStatementRepository,
)
from app.infrastructure.db.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.db.repositories.workspace_repo import (
    SQLAlchemyWorkspaceRepository,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.health.database_health import DatabaseHealth
from app.infrastructure.health.health_service import HealthService
from app.infrastructure.health.redis_health import RedisHealth
from app.infrastructure.security.jwt import decode_token
from app.infrastructure.security.password import BcryptPasswordHasher
from app.infrastructure.security.service import AuthService


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


# Define standard security scheme
security = HTTPBearer(auto_error=True)


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyUserRepository:
    """
    Dependency provider yielding UserRepository.
    """
    return SQLAlchemyUserRepository(session)


def get_workspace_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyWorkspaceRepository:
    """
    Dependency provider yielding WorkspaceRepository.
    """
    return SQLAlchemyWorkspaceRepository(session)


def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyRefreshTokenRepository:
    """
    Dependency provider yielding RefreshTokenRepository.
    """
    return SQLAlchemyRefreshTokenRepository(session)


def get_auth_service(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    workspace_repo: SQLAlchemyWorkspaceRepository = Depends(get_workspace_repository),
    refresh_token_repo: SQLAlchemyRefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
) -> AuthService:
    """
    Dependency provider yielding AuthService.
    """
    return AuthService(
        user_repo=user_repo,
        workspace_repo=workspace_repo,
        refresh_token_repo=refresh_token_repo,
        hasher=BcryptPasswordHasher(),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> User:
    """
    Authenticates access token and yields current User entity.
    """
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    try:
        user_id = UUID(payload["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject payload.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return user


def require_role(allowed_roles: list[UserRole]):
    """
    Role-based Access Control (RBAC) dependency helper.
    """

    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation forbidden: insufficient privileges.",
            )
        return current_user

    return role_dependency
