"""
FAISS VectorStore adapter implementation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import faiss
import numpy as np

from app.core.config import settings
from app.domain.entities.embedding import Embedding
from app.domain.interfaces.repositories import VectorStore

logger = logging.getLogger("equityiq.infrastructure.vector_store")


class FaissVectorStore(VectorStore):
    """
    Concrete adapter using local FAISS CPU flat indexes to search and store document embeddings.
    """

    def __init__(self, base_path: str = "storage/indices") -> None:
        """
        Initialize the FAISS store mapping workspace indices in memory.
        """
        self.base_path = Path(base_path)
        self.version = settings.VECTOR_INDEX_VERSION

        # Memory cache for active indices, mappings and configurations
        self.indices: dict[UUID, faiss.IndexFlatIP] = {}
        self.mappings: dict[UUID, list[UUID]] = {}
        self.metadata: dict[UUID, dict[str, Any]] = {}

    def _get_workspace_dir(self, workspace_id: UUID) -> Path:
        """
        Return the versioned index directory for a workspace.
        """
        return self.base_path / self.version / f"workspace_{workspace_id}"

    def _init_empty_index(self, workspace_id: UUID) -> faiss.IndexFlatIP:
        """
        Create and cache an empty IndexFlatIP for a workspace.
        """
        dimension = settings.EMBEDDING_DIMENSION
        index = faiss.IndexFlatIP(dimension)
        self.indices[workspace_id] = index
        self.mappings[workspace_id] = []
        self.metadata[workspace_id] = {
            "version": self.version,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "embedding_dimension": dimension,
            "chunk_count": 0,
        }
        return index

    async def add_embeddings(
        self, workspace_id: UUID, embeddings: list[Embedding]
    ) -> None:
        """
        Add a batch of vector embeddings to the workspace index.
        """
        if not embeddings:
            return

        # Ensure index exists in memory cache
        if workspace_id not in self.indices:
            await self.load_index(workspace_id)

        index = self.indices[workspace_id]
        mapping = self.mappings[workspace_id]
        meta = self.metadata[workspace_id]

        # Convert vectors list to float32 numpy array
        vectors = np.array([e.vector for e in embeddings], dtype=np.float32)

        # FAISS IndexFlatIP expects vectors to be L2 normalized to perform Cosine Similarity via dot product
        # Ensure they are normalized (our SentenceTransformerAdapter already normalizes them, but let's double check)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1.0
        vectors = vectors / norms

        # Add to index
        index.add(vectors)

        # Update mapping and metadata
        for e in embeddings:
            mapping.append(e.chunk_id)

        meta["chunk_count"] = len(mapping)
        logger.info(
            f"Added {len(embeddings)} embeddings to workspace index: {workspace_id}"
        )

    async def search(
        self,
        workspace_id: UUID,
        query_vector: list[float],
        limit: int,
        allowed_chunk_ids: list[UUID] | None = None,
    ) -> list[tuple[UUID, float]]:
        """
        Perform vector cosine similarity search with strict metadata pre-filtering.
        """
        # Load index if not already in memory cache
        if workspace_id not in self.indices:
            await self.load_index(workspace_id)

        index = self.indices[workspace_id]
        mapping = self.mappings[workspace_id]

        # Handle empty index
        if index.ntotal == 0 or not mapping:
            return []

        # Setup query vector
        query_np = np.array([query_vector], dtype=np.float32)
        # Normalize query vector for cosine similarity
        query_norm = np.linalg.norm(query_np)
        if query_norm > 0:
            query_np = query_np / query_norm

        # Configure ID Selector if pre-filtering chunk list is provided
        params = None
        if allowed_chunk_ids is not None:
            # Map allowed UUIDs to their integer offsets in our mapping list
            allowed_set = set(allowed_chunk_ids)
            allowed_indices = [
                idx for idx, cid in enumerate(mapping) if cid in allowed_set
            ]

            # If none of the allowed chunks are in our index mapping, return empty immediately
            if not allowed_indices:
                return []

            allowed_arr = np.array(allowed_indices, dtype=np.int64)
            selector = faiss.IDSelectorBatch(allowed_arr)
            params = faiss.SearchParameters()
            params.sel = selector

        # Run search
        # Limit cannot exceed total available indices
        search_limit = min(limit, index.ntotal)
        if search_limit <= 0:
            return []

        distances, indices = index.search(query_np, search_limit, params=params)

        # Package results
        results = []
        for dist, idx in zip(distances[0], indices[0], strict=False):
            if idx != -1:
                # Retrieve the UUID corresponding to the offset returned by FAISS
                chunk_uuid = mapping[idx]
                # Scale dot product score (should be between -1.0 and 1.0)
                results.append((chunk_uuid, float(dist)))

        return results

    async def delete_by_document(
        self, workspace_id: UUID, document_id: UUID, chunk_ids: list[UUID]
    ) -> None:
        """
        Placeholder for delete scoping. Since flat indices reorder indices on deletion,
        incremental deletions require complete index manager rebuild coordination.
        """
        # Remove IDs from mapping cache
        if workspace_id in self.mappings:
            mapping = self.mappings[workspace_id]
            to_remove = set(chunk_ids)
            self.mappings[workspace_id] = [
                cid for cid in mapping if cid not in to_remove
            ]
            if workspace_id in self.metadata:
                self.metadata[workspace_id]["chunk_count"] = len(
                    self.mappings[workspace_id]
                )

    async def save_index(self, workspace_id: UUID) -> None:
        """
        Serialize index weights and mapping configuration metadata to disk.
        """
        if workspace_id not in self.indices:
            return

        index = self.indices[workspace_id]
        mapping = self.mappings[workspace_id]
        meta = self.metadata[workspace_id]

        folder = self._get_workspace_dir(workspace_id)
        os.makedirs(folder, exist_ok=True)

        index_file = folder / "index.bin"
        meta_file = folder / "metadata.json"

        # Write FAISS index
        faiss.write_index(index, str(index_file))

        # Write mapping mapping along with config details
        meta_payload = {
            **meta,
            "chunk_id_mapping": [str(uid) for uid in mapping],
        }

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2)

        logger.info(
            f"Saved FAISS index and metadata configurations for workspace: {workspace_id}"
        )

    async def load_index(self, workspace_id: UUID) -> None:
        """
        Load index files and chunk mapping config from disk if they exist.
        """
        folder = self._get_workspace_dir(workspace_id)
        index_file = folder / "index.bin"
        meta_file = folder / "metadata.json"

        if not index_file.exists() or not meta_file.exists():
            # Initialize empty index if file is missing
            self._init_empty_index(workspace_id)
            return

        try:
            # Read index
            index = faiss.read_index(str(index_file))
            self.indices[workspace_id] = cast(faiss.IndexFlatIP, index)

            # Read metadata
            with open(meta_file, encoding="utf-8") as f:
                meta_payload = json.load(f)

            # Reconstruct mappings
            self.mappings[workspace_id] = [
                UUID(uid_str) for uid_str in meta_payload.pop("chunk_id_mapping", [])
            ]
            self.metadata[workspace_id] = meta_payload
            logger.info(f"Loaded FAISS index for workspace: {workspace_id} from disk")
        except Exception as e:
            logger.error(
                f"Failed to load FAISS index for workspace {workspace_id}: {e}"
            )
            self._init_empty_index(workspace_id)

    async def clear(self, workspace_id: UUID) -> None:
        """
        Clear all vector records and remove serialized files from disk.
        """
        self._init_empty_index(workspace_id)
        folder = self._get_workspace_dir(workspace_id)
        index_file = folder / "index.bin"
        meta_file = folder / "metadata.json"

        if index_file.exists():
            os.remove(index_file)
        if meta_file.exists():
            os.remove(meta_file)

        logger.info(f"Cleared FAISS workspace vector store for: {workspace_id}")
