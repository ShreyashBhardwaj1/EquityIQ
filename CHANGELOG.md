# Changelog

All notable changes to the EquityIQ project will be documented in this file.

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
