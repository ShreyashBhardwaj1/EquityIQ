"""
ConfidenceScorer application service.
"""

from uuid import UUID

from app.application.services.context_assembler import MergedContextChunk
from app.domain.entities.retrieval import RetrievalResult


class ConfidenceScorer:
    """
    Computes a deterministic confidence score [0.0 - 1.0] for a RAG response
    based on retrieval similarity, citation density, coverage, and chunk agreement.
    No LLM calls are used.
    """

    def __init__(
        self,
        w_similarity: float = 0.30,
        w_density: float = 0.30,
        w_coverage: float = 0.20,
        w_agreement: float = 0.20,
    ) -> None:
        self.w_similarity = w_similarity
        self.w_density = w_density
        self.w_coverage = w_coverage
        self.w_agreement = w_agreement

    def calculate_score(
        self,
        retrieval_results: list[RetrievalResult],
        merged_chunks: list[MergedContextChunk],
        cited_chunk_ids: list[UUID],
    ) -> float:
        """
        Calculate the deterministic confidence score.
        """
        if not retrieval_results:
            return 0.0

        # 1. Similarity Component (Max score)
        max_similarity = max((res.score for res in retrieval_results), default=0.0)
        similarity_score = min(1.0, max(0.0, max_similarity))

        # 2. Citation Density (Cited unique chunks / Total unique chunks retrieved)
        total_chunks_retrieved = len(retrieval_results)
        unique_cited = len(set(cited_chunk_ids))
        density_score = (
            unique_cited / total_chunks_retrieved if total_chunks_retrieved > 0 else 0.0
        )

        # 3. Retrieval Coverage (Number of chunks retrieved vs default target of 8)
        coverage_score = min(1.0, total_chunks_retrieved / 8.0)

        # 4. Chunk Agreement (Inverse of unique document sources)
        unique_docs = {
            res.metadata.get("document_id")
            for res in retrieval_results
            if res.metadata and res.metadata.get("document_id")
        }
        agreement_score = 1.0 / len(unique_docs) if unique_docs else 1.0

        final_score = (
            self.w_similarity * similarity_score
            + self.w_density * density_score
            + self.w_coverage * coverage_score
            + self.w_agreement * agreement_score
        )

        return min(1.0, max(0.0, final_score))

    def calculate_grounding_score(self, response_text: str) -> float:
        """
        Calculate a deterministic grounding score based on citation coverage across response sentences.
        """
        if not response_text:
            return 0.0

        import re

        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", response_text) if s.strip()
        ]
        if not sentences:
            return 0.0

        citation_pattern = re.compile(r"\[Chunk\s+(\d+)\]", re.IGNORECASE)
        cited_count = 0
        for sentence in sentences:
            if citation_pattern.search(sentence):
                cited_count += 1

        return cited_count / len(sentences)
