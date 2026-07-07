"""
Workspace API Router.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.workspace_service import WorkspaceService
from app.core.dependencies import get_current_user, get_workspace_service
from app.domain.entities.user import User
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class WorkspaceCreate(BaseModel):
    """
    Workspace creation request payload.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the workspace",
    )


class WorkspacePatch(BaseModel):
    """
    Workspace partial update request payload.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Optional updated display name",
    )


class WorkspaceResponse(BaseModel):
    """
    Workspace response model.
    """

    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class SwitchResponse(BaseModel):
    """
    Switch active workspace response mapping.
    """

    detail: str
    workspace_id: UUID


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceResponse:
    """
    Creates a new workspace and makes the requesting user its owner.
    """
    workspace = await workspace_service.create_workspace(
        name=request.name, owner_id=current_user.id
    )
    await session.commit()
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> list[WorkspaceResponse]:
    """
    Lists all active workspaces the user belongs to.
    """
    workspaces = await workspace_service.list_user_workspaces(current_user.id)
    return [
        WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            owner_id=ws.owner_id,
            created_at=ws.created_at,
            updated_at=ws.updated_at,
        )
        for ws in workspaces
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    """
    Retrieves details of a specific workspace, checking user membership.
    """
    workspace = await workspace_service.get_workspace(
        workspace_id=workspace_id, user_id=current_user.id
    )
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def patch_workspace(
    workspace_id: UUID,
    request: WorkspacePatch,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceResponse:
    """
    Partially updates workspace settings (Owner/Admin privileges required).
    """
    workspace = await workspace_service.update_workspace(
        workspace_id=workspace_id, user_id=current_user.id, name=request.name
    )
    await session.commit()
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Soft-deletes (archives) a workspace. Rejects if user has no other active workspaces.
    """
    await workspace_service.delete_workspace(
        workspace_id=workspace_id, user_id=current_user.id
    )
    await session.commit()
    return {"detail": "Workspace archived successfully."}


@router.post("/{workspace_id}/switch", response_model=SwitchResponse)
async def switch_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> SwitchResponse:
    """
    Verifies that the current user has valid membership access to switch to this workspace.
    """
    await workspace_service.get_workspace(
        workspace_id=workspace_id, user_id=current_user.id
    )
    return SwitchResponse(
        detail="Workspace active context switched successfully.",
        workspace_id=workspace_id,
    )
