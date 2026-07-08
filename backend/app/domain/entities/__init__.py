"""
Entities package containing domain entities for EquityIQ.
"""

from app.domain.entities.company import Company
from app.domain.entities.document import Document, DocumentType, ParsingStatus
from app.domain.entities.document_chunk import ChunkMetadata, DocumentChunk
from app.domain.entities.document_version import DocumentVersion
from app.domain.entities.financial_statement import (
    FinancialStatement,
    NormalizationAdjustment,
    StatementType,
)
from app.domain.entities.financial_statement_version import (
    FinancialStatementVersion,
)
from app.domain.entities.parsing_manifest import ParsingManifest
from app.domain.entities.ratio import Ratio
from app.domain.entities.recommendation import Recommendation, RecommendationType
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
    "Company",
    "ComparableCompanyAssumptions",
    "DCFAssumptions",
    "Document",
    "DocumentChunk",
    "DocumentType",
    "DocumentVersion",
    "FinancialStatement",
    "FinancialStatementVersion",
    "NormalizationAdjustment",
    "ParsingManifest",
    "ParsingStatus",
    "Ratio",
    "Recommendation",
    "RecommendationType",
    "StatementType",
    "User",
    "UserRole",
    "Valuation",
    "ValuationMethod",
    "Workspace",
    "WorkspaceMembership",
]
