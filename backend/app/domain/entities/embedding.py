"""
Embedding domain entity representing a semantic vector representation of a document chunk.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Embedding(BaseModel):
    """
    Domain entity tracking generated vector weights for a document chunk.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Unique identifier for this embedding record")
    chunk_id: UUID = Field(description="Reference to the associated document chunk")
    vector: list[float] = Field(
        description="Numerical floating-point vector coordinates"
    )
    model_name: str = Field(
        description="Name/version index of the embedding model used"
    )
    embedding_version: int = Field(
        default=1, description="Schema version of generated embedding"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
