# Technical Debt and Deferred Refinements

This document tracks engineering improvements and architecture modifications for the EquityIQ codebase that have been intentionally deferred to maintain release velocity.

---

## AI & RAG Subsystem

### 1. Prompt Response Caching
- **Description**: Implement a semantic caching layer (e.g. using Redis or a vector database cache) to intercept incoming user queries. If a semantically similar query was answered recently, serve the cached answer immediately.
- **Benefit**: Drastically reduces LLM latency and external API costs for repeated/common financial queries.
- **Status**: Deferred to release v1.1.0.

### 2. Multi-Provider Registry
- **Description**: Build a formal provider registry service allowing configuration-based hot-swapping between different LLM engines (Gemini, Claude, GPT, or local Ollama instances).
- **Benefit**: Prevents vendor lock-in and allows using specialized models for specific subsets of financial analysis tasks.
- **Status**: Deferred. Currently, provider selection is abstract but hard-wired to Gemini Pro with Flash fallback.

### 3. Token-Level Streaming
- **Description**: Expose token-level event streams (`Server-Sent Events` or `WebSockets`) from the LLM adapters up to the FastAPI API layers.
- **Benefit**: Enhances perceived performance and UI responsiveness during long answer generation tasks.
- **Status**: Deferred to Milestone 9.

### 4. Retrieval Reranking Models
- **Description**: Add a post-retrieval reranking step (e.g., using Cohere Rerank or a local cross-encoder model) after hybrid retrieval scores are combined.
- **Benefit**: Selects the most contextually relevant chunks from the top 20 candidate chunks, improving synthesis precision.
- **Status**: Deferred.

### 5. Automated RAG Evaluation Datasets
- **Description**: Set up automated benchmarking scripts using Ragas or TruLens frameworks against golden test datasets.
- **Benefit**: Quantifies grounding correctness, context recall, and faithfulness metrics across prompt or chunking changes.
- **Status**: Deferred. Currently covered via manual verification and unit assertions.
