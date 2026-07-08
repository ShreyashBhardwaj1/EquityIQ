"""
Unit tests for ChunkValidator.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from app.domain.entities.document_chunk import ChunkMetadata, DocumentChunk
from app.domain.exceptions import EntityValidationError
from app.domain.rules.chunk_validation import ChunkValidator


def create_mock_metadata(chunk_index: int, page_number: int = 1) -> ChunkMetadata:
    return ChunkMetadata(
        workspace_id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=None,
        document_type="10K",
        fiscal_year=2025,
        fiscal_period="FY",
        page_number=page_number,
        chunk_index=chunk_index,
        section_heading="Item 7",
        source_file="filing.pdf",
        parser_version="1.0.0",
        document_version=1,
        parse_version=1,
        created_at=datetime.utcnow(),
    )


def test_validation_success():
    doc_id = uuid4()
    meta1 = create_mock_metadata(chunk_index=0)
    meta1 = meta1.model_copy(update={"document_id": doc_id})

    meta2 = create_mock_metadata(chunk_index=1)
    meta2 = meta2.model_copy(update={"document_id": doc_id})

    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="This is the first chunk.",
            page_number=1,
            chunk_index=0,
            section_heading="Item 7",
            metadata=meta1,
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="This is the second chunk.",
            page_number=1,
            chunk_index=1,
            section_heading="Item 7",
            metadata=meta2,
        ),
    ]

    validator = ChunkValidator(max_chunk_size=1000)
    # Should run without raising EntityValidationError
    validator.validate_batch(chunks)


def test_validation_ordering_error():
    doc_id = uuid4()
    meta1 = create_mock_metadata(chunk_index=0)
    meta1 = meta1.model_copy(update={"document_id": doc_id})

    meta2 = create_mock_metadata(chunk_index=2) # Gap here: index 2 instead of 1
    meta2 = meta2.model_copy(update={"document_id": doc_id})

    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="First chunk.",
            page_number=1,
            chunk_index=0,
            metadata=meta1,
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="Second chunk.",
            page_number=1,
            chunk_index=2,
            metadata=meta2,
        ),
    ]

    validator = ChunkValidator(max_chunk_size=1000)
    with pytest.raises(EntityValidationError, match="Chunk ordering violation"):
        validator.validate_batch(chunks)


def test_validation_empty_chunk():
    doc_id = uuid4()
    meta = create_mock_metadata(chunk_index=0)
    meta = meta.model_copy(update={"document_id": doc_id})

    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="    ",  # whitespace only
            page_number=1,
            chunk_index=0,
            metadata=meta,
        )
    ]

    validator = ChunkValidator(max_chunk_size=1000)
    with pytest.raises(EntityValidationError, match="Empty chunk violation"):
        validator.validate_batch(chunks)


def test_validation_duplicate_content():
    doc_id = uuid4()
    meta1 = create_mock_metadata(chunk_index=0)
    meta1 = meta1.model_copy(update={"document_id": doc_id})

    meta2 = create_mock_metadata(chunk_index=1)
    meta2 = meta2.model_copy(update={"document_id": doc_id})

    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="Identical content.",
            page_number=1,
            chunk_index=0,
            metadata=meta1,
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="Identical content.",
            page_number=1,
            chunk_index=1,
            metadata=meta2,
        ),
    ]

    validator = ChunkValidator(max_chunk_size=1000)
    with pytest.raises(EntityValidationError, match="Duplicate chunk violation"):
        validator.validate_batch(chunks)


def test_validation_size_constraint():
    doc_id = uuid4()
    meta = create_mock_metadata(chunk_index=0)
    meta = meta.model_copy(update={"document_id": doc_id})

    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            content="A" * 1500,  # exceeds max size of 500
            page_number=1,
            chunk_index=0,
            metadata=meta,
        )
    ]

    validator = ChunkValidator(max_chunk_size=500)
    with pytest.raises(EntityValidationError, match="Size constraint violation"):
        validator.validate_batch(chunks)
