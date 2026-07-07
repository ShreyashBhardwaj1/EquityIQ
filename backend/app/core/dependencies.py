"""
Centralized dependency injection providers for FastAPI.
"""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.company_service import CompanyService
from app.application.services.document_service import DocumentService
from app.application.services.financial_statement_service import (
    FinancialStatementService,
)
from app.application.services.workspace_service import WorkspaceService
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


def get_workspace_service(
    workspace_repo: SQLAlchemyWorkspaceRepository = Depends(get_workspace_repository),
) -> WorkspaceService:
    """
    Dependency provider yielding WorkspaceService.
    """
    return WorkspaceService(workspace_repo)


def get_company_service(
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
) -> CompanyService:
    """
    Dependency provider yielding CompanyService.
    """
    return CompanyService(company_repo)


def get_document_service(
    doc_repo: SQLAlchemyDocumentRepository = Depends(get_document_repository),
) -> DocumentService:
    """
    Dependency provider yielding DocumentService.
    """
    return DocumentService(doc_repo)


def get_statement_service(
    statement_repo: SQLAlchemyFinancialStatementRepository = Depends(get_statement_repository),
) -> FinancialStatementService:
    """
    Dependency provider yielding FinancialStatementService.
    """
    return FinancialStatementService(statement_repo)


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


async def get_current_workspace_id(
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    current_user: User = Depends(get_current_user),
    workspace_repo: SQLAlchemyWorkspaceRepository = Depends(get_workspace_repository),
) -> UUID:
    """
    Resolves active workspace UUID from X-Workspace-ID header or personal default.
    """
    resolved_id: UUID

    if x_workspace_id:
        try:
            resolved_id = UUID(x_workspace_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Workspace-ID header format. Must be a valid UUID.",
            ) from None
    else:
        # Fallback to user's first active workspace
        user_workspaces = await workspace_repo.list_by_user(current_user.id)
        if not user_workspaces:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to any active workspace.",
            )
        resolved_id = user_workspaces[0].id

    # Verify membership relation
    membership = await workspace_repo.get_membership(resolved_id, current_user.id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this workspace.",
        )

    # Verify that workspace is active (not archived)
    workspace = await workspace_repo.get_by_id(resolved_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The specified workspace is inactive or archived.",
        )

    return resolved_id


def require_role(allowed_roles: list[UserRole]) -> Callable[[User], User]:
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
