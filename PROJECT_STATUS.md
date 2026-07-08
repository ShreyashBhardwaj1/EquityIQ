# Project Status: EquityIQ

---

## 1. Project Specifications

*   **Current Version**: `v0.7.0-document-intelligence`
*   **Overall Progress**: **70% Completed** (7 / 10 Milestones completed)
*   **Test Count**: **70 tests passing**
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

### Upcoming Milestones
*   **Milestone 6**: Vector Storage Pipeline & Hybrid Search Retrieval
*   **Milestone 7**: LLM Integration, Prompt-Injection Filters, Q&A Agent
*   **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
*   **Milestone 9**: Report Generation & SSE Streaming
*   **Milestone 10**: Next.js UI Frontend Implementation

---

## 3. Known Technical Debt

1. **`datetime.utcnow()` Deprecations (Minor)**: Hashing and database mapping layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+. Plan is to standardize on `datetime.now(timezone.utc)` post-v1.0.
2. **Local Storage Setup (Minor)**: Documents are currently uploaded to local disk storage (`storage/uploads`). In production, this will require migration to cloud block storage (e.g., AWS S3 or GCP Cloud Storage) with a storage adapter interface.
3. **Eager Celery Thread Execution (Minor)**: Celery eager test runner runs synchronously on the same event loop, resolved using a dedicated thread-spawning runner fallback. In production, we must monitor background Celery worker performance and pool configurations under concurrent document loads.
4. **OCR Fallback Warning (Minor)**: When Tesseract is not installed locally, the PDF parser catches the error gracefully but logs a standard warning. On production systems that do not require OCR, these warnings can be ignored or filtered.

---

## 4. Tomorrow's Development Goal

*   **Target Milestone**: **Milestone 6 — Vector Storage Pipeline & Hybrid Search Retrieval**
*   **Objective**: Establish local embedding generation services, integrate FAISS self-hosted vector databases, implement chunk semantic indexing/retrieval adapters, and construct a hybrid search resolver blending keyword search (BM25) and dense embeddings.
