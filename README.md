# EquityIQ

EquityIQ is a production-grade investment analysis and research platform built on Clean Architecture and Domain-Driven Design (DDD) principles. It automates financial statement normalization, DCF valuations, comps analysis, news sentiment parsing, and RAG-driven qualitative reports with strict mathematical traceability.

---

## Project Status

- **Overall Progress**: **60% Complete** (6 / 10 Milestones completed)
- **Build Status**: **Passing** (Ruff, MyPy, Import-Linter green)
- **Domain State**: **DOMAIN MODEL FROZEN** (Sealed contracts for downstream layers)
- **Test Suite**: **59 tests passing** with clean coverage across domain, DB lifecycles, repositories, and API routes.

---

## Current Features

✅ **Domain Layer**: Complete mathematical structures for valuations, normalized statement models, scoring rubrics, and financial entities.  
✅ **Infrastructure Foundation**: Async SQLAlchemy session managers, database engine pool lifecycles, health services (Postgres, Redis), and structured JSON logging.  
✅ **Identity & Authentication**: Secure registration, login, logout, and token rotation workflows using native `bcrypt` and JWT with `jti` replay protection.  
✅ **Workspace Management**: Multi-workspace scoping, membership authorization roles, active switches, and safety deletion rules.  
✅ **Company Management**: Row-isolated company registration, sorting, pagination filters, sector/ticker text search, and soft-delete duplicate restoration.  
✅ **Financial Data Foundation**: Secure document metadata uploads (limit 50MB, magic bytes validation for PDF/TXT/CSV), extensible validation engine, priority-based mapping normalization, statement version tracking, and workspace isolation.  
⏳ **Document Intelligence Pipeline**: Planned (Milestone 5).  
⏳ **RAG Pipeline**: Planned.  
⏳ **AI Research Agent**: Planned.  
⏳ **Report Generation**: Planned.  

---

## Technology Stack

| Layer | Mandated Technology | Role |
|---|---|---|
| **Language** | Python 3.12+ / TypeScript | Core Backend / Frontend |
| **Backend** | FastAPI | Async Web API Framework |
| **Security** | PyJWT / bcrypt | Token lifecycle management and secure password hashing |
| **Database** | SQLite (dev/test) / PostgreSQL (prod) | Relational Storage & ORM |
| **Migrations**| Alembic | DB Schema Migrations |
| **Task Queue**| Celery / Redis | Async Parsing and Embeddings processing |
| **Orchestration**| LangChain & LlamaIndex | Agent Tool Calling & Filing Table parsing |
| **Vector DB** | FAISS (local, self-hosted) | Embedded Contextual Retrieval |
| **Frontend** | React / Next.js (App Router) | Interactive User Interface |
| **UI Styling** | Tailwind CSS / Material UI (MUI) | Design Tokens and Complex Primitives |

---

## Architecture Overview

EquityIQ strictly enforces **Clean Architecture** boundaries where dependencies only flow inward. This is statically checked on every build using `import-linter`.

```
  [ Infrastructure / API ]
          │
          ▼
    [ Application ]
          │
          ▼
       [ Domain ] (Framework-Free)
```

1. **Domain Layer (`backend/app/domain/`)**: Framework-free definitions of entities (`Company`, `Document`, `FinancialStatement`, `Ratio`, `Valuation`, `Recommendation`, `User`, `Workspace`), value objects (`Ticker`, `Exchange`, `Money`, `FiscalPeriod`), domain Exceptions, and abstract Repository Protocols.
2. **Application Layer (`backend/app/application/`)**: Coordinates business logic and orchestration services relying purely on domain abstractions.
3. **Infrastructure Layer (`backend/app/infrastructure/`)**: Framework adapters implementing domain protocols (SQLAlchemy ORM mappings, repositories, security services, logging middleware).
4. **API Layer (`backend/app/api/`)**: FastAPI endpoints converting REST payloads directly into domain services.

---

## Core Engine Components (Milestone 4)

### Validation Engine
The platform includes an extensible, rules-based `ValidationEngine` that coordinates statement sanity checks. Built as a pipeline of `ValidationRule` implementations, it runs check guards such as:
- **StatementTypeRule**: Verifies that statement types match one of the canonical categories (`income`, `balance`, `cashflow`).
- **AccountingIdentityRule**: Validates double-entry accounting integrity on balance sheets (Assets = Liabilities + Equity).
- **DuplicateFiscalPeriodRule**: Prevents registering duplicate statements of the same type for a company in the same fiscal quarter or year.
- **FiscalPeriodOrderingRule**: Restricts fiscal years to a logical range (1900-2100).
- **Extensibility**: Custom rules can be injected dynamically without changing the engine's public interface.

### Normalization Engine
To support the "Canonical Data First" principle, the `NormalizationEngine` cleans and standardizes raw statement line items during ingestion. Mappings are defined via `NormalizationRule` models supporting:
- **Alias**: The raw text key parsed from files (e.g. "Cash & Cash Equivalents", "Cash and cash equivalents").
- **Canonical Name**: The standardized internal key (e.g. `cash_equivalents`).
- **Statement Type & Category Restrictions**: Filters mapping applicability.
- **Priority**: A precedence order ensuring that if multiple alias rules match, the highest priority rule wins.

### Document & Statement Versioning
The system maintains a comprehensive, immutable audit trail of all changes:
- **Document Versions**: When a filing document's physical file is re-uploaded, the system retains a copy of the old file on disk and registers a `DocumentVersion` snapshot detailing who changed it, the reason for the change, and the timestamp.
- **Financial Statement Versions**: Updates to statement figures (raw line items or adjustments) generate a `FinancialStatementVersion` snapshot of the previous values before applying changes, preserving historical records for recovery and audits.

---

## Project Structure

```
equityiq/
├── backend/
│   ├── app/
│   │   ├── domain/            # Pure Domain layer (Entities, value objects, protocols)
│   │   ├── application/       # Use case orchestrations and business services
│   │   ├── infrastructure/    # Adapters (SQLAlchemy, security, logging, external APIs)
│   │   ├── api/               # FastAPI routers and route handlers
│   │   └── workers/           # Celery async workers (Deferred)
│   ├── tests/
│   │   ├── unit/              # Fast unit tests for maths, rules, and security
│   │   └── integration/       # Database integration and auth/workspace/company API tests
│   ├── .import-linter.cfg     # Strict boundary constraint rules
│   └── pyproject.toml         # Packaging, Ruff, and MyPy configurations
├── frontend/                  # React/Next.js/TS client application
├── infra/                     # Postgres and Redis docker configurations
└── docs/                      # Technical specification plans, ADRs, and handovers
```

---

## Documentation Links
All core design plans and handovers are located inside the `docs/` folder:
- [EquityIQ Build Specification](file:///c:/Users/Shrey/OneDrive/Desktop/Study%20material%20AI&DS/Projects/EquityIQ/docs/specifications/EquityIQ_BUILD_SPEC.md)
- [Architecture Review ADR](file:///C:/Users/Shrey/.gemini/antigravity/brain/92c7678d-6005-486f-b20e-e4ab6bc03a4e/domain_architecture_review.md)
- [Code Audit Report](file:///C:/Users/Shrey/.gemini/antigravity/brain/92c7678d-6005-486f-b20e-e4ab6bc03a4e/code_audit_report.md)
- [Latest Session Handover](file:///c:/Users/Shrey/OneDrive/Desktop/Study%20material%20AI&DS/Projects/EquityIQ/docs/guides/session_handover.md)

---

## Running the Project

### Prerequisite Setup
1. Create and populate environment variables:
   ```bash
   cp .env.example .env
   ```
2. Build and start local database services:
   ```bash
   docker compose -f infra/docker-compose.yml up -d
   ```

### Running Backend Service
1. Navigate to the backend directory and install dependencies:
   ```bash
   cd backend
   pip install -e .
   ```
2. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Open API Docs Swagger page: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Testing & Code Quality

Verify all validation contracts are satisfied:

```bash
# 1. Format code styling
python -m ruff format backend/

# 2. Run Ruff Lint checks
python -m ruff check backend/

# 3. Verify static type checks
python -m mypy backend/

# 4. Check clean architecture imports boundary rules
python -c "import sys; from importlinter.cli import import_linter; sys.exit(import_linter())" lint --config backend/.import-linter.cfg

# 5. Run full test suite with coverage report
python -m pytest backend/ --cov=app --cov-report=term-missing
```

---

## Project Roadmap

- [x] **Milestone 1**: Scaffolding and CI Configuration
- [x] **Milestone 2**: Domain Layer Modeling and Math Engine
- [x] **Milestone 3A**: Infrastructure Foundation (Database Manager, ORMs, JSON Logging)
- [x] **Milestone 3B**: Identity & Authentication Platform (Bcrypt, JWT, Session Rotation)
- [x] **Milestone 3C**: Workspace & Company Management (FastAPI + Row-Level Security)
- [x] **Milestone 4**: Financial Data Foundation (Statement Ingestion & Pipelines)
- [ ] **Milestone 5**: Document Intelligence Pipeline (Asynchronous Parser Workers, OCR, & Chunk Extraction)
- [ ] **Milestone 6**: Vector Storage Pipeline & Hybrid Search Retrieval
- [ ] **Milestone 7**: LLM Integration, Prompt-Injection Filters, Q&A Agent
- [ ] **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
- [ ] **Milestone 9**: Report Drafting & SSE Streaming Generation
- [ ] **Milestone 10**: Frontend Application UI Implementation
