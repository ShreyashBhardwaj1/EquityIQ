"""
Application Service coordinating Document metadata and file versioning workflows.
"""

import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.domain.entities.document import Document, DocumentType, ParsingStatus
from app.domain.entities.document_version import DocumentVersion
from app.domain.exceptions import EntityValidationError
from app.domain.interfaces.repositories import DocumentRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod


class DocumentService:
    """
    Coordinates metadata CRUD, secure upload storage, and versioning for files.
    """

    def __init__(self, doc_repo: DocumentRepository, base_storage_path: str = "storage/uploads") -> None:
        """
        Initializes DocumentService.
        """
        self.doc_repo = doc_repo
        self.base_storage_path = base_storage_path

    def _verify_magic_bytes(self, file_content: bytes, filename: str) -> None:
        """
        Verifies that file magic bytes match allowed MIME types:
        - PDF: Starts with b'%PDF-'
        - TXT: Simple utf-8 characters check (fallback for text/csv files)
        """
        if filename.lower().endswith(".pdf"):
            if not file_content.startswith(b"%PDF-"):
                raise EntityValidationError("File is not a valid PDF document (header mismatch).")
        elif filename.lower().endswith((".txt", ".csv")):
            try:
                file_content[:1024].decode("utf-8")
            except UnicodeDecodeError as e:
                raise EntityValidationError("File contains invalid non-text characters.") from e
        else:
            raise EntityValidationError("Unsupported file extension. Only PDF, TXT, or CSV files are allowed.")

    async def upload_document(
        self,
        workspace_id: UUID,
        company_id: UUID,
        uploaded_by: UUID,
        filename: str,
        file_content: bytes,
        doc_type_str: str,
        fiscal_period_str: str,
    ) -> Document:
        """
        Validates, stores, and registers a new document in the system.
        """
        # Validate file size (limit to 50MB)
        if len(file_content) > 50 * 1024 * 1024:
            raise EntityValidationError("File size exceeds the maximum limit of 50MB.")

        # Verify magic bytes
        self._verify_magic_bytes(file_content, filename)

        # Parse and validate domain objects
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError as e:
            raise EntityValidationError(f"Unsupported document type: {doc_type_str}") from e

        parts = fiscal_period_str.split("-")
        period = parts[0]
        year = int(parts[1]) if len(parts) > 1 else 2000
        fiscal_period = FiscalPeriod(period, year)

        # Construct tenant-isolated folder structure on disk
        folder_path = Path(self.base_storage_path) / f"workspace_{workspace_id}" / f"company_{company_id}"
        os.makedirs(folder_path, exist_ok=True)

        # Generate unique file name on storage to avoid collisions
        unique_filename = f"{uuid4()}_{filename}"
        storage_path = str(folder_path / unique_filename)

        # Write file content to disk
        with open(storage_path, "wb") as f:
            f.write(file_content)

        # Persist Document Entity
        document = Document(
            id=uuid4(),
            workspace_id=workspace_id,
            company_id=company_id,
            doc_type=doc_type,
            fiscal_period=fiscal_period,
            storage_path=storage_path,
            parsing_status=ParsingStatus.COMPLETED,  # Parsing is skipped/completed for metadata milestone
            parsing_confidence=1.0,
            uploaded_by=uploaded_by,
        )

        return await self.doc_repo.save(document)

    async def get_document(self, workspace_id: UUID, document_id: UUID) -> Document:
        """
        Retrieves a document with workspace scoping check.
        """
        doc = await self.doc_repo.get(document_id=document_id, workspace_id=workspace_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in this workspace context.",
            )
        return doc

    async def list_documents(self, workspace_id: UUID, limit: int = 20, offset: int = 0) -> list[Document]:
        """
        Lists all document metadata in a workspace.
        """
        return await self.doc_repo.list_by_workspace(workspace_id=workspace_id, limit=limit, offset=offset)

    async def list_company_documents(
        self, workspace_id: UUID, company_id: UUID, fiscal_period_str: str | None = None
    ) -> list[Document]:
        """
        Lists company-specific document metadata in a workspace.
        """
        return await self.doc_repo.list_by_company(
            company_id=company_id, workspace_id=workspace_id, fiscal_period=fiscal_period_str
        )

    async def update_document_file(
        self,
        workspace_id: UUID,
        document_id: UUID,
        changed_by: UUID,
        filename: str,
        file_content: bytes,
        change_reason: str,
    ) -> Document:
        """
        Uploads a new file version for an existing document, creating an audit trail log.
        """
        doc = await self.get_document(workspace_id=workspace_id, document_id=document_id)

        # Validate file size and contents
        if len(file_content) > 50 * 1024 * 1024:
            raise EntityValidationError("File size exceeds the maximum limit of 50MB.")
        self._verify_magic_bytes(file_content, filename)

        # Retrieve existing versions to calculate version increment index
        versions = await self.doc_repo.list_versions(document_id=document_id)
        next_ver_index = len(versions) + 1

        # Create Version history entry for the OLD file state
        old_version = DocumentVersion(
            id=uuid4(),
            document_id=doc.id,
            version=next_ver_index,
            storage_path=doc.storage_path,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        await self.doc_repo.save_version(version=old_version)

        # Save the NEW file content to disk
        folder_path = Path(self.base_storage_path) / f"workspace_{workspace_id}" / f"company_{doc.company_id}"
        os.makedirs(folder_path, exist_ok=True)
        unique_filename = f"{uuid4()}_v{next_ver_index}_{filename}"
        new_storage_path = str(folder_path / unique_filename)

        with open(new_storage_path, "wb") as f:
            f.write(file_content)

        # Update document entity with the new storage path
        updated_doc = Document(
            id=doc.id,
            workspace_id=doc.workspace_id,
            company_id=doc.company_id,
            doc_type=doc.doc_type,
            fiscal_period=doc.fiscal_period,
            storage_path=new_storage_path,
            parsing_status=doc.parsing_status,
            parsing_confidence=doc.parsing_confidence,
            uploaded_by=doc.uploaded_by,
        )

        return await self.doc_repo.save(updated_doc)

    async def delete_document(self, workspace_id: UUID, document_id: UUID) -> None:
        """
        Deletes document metadata record and clears physical storage file.
        """
        doc = await self.get_document(workspace_id=workspace_id, document_id=document_id)

        # Remove physical file
        try:
            if os.path.exists(doc.storage_path):
                os.remove(doc.storage_path)
        except OSError:
            pass  # Suppress clean up failures to guarantee database deletion integrity

        # Delete database metadata (which cascades to document_versions)
        await self.doc_repo.delete(document_id=document_id, workspace_id=workspace_id)

    async def list_document_versions(self, workspace_id: UUID, document_id: UUID) -> list[DocumentVersion]:
        """
        List versions for a document. Enforces workspace checks first.
        """
        await self.get_document(workspace_id=workspace_id, document_id=document_id)
        return await self.doc_repo.list_versions(document_id=document_id)
