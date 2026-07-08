# Engineering Journal: Day 5 — Vector Storage & Hybrid Search Retrieval

## 1. Summary
Today was dedicated to implementing **Milestone 6 — Vector Storage Pipeline & Hybrid Search Retrieval**. We successfully integrated a local SentenceTransformers embedding generator, built a disk-backed FAISS vector store database adapter with strict database-assisted pre-filtering, engineered a synchronized SQLite FTS5 full-text keyword engine, normalizer utility, linear combine hybrid rank combiner, and exposed them via REST API retrieval endpoints.

---

## 2. Major Accomplishments
*   **Hugging Face local Embeddings**: Deployed `SentenceTransformerAdapter` running the `all-MiniLM-L6-v2` model locally on CPU to embed chunks and search queries without external dependencies.
*   **FAISS Vector Index**: Implemented memory-cached flat inner-product `IndexFlatIP` indices on disk isolated per workspace (`storage/indices/v1/workspace_{id}/index.bin`).
*   **Database-Assisted Pre-filtering**: Utilized SQL queries to pre-resolve chunk UUIDs matching metadata constraints (fiscal period, year, sector, document type) and filtered FAISS similarity calculations using native `faiss.IDSelectorBatch` to guarantee 100% strict workspace isolation.
*   **SQLite FTS5 Matching**: Integrated virtual table `document_chunks_fts USING fts5` inside Alembic migrations and added automatic synchronizers in the chunk repository to keep the virtual index up to date.
*   **Linear Rank Fusion**: Normalised search scores using Min-Max scaling, combining semantic and keyword results using a weighted linear combination:
    $$\text{Score}_{\text{hybrid}} = \alpha \cdot \text{Score}_{\text{semantic}} + (1 - \alpha) \cdot \text{Score}_{\text{keyword}}$$
*   **API Routes Deployed**: Added `/search/semantic`, `/search/hybrid`, and `/search/rebuild` API routes.
*   ** Celery Pipeline Integration**: Configured long-running parsing worker tasks to automatically run a workspace vector rebuild and generate dense embeddings on successfully parsed documents.

---

## 3. Architectural Decisions
*   **100% Strict Pre-filtering**: Chose database pre-filtering rather than post-filtering vector search results. Post-filtering vector search results is vulnerable to returning fewer items than requested (or empty sets) if top similarity vectors belong to a different workspace. Pre-filtering ensures exact top-K results are returned from the permitted workspace boundaries.
*   **Decoupled Vector DB Adapter Pattern**: Placed FAISS index logic entirely behind the `VectorStore` repository protocol interface. This makes it trivial to replace FAISS with cloud vector databases (like Pinecone, Qdrant, Chroma, or pgvector) in the future without modifying any application search or parsing code.
*   **Min-Max Scaling Normalization**: Chose Min-Max scaling to map raw BM25 scores (arbitrary positive floats) and cosine similarity scores (range $[0, 1]$) to a shared scale before rank fusion, preventing BM25 scores from dominating the weighted combination.

---

## 4. Problems Solved
*   **aiosqlite Bind Parameter Syntax Error**: SQLite fails to bind tuple parameters in raw text SQL queries (e.g., `chunk_id IN ?` causes a syntax error). Solved by using SQLAlchemy's `bindparam("allowed_ids", expanding=True)` compilation helper, which expands parameters dynamically to multiple binding tokens.
*   **MyPy SWIG keyword limitations**: MyPy flags SWIG-generated FAISS parameter constructors as unexpected keyword argument errors (`sel` keyword argument). Solved by instantiating `faiss.SearchParameters` empty and setting properties on the object dynamically (`params.sel = selector`).
*   **Schema Mismatch**: Declarative `Base` adds `updated_at` and `deleted_at` columns automatically. The migration script was updated to ensure both `embeddings` and `embedding_manifests` tables create these columns, preventing SQL lookup errors during DB sessions.

---

## 5. Lessons Learned
*   **SQLite FTS5 limitations**: FTS5 virtual tables act as separate tables without standard foreign key constraint checks. Keeping FTS5 in sync requires explicit writes on insert and delete stages in the main repository code.
*   **SWIG Wrappers Typing constraints**: C/C++ Python bindings (like FAISS) can have gaps in type definitions, requiring object property assignment fallbacks to maintain MyPy compliance.

---

## 6. Future Considerations
*   **Embedding Batching Tuning**: When uploading multi-hundred page documents, batch sizes and CPU core bounds must be managed to prevent memory overflows or Celery worker timeouts.
*   **Adjusting Alpha Weight**: Staging runs must tune the $\alpha$ parameter (default `0.70`) based on actual filing structure formats to balance semantic matches vs precise ticker keyword hits.

---

## 7. Personal Engineering Observations
Wrote a complete integration test suite in `test_search_api.py` that verifies the entire upload $\rightarrow$ Celery parse $\rightarrow$ embed $\rightarrow$ index $\rightarrow$ hybrid search cycle. Setting Celery eager execution mode enabled synchronous in-memory flow checks that make integration testing incredibly fast and predictable.
