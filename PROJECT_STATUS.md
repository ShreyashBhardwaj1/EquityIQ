# Project Status: EquityIQ

---

## 1. Project Specifications

*   **Current Version**: `v1.1.0-report-generation-streaming`
*   **Overall Progress**: **95% Completed** (9 / 10 Milestones completed)
*   **Test Count**: **133 tests passing**
*   **CI Validation State**: **Passing** — Ruff Lint, Ruff Format, MyPy (0 errors), and Import-Linter green

---

## 2. Milestone Board

### Completed Milestones
*   **Milestone 1**: Scaffolding & CI Pipeline Configuration (Ruff, MyPy, Pytest, Import-Linter)
*   **Milestone 2**: Domain Layer Modeling & Valuation Engine (Frozen Domain Entities)
*   **Milestone 3A**: Infrastructure Foundation (Database Manager, Health Services, JSON Logging)
*   **Milestone 3B**: Identity & Authentication Platform (Bcrypt Hasher, JWT Rotation, DB Revocation)
*   **Milestone 3C**: Workspace & Company Management (FastAPI Router + Row-Level Security Scoping)
*   **Milestone 4**: Financial Data Foundation (Metadata uploads, Extensible Validations, Normalization Mappings, Version Revisions)
*   **Milestone 5**: Document Intelligence Pipeline (Asynchronous Parser Workers, OCR fallback, Markdown tables, stable deterministic chunk identities via uuid5, and manifests tracking)
*   **Milestone 6**: Vector Storage Pipeline & Hybrid Search Retrieval (Local Hugging Face embeddings, FAISS CPU vector index, database-assisted pre-filtering, SQLite FTS5 keyword retrieval, min-max score normalization, and linear rank fusion)
*   **Milestone 7**: LLM Integration, Prompt-Injection Filters, Q&A Agent (RAG) (Gemini Pro/Flash integration, token budget managers, prompt injection guards, grounding scoring, explainable citations, and execution telemetry database tables)
*   **Milestone 8**: Financial Intelligence & Recommendation Engine (Config-driven Registry Ratio calculations, qualitative status categorization, Health Scoring, Risk evaluation, Policy-driven Recommendations, and consolidated Dashboard)
*   **Milestone 9**: Report Generation & Streaming Engine (Async LLM-synthesized reports grounded in Milestone 8 deterministic outputs, ReportContextAssembler, section-level anti-hallucination validators, SSE token streaming, Markdown/PDF/DOCX export, Celery async task, 5 REST endpoints)

### Upcoming Milestones
*   **Milestone 10**: Next.js UI Frontend Implementation (Phase 1: Authentication Complete)

---

## 3. Known Technical Debt

1. **`datetime.utcnow()` Deprecations (Minor)**: Hashing, database mapping, and index building layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+. Plan is to standardize on `datetime.now(timezone.utc)` post-v1.1.
2. **Local Storage Setup (Minor)**: Documents and FAISS index binary files are currently uploaded to local disk storage (`storage/uploads` and `storage/indices`). In production, this will require migration to cloud block storage (e.g., AWS S3 or GCP Cloud Storage) with a storage adapter interface.
3. **Eager Celery Thread Execution (Minor)**: Celery eager test runner runs synchronously on the same event loop, resolved using a dedicated thread-spawning runner fallback. In production, we must monitor background Celery worker performance and pool configurations under concurrent document loads.
4. **OCR Fallback Warning (Minor)**: When Tesseract is not installed locally, the PDF parser catches the error gracefully but logs a standard warning. On production systems that do not require OCR, these warnings can be ignored or filtered.
5. **Prompt Response Caching (Minor)**: Implementing a semantic vector cache layer to bypass the LLM for repeated queries.
6. **Multi-Provider Registry (Minor)**: Building a dynamic configuration-based factory to swap model providers (Gemini, Claude, GPT, Ollama).
7. **Retrieval Reranker Models (Minor)**: Injecting cross-encoders to rerank the top candidate context chunks retrieved by the hybrid search.
8. **Automated Ragas Benchmarks (Minor)**: Creating automated evaluation workflows against golden datasets to benchmark retrieval faithfulness.
9. **Optional PDF/DOCX Dependencies (Minor)**: WeasyPrint and python-docx are optional at runtime; if not installed, export falls back to plaintext. Production deployments requiring PDF/DOCX must install these explicitly.

---

## 4. Next Development Session Goal

*   **Target Milestone**: **Milestone 10 — Next.js Frontend Application (Phase 2)**
*   **Objective**: Build the Application Shell (Sidebar, Topbar, Routing, and core layout wrapping).
