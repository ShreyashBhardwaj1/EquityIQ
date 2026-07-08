"""
RetrievalService application service.
"""

import logging
import re
from uuid import UUID

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.retrieval import RetrievalQuery
from app.domain.interfaces.repositories import (
    ChunkRepository,
    EmbeddingProvider,
    VectorStore,
)

logger = logging.getLogger("equityiq.application.retrieval_service")


class RetrievalService:
    """
    Coordinates semantic vector searches and full-text keyword searches with strict pre-filtering.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        chunk_repo: ChunkRepository,
    ) -> None:
        """
        Initialize with core abstractions.
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.chunk_repo = chunk_repo

    def _sanitize_fts_query(self, query: str) -> str:
        """
        Sanitize search string to prevent FTS5 syntax errors.
        """
        clean = re.sub(r"[^\w\s]", " ", query)
        terms = clean.split()
        return " ".join(terms)

    async def list_allowed_chunk_ids(self, query: RetrievalQuery) -> list[UUID]:
        """
        Resolves the set of chunk IDs permitted by tenant metadata scopes.
        """
        return await self.chunk_repo.filter_chunk_ids(
            workspace_id=query.workspace_id,
            company_id=query.company_id,
            document_id=query.document_id,
            document_type=query.document_type,
            statement_type=query.statement_type,
            fiscal_year=query.fiscal_year,
            fiscal_period=query.fiscal_period,
        )

    async def semantic_search(
        self,
        query: RetrievalQuery,
        allowed_chunk_ids: list[UUID],
    ) -> list[tuple[UUID, float]]:
        """
        Execute vector similarity search restricted to allowed pre-filter chunk IDs.
        """
        if not allowed_chunk_ids:
            return []

        # Embed query text
        query_vector = await self.embedding_provider.embed_query(query.query_text)

        # Query FAISS via vector store
        raw_results = await self.vector_store.search(
            workspace_id=query.workspace_id,
            query_vector=query_vector,
            limit=query.limit,
            allowed_chunk_ids=allowed_chunk_ids,
        )
        return raw_results

    async def keyword_search(
        self,
        db_session: AsyncSession,
        query: RetrievalQuery,
        allowed_chunk_ids: list[UUID],
    ) -> list[tuple[UUID, float]]:
        """
        Execute full-text keyword search using SQLite FTS5.
        """
        if not allowed_chunk_ids:
            return []

        sanitized = self._sanitize_fts_query(query.query_text)
        if not sanitized:
            return []

        # Format chunk UUID string array for SQL IN query parameter mapping
        allowed_str_ids = [str(uid) for uid in allowed_chunk_ids]

        # SQLite FTS5 matches query and sorts by relevance (-bm25 score is positive, higher is better)
        sql_query = (
            "SELECT chunk_id, -bm25(document_chunks_fts) AS score "
            "FROM document_chunks_fts "
            "WHERE document_chunks_fts MATCH :search_query "
            "AND chunk_id IN :allowed_ids "
            "LIMIT :limit"
        )

        try:
            stmt = text(sql_query).bindparams(bindparam("allowed_ids", expanding=True))
            result = await db_session.execute(
                stmt,
                {
                    "search_query": sanitized,
                    "allowed_ids": allowed_str_ids,
                    "limit": query.limit,
                },
            )
            rows = result.all()
            return [(UUID(row[0]), float(row[1])) for row in rows]
        except Exception as e:
            # Degrade gracefully if virtual tables are not initialized or supported in current session binder
            logger.warning(f"Keyword FTS5 search bypassed or failed: {e}")
            return []
