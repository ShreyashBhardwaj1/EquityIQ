# Changelog

All notable changes to the EquityIQ project will be documented in this file.

---

## [v0.7.0-document-intelligence] - 2026-07-08

This release introduces the Document Intelligence Pipeline, implementing layout-aware document ingestion and processing workflows, paragraph-based semantic chunking, and deterministic metadata audit trails.

### Added
- **Layout-Aware PDF Ingestion**: Integrated `pdfplumber` parsing native PDF text page-by-page.
- **Table Extraction to Markdown**: Converted layout tables extracted from filings directly into clean Markdown tables for structured downstream ingestion.
- **Stable Chunk Identities**: Engineered deterministic chunk ID generation using `uuid.uuid5` utilizing the parent document UUID as the namespace and `chunk_index` as the name.
- **Parsing Manifest Audit Logs**: Created `ParsingManifest` tracking parser version, chunk strategy, size/overlap boundaries, duration, table count, chunk count, warnings, and extraction confidence.
- **Extensible Chunk Validation**: Deployed validation guards (`ChunkValidator`) verifying chunk ordering, duplicate content checks, empty text guards, metadata completeness, and size limits.
- **Asynchronous Task Workers**: Configured Celery and Redis to dispatch long-running document parses asynchronously, isolating parsing tasks from FastAPI thread context.
- **API Endpoints**:
  - `POST /documents/{id}/parse`: Dispatches background parsing task.
  - `POST /documents/{id}/reprocess`: Forces parser re-runs for future upgrades, incrementing `parse_version`.
  - `GET /documents/{id}/chunks`: Lists extracted chunks for a document, scoped by workspace ID.

### Changed
- **Database Schema**: Generated and applied migration `cda555623a44` to support `document_chunks` and `parsing_manifests` tables.
- **Parser Settings**: Configured thresholds (`MIN_NATIVE_TEXT_LENGTH`, `OCR_CONFIDENCE_THRESHOLD`, and `PARSER_TIMEOUT_SECONDS`) into settings rather than hardcoding.

### Engineering Improvements
- **Fallback Plain-Text Parsing**: Configured automatic fallback to raw text extraction if a file does not have a `.pdf` extension or if opening the PDF binary fails.
- **OCR Graceful Fallback**: Traps pytesseract import/binary exceptions, logging warnings and tracking them in manifest audit records instead of failing the pipeline.
- **Eager Celery Thread Execution**: Implemented thread-spawning fallback logic in task runners to prevent active event loop conflicts under FastAPI TestClient eager executions.

### Testing
- **Unit Verification**: Built fast unit tests validating chunker splits, paragraph sentence fallbacks, table MD conversions, and chunk validator constraints.
- **Integration Flow Tests**: Added `test_document_intelligence.py` verifying registration, upload, parsing dispatch, db status updates, chunks fetches, reprocess iterations, and workspace boundary security.

### Documentation
- **Technical Debt Register**: Updated registers to resolve synchronous ingestion debt and document new OCR logs warning details.
- **Engineering Journal**: Documented architectural decisions, lessons, and journals for Day 4.


## [v0.6.0-financial-data-foundation] - 2026-07-07

This release implements the core Financial Data Foundation, establishing secure document metadata management, extensible accounting validation guards, rules-based priority mapping normalization, statement auditing history logs, and strict workspace tenant-isolation.

### Added
- **Document Metadata CRUD**: Added endpoints under `/documents` to support document registration, metadata retrieval, partial updates, and deletion.
- **Secure File Storage**: Configured local storage directory writing isolated by workspace and company (`storage/uploads/workspace_{id}/company_{id}/`).
- **File Validation**: Integrated magic bytes checks (PDF headers `b'%PDF-'`, text/CSV encoding checks) and a strict 50MB file size ceiling.
- **Validation Engine**: Deployed an extensible rules-based `ValidationEngine` supporting custom rules injection.
- **Accounting Identity Rule**: Added check guard verifying double-entry assets/liabilities/equity consistency on balance sheets.
- **Duplicate Fiscal Period Rule**: Configured duplicate detection flagging attempts to post redundant statements of the same type/period.
- **Fiscal Period Ordering Rule**: Restricts reporting years to a logical range of 1900-2100.
- **Normalization Engine**: Implemented `NormalizationEngine` mapping reporting aliases to canonical names (e.g. "Revenues" -> "revenue").
- **Priority Mappings**: Evolved mapping rules to support a priority order, ensuring high-priority rules override lower ones.
- **Audited History Versioning**:
  - `DocumentVersion`: Snapshots old physical files on disk when re-uploading, tracking change reasons.
  - `FinancialStatementVersion`: Snapshots old statement values when updating figures, tracking auditors change reasons.
- **Side-by-side Comparison**: Added `/compare` endpoint returning as-reported raw values side-by-side with normalized canonical values and differences.

### Changed
- **Repository Interface Signatures**: Updated `DocumentRepository` and `FinancialStatementRepository` to support optional workspace scoping on queries, preserving compatibility with old test modules.
- **ORM Table Mappings**: Created `DocumentVersionORM` and `FinancialStatementVersionORM` mappings in SQLAlchemy.
- **Database Schema**: Generated and executed database migration `21b5bfd818a5` for version tables.

### Testing
- **Validation Engine Unit Tests**: Created `test_validation_engine.py` checking core validation rules and custom rules injection.
- **Normalization Pipeline Unit Tests**: Created `test_normalization_pipeline.py` checking aliases standardization.
- **API Flow Integration Tests**: Created `test_financial_data.py` executing complete API flows, including imbalanced statements failures, updating files/statements, comparison reports, and workspace isolation checks.

### Documentation
- **Technical Debt**: Documented temporary local storage storage setup and future asynchronous processing as technical debt.
- **Architecture & Roadmap**: Updated `README.md` with system flow overview and completed milestones.

### Validation
- **Ruff**: Passed formatting and lint checks cleanly.
- **MyPy**: Passed type validation (Success: no issues found in 96 source files).
- **Import-Linter**: Passed contract validation.
- **Pytest**: Deployed 59 tests passing cleanly.

---

## [v0.5.0-workspace-company] - 2026-07-07

This release establishes the core business multi-tenant architecture of EquityIQ, implementing workspace isolation, membership-scoped access authorization, company directory management, paginated filtration, soft-delete archival systems, and search capabilities.

### Added
- **Workspace CRUD**: Added creation, listing, detail fetch, partial updates (PATCH), and switch context routes under `/workspaces`.
- **Company CRUD**: Added creation, listing, scoped detail fetch, and partial updates (PATCH) under `/companies`.
- **Workspace Isolation**: Configured header-based active workspace context resolution (`X-Workspace-ID`) with fallback checks.
- **Workspace Membership Validation**: Integrated membership relationship checks preventing non-member access requests.
- **Cross-Workspace Authorization**: Deployed validation guards ensuring that analysts or users cannot access company resources belonging to workspaces where they lack memberships.
- **Search**: Integrated case-insensitive search matching query strings across company name, ticker symbol, exchange, and sector.
- **Pagination**: Implemented limit/offset pagination parameters for company directory listings.
- **Filtering**: Implemented listing filtration supporting exchange, sector, industry, and country fields.
- **Soft Deletion**: Configured soft deletion (archival setting `deleted_at`) for both Workspace and Company ORM models, preserving historical logs.
- **Company Restoration**: Automated automatic record restoration and update when creating a company whose ticker/exchange matches a soft-deleted record in the active workspace.
- **PATCH Support**: Wired PATCH routes for workspace name and company details, enabling partial modifications.

### Changed
- **Company Domain Scoping**: Updated the `Company` entity to include `workspace_id` and `country` fields.
- **Repository Interfaces**: Extended repository protocols to require workspace-scoped fetches, soft deletion, and pagination/filtration arguments.
- **Database Schema**: Replaced the global company ticker unique constraint with a composite constraint scoping `(workspace_id, ticker, exchange)`.

### Architecture
- **Multi-Tenant Row-Level Security (RLS)**: Enforced isolation at the repository and service layer. Every data access command explicitly filters on `workspace_id`, and dependency injection validates that the authenticated user possesses a valid membership for that workspace.
- **Soft Deletion Preservation**: Replaced hard cascades with timestamp-based archival, ensuring audit trails are retained.

### Testing
- **Integration Test Coverage**: Added `test_workspace_api.py` and `test_company_api.py` integration suites verifying CRUD lifecycles, sorting filters, text searches, and cross-workspace isolation boundaries.
- **Current Tests Count**: 49 passing tests.

### Validation
- **Ruff**: Passed formatting and lint checks.
- **MyPy**: Passed type validation (Success: no issues found in 105 source files).
- **Import-Linter**: Passed contract validation ("Domain boundary rule KEPT").
- **Pytest**: Passed with 100% success rate.

---

## [v0.4.0-authentication] - 2026-07-06

This release implements the core Identity & Authentication Platform, securing the backend API endpoints and organizing multi-tenant workspace isolation.

### Added
- **User and Workspace Domain Models**: Introduced pure `User`, `Workspace`, and `WorkspaceMembership` domain models representing system accounts, tenancy scopes, and user roles.
- **ORM Table Mappings**: Implemented `UserORM`, `WorkspaceORM`, `WorkspaceMembershipORM`, and `RefreshTokenORM` database mappings.
- **Clean Architecture Repositories**: Added concrete database adapters (`SQLAlchemyUserRepository`, `SQLAlchemyWorkspaceRepository`, and `SQLAlchemyRefreshTokenRepository`) for data persistence.
- **Password Hasher Interface**: Designed a decoupled `PasswordHasher` Protocol abstraction inside the domain layer.
- **Rotated Session Handler**: Built an `AuthService` supporting transactional user registrations, secure password checks, and refresh token rotation.
- **Authentication Endpoints**: Added FastAPI route handlers `/auth/register`, `/auth/login`, `/auth/refresh` (enforcing token rotation), `/auth/logout`, and `/auth/me`.

### Changed
- **Document Constraints Alignment**: Migrated the `documents` table to enforce non-nullable foreign keys linking `workspace_id` and `uploaded_by_id` to the `workspaces` and `users` tables.
- **Centralized Dependencies**: Updated `dependencies.py` to yield the new user/workspace repositories and expose the `get_current_user` JWT authentication provider.

### Architecture
- **Inward Dependency Flow**: Ensured all cryptography and web frameworks are isolated inside the infrastructure/API layers. Strictly checked and verified by `import-linter`.
- **Relational Integrity**: Enforced foreign key references at the database schema layer rather than relying purely on application-level lookups.

### Testing
- **Security & Integration Suites**: Added unit tests for Bcrypt hashing wrappers and JWT encoders (`test_security.py`).
- **Endpoint Lifecycles**: Created endpoint integration tests (`test_auth_api.py`) verifying user registration, duplicate email rejection, JWT payload parsing, rotation invalidation, and session logout.
- **Current Tests Count**: 47 active tests.

### Coverage
- **Core Coverage**: Verified overall backend test coverage at **86%**.

### Security
- **One-time Token Rotation**: Configured refresh tokens to rotate upon consumption (revoking the used token and issuing a new refresh/access token pair).
- **JWT Replay Protection**: Added a unique JWT ID (`jti`) claim to every token payload, resolving duplicate hashing risks.
- **Strict Role-Based Control**: Deployed a `require_role` helper to limit endpoint execution to `admin`, `analyst`, and `viewer` classifications.

### Known Limitations
- **Ingestion Linkage**: Nullable company and document constraints exist; these will be wired to active workspaces during company CRUD and document parsing phases.
