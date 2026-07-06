"""
Workspace and WorkspaceMembership entities representing resource boundaries.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Workspace(BaseModel):
    """
    Workspace boundary for scoping documents and reports.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str = Field(
        min_length=1, max_length=100, description="Display name of workspace"
    )
    owner_id: UUID = Field(description="User ID of the workspace owner")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record update timestamp"
    )


class WorkspaceMembership(BaseModel):
    """
    User membership role mapping inside a specific workspace.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str = Field(
        description="Role assigned to member (e.g., admin, analyst, viewer)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record update timestamp"
    )
