# Session Handover Document — EquityIQ

This document provides status information, completed milestones, architectural decisions, technical debt, and recommendations for the next developer resuming implementation of the EquityIQ project.

---

## 1. Project Status Summary
- **Current Milestone**: Milestone 4 Complete.
- **Model State**: **DOMAIN MODEL FROZEN**. The core Domain layer remains a sealed contract for downstream persistence.
- **Build Status**: **GREEN**. All static linting (Ruff, MyPy, Import-Linter) and test suites are fully passing.
- **Test Count & Coverage**: **59 tests passing** with **86% coverage** across all modules.

Repository Status:
- Stable
- Reviewed
- Ready for Milestone 5

---

## 2. Today's Accomplishments (Milestone 4)
1. **Domain Extensions**:
   - Created `DocumentVersion` and `FinancialStatementVersion` domain entities representing audit snapshots of old states (files and values) for recovery and verification.
2. **Database ORM & Migrations**:
   - Mapped new `DocumentVersionORM` and `FinancialStatementVersionORM` tables.
   - Deployed migration `21b5bfd818a5` introducing version logging tables.
3. **Application Services**:
   - Built `DocumentService` handling metadata registry, file size ceiling checks (50MB), extension MIME-type verification (magic bytes), local directory storage, and file versioning.
   - Built `FinancialStatementService` supporting statement CRUD, auditing logs creation, and coordinates validation and normalization mappings.
4. **Validation & Normalization Engines**:
   - Implemented rules-based extensible `ValidationEngine` with core checks (StatementType, AccountingIdentity, DuplicateFiscalPeriod, FiscalPeriodOrdering).
   - Implemented priority-based `NormalizationEngine` mapping reporting aliases to canonical names (e.g. "Revenues" -> "revenue"), sorting rules by priority descending.

---

## 3. Important Architectural Assumptions & Business Rules
- **"Canonical Data First"**: Downstream consumption services (e.g., valuation models, RAG pipelines) must strictly pull data from `normalized_line_items` instead of raw reported values.
- **Workspace Isolation**: Database queries explicitly join and check `workspace_id` via optional scoping arguments.
- **Revision History Integrity**: Modifying a document file or statement figures creates a historical snapshot of the old state under the respective version tables before the changes are committed.

---

## 4. Technical Debt & Known Limitations
1. **`datetime.utcnow()` Deprecations**: Hashing and database mapping layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+. Plan to standardize on `datetime.now(timezone.utc)` post-v1.0.
2. **Local Storage Setup**: Files are stored on local disk under `storage/uploads`. Production setups will require abstracting this into a Cloud Object Storage adapter (AWS S3 / GCP Cloud Storage).
3. **Synchronous Ingestion**: Document uploads run synchronously inside HTTP requests. Once parsing and OCR are introduced, this must be offloaded to Celery worker queues.

---

## 5. Recommended Starting Point for Milestone 5 (Document Intelligence Pipeline)
The next objective is to construct the Document Intelligence Pipeline:
1. **Celery Task Workers**: Configure Celery asynchronous queue execution backed by Redis.
2. **Filing Parsing Engine**: Integrate PDF parsers like `pdfplumber` or layout-aware parsers to extract raw unstructured text.
3. **OCR Fallbacks**: Implement fallbacks (e.g., Tesseract) for scanned/image-only financial PDFs.
4. **Semantic Chunking**: Structure parsed documents into semantic paragraphs and tables, generating chunk metadata.
5. **Confidence Scoring**: Assign extraction confidence scores to parsed values based on layout alignment.
