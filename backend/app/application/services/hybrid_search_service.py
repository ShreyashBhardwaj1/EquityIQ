"""
HybridSearchService application service.
"""

import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.retrieval_service import RetrievalService
from app.domain.entities.retrieval import RetrievalQuery, RetrievalResult
from app.domain.interfaces.repositories import ChunkRepository

logger = logging.getLogger("equityiq.application.hybrid_search_service")


class HybridSearchService:
    """
    Orchestrates combined semantic + keyword search workflows and normalizes scores.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        chunk_repo: ChunkRepository,
    ) -> None:
        """
        Initialize with dependencies.
        """
        self.retrieval_service = retrieval_service
        self.chunk_repo = chunk_repo
        self.metrics_log: list[dict[str, Any]] = []  # Monitoring hook list

    def _normalize_scores(self, results: list[tuple[UUID, float]]) -> dict[UUID, float]:
        """
        Scale search scores to a [0.0, 1.0] range using min-max scaling.
        """
        if not results:
            return {}
        scores = [score for _, score in results]
        min_score = min(scores)
        max_score = max(scores)
        diff = max_score - min_score

        if diff == 0.0:
            return {uid: 1.0 for uid, _ in results}

        return {uid: (score - min_score) / diff for uid, score in results}

    async def search(
        self,
        db_session: AsyncSession,
        query: RetrievalQuery,
        alpha: float = 0.70,
    ) -> list[RetrievalResult]:
        """
        Execute hybrid search merging vector similarity search and keyword FTS5.
        """
        start_time = time.perf_counter()

        # Step 1: Pre-filter chunks by metadata scopes
        allowed_ids = await self.retrieval_service.list_allowed_chunk_ids(query)
        if not allowed_ids:
            return []

        # Step 2: Run semantic similarity search
        semantic_results = await self.retrieval_service.semantic_search(
            query, allowed_ids
        )

        # Step 3: Run SQLite FTS5 keyword search
        keyword_results = await self.retrieval_service.keyword_search(
            db_session, query, allowed_ids
        )

        # Step 4: Normalize scores to [0.0, 1.0] before fusion
        norm_sem = self._normalize_scores(semantic_results)
        norm_key = self._normalize_scores(keyword_results)

        # Step 5: Merge scores using linear combination
        all_candidate_ids = set(norm_sem.keys()) | set(norm_key.keys())
        merged_scores: list[tuple[UUID, float]] = []

        for cid in all_candidate_ids:
            sem_score = norm_sem.get(cid, 0.0)
            key_score = norm_key.get(cid, 0.0)
            hybrid_score = alpha * sem_score + (1.0 - alpha) * key_score
            merged_scores.append((cid, hybrid_score))

        # Sort descending by combined scores and slice limit
        merged_scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates = merged_scores[query.offset : query.offset + query.limit]

        # Step 6: Load chunk texts and metadata details
        results = []
        for idx, (cid, score) in enumerate(top_candidates, 1):
            chunk = await self.chunk_repo.get(cid)
            if chunk:
                retrieved_sem_score = norm_sem.get(cid, None)
                retrieved_key_score = norm_key.get(cid, None)
                if cid in norm_sem and cid in norm_key:
                    method = "hybrid"
                elif cid in norm_sem:
                    method = "semantic"
                else:
                    method = "keyword"

                # Package domain result
                results.append(
                    RetrievalResult(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        score=score,
                        page_number=chunk.page_number,
                        section_heading=chunk.section_heading,
                        metadata={
                            "workspace_id": str(chunk.metadata.workspace_id),
                            "company_id": str(chunk.metadata.company_id),
                            "document_id": str(chunk.metadata.document_id),
                            "document_type": chunk.metadata.document_type,
                            "statement_type": chunk.metadata.statement_type,
                            "fiscal_year": chunk.metadata.fiscal_year,
                            "fiscal_period": chunk.metadata.fiscal_period,
                            "rank": idx,
                            "semantic_score": retrieved_sem_score,
                            "keyword_score": retrieved_key_score,
                            "hybrid_score": score,
                            "retrieval_method": method,
                        },
                    )
                )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 7: Log retrieval metrics for future monitoring hooks
        metric_entry = {
            "query_text": query.query_text,
            "workspace_id": str(query.workspace_id),
            "semantic_count": len(semantic_results),
            "keyword_count": len(keyword_results),
            "merged_count": len(results),
            "alpha_weight": alpha,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
        }
        self.metrics_log.append(metric_entry)
        logger.info(
            f"Hybrid search completed in {duration_ms:.2f}ms. "
            f"Semantic matches: {len(semantic_results)}, Keyword matches: {len(keyword_results)}."
        )

        return results
