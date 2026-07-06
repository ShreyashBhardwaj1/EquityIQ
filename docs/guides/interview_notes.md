# EquityIQ — Technical Interview Preparation Notes

This document provides explanations of key architectural decisions, design patterns, and anticipated technical questions/answers based on the EquityIQ implementation.

---

## 1. Core Architectural Explanations

### 1.1 Clean Architecture
- **Concept**: Structure the system as concentric layers with dependencies pointing inward only.
- **Implementation**:
  - `Domain`: Defines business entities, value objects, mathematical rules, and repository protocols. Completely framework-free.
  - `Application`: Orchestrates use cases via services that depend only on domain entities and interfaces.
  - `Infrastructure`: Implements concrete adapters (SQLAlchemy repositories, OpenAI/Gemini clients, FAISS).
  - `API`: Thin FastAPI routers exposing application capabilities.
- **Rationale**: Isolates core business logic (our financial valuation algorithms) from technical changes. Swapping APIs, databases, or libraries doesn't impact our financial engine.

### 1.2 Domain-Driven Design (DDD)
- **Concept**: Align software structure with business concepts, using entities, value objects, and repository protocols.
- **Value Objects**: Immutable, validated representations of data defined by their values, not identities (e.g. `Money` ensures we cannot add USD and EUR; `FiscalPeriod` ensures consistent reporting dates).
- **Entities**: Objects with identities that are tracked over time (e.g. `Company` has a unique ID and exchange listing).
- **Invariants**: Enforced business constraints. For example, `FinancialStatement` validates that `Assets = Liabilities + Equity` inside the entity before saving.

### 1.3 Dependency Inversion & Dependency Injection (DI)
- **Concept**: High-level modules should not depend on low-level modules; both should depend on abstractions.
- **Implementation**: Application services depend on interfaces (`CompanyRepository` Protocol) and receive concrete database implementations via constructor injection (`__init__(self, repo: CompanyRepository)`).
- **Rationale**: Eliminates tight coupling. We can swap a database or mock an LLM client in tests by simply passing an alternative implementation of the Protocol.

---

## 2. Anticipated Technical Questions and Answers

### Q1: Why did you separate the financial engine from the LLM? Why not let the LLM calculate DCF and ratios?
**Answer**: 
LLMs are probabilistic models designed for linguistic synthesis and reasoning; they are not deterministic calculation engines. They frequently fail at multi-step arithmetic, rounding, and sensitivity grid generations (hallucinations). 
In EquityIQ, we enforce **Principle 2**: all calculations (DCF, margins, solvency ratios) are implemented in pure Python and fully unit-tested. The LLM's role is strictly narrative synthesis and context grounding, consuming only the validated outputs of the Python financial engine.

### Q2: How do you programmatically enforce that developers don't violate Clean Architecture boundaries?
**Answer**: 
We use `import-linter` inside the CI pipeline (`.github/workflows/ci.yml`). It reads `.import-linter.cfg` which defines a contract stating that the `app.domain` package is forbidden from importing external libraries like `fastapi`, `sqlalchemy`, `celery`, `langchain`, or `llama_index`. If a developer attempts to import SQLAlchemy or FastAPI in a domain file, the CI run fails automatically.

### Q3: Why did you choose Python's `typing.Protocol` instead of Abstract Base Classes (`abc.ABC`)?
**Answer**: 
`typing.Protocol` supports **structural typing** (duck typing) rather than nominal typing. It allows concrete classes in the infrastructure layer (e.g. `OpenAIProvider`) to satisfy the interface without importing or inheriting from a common base class defined in the domain layer. This minimizes package-level coupling, simplifies unit testing mocks, and makes provider-swaps fully transparent.

### Q4: How does the system handle data conflicts between filing data and live market APIs?
**Answer**: 
We enforce a strict **Data-Source Precedence Rule** (Section 8.2):
1. **Historical financial figures** (e.g., balance sheet values for a completed period): the extracted filing values are authoritative. We never override them with market estimates.
2. **Current variables** (e.g., share price or current shares outstanding used for market cap): the live market API (`yfinance`) is authoritative since it reflects post-filing stock buybacks or dilutive events.
3. **Discrepancy Logging**: Disagreements exceeding 0.5% are recorded in the `data_source_log` database column for auditability instead of being silently ignored.

### Q5: How do you address the "dual-write" consistency problem between the relational database and the vector store?
**Answer**: 
When deleting a document, we execute a sequential workflow:
1. Delete vectors from the FAISS index first (committed).
2. Delete the metadata rows from the Postgres database.
3. If step 2 fails, the Celery task retries.
To handle transient failures or index drift, we run a nightly reconciliation job that matches database chunk counts against FAISS index IDs, automatically marking orphaned chunks as `sync_status = orphaned` and pruning them.
