"""
SQLAlchemy repository implementations package for EquityIQ.
"""

from app.infrastructure.db.repositories.base_repo import BaseRepository
from app.infrastructure.db.repositories.chunk_repo import SQLAlchemyChunkRepository
from app.infrastructure.db.repositories.citation_repo import (
    SQLAlchemyCitationRepository,
)
from app.infrastructure.db.repositories.company_repo import SQLAlchemyCompanyRepository
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
from app.infrastructure.db.repositories.health_score_repo import (
    SQLAlchemyHealthScoreRepository,
)
from app.infrastructure.db.repositories.parsing_manifest_repo import (
    SQLAlchemyParsingManifestRepository,
)
from app.infrastructure.db.repositories.ratio_repo import SQLAlchemyRatioRepository
from app.infrastructure.db.repositories.recommendation_repo import (
    SQLAlchemyRecommendationRepository,
)
from app.infrastructure.db.repositories.refresh_token_repo import (
    SQLAlchemyRefreshTokenRepository,
)
from app.infrastructure.db.repositories.report_repo import (
    SQLAlchemyReportRepository,
)
from app.infrastructure.db.repositories.risk_assessment_repo import (
    SQLAlchemyRiskAssessmentRepository,
)
from app.infrastructure.db.repositories.statement_repo import (
    SQLAlchemyFinancialStatementRepository,
)
from app.infrastructure.db.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.db.repositories.workspace_repo import (
    SQLAlchemyWorkspaceRepository,
)

__all__ = [
    "BaseRepository",
    "SQLAlchemyChunkRepository",
    "SQLAlchemyCitationRepository",
    "SQLAlchemyCompanyRepository",
    "SQLAlchemyConversationRepository",
    "SQLAlchemyDocumentRepository",
    "SQLAlchemyEmbeddingManifestRepository",
    "SQLAlchemyEmbeddingRepository",
    "SQLAlchemyFinancialStatementRepository",
    "SQLAlchemyHealthScoreRepository",
    "SQLAlchemyParsingManifestRepository",
    "SQLAlchemyRatioRepository",
    "SQLAlchemyRecommendationRepository",
    "SQLAlchemyRefreshTokenRepository",
    "SQLAlchemyReportRepository",
    "SQLAlchemyRiskAssessmentRepository",
    "SQLAlchemyUserRepository",
    "SQLAlchemyWorkspaceRepository",
]
