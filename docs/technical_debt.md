# Technical Debt Register — EquityIQ

This document tracks known limitations, design trade-offs, and future optimizations deferred during the development phases of the EquityIQ project.

---

## 1. AI & RAG Subsystem

### 1.1 Prompt Response Caching
- **Description**: Implement a semantic caching layer (e.g. using Redis or a vector database cache) to intercept incoming user queries. If a semantically similar query was answered recently, serve the cached answer immediately.
- **Benefit**: Drastically reduces LLM latency and external API costs for repeated/common financial queries.
- **Status**: Deferred to release v1.1.0.

### 1.2 Multi-Provider Registry
- **Description**: Build a formal provider registry service allowing configuration-based hot-swapping between different LLM engines (Gemini, Claude, GPT, or local Ollama instances).
- **Benefit**: Prevents vendor lock-in and allows using specialized models for specific subsets of financial analysis tasks.
- **Status**: Deferred. Currently, provider selection is abstract but hard-wired to Gemini Pro with Flash fallback.

### 1.3 Token-Level Streaming
- **Description**: Expose token-level event streams (`Server-Sent Events` or `WebSockets`) from the LLM adapters up to the FastAPI API layers.
- **Benefit**: Enhances perceived performance and UI responsiveness during long answer generation tasks.
- **Status**: Scheduled for Milestone 9.

### 1.4 Retrieval Reranking Models
- **Description**: Add a post-retrieval reranking step (e.g., using Cohere Rerank or a local cross-encoder model) after hybrid retrieval scores are combined.
- **Benefit**: Selects the most contextually relevant chunks from the top 20 candidate chunks, improving synthesis precision.
- **Status**: Deferred.

### 1.5 Automated RAG Evaluation Datasets
- **Description**: Set up automated benchmarking scripts using Ragas or TruLens frameworks against golden test datasets.
- **Benefit**: Quantifies grounding correctness, context recall, and faithfulness metrics across prompt or chunking changes.
- **Status**: Deferred. Currently covered via manual verification and unit assertions.

---

## 2. Infrastructure & Database

### 2.1 Embedded Vector Database (FAISS-CPU)
- **Limitation**: FAISS-cpu operates in-memory. While perfect for zero-dependency local development and portfolios, it does not scale to millions of documents. Large indices will result in high memory footprints on application/worker servers.
- **Future Improvement**: Migrate to a managed cluster (Qdrant/Pinecone) or unified database extensions (`pgvector` in PostgreSQL). The transition is protected by the constructor-injected `VectorStore` Protocol.

### 2.2 In-Process Text Embeddings (Sentence-Transformers)
- **Limitation**: Embedding chunks locally on CPU utilizing `Sentence-Transformers` introduces processing latency for large document uploads.
- **Future Improvement**: Offload embedding tasks to a dedicated GPU worker pool or migrate to a cloud API (OpenAI/Gemini embeddings) behind the `EmbeddingProvider` interface.

### 2.3 Statement Cache Policies
- **Justification**: Financial filings are static once published. Repeatedly parsing statement text blocks or querying `yfinance` API risks hitting rate limits and raises latency.
- **Plan**: Implement Redis caching with permanent TTLs for parsed and normalized statement line items.

### 2.4 Dynamic Provider Config Hot-Swap
- **Justification**: Current configurations load `LLM_PROVIDER` and API keys during startup. Swapping providers requires container restarts.
- **Plan**: Support run-time configuration overrides to enable seamless provider fallbacks if an API experiences downtime.

### 2.5 Local Storage Setup
- **Justification**: Uploaded documents are saved directly to local directory storage (`storage/uploads`).
- **Plan**: Migrate to a cloud-native block storage adapter interface (e.g. AWS S3 or Google Cloud Storage) for multi-server production deployment.

### 2.6 Synchronous Ingestion Metadata
- **Resolution**: Layout-aware parsing, OCR fallback, validation, and chunk extraction are now fully offloaded to Celery background task workers via task queues (Resolved in Milestone 5).

---

## 3. Architectural Trade-offs & Rationale

### 3.1 Pydantic v2 in the Domain Layer
- **Trade-off**: Strictly speaking, Clean Architecture advocates for pure language structures (dataclasses) in the core domain to prevent any third-party dependency. We decided to allow `pydantic` in `domain/` for robust validation schemas.
- **Rationale**: Pydantic v2 is extremely fast (Rust core) and simplifies input constraints mapping without database/framework coupling. It aligns with spec constraints.

### 3.2 Dual-Write Sync Verification
- **Trade-off**: Deleting documents requires concurrent database and vector index deletions, creating a dual-write transaction risk.
- **Rationale**: We chose a nightly automated reconciliation worker pattern to clean up mismatched vectors rather than complex distributed locks, prioritizing system throughput.

---

## 4. Security & Performance Considerations

### 4.1 Local Model Memory Footprints
- PyTorch and Hugging Face sentence transformers require substantial memory. Local Celery workers must be provisioned with sufficient RAM limits ($\ge 2\text{GB}$) to prevent OOM events under load.

### 4.2 Production Secrets Injection
- Avoid storing passwords in `.env.production` files. Use secure environment variable injection via AWS Secrets Manager, HashiCorp Vault, or GitHub Secrets during deployment pipelines.

### 4.3 OCR Fallback Logging
- **Limitation**: When Tesseract is not installed locally, the PDF parser catches the error gracefully but logs a standard warning. On production systems that do not require OCR, these warnings can be ignored or filtered.
