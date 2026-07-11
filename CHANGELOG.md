# Changelog

All notable changes to the EquityIQ project will be documented in this file.

---

## [v1.1.0-report-generation-streaming] - 2026-07-11

This release introduces the complete Report Generation & Streaming Engine (Milestone 9). The engine produces multi-section, LLM-synthesized investment research reports grounded exclusively in the deterministic outputs of the Milestone 8 Financial Intelligence pipeline. The LLM acts strictly as a narrative synthesizer — it never recalculates or invents financial metrics.

### Added
- **FinancialReport & FinancialReportVersion Entities**: New Pydantic domain entities tracking report lifecycle, versioning, content snapshots, model provenance, and generation metadata in `app/domain/entities/report.py`.
- **ReportRepository Protocol**: New domain interface defining `get`, `save`, `list_by_company`, `save_version`, and `get_versions` contracts in `app/domain/interfaces/repositories.py`.
- **ORM Persistence Models**: `FinancialReportORM` and `FinancialReportVersionORM` SQLAlchemy mappings in `app/infrastructure/db/models/report.py`.
- **SQLAlchemyReportRepository**: Complete upsert, list, and versioning adapter in `app/infrastructure/db/repositories/report_repo.py`.
- **Alembic Migration**: Migration `f1a2b3c4d5e6` creating `financial_reports` and `financial_report_versions` tables.
- **ReportContextAssembler**: Reads exclusively from Milestone 8 pre-computed tables (health scores, ratios, risks, recommendations) into a typed `ReportContext` grounding object.
- **ReportPromptBuilder**: Loads 8 structured Markdown prompt templates and binds `ReportContext` values to produce section-level prompts.
- **MarkdownValidator**: Structural LLM output validation — minimum length, unresolved placeholder detection, and balanced code block checks.
- **ReportSectionValidator**: Domain boundary enforcement — detects hallucinated ratings, missing scores, and fabricated risk categories per section.
- **ReportGenerationService**: Full 7-section pipeline orchestrator (context assembly → prompt building → LLM generation → validation → assembly → storage → version snapshot).
- **ReportSSEStreamingService**: Structured SSE event builders (`queued`, `progress`, `token`, `section_started`, `section_completed`, `completed`, `failed`, `heartbeat`) with async word-level replay generator.
- **ExportService**: Markdown (raw bytes), PDF (WeasyPrint with CSS styling), and DOCX (python-docx) export with standardized footer and graceful dependency fallback.
- **generate_report_task**: Celery background task executing the async pipeline in `app/workers/tasks.py`.
- **Report API Router**: 5 new endpoints under `GET|POST /companies/{id}/reports/...` covering generate, list, detail, SSE stream, and multi-format download.
- **Prompt Templates**: 8 structured Markdown templates in `app/prompts/reports/` covering system safety rules, executive summary, financial health, ratio analysis, trend analysis, risk assessment, recommendation, and appendix sections.

### Changed
- **`app/main.py`**: Registered `reports_router`.
- **`app/core/dependencies.py`**: Added `get_report_repository` and `get_report_generation_service` dependency providers.
- **`app/domain/rules/recommendation_engine.py`**: Fixed pre-existing MyPy `attr-defined` error — `RecommendationType` now imported from its canonical source `app.domain.entities.recommendation`.

### Validation
- **Ruff**: Passed formatting and check cleanly.
- **MyPy**: **0 errors** (fully clean type checks — first time in project history).
- **Import-Linter**: Domain boundary rule KEPT (194 files, 893 dependencies analyzed).
- **Pytest**: **133 tests passing** cleanly.

---

## [v1.0.0-financial-intelligence] - 2026-07-10

This release introduces the completed Financial Intelligence & Recommendation Engine, featuring dynamic registry-driven ratio calculations, multi-period trend categorization (accelerating, decelerating, recovery, decline, stable, volatile), health scoring, risk evaluation, policy-driven investment recommendations, and a consolidated dashboard endpoint with structured confidence breakdowns.

### Added
- **Centralized Configuration**: Configured settings for Ratio, Health, Risk, and Recommendation policy engines in `app/core/financial_config.py`.
- **Registry-driven Ratio Engine**: Added dynamic registry evaluation of financial ratios in `app/domain/rules/ratio_registry.py`, complete with validation rule checks and qualitative status classifications (Excellent, Healthy, Watch, Weak, Critical).
- **Multi-Period Trend Categorization**: Added chronological parsing and categorization of growth trends (revenue, net income, operating cash flow) across periods in `app/domain/rules/trend_engine.py`.
- **Weighted Health Scoring**: Added dynamic mapping of ratios against configurable scoring boundaries to output overall and category-level health scores in `app/domain/rules/health_scoring.py`.
- **Distress Risk Engine**: Evaluates ratio safety and solvency, flagging low/moderate/severe risk factors in `app/domain/rules/risk_engine.py`.
- **Policy-driven Recommendation Engine**: Resolves Buy/Hold/Sell ratings against health thresholds, risk ceilings, and growth constraints in `app/domain/rules/recommendation_engine.py`.
- **ORM Persistence Models**: Created mappings for Ratios, Health Scores, Risks, Recommendations, Policies, and Audit History, and executed migration head.
- **Explainability Service**: Provides detailed signals (positive/negative), policies applied, rules triggered, and ratio/risk/trend factors in `app/application/services/explainability_service.py`.
- **Consolidated Dashboard Endpoint**: Aggregates all computed results, trends, top ratios, highest risks, final ratings, and structured confidence breakdowns in a single response under `GET /companies/{id}/dashboard`.
- **Workspace Security Isolation**: Enforces active workspace membership constraints across all calculated models and routes.
- **Hardened RAG Grounding**: Strengthened LLM prompts in `app/prompts/answer_prompt.md` to prevent financial recomputation and enforce alignment with deterministic outputs.
- **Unit & Integration Verification**: Added 10 new tests validating rules, repository CRUDs, API routes, and tenant security isolation.

### Changed
- **Database Schema**: Autogenerated and applied migration `89ee9532b883` mapping the new financial intelligence tables.
- **RAG Subsystem**: Wired RAG Service to automatically retrieve the latest period's health score and pre-calculate tables to append to query contexts.

### Validation
- **Ruff**: Passed formatting and check cleanly.
- **MyPy**: Passed type checks successfully.
- **Import-Linter**: Preserved clean boundaries contract (kept).
- **Pytest**: 94 tests passing cleanly.

---

## [v0.9.0-rag-llm-integration] - 2026-07-09

This release introduces LLM Integration & Retrieval-Augmented Generation (RAG) capabilities, featuring Gemini 2.5 Pro primary service with Flash fallback, token budget auditing, prompt injection filters, grounding evaluations, explainable citation metadata, and execution latency telemetry tracking.

### Added
- **Gemini Adapter Layer**: Connected backend application flows to Gemini SDK utilizing Gemini 2.5 Pro as the primary completion model and Gemini 2.5 Flash as a fallback.
- **Prompt Injection Guard**: Created compiled safety checks validating incoming queries and grounding text for system instruction leaks, override attempts, role-switching, and XML manipulation.
- **Context Assembler**: Grouped consecutive chunk indexes under the same document section to optimize context and formatted them into XML-tagged blocks.
- **Token Budget Manager**: Created local token auditing (20,000 limits) using tiktoken, pruning chat turns first (oldest first) and then candidate context chunks.
- **Deterministic Grounding Score**: Exposed sentence-level citation analysis calculating the ratio of cited sentences to total generated sentences in responses.
- **LLM Telemetry Monitoring**: Created database model mappings recording input/output token counts, execution latency, metadata versions, and scores without recording query inputs.
- **Deep Citation Explainability**: Augmented citations with retrieval trace metadata including rank, semantic score, keyword score, hybrid score, and retrieval method.
- **Stateless & Stateful API Routes**: Added `POST /chat/ask` stateless grounding checks and `POST /chat/chat` multi-turn active sessions.
- **Unit Verification**: Built `test_refinements.py` verifying external prompt templates, grounding math, telemetry schemas, and citation fields mapping.

### Changed
- **Database Schema**: Executed migration revision `b6c989ff64f7` mapping `llm_requests` table and adding explainability columns to `citations` table.
- **Prompts Structure**: Externalized prompts into dedicated markdown files under `backend/app/prompts/` (system, answer, citation, summarizer instructions).
- **Session Lifecycles**: Configured `ConversationService` to run asynchronous background celery task summarizing chat session turns when history exceeds 10 turns.

### Improved
- **Clean Architecture Boundaries**: Preserved domain boundaries, mapping explainability metrics from search results to DB citation rows without mixing layers.
- **MyPy Typing**: Cleaned type reassignment checks in HybridSearchService to prevent union float warnings.

### Validation
- **Ruff**: Passed formatting and check cleanly.
- **MyPy**: Strict static typing analysis success with 0 warnings.
- **Import-Linter**: Preserved clean boundaries contract.
- **Pytest**: 84 tests passing cleanly with 87% coverage.

### Documentation
- **AI Architecture**: Created `docs/ai_architecture.md` detailing pipelines and workflows with Mermaid diagrams.
- **Technical Debt**: Created `docs/technical_debt.md` listing response caching, provider registry, streaming, reranking, and benchmarking as deferred items.

---

## [v0.8.0-vector-storage-hybrid-search] - 2026-07-08

This release introduces the Vector Storage Pipeline & Hybrid Search Retrieval system, implementing local SentenceTransformers vector embedding, disk-persisted FAISS CPU flat indexes with strict database-assisted pre-filtering, SQLite FTS5 full-text keyword retrieval, min-max score normalization, and linear combination hybrid rank fusion.

### Added
- **Local Vector Embeddings**: Integrated Hugging Face's `all-MiniLM-L6-v2` SentenceTransformers model for framework-independent, local vector generation (384-dim).
- **FAISS CPU Vector Store**: Deployed `FaissVectorStore` backing queries utilizing exact inner-product `IndexFlatIP` to calculate Cosine Similarity.
- **Strict Database-Assisted Pre-filtering**: Leveraged `faiss.IDSelectorBatch` to pre-filter FAISS vector searches using candidate chunk UUIDs resolved from SQL metadata queries. This enforces 100% strict workspace isolation.
- **SQLite FTS5 Full-Text Engine**: Created virtual table `document_chunks_fts USING fts5(content, chunk_id UNINDEXED)` in SQLite to support BM25-based keyword matching.
- **FTS5 Synchronization Triggers**: Connected chunk repository `save`, `save_batch`, and `delete_by_document` methods to SQLite FTS5 statements, keeping the virtual table indices in sync automatically.
- **Min-Max Score Normalization**: Implemented a Min-Max scaling utility in `HybridSearchService` to normalize vector similarity scores and BM25 keyword scores to a $[0.0, 1.0]$ range before ranking.
- **Linear Fusion Combine**: Blends normalized semantic and keyword scores dynamically via: `alpha * semantic_score + (1 - alpha) * keyword_score`.
- **API Endpoints**:
  - `POST /search/semantic`: Performs pure similarity vector searches.
  - `POST /search/hybrid`: Blends semantic vectors and FTS5 keyword matches.
  - `POST /search/rebuild`: Forces a complete rebuild of a workspace index from database chunk records.
- **Celery Worker Integration**: Wired the document parsing pipeline tasks to automatically rebuild the workspace index and generate embeddings for newly parsed documents.

### Changed
- **Database Schema**: Generated and applied migration `49d012359df1_add_embedding_and_manifest_tables.py` creating the `embeddings` and `embedding_manifests` tables (with `created_at`, `updated_at`, and `deleted_at` columns) and the FTS5 virtual table.
- **Core Configurations**: Added setting variables for `VECTOR_INDEX_VERSION`, `EMBEDDING_MODEL_NAME`, `EMBEDDING_DIMENSION`, and `EMBEDDING_BATCH_SIZE`.
- **Dependencies Module**: Added repository dependency providers (`get_embedding_repository`, `get_embedding_manifest_repository`) and application service providers (`get_embedding_service`, `get_retrieval_service`, `get_hybrid_search_service`, `get_index_manager`, `get_index_builder`).

### Engineering Improvements
- **Graceful Degradation**: Configured FTS5 keyword searches to log warnings and degrade gracefully (returning empty lists) if SQLite FTS5 queries fail or are not supported on the active database driver.
- **Type Checker Cleanups**: Avoided swig keyword arguments in `faiss.SearchParameters` to satisfy MyPy typing constraints.

### Testing
- **Unit Verification**: Built `test_embeddings_store.py` verifying FAISS CRUD operations, exact pre-filtering, and saving/loading index binary files to/from disk.
- **Integration API Tests**: Built `test_search_api.py` validating registration, uploads, synchronous parsing, vector embedding generation, `/search/semantic`, `/search/hybrid`, and manual index rebuilds, along with strict tenant isolation verification.

### Documentation
- **Updated Project Overview**: Documented the hybrid search architecture, indexing lifecycle, and retrieval pipeline details in `README.md`.
- **Engineering Journal**: Documented major accomplishments, decisions, lessons, and journals for Day 5.

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
