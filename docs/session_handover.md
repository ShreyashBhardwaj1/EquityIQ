# Session Handover: Milestone 5 to Milestone 6

## 1. Current Repository State
*   **Version Tag**: `v0.7.0-document-intelligence`
*   **Status**: Stable, green, reformatted, and type-checked.
*   **Test Suite**: 70 tests passing with coverage.
*   **Linter & Formatter**: Ruff checks passed, 108 backend files reformatted.
*   **MyPy**: Success (0 issues found across 108 files).
*   **Import Linter**: Domain boundary kept (0 contracts broken).

## 2. Completed Work (Milestone 5)
*   **PDF Ingestion & Layout Parsing**: Built `PDFParser` in `pdf_parser.py` using `pdfplumber` to extract native text per page and convert tables to clean Markdown format.
*   **OCR Graceful Fallback**: Traps pytesseract import or executable binary exceptions, writing warnings to database parsing manifests instead of failing parsing attempts.
*   **Plain-Text Fallback**: Ingests raw text directly if the document is not a PDF or if the PDF binary structure is corrupt.
*   **Paragraph Chunker**: Splits raw pages into paragraphs/sentences based on configured size and overlap limits, tracking active section headers.
*   **Stable Chunk Identities**: Engineered deterministic UUIDs via `uuid.uuid5` utilizing the parent `document.id` as the namespace and `chunk_index` as the name.
*   **Extensible Chunk Validation**: Deployed `ChunkValidator` checking batch ordering, empty chunks, duplicates, metadata completeness, and size limit checks before database writes.
*   **Celery Worker Integration**: Orchestrated parsing as an asynchronous background worker pipeline, including dynamic status transitions (`PENDING` -> `PROCESSING` -> `COMPLETED`/`FAILED`).
*   **API Routes**:
    *   `POST /documents/{id}/parse` (queue background parse)
    *   `POST /documents/{id}/reprocess` (queue reprocess and increment `parse_version`)
    *   `GET /documents/{id}/chunks` (fetch chunks with workspace scoping)

## 3. Starting Point for Milestone 6
Tomorrow's goal is **Milestone 6 — Vector Storage Pipeline & Hybrid Search Retrieval**.
*   **Scope**:
    1.  Design/integrate local embedding generator services (such as Hugging Face `Sentence-Transformers`).
    2.  Integrate local FAISS database adapters for self-hosted dense vectors.
    3.  Develop index persistence and workspace isolation rules for the vector store.
    4.  Implement a hybrid search resolver combining dense vector search and keyword search (BM25 or text database filtering) with workspace filtering.

## 4. Key Assumptions
*   **In-Memory FAISS Vector Store**: We assume a self-hosted local FAISS vector store is sufficient for development/testing stages, matching the constructor-injected interface pattern.
*   **Celery Configuration**: Development tasks run eagerly on a separate worker thread within integration tests, but will run on a separate container queue in staging/production setups.

## 5. Technical Debt Register
1.  **`datetime.utcnow()` Deprecations**: Hashing and database mapping layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+.
2.  **Local Storage Directory**: Documents are currently uploaded to local disk storage (`storage/uploads`). Production will require cloud block storage (e.g. AWS S3).
3.  **OCR Fallback Warning Logging**: Pytesseract logs standard console warnings when the system lacks a local Tesseract binary. This is standard behavior.
