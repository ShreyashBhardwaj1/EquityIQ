"""
Centralized dependency injection providers for FastAPI.
"""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.company_service import CompanyService
from app.application.services.conversation_service import ConversationService
from app.application.services.document_service import DocumentService
from app.application.services.embedding_service import EmbeddingService
from app.application.services.financial_statement_service import (
    FinancialStatementService,
)
from app.application.services.hybrid_search_service import HybridSearchService
from app.application.services.index_builder import IndexBuilder
from app.application.services.index_manager import IndexManager
from app.application.services.rag_service import RAGService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.workspace_service import WorkspaceService
from app.core.config import Settings, settings
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.providers import LLMProvider, TokenizerProvider
from app.domain.interfaces.repositories import (
    EmbeddingProvider,
    VectorStore,
)
from app.infrastructure.db.manager import DatabaseManager, db_manager
from app.infrastructure.db.repositories.chunk_repo import SQLAlchemyChunkRepository
from app.infrastructure.db.repositories.citation_repo import (
    SQLAlchemyCitationRepository,
)
from app.infrastructure.db.repositories.company_repo import (
    SQLAlchemyCompanyRepository,
)
from app.infrastructure.db.repositories.conversation_repo import (
    SQLAlchemyConversationRepository,
)
from app.infrastructure.db.repositories.document_repo import (
    SQLAlchemyDocumentRepository,
)
from app.infrastructure.db.repositories.embedding_manifest_repo import (
    SQLAlchemyEmbeddingManifestRepository,
)
from app.infrastructure.db.repositories.embedding_repo import (
    SQLAlchemyEmbeddingRepository,
)
from app.infrastructure.db.repositories.parsing_manifest_repo import (
    SQLAlchemyParsingManifestRepository,
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


def get_chunk_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyChunkRepository:
    """
    Dependency provider yielding Chunk repository.
    """
    return SQLAlchemyChunkRepository(session)


def get_parsing_manifest_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyParsingManifestRepository:
    """
    Dependency provider yielding ParsingManifest repository.
    """
    return SQLAlchemyParsingManifestRepository(session)


def get_embedding_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyEmbeddingRepository:
    """
    Dependency provider yielding Embedding repository.
    """
    return SQLAlchemyEmbeddingRepository(session)


def get_embedding_manifest_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyEmbeddingManifestRepository:
    """
    Dependency provider yielding EmbeddingManifest repository.
    """
    return SQLAlchemyEmbeddingManifestRepository(session)


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
    statement_repo: SQLAlchemyFinancialStatementRepository = Depends(
        get_statement_repository
    ),
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


# Global cached provider instances to avoid reloading weights repeatedly
_embedding_provider = None
_vector_store = None


def get_embedding_provider() -> EmbeddingProvider:
    """
    Dependency provider yielding the singleton EmbeddingProvider model instance.
    """
    global _embedding_provider
    if _embedding_provider is None:
        from app.infrastructure.embeddings.sentence_transformer_adapter import (
            SentenceTransformerAdapter,
        )

        _embedding_provider = SentenceTransformerAdapter()
    return _embedding_provider


def get_vector_store() -> VectorStore:
    """
    Dependency provider yielding the singleton VectorStore FAISS index wrapper.
    """
    global _vector_store
    if _vector_store is None:
        from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore

        _vector_store = FaissVectorStore()
    return _vector_store


def get_index_manager(
    vector_store: VectorStore = Depends(get_vector_store),
) -> IndexManager:
    """
    Dependency provider yielding the IndexManager service.
    """
    from app.application.services.index_manager import IndexManager

    return IndexManager(vector_store)


def get_index_builder(
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    vector_store: VectorStore = Depends(get_vector_store),
) -> IndexBuilder:
    """
    Dependency provider yielding the IndexBuilder service.
    """
    from app.application.services.index_builder import IndexBuilder

    return IndexBuilder(embedding_provider, vector_store)


def get_embedding_service(
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    index_builder: IndexBuilder = Depends(get_index_builder),
) -> EmbeddingService:
    """
    Dependency provider yielding the EmbeddingService.
    """
    from app.application.services.embedding_service import EmbeddingService

    return EmbeddingService(embedding_provider, index_builder)


def get_retrieval_service(
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    vector_store: VectorStore = Depends(get_vector_store),
    chunk_repo: SQLAlchemyChunkRepository = Depends(get_chunk_repository),
) -> RetrievalService:
    """
    Dependency provider yielding the RetrievalService.
    """
    from app.application.services.retrieval_service import RetrievalService

    return RetrievalService(embedding_provider, vector_store, chunk_repo)


def get_hybrid_search_service(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    chunk_repo: SQLAlchemyChunkRepository = Depends(get_chunk_repository),
) -> HybridSearchService:
    """
    Dependency provider yielding the HybridSearchService.
    """
    from app.application.services.hybrid_search_service import HybridSearchService

    return HybridSearchService(retrieval_service, chunk_repo)


def get_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyConversationRepository:
    """
    Dependency provider yielding Conversation repository.
    """
    return SQLAlchemyConversationRepository(session)


def get_citation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyCitationRepository:
    """
    Dependency provider yielding Citation repository.
    """
    return SQLAlchemyCitationRepository(session)


_llm_provider = None
_tokenizer_provider = None


def get_tokenizer_provider() -> TokenizerProvider:
    """
    Dependency provider yielding TokenizerAdapter singleton.
    """
    global _tokenizer_provider
    if _tokenizer_provider is None:
        from app.infrastructure.llm.tokenizer_adapter import (
            TiktokenTokenizerAdapter,
        )

        _tokenizer_provider = TiktokenTokenizerAdapter()
    return _tokenizer_provider


def get_llm_provider() -> LLMProvider:
    """
    Dependency provider yielding LLMProvider adapter instance.
    """
    global _llm_provider
    if _llm_provider is None:
        from app.infrastructure.llm.gemini_adapter import GeminiAdapter

        _llm_provider = GeminiAdapter()
    return _llm_provider


def get_conversation_service(
    conv_repo: SQLAlchemyConversationRepository = Depends(get_conversation_repository),
    cit_repo: SQLAlchemyCitationRepository = Depends(get_citation_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> ConversationService:
    """
    Dependency provider yielding ConversationService.
    """
    return ConversationService(
        conversation_repo=conv_repo,
        citation_repo=cit_repo,
        llm_provider=llm_provider,
    )


def get_rag_service(
    hybrid_search: HybridSearchService = Depends(get_hybrid_search_service),
    chunk_repo: SQLAlchemyChunkRepository = Depends(get_chunk_repository),
    conv_service: ConversationService = Depends(get_conversation_service),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    tokenizer_provider: TokenizerProvider = Depends(get_tokenizer_provider),
) -> RAGService:
    """
    Dependency provider yielding the RAGService orchestrator.
    """
    from app.application.services.citation_service import CitationService
    from app.application.services.confidence_scorer import ConfidenceScorer
    from app.application.services.context_assembler import ContextAssembler
    from app.application.services.prompt_builder import PromptBuilder
    from app.application.services.prompt_injection_guard import PromptInjectionGuard
    from app.application.services.response_validator import ResponseValidator
    from app.application.services.token_budget_manager import TokenBudgetManager

    assembler = ContextAssembler(chunk_repo)
    budget_manager = TokenBudgetManager(tokenizer_provider)
    prompt_builder = PromptBuilder()
    guard = PromptInjectionGuard()
    validator = ResponseValidator()
    scorer = ConfidenceScorer()
    cit_service = CitationService()

    return RAGService(
        hybrid_search_service=hybrid_search,
        prompt_injection_guard=guard,
        context_assembler=assembler,
        token_budget_manager=budget_manager,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        response_validator=validator,
        confidence_scorer=scorer,
        citation_service=cit_service,
        conversation_service=conv_service,
    )
