"""
ParsingManifest domain entity representing execution metrics of a document parse.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParsingManifest(BaseModel):
    """
    Domain entity tracking parse execution configurations and audit metrics.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Unique identifier for this manifest record")
    document_id: UUID = Field(description="Associated document ID")
    parser_version: str = Field(description="Version index of parser tool")
    chunk_strategy: str = Field(
        description="Strategy classification (e.g. semantic_layout)"
    )
    chunk_size: int = Field(gt=0, description="Max character length per chunk")
    overlap: int = Field(
        ge=0, description="Character overlap between consecutive chunks"
    )
    parse_duration: float = Field(ge=0.0, description="Parse execution time in seconds")
    chunk_count: int = Field(ge=0, description="Total number of chunks produced")
    table_count: int = Field(
        ge=0, description="Total number of layout tables extracted"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal warning logs collected during run"
    )
    extraction_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall parsing/OCR character confidence",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
