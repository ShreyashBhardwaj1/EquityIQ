"""
SQLAlchemy repository adapter for DocumentChunk.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.document_chunk import ChunkMetadata, DocumentChunk
from app.domain.interfaces.repositories import ChunkRepository
from app.infrastructure.db.models.document_chunk import DocumentChunkORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyChunkRepository(BaseRepository[DocumentChunkORM], ChunkRepository):
    """
    SQLAlchemy-backed implementation of the ChunkRepository interface.
    """

    def _to_domain(self, orm: DocumentChunkORM) -> DocumentChunk:
        """Translates ORM model to Domain Entity."""
        meta = orm.metadata_json
        metadata = ChunkMetadata(
            workspace_id=UUID(meta["workspace_id"]),
            company_id=UUID(meta["company_id"]),
            document_id=UUID(meta["document_id"]),
            statement_type=meta.get("statement_type"),
            document_type=meta["document_type"],
            fiscal_year=meta.get("fiscal_year"),
            fiscal_period=meta.get("fiscal_period"),
            page_number=orm.page_number,
            chunk_index=orm.chunk_index,
            section_heading=orm.section_heading,
            source_file=meta["source_file"],
            parser_version=meta["parser_version"],
            document_version=meta.get("document_version", 1),
            parse_version=meta.get("parse_version", 1),
        )

        return DocumentChunk(
            id=orm.id,
            document_id=orm.document_id,
            content=orm.content,
            page_number=orm.page_number,
            chunk_index=orm.chunk_index,
            section_heading=orm.section_heading,
            metadata=metadata,
        )

    def _to_orm(self, domain: DocumentChunk) -> DocumentChunkORM:
        """Translates Domain Entity to ORM model."""
        meta = domain.metadata
        metadata_json = {
            "workspace_id": str(meta.workspace_id),
            "company_id": str(meta.company_id),
            "document_id": str(meta.document_id),
            "statement_type": meta.statement_type,
            "document_type": meta.document_type,
            "fiscal_year": meta.fiscal_year,
            "fiscal_period": meta.fiscal_period,
            "source_file": meta.source_file,
            "parser_version": meta.parser_version,
            "document_version": meta.document_version,
            "parse_version": meta.parse_version,
        }

        return DocumentChunkORM(
            id=domain.id,
            document_id=domain.document_id,
            content=domain.content,
            page_number=domain.page_number,
            chunk_index=domain.chunk_index,
            section_heading=domain.section_heading,
            metadata_json=metadata_json,
        )

    async def save(self, chunk: DocumentChunk) -> DocumentChunk:
        """
        Persists a single DocumentChunk.
        """
        orm = self._to_orm(chunk)
        self._add(orm)
        await self.session.flush()
        return self._to_domain(orm)

    async def save_batch(self, chunks: list[DocumentChunk]) -> None:
        """
        Persists a batch of DocumentChunks using standard SQLAlchemy session add_all.
        """
        if not chunks:
            return
        orms = [self._to_orm(c) for c in chunks]
        self.session.add_all(orms)
        await self.session.flush()

    async def list_by_document(
        self, document_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[DocumentChunk]:
        """
        Lists all chunks of a document ordered by chunk_index.
        """
        query = (
            select(DocumentChunkORM)
            .where(DocumentChunkORM.document_id == document_id)
            .order_by(DocumentChunkORM.chunk_index.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def delete_by_document(self, document_id: UUID) -> None:
        """
        Deletes all chunks of a document.
        """
        query = delete(DocumentChunkORM).where(
            DocumentChunkORM.document_id == document_id
        )
        await self.session.execute(query)
        await self.session.flush()

    async def get(self, chunk_id: UUID) -> DocumentChunk | None:
        """
        Retrieves a chunk by its ID.
        """
        query = select(DocumentChunkORM).where(DocumentChunkORM.id == chunk_id)
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None
