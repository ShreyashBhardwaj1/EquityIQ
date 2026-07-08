# GitHub Release Assets: v0.7.0-document-intelligence

## Release Title
EquityIQ v0.7.0 — Document Intelligence Pipeline & Async Parser Workers

## Executive Summary
This release establishes the deterministic Document Intelligence Pipeline, introducing background layout-aware document ingestion and processing workflows. Filings (PDF, TXT, CSV) are parsed page-by-page, with layout tables formatted to Markdown, segmenting text into semantic paragraphs and validating constraints before batch persistence. The pipeline is executed asynchronously utilizing Celery background tasks and Redis queues.

---

## Architecture Highlights
*   **Decoupled Parsers**: PDF extraction is encapsulated behind a clean, framework-independent parser interface utilizing `pdfplumber` and optional `pytesseract` OCR fallbacks.
*   **Stable Chunk Identities**: Chunk UUIDs are generated deterministically using `uuid.uuid5` scoped by the parent document ID. Reprocessing same contents yields identical IDs, preventing index fragmentation.
*   **Extensible Batch Validation**: Deployed validation engine check guards to verify chunk sequences, unique contents, metadata completeness, and maximum size limits.
*   **Asynchronous Processing**: Background Celery worker tasks isolate resource-intensive layout parsing and chunk extraction from web server requests.

---

## What's New
*   **PDF Parsing**: Layout preservation and Markdown formatting of tables.
*   **Plain-Text / Corrupted Fallback**: Graceful fallback to raw text extraction if the PDF is corrupt or has a non-pdf extension.
*   **Extensible Validator**: Structural ordering, duplicate text, empty content, and metadata validations.
*   **Async Operations**: Dispatched task pipelines under Celery background workers.
*   **API Routes**: Dedicated endpoints for parsing, re-runs, and listing scoping.

---

## Engineering Metrics
*   **Verification Status**: 70 tests passing (100% green).
*   **MyPy Validation**: Checked 108 source files with zero errors.
*   **Ruff Quality**: Clean lints and formatting (108 files formatted).
*   **Import Contracts**: Domain layer remains completely clean (0 architecture contract violations).

---

## Lessons Learned
1.  **Event Loop Conflicts under Test Eager Runs**: Re-evaluating `loop.run_until_complete` calls during eager Celery runs under FastAPI request event loops. Resolved via a thread-spawning runner fallback.
2.  **Strict PDF Parsers**: PDF metadata checks in `pdfplumber` reject plain text strings; resolved by building defensive fallback reads.

---

## Breaking Changes
*   None. Backward compatibility has been fully preserved.

## Upgrade Notes
*   Ensure Redis is running (`redis://localhost:6379/0`) before starting backend celery workers.
*   Start the celery worker pool with:
    ```bash
    celery -A app.workers.celery_app.celery_app worker --loglevel=info
    ```
*   Optional: Install `pytesseract` and the Tesseract OCR system binary locally to enable OCR fallback on scanned documents.

---

## Repository Status
*   **Milestones Completed**: 7 / 10 (70% Completion).
*   **Status**: Frozen at version `v0.7.0-document-intelligence`.

## What's Next (Milestone 6)
*   **Objective**: Vector Storage Pipeline & Hybrid Search Retrieval. Incorporate `Sentence-Transformers` local embedding generation and `FAISS-cpu` self-hosted vector indexing.
