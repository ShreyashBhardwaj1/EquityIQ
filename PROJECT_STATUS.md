# Project Status: EquityIQ

---

## 1. Project Specifications

*   **Current Version**: `v0.6.0-financial-data-foundation`
*   **Overall Progress**: **60% Completed** (6 / 10 Milestones completed)
*   **Test Count**: **59 tests passing**
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

### Upcoming Milestones
*   **Milestone 5**: Document Intelligence Pipeline (Asynchronous Parser Workers, OCR, & Chunk Extraction)
*   **Milestone 6**: Vector Storage Pipeline & Hybrid search
*   **Milestone 7**: LLM Integration & RAG Q&A Agent
*   **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
*   **Milestone 9**: Report Generation & SSE Streaming
*   **Milestone 10**: Next.js UI Frontend Implementation

---

## 3. Known Technical Debt

1. **`datetime.utcnow()` Deprecations (Minor)**: Hashing and database mapping layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+. Plan is to standardize on `datetime.now(timezone.utc)` post-v1.0.
2. **Local Storage Setup (Minor)**: Documents are currently uploaded to local disk storage (`storage/uploads`). In production, this will require migration to cloud block storage (e.g., AWS S3 or GCP Cloud Storage) with a storage adapter interface.
3. **Synchronous Ingestion (Minor)**: Document upload and metadata verification run synchronously inside FastAPI requests. As we integrate PDF parsing and OCR extraction, this will be offloaded to asynchronous background Celery tasks.

---

## 4. Tomorrow's Development Goal

*   **Target Milestone**: **Milestone 5 — Document Intelligence Pipeline**
*   **Objective**: Establish asynchronous parsing queues (Celery + Redis), integrated PDF text parser engines (`pdfplumber` / OCR fallback), semantic text chunking, and document chunk persistence for downstream RAG consumption.
