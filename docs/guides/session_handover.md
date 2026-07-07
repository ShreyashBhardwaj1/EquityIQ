# Session Handover Document — EquityIQ

This document provides status information, completed milestones, architectural/security decisions, lessons learned, and recommendations for the next developer resuming implementation of the EquityIQ project.

---

## 1. Project Status Summary
- **Current Milestone**: Milestone 3C Complete.
- **Model State**: **DOMAIN MODEL FROZEN**. The core Domain layer remains a sealed contract for downstream persistence.
- **Build Status**: **GREEN**. All static linting (Ruff, MyPy, Import-Linter) and test suites are fully passing.
- **Test Count & Coverage**: **49 tests passing** with **86% coverage** across all modules.

Repository Status:
- Stable
- Reviewed
- Ready for Milestone 4

---

## 2. Today's Accomplishments (Milestone 3C)
1. **Workspace Scoped Entities**:
   - Scoped the `Company` entity and `CompanyORM` model with a foreign key to the active workspace.
   - Refined the database unique constraint to ensure ticker and exchange combinations are unique *only* within a specific workspace `(workspace_id, ticker, exchange)`.
2. **Repository & Service Layer Extensions**:
   - Implemented soft deletion policies (archiving with `deleted_at = func.now()`) for workspaces and companies, avoiding hard cascades.
   - Added company directory pagination, filtration (by country, exchange, sector, industry), sorting overrides (defaulting to `created_at` DESC), and text searching.
   - Wired auto-restoration of soft-deleted company records on duplicate creation requests.
3. **API Scoping and Header Resolution**:
   - Built a custom dependency injection helper that resolves the active workspace from the HTTP `X-Workspace-ID` header, falling back to the user's first personal workspace, and validating membership permissions.
   - Implemented PATCH endpoints for workspaces and companies, supporting partial updates.
   - Configured route handlers to commit database session transactions on successful state writes.

---

## 3. Business Rules Added
- **Owner-only Workspace Deletion**: Only the workspace owner can soft-delete a workspace.
- **Workspace Deletion Safety**: Users cannot soft-delete their last remaining active workspace.
- **Soft-Delete Recovery**: Creating a company whose ticker/exchange matches a soft-deleted one inside the active workspace will restore and update the existing record.
- **Membership Verification**: Users must possess membership in the resolved active workspace, otherwise they receive a 403 Forbidden.

---

## 4. Technical Debt & Known Limitations
1. **`datetime.utcnow()` Deprecations**: Hashing and database mapping layers contain calls to `datetime.utcnow()`, raising deprecation warnings under Python 3.12+. Plan to standardize on `datetime.now(timezone.utc)` post-v1.0.
2. **Mocking External Providers**: Health checks require live Postgres/Redis. Integration tests override the database but skip mock connections for external Redis systems.

---

## 5. Three Lessons Learned

### Lesson 1
A strong authentication and workspace model dramatically simplifies business-layer implementation.

### Lesson 2
Multi-tenancy must be enforced consistently across every layer of the application.

### Lesson 3
Reusing existing modules instead of creating unnecessary abstractions keeps the codebase cohesive and maintainable.

---

## 6. Recommended Starting Point for Milestone 4 (Financial Data Foundation)
The next objective is to setup file ingestion pipelines:
1. **Upload Routers**: Implement `POST /documents/upload` enabling authenticated users to upload financial PDF filings.
2. **Asynchronous Processing**: Configure Celery task queues backed by Redis to manage PDF processing.
3. **Text Extraction**: Integrate parsing adapters using tools like PyPDF, pdfplumber, or layout engines to retrieve unstructured text.
4. **Validation**: Assert validation tests under `tests/integration/test_ingestion_api.py`.
