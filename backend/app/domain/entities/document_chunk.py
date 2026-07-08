"""
DocumentChunk and ChunkMetadata domain entities representing parsed content blocks.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChunkMetadata(BaseModel):
    """
    Value object containing contextual metadata descriptors for document chunks.
    """

    model_config = ConfigDict(frozen=True)

    workspace_id: UUID = Field(description="Tenant isolation scope")
    company_id: UUID = Field(description="Scoping company identifier")
    document_id: UUID = Field(description="Source document identifier")
    statement_type: str | None = Field(
        default=None, description="Statement category if applicable"
    )
    document_type: str = Field(
        description="Type category of document (e.g. 10K, earnings_call)"
    )
    fiscal_year: int | None = Field(default=None, description="Filing fiscal year")
    fiscal_period: str | None = Field(
        default=None, description="Filing fiscal period (e.g. Q1, FY)"
    )
    page_number: int = Field(ge=1, description="Page index where chunk is located")
    chunk_index: int = Field(ge=0, description="Logical index within document sequence")
    section_heading: str | None = Field(
        default=None, description="Logical section header"
    )
    source_file: str = Field(description="Filename on upload")
    parser_version: str = Field(description="Version index of parser tool")
    document_version: int = Field(
        default=1, description="Uploaded file version context"
    )
    parse_version: int = Field(default=1, description="Run execution version index")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class DocumentChunk(BaseModel):
    """
    Domain entity representing parsed textual or tabular content sections.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Unique identifier for the chunk")
    document_id: UUID = Field(description="Associated parent document ID")
    content: str = Field(
        min_length=1, description="Extracted raw text or Markdown table content"
    )
    page_number: int = Field(ge=1, description="Page index where chunk is located")
    chunk_index: int = Field(
        ge=0, description="Logical position in sequential parser list"
    )
    section_heading: str | None = Field(
        default=None, description="Nearest preceding structural section header"
    )
    metadata: ChunkMetadata = Field(description="Rich context descriptor tags")
