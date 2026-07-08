"""
Unit tests for ChunkingService.
"""

from uuid import uuid4

from app.application.services.chunking_service import ChunkingService
from app.domain.entities.document import Document, DocumentType
from app.domain.value_objects.fiscal_period import FiscalPeriod


def test_chunk_document_basic():
    doc = Document(
        id=uuid4(),
        workspace_id=uuid4(),
        company_id=uuid4(),
        doc_type=DocumentType.TEN_K,
        fiscal_period=FiscalPeriod("FY", 2024),
        storage_path="path/to/filing.pdf",
        uploaded_by=uuid4(),
    )

    pages = [
        "Item 1. Business Description\n\nThis is paragraph one of the business details.",
        "Item 2. Properties\n\nThis is paragraph two on properties. \n\nItem 3. Legal Proceedings\n\nNo legal issues.",
    ]

    chunker = ChunkingService(chunk_size=500, overlap=50)
    chunks = chunker.chunk_document(doc, pages)

    assert len(chunks) > 0
    # Check sequential indexes
    for idx, chunk in enumerate(chunks):
        assert chunk.chunk_index == idx
        assert chunk.document_id == doc.id

    # Check header tracking
    assert chunks[0].section_heading == "Item 1. Business Description"


def test_chunk_document_large_paragraph_sentence_splitting():
    doc = Document(
        id=uuid4(),
        workspace_id=uuid4(),
        company_id=uuid4(),
        doc_type=DocumentType.TEN_K,
        fiscal_period=FiscalPeriod("FY", 2024),
        storage_path="path/to/filing.pdf",
        uploaded_by=uuid4(),
    )

    # Large contiguous paragraph exceeding chunk size of 100
    large_paragraph = (
        "This is sentence one. "
        "This is sentence two which has some details. "
        "This is sentence three with more content."
    )
    pages = [large_paragraph]

    # Max size 100 will force sentence splitting
    chunker = ChunkingService(chunk_size=100, overlap=20)
    chunks = chunker.chunk_document(doc, pages)

    assert len(chunks) >= 2
    # Verify contents have sentences
    for chunk in chunks:
        assert len(chunk.content) <= 120  # Max size + small buffer
