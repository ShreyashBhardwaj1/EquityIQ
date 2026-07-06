"""
SQLAlchemy repository adapter for Workspace.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.workspace import Workspace, WorkspaceMembership
from app.domain.interfaces.repositories import WorkspaceRepository
from app.infrastructure.db.models.workspace import WorkspaceORM
from app.infrastructure.db.models.workspace_membership import (
    WorkspaceMembershipORM,
)
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyWorkspaceRepository(BaseRepository[WorkspaceORM], WorkspaceRepository):
    """
    SQLAlchemy-backed implementation of the WorkspaceRepository interface.
    """

    def _to_domain(self, orm: WorkspaceORM) -> Workspace:
        """Translates WorkspaceORM model to Domain Entity."""
        return Workspace(
            id=orm.id,
            name=orm.name,
            owner_id=orm.owner_id,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: Workspace) -> WorkspaceORM:
        """Translates Workspace Domain Entity to ORM model."""
        return WorkspaceORM(
            id=domain.id,
            name=domain.name,
            owner_id=domain.owner_id,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def _membership_to_domain(self, orm: WorkspaceMembershipORM) -> WorkspaceMembership:
        """Translates WorkspaceMembershipORM model to Domain Entity."""
        return WorkspaceMembership(
            id=orm.id,
            workspace_id=orm.workspace_id,
            user_id=orm.user_id,
            role=orm.role,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _membership_to_orm(self, domain: WorkspaceMembership) -> WorkspaceMembershipORM:
        """Translates WorkspaceMembership Domain Entity to ORM model."""
        return WorkspaceMembershipORM(
            id=domain.id,
            workspace_id=domain.workspace_id,
            user_id=domain.user_id,
            role=domain.role,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        """
        Retrieves a workspace by its UUID.
        """
        orm = await self._get(WorkspaceORM, workspace_id)
        return self._to_domain(orm) if orm else None

    async def save(self, workspace: Workspace) -> Workspace:
        """
        Persists a Workspace domain entity.
        """
        existing_orm = await self.session.get(WorkspaceORM, workspace.id)
        orm = self._to_orm(workspace)

        if existing_orm:
            existing_orm.name = orm.name
            existing_orm.owner_id = orm.owner_id
            existing_orm.updated_at = orm.updated_at
            await self.session.flush()
            return self._to_domain(existing_orm)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def list_by_user(self, user_id: UUID) -> list[Workspace]:
        """
        Lists workspaces owned by user or where user has membership.
        """
        query = (
            select(WorkspaceORM)
            .outerjoin(
                WorkspaceMembershipORM,
                WorkspaceORM.id == WorkspaceMembershipORM.workspace_id,
            )
            .where(
                (WorkspaceORM.owner_id == user_id)
                | (WorkspaceMembershipORM.user_id == user_id)
            )
            .distinct()
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def save_membership(
        self, membership: WorkspaceMembership
    ) -> WorkspaceMembership:
        """
        Persists a WorkspaceMembership entity.
        """
        existing_orm = await self.session.get(WorkspaceMembershipORM, membership.id)
        orm = self._membership_to_orm(membership)

        if existing_orm:
            existing_orm.workspace_id = orm.workspace_id
            existing_orm.user_id = orm.user_id
            existing_orm.role = orm.role
            existing_orm.updated_at = orm.updated_at
            await self.session.flush()
            return self._membership_to_domain(existing_orm)
        else:
            self.session.add(orm)
            await self.session.flush()
            return self._membership_to_domain(orm)

    async def get_membership(
        self, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMembership | None:
        """
        Retrieves a membership link by workspace and user.
        """
        query = select(WorkspaceMembershipORM).where(
            WorkspaceMembershipORM.workspace_id == workspace_id,
            WorkspaceMembershipORM.user_id == user_id,
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._membership_to_domain(orm) if orm else None

    async def delete_membership(self, workspace_id: UUID, user_id: UUID) -> None:
        """
        Deletes a user's membership in a workspace.
        """
        query = delete(WorkspaceMembershipORM).where(
            WorkspaceMembershipORM.workspace_id == workspace_id,
            WorkspaceMembershipORM.user_id == user_id,
        )
        await self.session.execute(query)
        await self.session.flush()
