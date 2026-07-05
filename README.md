# EquityIQ

EquityIQ is a production-grade investment analysis and research platform built on Clean Architecture and Domain-Driven Design (DDD) principles. It automates financial statement normalization, DCF valuations, comps analysis, news sentiment parsing, and RAG-driven qualitative reports with strict mathematical traceability.

---

## Current Implementation Status
- **Build Status**: **Passing** (Ruff, MyPy, Import-Linter green)
- **Domain Model State**: **DOMAIN MODEL FROZEN** (Sealed contract for downstream persistence and service layers)
- **Test coverage**: **97.06%** coverage on active core Domain & Financial Engine files (38 passed unit tests)

---

## Technology Stack

| Layer | Mandated Technology | Role |
|---|---|---|
| **Language** | Python 3.12+ / TypeScript | Core Backend / Frontend |
| **Backend** | FastAPI | Async Web API Framework |
| **Database** | PostgreSQL / SQLAlchemy (async) | Relational Storage & ORM |
| **Migrations**| Alembic | DB Schema Migrations |
| **Task Queue**| Celery / Redis | Async Parsing and Embeddings processing |
| **Orchestration**| LangChain & LlamaIndex | Agent Tool Calling & Filing Table parsing |
| **Vector DB** | FAISS (local, self-hosted) | Embedded Contextual Retrieval |
| **Frontend** | React / Next.js (App Router) | Interactive User Interface |
| **UI Styling** | Tailwind CSS / Material UI (MUI) | Design Tokens and Complex Primitives |

---

## Architectural Layers

EquityIQ strictly enforces **Clean Architecture** boundaries where dependencies only flow inward:

```
  [ Infrastructure / API ]
          │
          ▼
    [ Application ]
          │
          ▼
       [ Domain ] (Framework-Free)
```

1. **Domain Layer (`app/domain/`)**: Contains pure Python definitions of entities (`Company`, `Document`, `FinancialStatement`, `Ratio`, `Valuation`, `Recommendation`), value objects (`Ticker`, `Exchange`, `Money`, `FiscalPeriod`), exceptions, and abstract Protocols standardizing operations.
2. **Application Layer (`app/application/`)**: Coordinates use cases through services (parsing, ratio calculation, DCF math, recommendation engines) relying purely on domain abstractions.
3. **Infrastructure Layer (`app/infrastructure/`)**: Standard adapters implementing the domain protocols (SQLAlchemy DB models, FAISS indexing, OpenAI/Gemini clients).
4. **API Layer (`app/api/`)**: Lightweight FastAPI routers translating REST payloads directly to application layer inputs.

---

## Project Directory Tree
```
equityiq/
├── backend/
│   ├── app/
│   │   ├── domain/            # PURE Domain layer (Entities, Value Objects, rules, interfaces)
│   │   ├── application/       # Application services orchestrating use cases
│   │   ├── infrastructure/    # Concrete adapters (SQLAlchemy, Celery, FAISS, OpenAI)
│   │   ├── api/               # FastAPI routers
│   │   └── workers/           # Celery task definitions
│   ├── tests/
│   │   └── unit/              # Core Domain and Financial Engine unit tests
│   ├── .import-linter.cfg     # Enforces clean boundary limits
│   └── pyproject.toml         # Python packaging and linting specifications
├── frontend/                  # React/Next.js/TS frontend application
├── infra/                     # Local Postgres & Redis Docker Compose services
├── docs/                      # Architectural ADRs, Interview notes, and Tech Debt logs
└── Makefile                   # Development shortcuts
```

---

## Developer Commands

Shortcuts are managed via the root-level `Makefile`:

- **Install Dependencies**:
  ```bash
  make install
  ```
- **Run Containers (Postgres + Redis)**:
  ```bash
  make docker
  ```
- **Format Code**:
  ```bash
  make format
  ```
- **Lint Code (Ruff + MyPy + Import-Linter)**:
  ```bash
  make lint
  ```
- **Run Tests**:
  ```bash
  make test
  ```

---

## Project Roadmap

- [x] **Milestone 1**: Scaffolding and CI Configuration
- [x] **Milestone 2**: Domain Layer Modeling and Math Engine (Model Frozen)
- [ ] **Milestone 3**: Auth + Workspace + Company CRUD (FastAPI + SQLAlchemy)
- [ ] **Milestone 4**: Ingestion Pipeline (Upload + Text Extract + Table Parse)
- [ ] **Milestone 5**: Financial Extraction, Normalization, & Precedence Checks
- [ ] **Milestone 6**: Vector Storage Pipeline & Hybrid Search Retrieval
- [ ] **Milestone 7**: LLM Integration, Prompt-Injection Filters, Q&A Agent
- [ ] **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
- [ ] **Milestone 9**: Report Drafting & SSE Streaming Generation
- [ ] **Milestone 10**: Frontend Application UI Implementation
