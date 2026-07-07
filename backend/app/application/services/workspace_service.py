"""
Workspace application service.
"""

from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.domain.entities.workspace import Workspace, WorkspaceMembership
from app.domain.interfaces.repositories import WorkspaceRepository


class WorkspaceService:
    """
    Coordinates CRUD operations and rules for Workspace entities.
    """

    def __init__(self, workspace_repo: WorkspaceRepository) -> None:
        """
        Initializes WorkspaceService.
        """
        self.workspace_repo = workspace_repo

    async def create_workspace(self, name: str, owner_id: UUID) -> Workspace:
        """
        Creates a new workspace and automatically joins owner as owner role.
        """
        ws_id = uuid4()
        workspace = Workspace(id=ws_id, name=name, owner_id=owner_id)
        saved_ws = await self.workspace_repo.save(workspace)

        membership = WorkspaceMembership(
            id=uuid4(), workspace_id=ws_id, user_id=owner_id, role="owner"
        )
        await self.workspace_repo.save_membership(membership)
        return saved_ws

    async def get_workspace(self, workspace_id: UUID, user_id: UUID) -> Workspace:
        """
        Retrieves a workspace ensuring user membership exists.
        """
        membership = await self.workspace_repo.get_membership(workspace_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this workspace.",
            )

        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found.",
            )
        return workspace

    async def update_workspace(
        self, workspace_id: UUID, user_id: UUID, name: str | None = None
    ) -> Workspace:
        """
        Partially updates workspace fields (PATCH) if user is Owner/Admin.
        """
        membership = await self.workspace_repo.get_membership(workspace_id, user_id)
        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Owners or Admins may update the workspace.",
            )

        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found.",
            )

        updated_name = name if name is not None else workspace.name
        updated = Workspace(
            id=workspace.id,
            name=updated_name,
            owner_id=workspace.owner_id,
            created_at=workspace.created_at,
        )
        return await self.workspace_repo.save(updated)

    async def delete_workspace(self, workspace_id: UUID, user_id: UUID) -> None:
        """
        Soft deletes (archives) workspace if user is Owner and has remaining workspaces.
        """
        membership = await self.workspace_repo.get_membership(workspace_id, user_id)
        if not membership or membership.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Owners may delete a workspace.",
            )

        user_memberships = await self.workspace_repo.list_memberships_by_user(user_id)
        active_workspaces = []
        for m in user_memberships:
            ws = await self.workspace_repo.get_by_id(m.workspace_id)
            if ws:
                active_workspaces.append(ws)

        if len(active_workspaces) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user may never delete their last remaining workspace.",
            )

        await self.workspace_repo.delete(workspace_id)

    async def list_user_workspaces(self, user_id: UUID) -> list[Workspace]:
        """
        Lists all workspaces associated with the user.
        """
        return await self.workspace_repo.list_by_user(user_id)
