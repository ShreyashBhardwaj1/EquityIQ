"""
EmbeddingService application service.
"""

from uuid import UUID

from app.application.services.index_builder import IndexBuilder
from app.domain.entities.embedding_manifest import EmbeddingManifest
from app.domain.interfaces.repositories import (
    ChunkRepository,
    EmbeddingManifestRepository,
    EmbeddingProvider,
    EmbeddingRepository,
)


class EmbeddingService:
    """
    Application service managing text vectorizations and coordinating document embedding runs.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        index_builder: IndexBuilder,
    ) -> None:
        """
        Initialize with injected dependencies.
        """
        self.embedding_provider = embedding_provider
        self.index_builder = index_builder

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate a unit-normalized vector embedding for a single string.
        """
        return await self.embedding_provider.embed_query(text)

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate unit-normalized vector embeddings for a list of strings.
        """
        return await self.embedding_provider.embed_documents(texts)

    async def generate_document_embeddings(
        self,
        workspace_id: UUID,
        document_id: UUID,
        chunk_repo: ChunkRepository,
        embedding_repo: EmbeddingRepository,
        manifest_repo: EmbeddingManifestRepository,
    ) -> EmbeddingManifest | None:
        """
        Delegates document indexing execution to the IndexBuilder.
        """
        return await self.index_builder.build_index_for_document(
            workspace_id=workspace_id,
            document_id=document_id,
            chunk_repo=chunk_repo,
            embedding_repo=embedding_repo,
            manifest_repo=manifest_repo,
        )
