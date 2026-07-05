# Technical Debt Register — EquityIQ

This document tracks known limitations, design trade-offs, and future optimizations deferred during the scaffolding and domain modeling phases of the EquityIQ project.

---

## 1. Known Limitations & Constraints

### 1.1 Embedded Vector Database (FAISS-CPU)
- **Status**: Current Decision
- **Limitation**: FAISS-cpu operates in-memory. While perfect for zero-dependency local development and portfolios, it does not scale to millions of documents. Large indices will result in high memory footprints on application/worker servers.
- **Future Improvement**: Migrate to a managed cluster (Qdrant/Pinecone) or unified database extensions (`pgvector` in PostgreSQL). The transition is protected by the constructor-injected `VectorStore` Protocol.

### 1.2 In-Process Text Embeddings (Sentence-Transformers)
- **Status**: Current Decision
- **Limitation**: Embedding chunks locally on CPU utilizing `Sentence-Transformers` introduces processing latency for large document uploads.
- **Future Improvement**: Offload embedding tasks to a dedicated GPU worker pool or migrate to a cloud API (OpenAI/Gemini embeddings) behind the `EmbeddingProvider` interface.

---

## 2. Deferred Architectural Improvements

### 2.1 Statement Cache Policies
- **Status**: Future Improvement
- **Justification**: Financial filings are static once published. Repeatedly parsing statement text blocks or querying `yfinance` API risks hitting rate limits and raises latency.
- **Plan**: Implement Redis caching with permanent TTLs for parsed and normalized statement line items.

### 2.2 Dynamic Provider Config Hot-Swap
- **Status**: Future Improvement
- **Justification**: Current configurations load `LLM_PROVIDER` and API keys during startup. Swapping providers requires container restarts.
- **Plan**: Support run-time configuration overrides to enable seamless provider fallbacks if an API experiences downtime.

---

## 3. Architectural Trade-offs & Rationale

### 3.1 Pydantic v2 in the Domain Layer
- **Trade-off**: Strictly speaking, Clean Architecture advocates for pure language structures (dataclasses) in the core domain to prevent any third-party dependency. We decided to allow `pydantic` in `domain/` for robust validation schemas.
- **Rationale**: Pydantic v2 is extremely fast (Rust core) and simplifies input constraints mapping without database/framework coupling. It aligns with spec constraints.

### 3.2 Dual-Write Sync Verification
- **Trade-off**: Deleting documents requires concurrent database and vector index deletions, creating a dual-write transaction risk.
- **Rationale**: We chose a nightly automated reconciliation worker pattern (details in ADR 004) to clean up mismatched vectors rather than complex distributed locks, prioritizing system throughput.

---

## 4. Security & Performance Considerations

### 4.1 Local Model Memory Footprints
- PyTorch and Hugging Face sentence transformers require substantial memory. Local Celery workers must be provisioned with sufficient RAM limits ($\ge 2\text{GB}$) to prevent OOM events under load.

### 4.2 Production Secrets Injection
- Avoid storing passwords in `.env.production` files. Use secure environment variable injection via AWS Secrets Manager, HashiCorp Vault, or GitHub Secrets during deployment pipelines.
