"""
SQLAlchemy repository adapter for ParsingManifest.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.parsing_manifest import ParsingManifest
from app.domain.interfaces.repositories import ParsingManifestRepository
from app.infrastructure.db.models.parsing_manifest import ParsingManifestORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyParsingManifestRepository(
    BaseRepository[ParsingManifestORM], ParsingManifestRepository
):
    """
    SQLAlchemy-backed implementation of the ParsingManifestRepository interface.
    """

    def _to_domain(self, orm: ParsingManifestORM) -> ParsingManifest:
        """Translates ORM model to Domain Entity."""
        return ParsingManifest(
            id=orm.id,
            document_id=orm.document_id,
            parser_version=orm.parser_version,
            chunk_strategy=orm.chunk_strategy,
            chunk_size=orm.chunk_size,
            overlap=orm.overlap,
            parse_duration=orm.parse_duration,
            chunk_count=orm.chunk_count,
            table_count=orm.table_count,
            warnings=list(orm.warnings),
            extraction_confidence=orm.extraction_confidence,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: ParsingManifest) -> ParsingManifestORM:
        """Translates Domain Entity to ORM model."""
        return ParsingManifestORM(
            id=domain.id,
            document_id=domain.document_id,
            parser_version=domain.parser_version,
            chunk_strategy=domain.chunk_strategy,
            chunk_size=domain.chunk_size,
            overlap=domain.overlap,
            parse_duration=domain.parse_duration,
            chunk_count=domain.chunk_count,
            table_count=domain.table_count,
            warnings=domain.warnings,
            extraction_confidence=domain.extraction_confidence,
            created_at=domain.created_at,
        )

    async def save(self, manifest: ParsingManifest) -> ParsingManifest:
        """
        Persists a ParsingManifest.
        """
        existing = await self.get_by_document(manifest.document_id)
        orm = self._to_orm(manifest)

        if existing:
            # Overwrite existing record for document
            existing_orm = await self.session.get(ParsingManifestORM, existing.id)
            if existing_orm:
                existing_orm.parser_version = orm.parser_version
                existing_orm.chunk_strategy = orm.chunk_strategy
                existing_orm.chunk_size = orm.chunk_size
                existing_orm.overlap = orm.overlap
                existing_orm.parse_duration = orm.parse_duration
                existing_orm.chunk_count = orm.chunk_count
                existing_orm.table_count = orm.table_count
                existing_orm.warnings = orm.warnings
                existing_orm.extraction_confidence = orm.extraction_confidence
                await self.session.flush()
                return self._to_domain(existing_orm)

        self._add(orm)
        await self.session.flush()
        return self._to_domain(orm)

    async def get_by_document(self, document_id: UUID) -> ParsingManifest | None:
        """
        Retrieves the parsing manifest of a document.
        """
        query = select(ParsingManifestORM).where(
            ParsingManifestORM.document_id == document_id
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def delete_by_document(self, document_id: UUID) -> None:
        """
        Deletes the parsing manifest of a document.
        """
        query = delete(ParsingManifestORM).where(
            ParsingManifestORM.document_id == document_id
        )
        await self.session.execute(query)
        await self.session.flush()
