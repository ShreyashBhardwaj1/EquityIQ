"""
Search and retrieval API router.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.hybrid_search_service import HybridSearchService
from app.application.services.index_builder import IndexBuilder
from app.core.dependencies import (
    get_chunk_repository,
    get_current_workspace_id,
    get_document_repository,
    get_embedding_repository,
    get_hybrid_search_service,
    get_index_builder,
)
from app.domain.entities.retrieval import RetrievalQuery, RetrievalResult
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/search", tags=["Search & Retrieval"])


class SearchRequest(BaseModel):
    """
    Search request body payload schema.
    """

    query_text: str = Field(..., description="Query query string to search for")
    company_id: UUID | None = Field(
        default=None, description="Filter by company identifier"
    )
    document_id: UUID | None = Field(
        default=None, description="Filter by document identifier"
    )
    document_type: str | None = Field(
        default=None, description="Filter by document type limit (e.g. 10K)"
    )
    statement_type: str | None = Field(
        default=None, description="Filter by statement classification"
    )
    fiscal_year: int | None = Field(
        default=None, description="Filter by reporting year"
    )
    fiscal_period: str | None = Field(
        default=None, description="Filter by reporting quarter/period"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max result items count")
    offset: int = Field(default=0, ge=0, description="Pagination offsets count")


class HybridSearchRequest(SearchRequest):
    """
    Hybrid search request body extending standard request with alpha weights.
    """

    alpha: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Linear search weights ratio (1.0 = pure semantic, 0.0 = pure keyword)",
    )


@router.post("/semantic", response_model=list[RetrievalResult])
async def semantic_search(
    request: SearchRequest,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db_session),
    hybrid_service: HybridSearchService = Depends(get_hybrid_search_service),
) -> list[RetrievalResult]:
    """
    Execute semantic similarity vector search across all parsed document chunks in a workspace.
    """
    query = RetrievalQuery(
        query_text=request.query_text,
        workspace_id=workspace_id,
        company_id=request.company_id,
        document_id=request.document_id,
        document_type=request.document_type,
        statement_type=request.statement_type,
        fiscal_year=request.fiscal_year,
        fiscal_period=request.fiscal_period,
        limit=request.limit,
        offset=request.offset,
    )

    # Pure semantic is hybrid search with alpha set to 1.0 (completely ignores keyword BM25 score)
    return await hybrid_service.search(db, query, alpha=1.0)


@router.post("/hybrid", response_model=list[RetrievalResult])
async def hybrid_search(
    request: HybridSearchRequest,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db_session),
    hybrid_service: HybridSearchService = Depends(get_hybrid_search_service),
) -> list[RetrievalResult]:
    """
    Execute weighted hybrid search blending semantic vectors and SQLite FTS5 keyword results.
    """
    query = RetrievalQuery(
        query_text=request.query_text,
        workspace_id=workspace_id,
        company_id=request.company_id,
        document_id=request.document_id,
        document_type=request.document_type,
        statement_type=request.statement_type,
        fiscal_year=request.fiscal_year,
        fiscal_period=request.fiscal_period,
        limit=request.limit,
        offset=request.offset,
    )

    return await hybrid_service.search(db, query, alpha=request.alpha)


@router.post("/rebuild", status_code=status.HTTP_200_OK)
async def rebuild_workspace_index(
    workspace_id: UUID = Depends(get_current_workspace_id),
    index_builder: IndexBuilder = Depends(get_index_builder),
    doc_repo: Any = Depends(get_document_repository),
    chunk_repo: Any = Depends(get_chunk_repository),
    embedding_repo: Any = Depends(get_embedding_repository),
) -> dict[str, str]:
    """
    Force clean indexing and build workspace FAISS vector indices from scratch.
    """
    try:
        await index_builder.rebuild_workspace_index(
            workspace_id=workspace_id,
            doc_repo=doc_repo,
            chunk_repo=chunk_repo,
            embedding_repo=embedding_repo,
        )
        return {
            "status": "success",
            "message": f"Workspace FAISS index rebuilt successfully for workspace: {workspace_id}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebuild workspace FAISS index: {e}",
        ) from None
