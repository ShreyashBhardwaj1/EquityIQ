"""
IndexBuilder application service.
"""

import time
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.entities.document import ParsingStatus
from app.domain.entities.embedding import Embedding
from app.domain.entities.embedding_manifest import EmbeddingManifest
from app.domain.interfaces.repositories import (
    ChunkRepository,
    DocumentRepository,
    EmbeddingManifestRepository,
    EmbeddingProvider,
    EmbeddingRepository,
    VectorStore,
)


class IndexBuilder:
    """
    Coordinates document indexing execution runs and index rebuild processes.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        """
        Initialize with provider and store adapters.
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    async def build_index_for_document(
        self,
        workspace_id: UUID,
        document_id: UUID,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
        manifest_repo: EmbeddingManifestRepository,
    ) -> EmbeddingManifest | None:
        """
        Generate embeddings for a document's chunks, save them, and update the FAISS index.
        """
        chunks = await chunk_repo.list_by_document(document_id, limit=10000)
        if not chunks:
            return None

        # Track execution duration
        start_time = time.perf_counter()

        # Embed all texts batch-wise
        texts = [c.content for c in chunks]
        vectors = await self.embedding_provider.embed_documents(texts)

        # Create domain entities
        embeddings = [
            Embedding(
                id=uuid4(),
                chunk_id=chunk.id,
                vector=vector,
                model_name=self.embedding_provider.get_model_name(),
                embedding_version=1,
                created_at=datetime.utcnow(),
            )
            for chunk, vector in zip(chunks, vectors, strict=False)
        ]

        # Save to database
        await embedding_repo.save_batch(embeddings)

        # Add to FAISS index and serialize
        await self.vector_store.add_embeddings(workspace_id, embeddings)
        await self.vector_store.save_index(workspace_id)

        duration = time.perf_counter() - start_time

        # Create and save embedding manifest audit record
        manifest = EmbeddingManifest(
            id=uuid4(),
            embedding_model=self.embedding_provider.get_model_name(),
            embedding_dimension=self.embedding_provider.get_dimension(),
            normalized=True,
            duration=duration,
            chunk_count=len(embeddings),
            workspace_id=workspace_id,
            created_at=datetime.utcnow(),
        )

        await manifest_repo.save(manifest)
        return manifest

    async def rebuild_workspace_index(
        self,
        workspace_id: UUID,
        doc_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
    ) -> None:
        """
        Reconstruct a workspace vector index from database chunk records.
        """
        # Clear vector index memory and disk files
        await self.vector_store.clear(workspace_id)

        # List all documents in the workspace
        documents = await doc_repo.list_by_workspace(workspace_id, limit=1000)
        if not documents:
            return

        all_embeddings: list[Embedding] = []

        # Re-index completed documents
        for doc in documents:
            if doc.parsing_status != ParsingStatus.COMPLETED:
                continue

            chunks = await chunk_repo.list_by_document(doc.id, limit=10000)
            if not chunks:
                continue

            chunk_ids = [c.id for c in chunks]
            # Fetch existing embeddings from DB
            embeddings = await embedding_repo.get_by_chunks(chunk_ids)

            # If some chunks are missing embeddings, generate them
            existing_chunk_ids = {e.chunk_id for e in embeddings}
            missing_chunks = [c for c in chunks if c.id not in existing_chunk_ids]

            if missing_chunks:
                texts = [c.content for c in missing_chunks]
                vectors = await self.embedding_provider.embed_documents(texts)
                new_embeddings = [
                    Embedding(
                        id=uuid4(),
                        chunk_id=c.id,
                        vector=vector,
                        model_name=self.embedding_provider.get_model_name(),
                        embedding_version=1,
                        created_at=datetime.utcnow(),
                    )
                    for c, vector in zip(missing_chunks, vectors, strict=False)
                ]
                await embedding_repo.save_batch(new_embeddings)
                embeddings.extend(new_embeddings)

            all_embeddings.extend(embeddings)

        # Load fresh embeddings into index
        if all_embeddings:
            await self.vector_store.add_embeddings(workspace_id, all_embeddings)
            await self.vector_store.save_index(workspace_id)
