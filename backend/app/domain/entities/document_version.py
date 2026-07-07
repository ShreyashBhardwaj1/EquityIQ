"""
DocumentVersion entity representing historical versions of document metadata.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentVersion(BaseModel):
    """
    Tracks audit versions of a document when files or metadata are updated.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Unique identifier for the version record")
    document_id: UUID = Field(description="Associated document ID")
    version: int = Field(ge=1, description="Version increment number")
    storage_path: str = Field(min_length=1, description="Path in local storage")
    changed_by: UUID = Field(description="UUID of user initiating change")
    change_reason: str = Field(min_length=1, description="Why document was updated")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
