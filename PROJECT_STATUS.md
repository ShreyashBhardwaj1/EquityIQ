# Project Status: EquityIQ

---

## 1. Project Specifications

*   **Current Version**: `v0.4.0-authentication`
*   **Overall Progress**: **~62% Completed**
*   **Test Count**: **47 tests passing**
*   **Code Coverage**: **86% coverage**
*   **CI Validation State**: **Passing** (Ruff Lint, Ruff Format, MyPy types, and Import-Linter green)

---

## 2. Milestone Board

### Completed Milestones
*   **Milestone 1**: Scaffolding & CI Pipeline Configuration (Ruff, MyPy, Pytest, Import-Linter)
*   **Milestone 2**: Domain Layer Modeling & Valuation Engine (Frozen Domain Entities)
*   **Milestone 3A**: Infrastructure Foundation (Database Manager, Health Services, JSON Logging)
*   **Milestone 3B**: Identity & Authentication Platform (Bcrypt Hasher, JWT Rotation, DB Revocation)

### Current Active Milestone
*   **Milestone 3C**: Workspace & Company Management (FastAPI Router + Row-Level Security Scoping)

### Upcoming Milestones
*   **Milestone 4**: Document Ingestion Pipeline (MIME checks, file storage, Celery text extraction)
*   **Milestone 5**: Financial Data Normalization & Precedence engine
*   **Milestone 6**: Vector Storage Pipeline & Hybrid search
*   **Milestone 7**: LLM Integration & RAG Q&A Agent
*   **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
*   **Milestone 9**: Report Generation & SSE Streaming
*   **Milestone 10**: Next.js UI Frontend Implementation

---

## 3. Known Technical Debt

1. **`datetime.utcnow()` Deprecations (Minor)**: Hashing and database mapping layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+. Plan is to standardize on `datetime.now(timezone.utc)` post-v1.0.
2. **Mocking External Providers (Minor)**: Health probes query live external Redis/Postgres links; tests override the database layer with in-memory SQLite but skip external TCP mocking.

---

## 4. Tomorrow's Development Goal

*   **Target Milestone**: **Milestone 3C — Workspace & Company Management**
*   **Objective**: Implement row-level workspace scoping, Company CRUD operations, and Document workspace ownership validations.
