# EquityIQ

EquityIQ is a production-grade investment analysis and research platform built on Clean Architecture and Domain-Driven Design (DDD) principles. It automates financial statement normalization, DCF valuations, comps analysis, news sentiment parsing, and RAG-driven qualitative reports with strict mathematical traceability.

---

## Project Status

- **Overall Progress**: **~62% Complete**
- **Build Status**: **Passing** (Ruff, MyPy, Import-Linter green)
- **Domain Model State**: **DOMAIN MODEL FROZEN** (Sealed contracts for downstream layers)
- **Test Suite**: **47 tests passing** with **86% coverage** across domain, DB lifecycles, repositories, and authentication routes.

---

## Current Features

✅ **Domain Layer**: Complete mathematical structures for valuations, normalized statement models, scoring rubrics, and financial entities.  
✅ **Infrastructure Foundation**: Async SQLAlchemy session managers, database engine pool lifecycles, health services (Postgres, Redis), and structured JSON logging.  
✅ **Identity & Authentication**: Secure registration, login, logout, and token rotation workflows using native `bcrypt` and JWT with `jti` replay protection.  
🚧 **Workspace & Company Management**: In Progress (Milestone 3C).  
⏳ **Financial Statement Ingestion**: Planned.  
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
| **Database** | PostgreSQL / SQLAlchemy (async) | Relational Storage & ORM |
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

## Project Structure

```
equityiq/
├── backend/
│   ├── app/
│   │   ├── domain/            # Pure Domain layer (Entities, value objects, protocols)
│   │   ├── application/       # Use case orchestrations and business services
│   │   ├── infrastructure/    # Adapters (SQLAlchemy, security, logging, external APIs)
│   │   ├── api/               # FastAPI routers and route handlers
│   │   └── workers/           # Celery async workers
│   ├── tests/
│   │   ├── unit/              # Fast unit tests for maths, rules, and security
│   │   └── integration/       # Database integration and auth lifecycle tests
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

# 4. Check clean architecture imports
C:\Users\Shrey\AppData\Roaming\Python\Python314\Scripts\import-linter.exe lint --config backend/.import-linter.cfg

# 5. Run full test suite with coverage report
python -m pytest backend/ --cov=app --cov-report=term-missing
```

---

## Project Roadmap

- [x] **Milestone 1**: Scaffolding and CI Configuration
- [x] **Milestone 2**: Domain Layer Modeling and Math Engine
- [x] **Milestone 3A**: Infrastructure Foundation (Database Manager, ORMs, JSON Logging)
- [x] **Milestone 3B**: Identity & Authentication Platform (Bcrypt, JWT, Session Rotation)
- [ ] **Milestone 3C**: Workspace & Company Management (FastAPI + Row-Level Security)
- [ ] **Milestone 4**: Ingestion Pipeline (Upload + Text Extract + Table Parse)
- [ ] **Milestone 5**: Financial Extraction, Normalization, & Precedence Checks
- [ ] **Milestone 6**: Vector Storage Pipeline & Hybrid Search Retrieval
- [ ] **Milestone 7**: LLM Integration, Prompt-Injection Filters, Q&A Agent
- [ ] **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
- [ ] **Milestone 9**: Report Drafting & SSE Streaming Generation
- [ ] **Milestone 10**: Frontend Application UI Implementation
