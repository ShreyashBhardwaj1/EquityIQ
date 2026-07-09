"""
ContextAssembler application service.
"""

from uuid import UUID

from app.domain.entities.document_chunk import DocumentChunk
from app.domain.entities.retrieval import RetrievalResult
from app.domain.interfaces.repositories import ChunkRepository


class MergedContextChunk:
    """
    Represents a merged or single chunk context block prepared for the prompt.
    """

    def __init__(
        self,
        chunk_ids: list[UUID],
        document_id: UUID,
        document_name: str,
        start_page: int,
        end_page: int,
        section_heading: str | None,
        content: str,
        max_score: float,
        retrieval_method: str = "hybrid",
        rank: int = 1,
        semantic_score: float | None = None,
        keyword_score: float | None = None,
        hybrid_score: float = 0.0,
    ) -> None:
        self.chunk_ids = chunk_ids
        self.document_id = document_id
        self.document_name = document_name
        self.start_page = start_page
        self.end_page = end_page
        self.section_heading = section_heading
        self.content = content
        self.max_score = max_score
        self.retrieval_method = retrieval_method
        self.rank = rank
        self.semantic_score = semantic_score
        self.keyword_score = keyword_score
        self.hybrid_score = hybrid_score


class ContextAssembler:
    """
    Deduplicates, groups, and merge consecutive adjacent chunks belonging to the same
    document and section to reduce prompt noise, formatting them into XML bounds.
    """

    def __init__(self, chunk_repo: ChunkRepository) -> None:
        self.chunk_repo = chunk_repo

    async def assemble_context(
        self, retrieval_results: list[RetrievalResult]
    ) -> tuple[str, list[MergedContextChunk]]:
        """
        Deduplicates, merges adjacent consecutive chunks, and formats the output XML string.
        """
        if not retrieval_results:
            return "", []

        # Step 1: Deduplicate by chunk_id
        seen: set[UUID] = set()
        unique_results: list[RetrievalResult] = []
        for res in retrieval_results:
            if res.chunk_id not in seen:
                seen.add(res.chunk_id)
                unique_results.append(res)

        # Step 2: Fetch full DocumentChunks to get chunk_index and source_file metadata
        chunks_map: dict[UUID, DocumentChunk] = {}
        for r in unique_results:
            chunk_detail = await self.chunk_repo.get(r.chunk_id)
            if chunk_detail:
                chunks_map[r.chunk_id] = chunk_detail

        # Create lookup for score and method
        scores_map = {res.chunk_id: res.score for res in unique_results}
        methods_map = {
            res.chunk_id: res.metadata.get("retrieval_method", "hybrid")
            for res in unique_results
        }
        ranks_map = {
            res.chunk_id: res.metadata.get("rank", 1) for res in unique_results
        }
        semantic_scores_map = {
            res.chunk_id: res.metadata.get("semantic_score", None)
            for res in unique_results
        }
        keyword_scores_map = {
            res.chunk_id: res.metadata.get("keyword_score", None)
            for res in unique_results
        }
        hybrid_scores_map = {
            res.chunk_id: res.metadata.get("hybrid_score", 0.0)
            for res in unique_results
        }

        # Step 3: Sort chunks by document_id and chunk_index to prepare for adjacency merging
        valid_chunk_details = [
            chunks_map[cid] for cid in chunks_map if cid in chunks_map
        ]
        valid_chunk_details.sort(key=lambda x: (x.document_id, x.chunk_index))

        # Step 4: Merge adjacent chunks
        merged_chunks: list[MergedContextChunk] = []

        for chunk in valid_chunk_details:
            score = scores_map.get(chunk.id, 0.0)
            method = methods_map.get(chunk.id, "hybrid")
            rank = ranks_map.get(chunk.id, 1)
            sem_score = semantic_scores_map.get(chunk.id, None)
            key_score = keyword_scores_map.get(chunk.id, None)
            hyb_score = hybrid_scores_map.get(chunk.id, 0.0)

            doc_name = (
                chunk.metadata.source_file
                if chunk.metadata and chunk.metadata.source_file
                else "Unknown"
            )

            if not merged_chunks:
                # Add first chunk
                merged_chunks.append(
                    MergedContextChunk(
                        chunk_ids=[chunk.id],
                        document_id=chunk.document_id,
                        document_name=doc_name,
                        start_page=chunk.page_number,
                        end_page=chunk.page_number,
                        section_heading=chunk.section_heading,
                        content=chunk.content.strip(),
                        max_score=score,
                        retrieval_method=method,
                        rank=rank,
                        semantic_score=sem_score,
                        keyword_score=key_score,
                        hybrid_score=hyb_score,
                    )
                )
                continue

            last = merged_chunks[-1]
            last_chunk_id = last.chunk_ids[-1]
            last_chunk_detail = chunks_map[last_chunk_id]

            is_same_doc = chunk.document_id == last.document_id
            is_consecutive = chunk.chunk_index == last_chunk_detail.chunk_index + 1
            is_same_section = chunk.section_heading == last.section_heading

            if is_same_doc and is_consecutive and is_same_section:
                # Merge current chunk into the last merged block
                last.chunk_ids.append(chunk.id)
                last.end_page = max(last.end_page, chunk.page_number)
                last.content += "\n\n" + chunk.content.strip()
                last.max_score = max(last.max_score, score)
                last.rank = min(last.rank, rank)
                if sem_score is not None:
                    last.semantic_score = max(last.semantic_score or 0.0, sem_score)
                if key_score is not None:
                    last.keyword_score = max(last.keyword_score or 0.0, key_score)
                last.hybrid_score = max(last.hybrid_score, hyb_score)
            else:
                # Add as a new merged block
                merged_chunks.append(
                    MergedContextChunk(
                        chunk_ids=[chunk.id],
                        document_id=chunk.document_id,
                        document_name=doc_name,
                        start_page=chunk.page_number,
                        end_page=chunk.page_number,
                        section_heading=chunk.section_heading,
                        content=chunk.content.strip(),
                        max_score=score,
                        retrieval_method=method,
                        rank=rank,
                        semantic_score=sem_score,
                        keyword_score=key_score,
                        hybrid_score=hyb_score,
                    )
                )

        # Step 5: Format context into structured XML blocks with metadata attributes
        # Assign short sequential labels (e.g. Chunk 1, Chunk 2) for prompt context mapping
        lines = ["<retrieved_context>"]
        for idx, mc in enumerate(merged_chunks, 1):
            sec_attr = f' section="{mc.section_heading}"' if mc.section_heading else ""
            lines.append(
                f'<chunk id="Chunk {idx}" document="{mc.document_name}" '
                f'page="{mc.start_page}-{mc.end_page}"{sec_attr} '
                f'score="{mc.max_score:.4f}" method="{mc.retrieval_method}">'
            )
            lines.append(mc.content)
            lines.append("</chunk>")
        lines.append("</retrieved_context>")

        return "\n".join(lines), merged_chunks
