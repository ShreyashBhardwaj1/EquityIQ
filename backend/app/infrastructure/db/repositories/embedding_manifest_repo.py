"""
SQLAlchemy repository adapter for EmbeddingManifest.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.embedding_manifest import EmbeddingManifest
from app.domain.interfaces.repositories import EmbeddingManifestRepository
from app.infrastructure.db.models.embedding_manifest import EmbeddingManifestORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyEmbeddingManifestRepository(
    BaseRepository[EmbeddingManifestORM], EmbeddingManifestRepository
):
    """
    SQLAlchemy-backed implementation of the EmbeddingManifestRepository interface.
    """

    def _to_domain(self, orm: EmbeddingManifestORM) -> EmbeddingManifest:
        """Translates ORM model to Domain Entity."""
        return EmbeddingManifest(
            id=orm.id,
            embedding_model=orm.embedding_model,
            embedding_dimension=orm.embedding_dimension,
            normalized=orm.normalized,
            duration=orm.duration,
            chunk_count=orm.chunk_count,
            workspace_id=orm.workspace_id,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: EmbeddingManifest) -> EmbeddingManifestORM:
        """Translates Domain Entity to ORM model."""
        return EmbeddingManifestORM(
            id=domain.id,
            embedding_model=domain.embedding_model,
            embedding_dimension=domain.embedding_dimension,
            normalized=domain.normalized,
            duration=domain.duration,
            chunk_count=domain.chunk_count,
            workspace_id=domain.workspace_id,
            created_at=domain.created_at,
        )

    async def save(self, manifest: EmbeddingManifest) -> EmbeddingManifest:
        """
        Persists a single embedding execution manifest record.
        """
        orm = self._to_orm(manifest)
        self._add(orm)
        await self.session.flush()
        return self._to_domain(orm)

    async def get_by_id(self, manifest_id: UUID) -> EmbeddingManifest | None:
        """
        Retrieves a manifest record by its unique ID.
        """
        query = select(EmbeddingManifestORM).where(
            EmbeddingManifestORM.id == manifest_id
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_workspace(self, workspace_id: UUID) -> list[EmbeddingManifest]:
        """
        Lists all manifests associated with a workspace.
        """
        query = select(EmbeddingManifestORM).where(
            EmbeddingManifestORM.workspace_id == workspace_id
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def delete_by_workspace(self, workspace_id: UUID) -> None:
        """
        Deletes all manifests for a workspace.
        """
        query = delete(EmbeddingManifestORM).where(
            EmbeddingManifestORM.workspace_id == workspace_id
        )
        await self.session.execute(query)
        await self.session.flush()
