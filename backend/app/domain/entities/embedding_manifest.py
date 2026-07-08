"""
EmbeddingManifest domain entity representing execution metrics of a vector embedding run.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingManifest(BaseModel):
    """
    Domain entity tracking vector generation configurations and audit metrics.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Unique identifier for this manifest record")
    embedding_model: str = Field(description="Name/identifier of the model used")
    embedding_dimension: int = Field(
        gt=0, description="Length dimensions of generated vectors"
    )
    normalized: bool = Field(
        description="Whether vectors are unit-normalized (L2 normalization)"
    )
    duration: float = Field(ge=0.0, description="Embedding execution time in seconds")
    chunk_count: int = Field(
        ge=0, description="Total number of chunk embeddings generated"
    )
    workspace_id: UUID = Field(description="Associated workspace ID tenancy context")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
