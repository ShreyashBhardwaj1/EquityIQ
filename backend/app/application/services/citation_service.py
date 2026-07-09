"""
CitationService application service.
"""

import logging
import re
import uuid
from uuid import UUID

from app.application.services.context_assembler import MergedContextChunk
from app.domain.entities.conversation import Citation

logger = logging.getLogger("equityiq.application.citation_service")


class CitationService:
    """
    Parses citation tags (e.g. '[Chunk X]') from LLM response text and maps them back to
    source document metadata and chunk identifiers.
    """

    def __init__(self) -> None:
        self.citation_pattern = re.compile(r"\[Chunk\s+(\d+)\]", re.IGNORECASE)

    def extract_citations(
        self,
        response_text: str,
        message_id: UUID,
        merged_chunks: list[MergedContextChunk],
    ) -> list[Citation]:
        """
        Parses response text and returns a list of domain Citation entities.
        """
        citations: list[Citation] = []
        matches = self.citation_pattern.findall(response_text)

        # Deduplicate referenced indexes to avoid redundant citations
        unique_indexes = sorted({int(m) for m in matches})

        for idx in unique_indexes:
            list_idx = idx - 1
            if 0 <= list_idx < len(merged_chunks):
                mc = merged_chunks[list_idx]
                primary_chunk_id = mc.chunk_ids[0] if mc.chunk_ids else None

                citations.append(
                    Citation(
                        id=uuid.uuid4(),
                        message_id=message_id,
                        chunk_id=primary_chunk_id,
                        document_id=mc.document_id,
                        document_name=mc.document_name,
                        page_number=mc.start_page,
                        section_heading=mc.section_heading,
                        snippet_preview=mc.content[:200].strip()
                        + ("..." if len(mc.content) > 200 else ""),
                        score=mc.max_score,
                        rank=mc.rank,
                        semantic_score=mc.semantic_score,
                        keyword_score=mc.keyword_score,
                        hybrid_score=mc.hybrid_score,
                        retrieval_method=mc.retrieval_method,
                    )
                )

        return citations
