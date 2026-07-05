# ADR 004: Local FAISS Vector Store and DB Synchronization

## Status
Proposed & Approved

## Problem
RAG systems require a vector store to retrieve semantic passages. While managed services (Qdrant, Pinecone) are common, they introduce external infrastructure dependencies, cost, and network latency during local portfolio development. However, using a local vector store runs the risk of a "dual-write" problem where the metadata database (Postgres) and the vector store become out of sync when documents are deleted or modified.

## Decision
1. **Self-hosted FAISS**: We will use a local, self-hosted `FAISS` index (via `faiss-cpu`) to keep the vector database embedded in the application workspace, avoiding external dependencies.
2. **VectorStore Interface**: Wrap FAISS operations in a clean `VectorStore` protocol in `domain/interfaces/` so swapping to a managed service later is a simple configuration change.
3. **Transaction / Nightly Sync Strategy**:
   - Deletions are executed in an all-or-nothing pattern: delete from FAISS first, then delete from Postgres (`document_chunks` table). If Postgres fails, the worker task is retried.
   - We introduce a `sync_status` field on `document_chunks` and a nightly reconciliation job that matches FAISS membership counts with the database rows, flagging and repairing orphaned chunks.

## Alternatives Considered
- **Managed Vector DB (Qdrant/Pinecone)**: Rejected for MVP to ensure zero dependency cost, but made swappable via the `VectorStore` interface.
- **pgvector in PostgreSQL**: While attractive for unified storage, compiling and running `pgvector` inside minimal Postgres images is more complex to set up locally across different operating systems. FAISS is extremely simple and fast to run locally in pure Python.

## Trade-offs
- **Pros**:
  - Zero external costs and zero internet dependence for vector queries.
  - Swapping to another vector DB is a configuration change.
  - Automated nightly reconciliation guarantees DB-vector consistency.
- **Cons**:
  - High memory usage if the index grows extremely large (though small for a portfolio/demo system).
  - Dual-write synchronization logic requires extra code.

## Consequences
- The FAISS index files will be stored in a local directory specified by `FAISS_INDEX_PATH` (or docker volume).
- Database operations must track the model version (`embedding_model_version`) to prevent mixing embeddings.
