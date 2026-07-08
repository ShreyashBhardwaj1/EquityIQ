"""
SQLAlchemy repository adapter for Document.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.document import Document, DocumentType, ParsingStatus
from app.domain.entities.document_version import DocumentVersion
from app.domain.interfaces.repositories import DocumentRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.document import DocumentORM
from app.infrastructure.db.models.document_version import DocumentVersionORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyDocumentRepository(BaseRepository[DocumentORM], DocumentRepository):
    """
    SQLAlchemy-backed implementation of the DocumentRepository interface.
    """

    def _to_domain(self, orm: DocumentORM) -> Document:
        """Translates ORM model to Domain Entity."""
        parts = orm.fiscal_period.split("-")
        period = parts[0]
        year = int(parts[1]) if len(parts) > 1 else 2000

        if orm.workspace_id is None or orm.uploaded_by_id is None:
            raise ValueError(
                "Database Document record must contain workspace_id and uploaded_by_id."
            )

        return Document(
            id=orm.id,
            workspace_id=orm.workspace_id,
            company_id=orm.company_id,
            doc_type=DocumentType(orm.doc_type),
            fiscal_period=FiscalPeriod(period, year),
            storage_path=orm.storage_path,
            parsing_status=ParsingStatus(orm.parsing_status),
            parsing_confidence=(
                orm.parsing_confidence if orm.parsing_confidence is not None else 1.0
            ),
            uploaded_by=orm.uploaded_by_id,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: Document) -> DocumentORM:
        """Translates Domain Entity to ORM model."""
        fp_str = f"{domain.fiscal_period.period}-{domain.fiscal_period.year}"
        return DocumentORM(
            id=domain.id,
            workspace_id=domain.workspace_id,
            company_id=domain.company_id,
            doc_type=domain.doc_type.value,
            fiscal_period=fp_str,
            storage_path=domain.storage_path,
            parsing_status=domain.parsing_status.value,
            parsing_confidence=domain.parsing_confidence,
            uploaded_by_id=domain.uploaded_by,
            created_at=domain.created_at,
        )

    def _version_to_domain(self, orm: DocumentVersionORM) -> DocumentVersion:
        """Translates DocumentVersionORM to Domain Entity."""
        return DocumentVersion(
            id=orm.id,
            document_id=orm.document_id,
            version=orm.version,
            storage_path=orm.storage_path,
            changed_by=orm.changed_by,
            change_reason=orm.change_reason,
            created_at=orm.created_at,
        )

    def _version_to_orm(self, domain: DocumentVersion) -> DocumentVersionORM:
        """Translates DocumentVersion Domain Entity to ORM model."""
        return DocumentVersionORM(
            id=domain.id,
            document_id=domain.document_id,
            version=domain.version,
            storage_path=domain.storage_path,
            changed_by=domain.changed_by,
            change_reason=domain.change_reason,
            created_at=domain.created_at,
        )

    async def get(
        self, document_id: UUID, workspace_id: UUID | None = None
    ) -> Document | None:
        """
        Retrieves a document by its ID, with optional workspace scoping.
        """
        query = select(DocumentORM).where(DocumentORM.id == document_id)
        if workspace_id:
            query = query.where(DocumentORM.workspace_id == workspace_id)
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, document: Document) -> Document:
        """
        Persists a Document entity.
        """
        existing_orm = await self.session.get(DocumentORM, document.id)
        orm = self._to_orm(document)

        if existing_orm:
            existing_orm.workspace_id = orm.workspace_id
            existing_orm.company_id = orm.company_id
            existing_orm.doc_type = orm.doc_type
            existing_orm.fiscal_period = orm.fiscal_period
            existing_orm.storage_path = orm.storage_path
            existing_orm.parsing_status = orm.parsing_status
            existing_orm.parsing_confidence = orm.parsing_confidence
            existing_orm.uploaded_by_id = orm.uploaded_by_id
            await self.session.flush()
            return self._to_domain(existing_orm)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def list_by_workspace(
        self, workspace_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Document]:
        """
        Lists all active documents inside a workspace.
        """
        query = (
            select(DocumentORM)
            .where(DocumentORM.workspace_id == workspace_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def list_by_company(
        self,
        company_id: UUID,
        workspace_id: UUID | None = None,
        fiscal_period: str | None = None,
    ) -> list[Document]:
        """
        Lists documents associated with a company, with optional workspace scoping.
        """
        query = select(DocumentORM).where(DocumentORM.company_id == company_id)
        if workspace_id:
            query = query.where(DocumentORM.workspace_id == workspace_id)
        if fiscal_period:
            query = query.where(DocumentORM.fiscal_period == fiscal_period)

        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def delete(self, document_id: UUID, workspace_id: UUID | None = None) -> None:
        """
        Deletes a document, with optional workspace scoping.
        """
        query = delete(DocumentORM).where(DocumentORM.id == document_id)
        if workspace_id:
            query = query.where(DocumentORM.workspace_id == workspace_id)
        await self.session.execute(query)
        await self.session.flush()

    async def save_version(self, version: DocumentVersion) -> None:
        """
        Persists a DocumentVersion ORM record.
        """
        orm = self._version_to_orm(version)
        self.session.add(orm)
        await self.session.flush()

    async def list_versions(self, document_id: UUID) -> list[DocumentVersion]:
        """
        Lists all metadata versions for a document.
        """
        query = (
            select(DocumentVersionORM)
            .where(DocumentVersionORM.document_id == document_id)
            .order_by(DocumentVersionORM.version.asc())
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._version_to_domain(orm) for orm in orms]
