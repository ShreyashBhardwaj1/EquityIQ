# Architecture Overview: EquityIQ

EquityIQ is built on Clean Architecture and Domain-Driven Design (DDD) principles. This ensures that dependencies flow strictly inward:

```
  [ Infrastructure / API ]
          │
          ▼
    [ Application ]
          │
          ▼
       [ Domain ] (Framework-Free)
```

---

## 1. Architectural Layers

### Domain Layer (`backend/app/domain/`)
- Contains the enterprise business rules, entities (`Company`, `Document`, `FinancialStatement`, `Ratio`, `Valuation`, `Recommendation`, `User`, `Workspace`), value objects (`Ticker`, `Exchange`, `Money`, `FiscalPeriod`), and repository protocols.
- **Framework-Free**: Zero dependencies on databases, HTTP libraries, or AI frameworks.

### Application Layer (`backend/app/application/`)
- Coordinates business logic and orchestration services:
  - `CompanyService` / `WorkspaceService` / `FinancialStatementService`
  - `HybridSearchService` / `RAGService`
  - `FinancialIntelligenceService` / `ExplainabilityService` / `DashboardService`
- Purely depends on domain repository interfaces, not concrete implementations.

### Infrastructure Layer (`backend/app/infrastructure/`)
- Framework adapters implementing domain protocols:
  - SQLAlchemy ORM mappings and concrete repositories.
  - Hugging Face local embedding adapters (`SentenceTransformerAdapter`).
  - Local disk-backed FAISS vector store database adapters (`FaissVectorStore`).
  - SQLite FTS5 BM25 search adapters.
  - Gemini GenAI SDK adapters.

### API Layer (`backend/app/api/`)
- FastAPI endpoints mapping HTTP payloads, managing session lifecycles, and enforcing workspace tenancy scoping.

---

## 2. Core Subsystems & Pipelines

### Financial Data & Intelligence Pipeline (Milestone 8)
Calculates key ratios, trends, health scores, and recommends signals deterministically:
```
Financial Statement Ingestion
            │
            ▼
Registry-Driven Ratios Calculation (Excellent/Healthy/Watch/Weak/Critical)
            │
            ▼
Multi-Period Trend Analysis (Accelerating/Decelerating/Recovery/Decline/Stable/Volatile)
            │
            ▼
Weighted Health Scoring (Liquidity, Profitability, Leverage, Efficiency, Cash Flow, Growth)
            │
            ▼
Distress Risk Assessment (Severe/Moderate/Low)
            │
            ▼
Policy-Driven Recommendations (Buy/Hold/Sell) + History Audits
```

### Document Intelligence & Hybrid Search Pipeline
1.  **Ingestion**: Layout-aware `pdfplumber` parsers extract texts and convert tables to markdown.
2.  **Chunking**: Chunks generated deterministically via `uuid5` hashes.
3.  **Indexing**: Generates 384-dimension local vectors stored in flat FAISS database with SQLite FTS5 BM25 keyword indices.
4.  **Retrieval**: Combines semantic cosine similarity and BM25 FTS5 keyword results using Min-Max scaling and Linear Combination fusion:
    $$\text{Score}_{\text{hybrid}} = \alpha \cdot \text{Score}_{\text{semantic}} + (1 - \alpha) \cdot \text{Score}_{\text{keyword}}$$

### RAG Subsystem
Wires Hybrid Search and Gemini 2.5 Pro (with Flash fallback), validating prompts against injection guards and auditing response citations via grounding formulas:
$$\text{Grounding Score} = \frac{\text{Cited Sentences}}{\text{Total Sentences}}$$

---

## 3. Technology Stack & Boundaries
- **FastAPI**: Async HTTP endpoints.
- **SQLAlchemy + Alembic**: Database mapping and migration management.
- **FAISS (CPU)**: Local similarity searching.
- **SentenceTransformers (`all-MiniLM-L6-v2`)**: Local dense embeddings.
- **Celery + Redis**: Long-running asynchronous parser workers.
- **Gemini SDK (Pro/Flash)**: Grounded report drafting and citations.
- **Import-Linter**: Enforces clean boundary rules statically on every build.
