# Project Status: EquityIQ

---

## 1. Project Specifications

*   **Current Version**: `v0.8.0-vector-storage-hybrid-search`
*   **Overall Progress**: **80% Completed** (8 / 10 Milestones completed)
*   **Test Count**: **72 tests passing**
*   **Code Coverage**: **86% coverage**
*   **CI Validation State**: **Passing** (Ruff Lint, Ruff Format, MyPy types, and Import-Linter green)

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
*   **Milestone 6**: Vector Storage Pipeline & Hybrid Search Retrieval (Local Hugging Face embeddings, FAISS CPU vector index, database-assisted strict pre-filtering, SQLite FTS5 full-text keyword retrieval, min-max score normalization, and linear rank fusion)

### Upcoming Milestones
*   **Milestone 7**: LLM Integration, Prompt-Injection Filters, Q&A Agent (RAG)
*   **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
*   **Milestone 9**: Report Generation & SSE Streaming
*   **Milestone 10**: Next.js UI Frontend Implementation

---

## 3. Known Technical Debt

1. **`datetime.utcnow()` Deprecations (Minor)**: Hashing, database mapping, and index building layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+. Plan is to standardize on `datetime.now(timezone.utc)` post-v1.0.
2. **Local Storage Setup (Minor)**: Documents and FAISS index binary files are currently uploaded to local disk storage (`storage/uploads` and `storage/indices`). In production, this will require migration to cloud block storage (e.g., AWS S3 or GCP Cloud Storage) with a storage adapter interface.
3. **Eager Celery Thread Execution (Minor)**: Celery eager test runner runs synchronously on the same event loop, resolved using a dedicated thread-spawning runner fallback. In production, we must monitor background Celery worker performance and pool configurations under concurrent document loads.
4. **OCR Fallback Warning (Minor)**: When Tesseract is not installed locally, the PDF parser catches the error gracefully but logs a standard warning. On production systems that do not require OCR, these warnings can be ignored or filtered.

---

## 4. Tomorrow's Development Goal

*   **Target Milestone**: **Milestone 7 — LLM Integration & Retrieval-Augmented Generation (RAG)**
*   **Objective**: Integrate large language model providers (e.g., Gemini or self-hosted models), construct prompt engineering logic, deploy prompt-injection sanitization filters, and create the Q&A retrieval-augmented research agent.
