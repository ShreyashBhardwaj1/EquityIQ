"""
Entities package containing domain entities for EquityIQ.
"""

from app.domain.entities.company import Company
from app.domain.entities.conversation import (
    Citation,
    Conversation,
    ConversationMessage,
    LLMRequest,
)
from app.domain.entities.document import Document, DocumentType, ParsingStatus
from app.domain.entities.document_chunk import ChunkMetadata, DocumentChunk
from app.domain.entities.document_version import DocumentVersion
from app.domain.entities.embedding import Embedding
from app.domain.entities.embedding_manifest import EmbeddingManifest
from app.domain.entities.financial_intelligence import (
    FinancialHealthScore,
    RatioCalculationResult,
    RatioCategory,
    RatioDefinition,
    RecommendationHistory,
    RecommendationPolicy,
    RiskAssessment,
    SeverityLevel,
    TrendState,
)
from app.domain.entities.financial_statement import (
    FinancialStatement,
    NormalizationAdjustment,
    StatementType,
)
from app.domain.entities.financial_statement_version import (
    FinancialStatementVersion,
)
from app.domain.entities.parsing_manifest import ParsingManifest
from app.domain.entities.portfolio_signal import PortfolioSignal
from app.domain.entities.ratio import Ratio
from app.domain.entities.recommendation import Recommendation, RecommendationType
from app.domain.entities.report import (
    FinancialReport,
    FinancialReportVersion,
    ReportStatus,
)
from app.domain.entities.retrieval import RetrievalQuery, RetrievalResult
from app.domain.entities.user import User, UserRole
from app.domain.entities.valuation import (
    ComparableCompanyAssumptions,
    DCFAssumptions,
    Valuation,
    ValuationMethod,
)
from app.domain.entities.workspace import Workspace, WorkspaceMembership

__all__ = [
    "ChunkMetadata",
    "Citation",
    "Company",
    "ComparableCompanyAssumptions",
    "Conversation",
    "ConversationMessage",
    "DCFAssumptions",
    "Document",
    "DocumentChunk",
    "DocumentType",
    "DocumentVersion",
    "Embedding",
    "EmbeddingManifest",
    "FinancialHealthScore",
    "FinancialReport",
    "FinancialReportVersion",
    "FinancialStatement",
    "FinancialStatementVersion",
    "LLMRequest",
    "NormalizationAdjustment",
    "ParsingManifest",
    "ParsingStatus",
    "PortfolioSignal",
    "Ratio",
    "RatioCalculationResult",
    "RatioCategory",
    "RatioDefinition",
    "Recommendation",
    "RecommendationHistory",
    "RecommendationPolicy",
    "RecommendationType",
    "ReportStatus",
    "RetrievalQuery",
    "RetrievalResult",
    "RiskAssessment",
    "SeverityLevel",
    "StatementType",
    "TrendState",
    "User",
    "UserRole",
    "Valuation",
    "ValuationMethod",
    "Workspace",
    "WorkspaceMembership",
]
