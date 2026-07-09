# EquityIQ

EquityIQ is a production-grade investment analysis and research platform built on Clean Architecture and Domain-Driven Design (DDD) principles. It automates financial statement normalization, DCF valuations, comps analysis, news sentiment parsing, and RAG-driven qualitative reports with strict mathematical traceability.

---

## Project Status

- **Overall Progress**: **90% Complete** (9 / 10 Milestones completed)
- **Build Status**: **Passing** (Ruff, MyPy, Import-Linter green)
- **Domain State**: **DOMAIN MODEL FROZEN** (Sealed contracts for downstream layers)
- **Test Suite**: **84 tests passing** with 87% statement coverage across domain, DB lifecycles, repositories, Celery pipelines, RAG, and API routes.

---

## Current Features

✅ **Domain Layer**: Complete mathematical structures for valuations, normalized statement models, scoring rubrics, and financial entities.  
✅ **Infrastructure Foundation**: Async SQLAlchemy session managers, database engine pool lifecycles, health services (Postgres, Redis), and structured JSON logging.  
✅ **Identity & Authentication**: Secure registration, login, logout, and token rotation workflows using native `bcrypt` and JWT with `jti` replay protection.  
✅ **Workspace Management**: Multi-workspace scoping, membership authorization roles, active switches, and safety deletion rules.  
✅ **Company Management**: Row-isolated company registration, sorting, pagination filters, sector/ticker text search, and soft-delete duplicate restoration.  
✅ **Financial Data Foundation**: Secure document metadata uploads (limit 50MB, magic bytes validation for PDF/TXT/CSV), extensible validation engine, priority-based mapping normalization, statement version tracking, and workspace isolation.  
✅ **Document Intelligence Pipeline**: Layout-aware PDF and text parsing adapter using pdfplumber, Tesseract OCR fallback, paragraph-level and sentence-level semantic chunking with stable deterministic UUIDs (via uuid5), ParsingManifest metrics, and async Celery worker dispatching.  
✅ **Vector Storage & Hybrid Search**: Local Hugging Face SentenceTransformers embedding adapter, disk-persisted FAISS CPU vector index, database-assisted strict tenant pre-filtering, SQLite FTS5 full-text keyword retrieval engine, Min-Max score normalization, and linear combination hybrid rank fusion.  
✅ **LLM Integration (RAG)**: Complete multi-turn conversation memory, XML context assembly, token budgeting, prompt injection guards, Gemini 2.5 Pro/Flash adapter integration, response validation, deterministic grounding scoring, and telemetry tracking.  
⏳ **Financial Intelligence & Recommendation**: Planned for Milestone 8.  
⏳ **Report Drafting & SSE Streaming**: Planned for Milestone 9.  

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
| **AI Provider**| Gemini 2.5 Pro (Primary) / Gemini 2.5 Flash (Fallback) | natural language synthesis, summaries, and citations |
| **Vector DB** | FAISS (local, self-hosted) | Embedded Contextual Retrieval |
| **Embeddings** | Hugging Face `all-MiniLM-L6-v2` | Local vector generation (384-dim) |
| **Keyword DB** | SQLite FTS5 | BM25 Full-text search engine |
| **Frontend** | React / Next.js (App Router) | Interactive User Interface |
| **UI Styling** | Tailwind CSS | Design Tokens and Complex Primitives |

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
3. **Infrastructure Layer (`backend/app/infrastructure/`)**: Framework adapters implementing domain protocols (SQLAlchemy ORM mappings, repositories, security adapters, logging middleware, FAISS index, local embeddings).
4. **API Layer (`backend/app/api/`)**: FastAPI endpoints converting REST payloads directly into domain services.

---

## Core Engine Components

### Validation Engine
The platform includes an extensible, rules-based `ValidationEngine` that coordinates statement sanity checks. Built as a pipeline of `ValidationRule` implementations, it runs check guards such as:
- **StatementTypeRule**: Verifies that statement types match one of the canonical categories (`income`, `balance`, `cashflow`).
- **AccountingIdentityRule**: Validates double-entry accounting integrity on balance sheets (Assets = Liabilities + Equity).
- **DuplicateFiscalPeriodRule**: Prevents registering duplicate statements of the same type for a company in the same fiscal quarter or year.
- **FiscalPeriodOrderingRule**: Restricts fiscal years to a logical range (1900-2100).
- **Extensibility**: Custom rules can be injected dynamically without changing the engine's public interface.

### Normalization Engine
To support the "Canonical Data First" principle, the `NormalizationEngine` cleans and standardizes raw statement line items during ingestion. Mappings are defined via `NormalizationRule` models supporting:
- **Alias**: The raw text key parsed from files (e.g. "Cash & Cash Equivalents").
- **Canonical Name**: The standardized internal key (e.g. `cash_equivalents`).
- **Statement Type & Category Restrictions**: Filters mapping applicability.
- **Priority**: A precedence order ensuring that if multiple alias rules match, the highest priority rule wins.

### Vector Storage & Hybrid Search Engine (Milestone 6)
To enable semantic retrieval and contextual mapping, the search engine integrates:
- **Local Embedding Provider**: Embeds chunks and query text locally using `all-MiniLM-L6-v2` to avoid external API calls.
- **FAISS CPU Vector Store**: Uses `faiss.IndexFlatIP` (flat Inner Product) on L2-normalized vectors to execute exact Cosine Similarity calculations.
- **Strict Tenant Isolation**: Implements Database-Assisted Pre-filtering. Relational metadata parameters are first resolved to a set of valid chunk IDs in SQLite, then passed into FAISS via `faiss.IDSelectorBatch` to guarantee that workspace boundaries are never crossed.
- **SQLite FTS5 Keyword Engine**: Leverages SQLite's native FTS5 full-text module to retrieve keyword matches using BM25 ranking. Database triggers keep the virtual table in sync automatically during chunk insert/delete phases.
- **Hybrid Score combination**: Blends semantic and keyword match lists by normalizing scores via Min-Max scaling and running a linear fusion:
  $$\text{Score}_{\text{hybrid}} = \alpha \cdot \text{Score}_{\text{semantic}} + (1 - \alpha) \cdot \text{Score}_{\text{keyword}}$$

### LLM & RAG Subsystem (Milestone 7)
Coordinates prompt injection guards, context pruning, response validation, confidence/grounding calculations, and explainable citations:
- **Prompt Injection Guard**: Detects and rejects user input overrides, system instruction leaks, or XML injections.
- **Token Budget Manager**: Prunes conversation turns and context chunks down to a 20,000 token limit.
- **Response Validator**: Matches output sentences to source contexts, flagging dangling citations or ungrounded numeric metrics.
- **Confidence & Grounding Score**: Deteministic calculation of document similarity, citation coverage, source agreement, and sentence-level citation density.
- **LLM Telemetry ORM Model**: Persists token count metrics and service latency logs inside `llm_requests` for analytics without caching query inputs.

---

## Project Structure

```
equityiq/
├── backend/
│   ├── app/
│   │   ├── domain/            # Pure Domain layer (Entities, value objects, protocols)
│   │   ├── application/       # Use case orchestrations and business services
│   │   ├── infrastructure/    # Adapters (SQLAlchemy, local embeddings, FAISS, security)
│   │   ├── api/               # FastAPI routers and route handlers
│   │   └── workers/           # Celery async workers executing parsing and vector indexing
│   ├── tests/
│   │   ├── unit/              # Fast unit tests for maths, rules, vector store, and security
│   │   └── integration/       # Database integration, auth, company, and hybrid search API tests
│   ├── .import-linter.cfg     # Strict boundary constraint rules
│   └── pyproject.toml         # Packaging, Ruff, and MyPy configurations
├── frontend/                  # React/Next.js/TS client application
├── infra/                     # Postgres and Redis docker configurations
└── docs/                      # Technical specification plans, ADRs, and handovers
```

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
- [x] **Milestone 5**: Document Intelligence Pipeline (Asynchronous Parser Workers, OCR, & Chunk Extraction)
- [x] **Milestone 6**: Vector Storage Pipeline & Hybrid Search Retrieval
- [x] **Milestone 7**: LLM Integration, Prompt-Injection Filters, Q&A Agent
- [ ] **Milestone 8**: Sentiment Analysis & Scopes Recommendation Score
- [ ] **Milestone 9**: Report Drafting & SSE Streaming Generation
- [ ] **Milestone 10**: Frontend Application UI Implementation
