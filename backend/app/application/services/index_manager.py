"""
IndexManager application service.
"""

import logging
from uuid import UUID

from app.domain.entities.embedding import Embedding
from app.domain.interfaces.repositories import VectorStore

logger = logging.getLogger("equityiq.application.index_manager")


class IndexManager:
    """
    Coordinates load, save, update, and deletion operations for workspace vector indices.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        """
        Initialize with VectorStore adapter dependency.
        """
        self.vector_store = vector_store

    async def load_workspace_index(self, workspace_id: UUID) -> None:
        """
        Force deserialization and cache load of a workspace vector index.
        """
        await self.vector_store.load_index(workspace_id)

    async def save_workspace_index(self, workspace_id: UUID) -> None:
        """
        Serialize and write active workspace vector index weights to disk.
        """
        await self.vector_store.save_index(workspace_id)

    async def clear_workspace_index(self, workspace_id: UUID) -> None:
        """
        Remove indices cache and delete files from storage uploads.
        """
        await self.vector_store.clear(workspace_id)

    async def append_workspace_embeddings(
        self, workspace_id: UUID, embeddings: list[Embedding]
    ) -> None:
        """
        Add new embeddings to the active workspace index.
        """
        if not embeddings:
            return
        await self.vector_store.add_embeddings(workspace_id, embeddings)
