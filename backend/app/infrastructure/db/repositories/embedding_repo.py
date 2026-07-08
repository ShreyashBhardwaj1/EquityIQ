"""
SQLAlchemy repository adapter for Embedding.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.embedding import Embedding
from app.domain.interfaces.repositories import EmbeddingRepository
from app.infrastructure.db.models.document_chunk import DocumentChunkORM
from app.infrastructure.db.models.embedding import EmbeddingORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyEmbeddingRepository(BaseRepository[EmbeddingORM], EmbeddingRepository):
    """
    SQLAlchemy-backed implementation of the EmbeddingRepository interface.
    """

    def _to_domain(self, orm: EmbeddingORM) -> Embedding:
        """Translates ORM model to Domain Entity."""
        return Embedding(
            id=orm.id,
            chunk_id=orm.chunk_id,
            vector=orm.vector,
            model_name=orm.model_name,
            embedding_version=orm.embedding_version,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: Embedding) -> EmbeddingORM:
        """Translates Domain Entity to ORM model."""
        return EmbeddingORM(
            id=domain.id,
            chunk_id=domain.chunk_id,
            vector=domain.vector,
            model_name=domain.model_name,
            embedding_version=domain.embedding_version,
            created_at=domain.created_at,
        )

    async def save(self, embedding: Embedding) -> Embedding:
        """
        Persists a single embedding.
        """
        orm = self._to_orm(embedding)
        self._add(orm)
        await self.session.flush()
        return self._to_domain(orm)

    async def save_batch(self, embeddings: list[Embedding]) -> None:
        """
        Persists a batch of embeddings using standard add_all.
        """
        if not embeddings:
            return
        orms = [self._to_orm(e) for e in embeddings]
        self.session.add_all(orms)
        await self.session.flush()

    async def get_by_chunk(self, chunk_id: UUID) -> Embedding | None:
        """
        Retrieves embedding record for a chunk.
        """
        query = select(EmbeddingORM).where(EmbeddingORM.chunk_id == chunk_id)
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_chunks(self, chunk_ids: list[UUID]) -> list[Embedding]:
        """
        Retrieves multiple embeddings by chunk IDs.
        """
        if not chunk_ids:
            return []
        query = select(EmbeddingORM).where(EmbeddingORM.chunk_id.in_(chunk_ids))
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def delete_by_document(self, document_id: UUID) -> None:
        """
        Deletes all embeddings associated with a document's chunks.
        """
        # Find all chunk IDs for the document
        chunk_query = select(DocumentChunkORM.id).where(
            DocumentChunkORM.document_id == document_id
        )
        chunk_result = await self.session.execute(chunk_query)
        chunk_ids = chunk_result.scalars().all()

        if not chunk_ids:
            return

        query = delete(EmbeddingORM).where(EmbeddingORM.chunk_id.in_(chunk_ids))
        await self.session.execute(query)
        await self.session.flush()
