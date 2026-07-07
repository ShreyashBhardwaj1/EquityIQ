# Engineering Journal — Day 3

## 1. Today's Objectives
The primary objective of today's session was to establish the **Financial Data Foundation** (Milestone 4) for EquityIQ. This includes:
1. Building secure document metadata management with file size constraints and file type verification.
2. Developing an extensible validation engine to enforce accounting identities and detect duplicate entries.
3. Building a deterministic priority-based normalization engine to standardize reported financial values.
4. Implementing immutable version tracking histories for documents and financial statements.
5. Guaranteeing workspace tenant-isolation boundaries across all financial resources.

## 2. Milestones Completed
- **Milestone 4 — Financial Data Foundation**: Successfully implemented, test-verified, and statically checked.

## 3. Architecture Decisions & Rationale
- **"Canonical Data First" Principle**: 
  - *Decision*: We decided that all downstream analytical components (e.g. valuation models, LLM prompts) must strictly consume data from `normalized_line_items` instead of raw reported values.
  - *Rationale*: Raw filings are notoriously inconsistent. Companies use different names for the same financial items (e.g. "Revenues" vs "Revenue" vs "Net Sales"). Normalizing this data at the ingestion layer guarantees consistency and reliability across the platform.
- **Double-Entry Validation in Domain Layer**:
  - *Decision*: We kept validation rules like accounting identity check (Assets = Liabilities + Equity) in the domain layer.
  - *Rationale*: Validation rules represent fundamental truths of business and accounting. Placing them in the domain layer keeps them framework-free and guarantees that no invalid financial statement can ever be persisted or instantiated in the system.
- **Audited Snapshots vs Cascading Deletes**:
  - *Decision*: We implemented `DocumentVersion` and `FinancialStatementVersion` ORM entities. When files are replaced or figures updated, a snapshot of the old state is registered before changes commit.
  - *Rationale*: Re-uploading filings or adjusting line items happens frequently due to audits or corrections. Storing historical versions guarantees a complete audit trail for compliance, auditing, and future recovery.

## 4. Technical Challenges & Solutions
- **Challenge: Backward Compatibility of Repositories**:
  - *Challenge*: The addition of `workspace_id` scoping to document and statement repository methods broke existing unit/integration tests that were calling them without a workspace context.
  - *Solution*: We refactored repository protocols and concrete implementations (`SQLAlchemyDocumentRepository`, `SQLAlchemyFinancialStatementRepository`) to make `workspace_id` an optional parameter (`workspace_id: UUID | None = None`). When passed, it strictly scopes queries to the workspace context (supporting RLS); when omitted (e.g., in legacy tests), it executes a global query.
- **Challenge: Parameter Ordering Mismatch**:
  - *Challenge*: During integration test runs, the statement PATCH route returned a `404 Not Found`. We traced this to a parameter ordering mismatch in service-to-repository calls, where `workspace_id` was mistakenly passed as `statement_id`.
  - *Solution*: We refactored all repository method calls in `DocumentService` and `FinancialStatementService` to use explicit keyword arguments (e.g. `self.statement_repo.get(statement_id=statement_id, workspace_id=workspace_id)`), completely eliminating ordering bugs.

## 5. Engineering Reflections & Lessons Learned

### Lesson 1: Explicit Parameter Binding Prevents Silent Bugs
Positional arguments in complex codebase adapters are highly prone to ordering errors, especially when multiple parameters share the same type (like `UUID`). Standardizing on keyword arguments for all service-to-repository invocations completely eliminates this class of bugs.

### Lesson 2: Extensible Design Beats Hardcoding
Designing the validation engine around a list of pluggable `ValidationRule` protocols allowed us to easily add checks for duplicate periods and year ranges without altering the engine's core orchestration logic. It keeps components focused and reusable.

### Lesson 3: Leverage Pydantic to Validate Configuration Constraints
Using Pydantic's `Field(default=...)` parameters in `NormalizationRule` models ensures that both Pydantic's runtime validation and MyPy's static type checker have a consistent understanding of default values, preventing type checking failures.
