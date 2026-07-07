"""
Document API Router.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.document_service import DocumentService
from app.core.dependencies import (
    get_current_user,
    get_current_workspace_id,
    get_document_service,
)
from app.domain.entities.user import User
from app.domain.exceptions import EntityValidationError
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/documents", tags=["Documents"])


# Response models
class DocumentResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    company_id: UUID
    doc_type: str
    fiscal_period: str
    storage_path: str
    parsing_status: str
    parsing_confidence: float
    uploaded_by: UUID
    created_at: datetime


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version: int
    storage_path: str
    changed_by: UUID
    change_reason: str
    created_at: datetime


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    company_id: UUID = Form(...),
    doc_type: str = Form(...),
    fiscal_period: str = Form(...),
    file: UploadFile = File(...),
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    """
    Upload a document and register its metadata.
    """
    try:
        content = await file.read()
        doc = await doc_service.upload_document(
            workspace_id=workspace_id,
            company_id=company_id,
            uploaded_by=current_user.id,
            filename=file.filename or "unknown",
            file_content=content,
            doc_type_str=doc_type,
            fiscal_period_str=fiscal_period,
        )
        await db.commit()
        return DocumentResponse(
            id=doc.id,
            workspace_id=doc.workspace_id,
            company_id=doc.company_id,
            doc_type=doc.doc_type.value,
            fiscal_period=f"{doc.fiscal_period.period}-{doc.fiscal_period.year}",
            storage_path=doc.storage_path,
            parsing_status=doc.parsing_status.value,
            parsing_confidence=doc.parsing_confidence,
            uploaded_by=doc.uploaded_by,
            created_at=doc.created_at,
        )
    except EntityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    limit: int = 20,
    offset: int = 0,
    company_id: UUID | None = None,
    workspace_id: UUID = Depends(get_current_workspace_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    """
    List all documents in the active workspace, optionally filtered by company.
    """
    if company_id:
        docs = await doc_service.list_company_documents(workspace_id, company_id)
    else:
        docs = await doc_service.list_documents(workspace_id, limit, offset)

    return [
        DocumentResponse(
            id=doc.id,
            workspace_id=doc.workspace_id,
            company_id=doc.company_id,
            doc_type=doc.doc_type.value,
            fiscal_period=f"{doc.fiscal_period.period}-{doc.fiscal_period.year}",
            storage_path=doc.storage_path,
            parsing_status=doc.parsing_status.value,
            parsing_confidence=doc.parsing_confidence,
            uploaded_by=doc.uploaded_by,
            created_at=doc.created_at,
        )
        for doc in docs
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """
    Retrieve metadata for a specific document.
    """
    doc = await doc_service.get_document(workspace_id, document_id)
    return DocumentResponse(
        id=doc.id,
        workspace_id=doc.workspace_id,
        company_id=doc.company_id,
        doc_type=doc.doc_type.value,
        fiscal_period=f"{doc.fiscal_period.period}-{doc.fiscal_period.year}",
        storage_path=doc.storage_path,
        parsing_status=doc.parsing_status.value,
        parsing_confidence=doc.parsing_confidence,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    change_reason: str = Form(...),
    file: UploadFile = File(...),
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    doc_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    """
    Update a document's file content (re-upload), automatically creating a version log.
    """
    try:
        content = await file.read()
        doc = await doc_service.update_document_file(
            workspace_id=workspace_id,
            document_id=document_id,
            changed_by=current_user.id,
            filename=file.filename or "unknown",
            file_content=content,
            change_reason=change_reason,
        )
        await db.commit()
        return DocumentResponse(
            id=doc.id,
            workspace_id=doc.workspace_id,
            company_id=doc.company_id,
            doc_type=doc.doc_type.value,
            fiscal_period=f"{doc.fiscal_period.period}-{doc.fiscal_period.year}",
            storage_path=doc.storage_path,
            parsing_status=doc.parsing_status.value,
            parsing_confidence=doc.parsing_confidence,
            uploaded_by=doc.uploaded_by,
            created_at=doc.created_at,
        )
    except EntityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    doc_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a document and clean up physical storage files.
    """
    await doc_service.delete_document(workspace_id, document_id)
    await db.commit()


@router.get("/{document_id}/versions", response_model=list[DocumentVersionResponse])
async def list_document_versions(
    document_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    doc_service: DocumentService = Depends(get_document_service),
) -> list[DocumentVersionResponse]:
    """
    List historical version logs for a document.
    """
    versions = await doc_service.list_document_versions(workspace_id, document_id)
    return [
        DocumentVersionResponse(
            id=v.id,
            document_id=v.document_id,
            version=v.version,
            storage_path=v.storage_path,
            changed_by=v.changed_by,
            change_reason=v.change_reason,
            created_at=v.created_at,
        )
        for v in versions
    ]
