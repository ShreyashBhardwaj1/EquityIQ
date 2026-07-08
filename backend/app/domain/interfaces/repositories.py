"""
Repository Interfaces (Protocols) for data access abstraction.
"""

from typing import Protocol
from uuid import UUID

from app.domain.entities.company import Company
from app.domain.entities.document import Document
from app.domain.entities.document_chunk import DocumentChunk
from app.domain.entities.document_version import DocumentVersion
from app.domain.entities.financial_statement import FinancialStatement
from app.domain.entities.financial_statement_version import (
    FinancialStatementVersion,
)
from app.domain.entities.parsing_manifest import ParsingManifest
from app.domain.entities.user import User
from app.domain.entities.workspace import Workspace, WorkspaceMembership


class CompanyRepository(Protocol):
    """Abstract interface for Company data persistence operations."""

    async def get_by_id(self, workspace_id: UUID, company_id: UUID) -> Company | None:
        """Retrieve a company by its unique ID and workspace scoping."""
        ...

    async def get_by_ticker(
        self,
        workspace_id: UUID,
        ticker: str,
        exchange: str | None = None,
        include_deleted: bool = False,
    ) -> Company | None:
        """Retrieve a company by its unique ticker symbol, optional exchange, and workspace scoping."""
        ...

    async def save(self, company: Company) -> Company:
        """Save/persist a company entity."""
        ...

    async def list_by_workspace(
        self,
        workspace_id: UUID,
        limit: int = 20,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
        exchange: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        country: str | None = None,
    ) -> list[Company]:
        """List companies in a workspace with filters, sorting, and pagination."""
        ...

    async def search_companies(
        self, workspace_id: UUID, query_str: str
    ) -> list[Company]:
        """Search companies in a workspace by name, ticker, exchange, or sector."""
        ...

    async def delete(self, workspace_id: UUID, company_id: UUID) -> None:
        """Delete/soft-delete a company from a workspace."""
        ...


class DocumentRepository(Protocol):
    """Abstract interface for Document data persistence operations."""

    async def get(
        self, document_id: UUID, workspace_id: UUID | None = None
    ) -> Document | None:
        """Retrieve a document by its unique ID, with optional workspace scoping."""
        ...

    async def save(self, document: Document) -> Document:
        """Save/persist a document entity."""
        ...

    async def list_by_workspace(
        self, workspace_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Document]:
        """List all documents in a workspace."""
        ...

    async def list_by_company(
        self,
        company_id: UUID,
        workspace_id: UUID | None = None,
        fiscal_period: str | None = None,
    ) -> list[Document]:
        """List documents associated with a company, with optional workspace scoping."""
        ...

    async def delete(self, document_id: UUID, workspace_id: UUID | None = None) -> None:
        """Delete/soft-delete a document, with optional workspace scoping."""
        ...

    async def save_version(self, version: DocumentVersion) -> None:
        """Save a new metadata or file audit version for a document."""
        ...

    async def list_versions(self, document_id: UUID) -> list[DocumentVersion]:
        """List all audit versions of a document."""
        ...


class FinancialStatementRepository(Protocol):
    """Abstract interface for FinancialStatement data persistence operations."""

    async def get(
        self, statement_id: UUID, workspace_id: UUID | None = None
    ) -> FinancialStatement | None:
        """Retrieve a statement by its unique ID, with optional workspace scoping."""
        ...

    async def get_by_period(
        self,
        company_id: UUID,
        statement_type: str,
        fiscal_period: str,
        workspace_id: UUID | None = None,
    ) -> FinancialStatement | None:
        """Retrieve a unique statement by company, type, period, and optional workspace scoping."""
        ...

    async def save(self, statement: FinancialStatement) -> FinancialStatement:
        """Save/persist a statement entity."""
        ...

    async def list_by_company(
        self, company_id: UUID, workspace_id: UUID | None = None
    ) -> list[FinancialStatement]:
        """List all statements associated with a company, with optional workspace scoping."""
        ...

    async def delete(
        self, statement_id: UUID, workspace_id: UUID | None = None
    ) -> None:
        """Delete a statement, with optional workspace scoping."""
        ...

    async def save_version(self, version: FinancialStatementVersion) -> None:
        """Save a new historical revision version for a statement."""
        ...

    async def list_versions(
        self, statement_id: UUID
    ) -> list[FinancialStatementVersion]:
        """List all historical revisions of a statement."""
        ...


class ChunkRepository(Protocol):
    """Abstract interface for DocumentChunk data persistence operations."""

    async def save(self, chunk: DocumentChunk) -> DocumentChunk:
        """Save a single document chunk."""
        ...

    async def save_batch(self, chunks: list[DocumentChunk]) -> None:
        """Save a list of document chunks in a batch."""
        ...

    async def list_by_document(
        self, document_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[DocumentChunk]:
        """List chunks associated with a document, ordered by chunk_index."""
        ...

    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all chunks associated with a document."""
        ...

    async def get(self, chunk_id: UUID) -> DocumentChunk | None:
        """Retrieve a specific chunk by its ID."""
        ...


class ParsingManifestRepository(Protocol):
    """Abstract interface for ParsingManifest data persistence operations."""

    async def save(self, manifest: ParsingManifest) -> ParsingManifest:
        """Save a parsing manifest metadata record."""
        ...

    async def get_by_document(self, document_id: UUID) -> ParsingManifest | None:
        """Retrieve the parsing manifest associated with a document."""
        ...

    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete the parsing manifest associated with a document."""
        ...


class UserRepository(Protocol):
    """Abstract interface for User data persistence operations."""

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by their unique ID."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their unique email."""
        ...

    async def save(self, user: User) -> User:
        """Save/persist a user entity."""
        ...


class WorkspaceRepository(Protocol):
    """Abstract interface for Workspace data persistence operations."""

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        """Retrieve a workspace by its unique ID."""
        ...

    async def save(self, workspace: Workspace) -> Workspace:
        """Save/persist a workspace entity."""
        ...

    async def delete(self, workspace_id: UUID) -> None:
        """Archive/soft-delete a workspace."""
        ...

    async def list_by_user(self, user_id: UUID) -> list[Workspace]:
        """List workspaces where the user is owner or member (excluding archived ones)."""
        ...

    async def save_membership(
        self, membership: WorkspaceMembership
    ) -> WorkspaceMembership:
        """Save/persist a workspace membership."""
        ...

    async def get_membership(
        self, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMembership | None:
        """Retrieve a membership relation."""
        ...

    async def delete_membership(self, workspace_id: UUID, user_id: UUID) -> None:
        """Delete a membership relation."""
        ...

    async def list_memberships_by_user(
        self, user_id: UUID
    ) -> list[WorkspaceMembership]:
        """List all memberships for a user."""
        ...
