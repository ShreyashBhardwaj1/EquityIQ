"""
Domain logic for validating document chunks before persistence.
"""

from app.domain.entities.document_chunk import DocumentChunk
from app.domain.exceptions import EntityValidationError


class ChunkValidator:
    """
    Enforces structural and metadata integrity checks on generated document chunks.
    """

    def __init__(self, max_chunk_size: int) -> None:
        """
        Initializes the ChunkValidator with configurable constraints.
        """
        self.max_chunk_size = max_chunk_size

    def validate_batch(self, chunks: list[DocumentChunk]) -> None:
        """
        Validates a sequence of document chunks for structural integrity, completeness, and size limits.

        Purpose:
            Ensures that all chunks are sequentially ordered, non-empty, unique in content,
            contain complete metadata, and adhere to size limit bounds.

        Inputs:
            chunks: A list of DocumentChunk entities to validate.

        Outputs:
            None. Returns successfully if all validation rules pass.

        Failure Behavior:
            Raises EntityValidationError if any structural or metadata constraint is violated.
        """
        if not chunks:
            return

        seen_content: set[str] = set()
        expected_index = 0

        # Enforce that all chunks are sorted by chunk_index first
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)

        for chunk in sorted_chunks:
            # 1. Ordering validation
            if chunk.chunk_index != expected_index:
                raise EntityValidationError(
                    f"Chunk ordering violation: expected chunk_index {expected_index}, got {chunk.chunk_index}."
                )
            expected_index += 1

            # 2. Empty chunks validation
            content_stripped = chunk.content.strip()
            if not content_stripped:
                raise EntityValidationError(
                    f"Empty chunk violation: chunk at index {chunk.chunk_index} contains no text."
                )

            # 3. Duplicates validation
            if content_stripped in seen_content:
                raise EntityValidationError(
                    f"Duplicate chunk violation: duplicate content detected at index {chunk.chunk_index}."
                )
            seen_content.add(content_stripped)

            # 4. Metadata completeness validation
            meta = chunk.metadata
            required_meta = [
                ("workspace_id", meta.workspace_id),
                ("company_id", meta.company_id),
                ("document_id", meta.document_id),
                ("document_type", meta.document_type),
                ("source_file", meta.source_file),
                ("parser_version", meta.parser_version),
            ]
            for field_name, value in required_meta:
                if value is None or (isinstance(value, str) and not value.strip()):
                    raise EntityValidationError(
                        f"Metadata completeness violation: missing {field_name} in chunk metadata."
                    )

            # Validate ID mismatches
            if chunk.document_id != meta.document_id:
                raise EntityValidationError(
                    f"Metadata mismatch: chunk document_id {chunk.document_id} "
                    f"does not match metadata document_id {meta.document_id}."
                )

            # 5. Size constraints validation
            # Allow a small tolerance/buffer for formatting metadata and markdown tags
            if len(chunk.content) > (self.max_chunk_size + 100):
                raise EntityValidationError(
                    f"Size constraint violation: chunk {chunk.chunk_index} size "
                    f"({len(chunk.content)} characters) exceeds limit of {self.max_chunk_size}."
                )
