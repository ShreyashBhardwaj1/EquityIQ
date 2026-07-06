# Session Handover Document — EquityIQ

This document provides status information, completed milestones, architectural/security decisions, and recommendations for the next developer resuming implementation of the EquityIQ project.

---

## 1. Project Status Summary
- **Current Milestone**: Milestone 3B Complete.
- **Model State**: **DOMAIN MODEL FROZEN**. The core Domain layer remains a sealed contract for downstream persistence.
- **Build Status**: **GREEN**. All static linting (Ruff, MyPy, Import-Linter) and test suites are fully passing.
- **Test Count & Coverage**: **47 tests passing** with **86% coverage** across all modules.

---

## 2. Completed Work
1. **Infrastructure Foundation (Milestone 3A)**:
   - Configured Pydantic Settings, setup structured JSON logging middlewares, and async database session lifecycle management.
   - Built declarative ORM schemas for `companies`, `documents`, and `financial_statements` with dialect-agnostic JSONB configurations.
2. **Identity & Authentication (Milestone 3B)**:
   - Implemented `User`, `Workspace`, and `WorkspaceMembership` entities in the domain layer.
   - Created concrete repository adapters: `SQLAlchemyUserRepository`, `SQLAlchemyWorkspaceRepository`, and `SQLAlchemyRefreshTokenRepository`.
   - Setup Bcrypt hashing (abstracted via `PasswordHasher` protocol) and JWT token operations (with **one-time-use refresh token rotation** and **`jti` replay protection**).
   - Exposed API endpoints for Register, Login, Refresh, Logout, and `/auth/me`.
3. **Repository Audit & Improvements**:
   - Enforced foreign key constraints on `documents.workspace_id` -> `workspaces.id` and `documents.uploaded_by_id` -> `users.id`, making them non-nullable at the database schema layer to match the domain model's invariants.
   - Bootstrapped database migrations with Alembic and verified batch migrations for SQLite and PostgreSQL.

---

## 3. Next Milestone: Milestone 3C (Workspace & Company Management)
The next objective is to implement Company CRUD operations and row-level workspace scoping:
- **Company CRUD Routes**: Provide REST endpoints under `/companies` to create, read, update, and delete company records.
- **Workspace Scoping**: Enforce row-level security boundaries where all assets (documents, statements, valuations) queried or modified must validate the user's workspace membership.
- **FastAPI DI Helpers**: Implement workspace context dependencies verifying membership roles before route execution.

---

## 4. Dependencies & Security Decisions
- **Token Rotation**: Consumed refresh tokens are immediately flagged as revoked in the database. Ensure any refresh token verification checks both expiry and the `is_revoked` state.
- **`jti` Claim**: Every generated access/refresh token has a unique JWT ID (`jti`) to prevent duplicates during rapid integration testing.
- **Transactional Register**: Registration, workspace creation, membership association, and token insertion must be executed in a single transaction block.

---

## 5. Recommended Starting Point for Next Session
1. Navigate to the `backend/` directory.
2. Review company query filters in [test_repositories.py](file:///c:/Users/Shrey/OneDrive/Desktop/Study%20material%20AI&DS/Projects/EquityIQ/backend/tests/integration/test_repositories.py).
3. Create the company routes under `backend/app/api/v1/companies.py` and register the router inside `app/main.py`.
4. Inject workspace validation dependencies (`get_current_workspace` or `require_workspace_membership`) into the company endpoints.
5. Verify changes by executing:
   ```bash
   python -m pytest backend/
   ```
