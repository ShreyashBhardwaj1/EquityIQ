# Changelog

All notable changes to the EquityIQ project will be documented in this file.

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
