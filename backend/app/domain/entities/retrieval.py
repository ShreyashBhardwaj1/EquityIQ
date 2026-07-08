"""
Retrieval result and query entities for query execution and ranking.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalQuery(BaseModel):
    """
    Search parameter container scoping similarity search, keyword searches, and tenanted metadata queries.
    """

    query_text: str = Field(
        description="Raw text query to search and retrieve context for"
    )
    workspace_id: UUID = Field(description="Scoping target workspace identifier")
    company_id: UUID | None = Field(
        default=None, description="Optional scoping company identifier"
    )
    document_id: UUID | None = Field(
        default=None, description="Optional scoping document identifier"
    )
    document_type: str | None = Field(
        default=None, description="Optional scoping document type limit (e.g. 10K)"
    )
    statement_type: str | None = Field(
        default=None, description="Optional statement classification limit"
    )
    fiscal_year: int | None = Field(
        default=None, description="Optional scoping report year limit"
    )
    fiscal_period: str | None = Field(
        default=None, description="Optional scoping report period limit (e.g. FY-2024)"
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Max result count to return"
    )
    offset: int = Field(default=0, ge=0, description="Listing pagination offset")


class RetrievalResult(BaseModel):
    """
    Result container representing a single matching chunk returned from a search query.
    """

    chunk_id: UUID = Field(description="Matching document chunk identifier")
    content: str = Field(
        description="Standardized chunk text or formatted markdown table"
    )
    score: float = Field(description="Relevance confidence ranking score")
    page_number: int = Field(
        description="Document page sequence index containing this content"
    )
    section_heading: str | None = Field(
        default=None, description="Active section heading annotation if resolved"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata audit trail mapping copy"
    )
