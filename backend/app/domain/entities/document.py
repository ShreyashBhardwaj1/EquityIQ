"""
Document entity representing ingested filings or textual data.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects.fiscal_period import FiscalPeriod


class DocumentType(StrEnum):
    """Supported document types for ingestion."""

    TEN_K = "10K"
    TEN_Q = "10Q"
    INVESTOR_DECK = "investor_deck"
    EARNINGS_CALL = "earnings_call"
    NEWS = "news"


class ParsingStatus(StrEnum):
    """Document processing workflow states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """
    Document entity representing an uploaded financial filing, press release, or report.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique identifier for the document")
    workspace_id: UUID = Field(description="Scoping workspace identifier")
    company_id: UUID = Field(description="Associated company identifier")
    doc_type: DocumentType = Field(description="Category of the document")
    fiscal_period: FiscalPeriod = Field(
        description="Associated fiscal period value object"
    )
    storage_path: str = Field(min_length=1, description="File path in object storage")
    parsing_status: ParsingStatus = Field(
        default=ParsingStatus.PENDING, description="Current workflow state"
    )
    parsing_confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="OCR/Parsing engine confidence score"
    )
    uploaded_by: UUID = Field(description="User identifier who uploaded the file")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
