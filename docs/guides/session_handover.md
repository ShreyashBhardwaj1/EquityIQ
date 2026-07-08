# Session Handover: Milestone 6 to Milestone 7

## 1. Current Repository State
*   **Version Tag**: `v0.8.0-vector-storage-hybrid-search`
*   **Status**: Stable, verified, reformatted, and type-checked.
*   **Test Suite**: 72 tests passing with clean coverage.
*   **Linter & Formatter**: Ruff checks passed, 124 backend files formatted.
*   **MyPy**: Success (0 issues found across 124 source files).
*   **Import Linter**: Domain boundary kept (1 contract kept, 0 broken).

## 2. Completed Work (Milestone 6)
*   **Local Embeddings**: Implemented `SentenceTransformerAdapter` leveraging Hugging Face's `all-MiniLM-L6-v2` locally (384 dimensions).
*   **Vector Database Store**: Implemented `FaissVectorStore` (flat Inner Product) for Cosine Similarity. Segregates files by versioned workspace directories on disk: `storage/indices/v1/workspace_{id}/index.bin`.
*   **Database-Assisted Pre-filtering**: Leveraged `faiss.IDSelectorBatch` to pre-filter FAISS queries using UUIDs resolved from SQLite metadata queries, ensuring 100% tenant workspace boundary isolation.
*   **SQLite FTS5 Keyword Matching**: Created SQLite virtual table `document_chunks_fts USING fts5(content, chunk_id UNINDEXED)` and synchronized database insertions/deletions automatically via repository hooks.
*   **Hybrid Rank Fusion**: Normalizes similarity and BM25 scores using Min-Max scaling, combining them linearly: `alpha * semantic + (1 - alpha) * keyword`.
*   **API routes**:
    *   `POST /search/semantic`
    *   `POST /search/hybrid`
    *   `POST /search/rebuild` (manually rebuilds workspace FAISS index from DB)
*   **Worker Pipeline Sync**: Celery parsing task automatically builds/updates FAISS vector indexes when document parsing finishes.

## 3. Starting Point for Milestone 7
Tomorrow's goal is **Milestone 7 — LLM Integration & Retrieval-Augmented Generation (RAG)**.
*   **Scope**:
    1.  Integrate LLM providers (e.g. Google Gemini API, OpenAI, or local execution blocks) with replaceable adapter interfaces.
    2.  Implement prompt template builders for question answering and analysis.
    3.  Implement prompt-injection sanitization filters to prevent prompt hacking.
    4.  Implement retrieval-augmented research agent querying the hybrid search index and generating context-enriched report fragments.
*   **Dependencies to build**:
    *   `LLMProvider` interface protocol.
    *   LLM concrete infrastructure adapters.
    *   `ResearchService` or `RagService` orchestrating retrieval context assembly and query generation.

## 4. Key Assumptions
*   **API Keys**: Staged environment secrets (like `GEMINI_API_KEY`) will be populated via `.env` file configuration.
*   **FAISS Vector Index**: The self-hosted local FAISS vector index remains disk-backed per workspace and is sufficient for retrieval tasks.

## 5. Technical Debt Register
1.  **`datetime.utcnow()` Deprecations**: Hashing, database mapping, and index building layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+.
2.  **Local Storage Directory**: Chunks, uploaded documents, and FAISS index files are currently saved in local directories (`storage/uploads` and `storage/indices`). In production, this requires migrating to cloud storage adapters (like AWS S3).
3.  **OCR Fallback Warning Logging**: Console logs warning alerts when pytesseract/Tesseract is missing. This is normal and expected on standard local machines.

## 6. Critical Engineering Notes
*   **aiosqlite Expanding Parameters**: In raw SQL executed via SQLAlchemy `session.execute(text(...))`, executing list comparisons like `IN :allowed_ids` in SQLite requires wrapping the SQL statement with `bindparam("allowed_ids", expanding=True)`.
*   **MyPy FAISS SWIG Wrapper**: The SWIG wrapper for FAISS Python stubs does not define constructor keyword arguments for `faiss.SearchParameters`. To satisfy MyPy, instantiate the parameters class empty and assign attributes directly (e.g., `params.sel = selector`).
