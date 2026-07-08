"""
Unit tests for FaissVectorStore and vector persistence.
"""

import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from app.domain.entities.embedding import Embedding
from app.infrastructure.vector_store.faiss_vector_store import FaissVectorStore


@pytest.fixture
def temp_store_dir() -> str:
    """
    Fixture yielding a temporary directory path for FAISS index testing.
    """
    path = "./test_storage_indices"
    os.makedirs(path, exist_ok=True)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.mark.asyncio
async def test_faiss_vector_store_operations(temp_store_dir: str) -> None:
    """
    Test standard CRUD, pre-filtering search, and serialization in FaissVectorStore.
    """
    store = FaissVectorStore(base_path=temp_store_dir)
    workspace_id = uuid4()

    # Generate test embeddings
    chunk_id_1 = uuid4()
    chunk_id_2 = uuid4()
    chunk_id_3 = uuid4()

    # 384-dimensional unit vectors (orthonormal basis vectors)
    vec1 = [0.0] * 384
    vec1[0] = 1.0  # [1, 0, 0, ...]

    vec2 = [0.0] * 384
    vec2[1] = 1.0  # [0, 1, 0, ...]

    vec3 = [0.0] * 384
    vec3[2] = 1.0  # [0, 0, 1, ...]

    e1 = Embedding(
        id=uuid4(), chunk_id=chunk_id_1, vector=vec1, model_name="test-model"
    )
    e2 = Embedding(
        id=uuid4(), chunk_id=chunk_id_2, vector=vec2, model_name="test-model"
    )
    e3 = Embedding(
        id=uuid4(), chunk_id=chunk_id_3, vector=vec3, model_name="test-model"
    )

    # Save to store
    await store.add_embeddings(workspace_id, [e1, e2, e3])

    # Verify memory cached mappings
    assert len(store.mappings[workspace_id]) == 3
    assert store.mappings[workspace_id][0] == chunk_id_1

    # Run search matching vec1 closely (cosine similarity)
    results = await store.search(workspace_id, query_vector=vec1, limit=5)
    assert len(results) == 3
    # First result should match chunk_id_1 exactly (score near 1.0)
    assert results[0][0] == chunk_id_1
    assert pytest.approx(results[0][1], abs=1e-5) == 1.0

    # Test pre-filtering: restrict allowed search items to chunk 2 and 3
    filtered_results = await store.search(
        workspace_id,
        query_vector=vec1,
        limit=5,
        allowed_chunk_ids=[chunk_id_2, chunk_id_3],
    )
    assert len(filtered_results) == 2
    # chunk_id_1 is excluded. Nearest allowed chunk should be returned
    returned_chunk_ids = [uid for uid, _ in filtered_results]
    assert chunk_id_1 not in returned_chunk_ids
    assert chunk_id_2 in returned_chunk_ids
    assert chunk_id_3 in returned_chunk_ids

    # Save index to disk
    await store.save_index(workspace_id)
    ws_dir = Path(temp_store_dir) / store.version / f"workspace_{workspace_id}"
    assert (ws_dir / "index.bin").exists()
    assert (ws_dir / "metadata.json").exists()

    # Clear memory cache and re-load from disk
    new_store = FaissVectorStore(base_path=temp_store_dir)
    await new_store.load_index(workspace_id)

    assert len(new_store.mappings[workspace_id]) == 3
    assert new_store.mappings[workspace_id][0] == chunk_id_1

    # Search reload verification
    reload_results = await new_store.search(workspace_id, query_vector=vec1, limit=5)
    assert reload_results[0][0] == chunk_id_1

    # Clear store
    await new_store.clear(workspace_id)
    assert not (ws_dir / "index.bin").exists()
