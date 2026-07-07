"""
Repository Interfaces (Protocols) for data access abstraction.
"""

from typing import Protocol
from uuid import UUID

from app.domain.entities.company import Company
from app.domain.entities.document import Document
from app.domain.entities.financial_statement import FinancialStatement
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

    async def get(self, document_id: UUID) -> Document | None:
        """Retrieve a document by its unique ID."""
        ...

    async def save(self, document: Document) -> Document:
        """Save/persist a document entity."""
        ...

    async def list_by_company(
        self, company_id: UUID, fiscal_period: str | None = None
    ) -> list[Document]:
        """List documents associated with a company, optionally filtered by fiscal period."""
        ...


class FinancialStatementRepository(Protocol):
    """Abstract interface for FinancialStatement data persistence operations."""

    async def get(self, statement_id: UUID) -> FinancialStatement | None:
        """Retrieve a statement by its unique ID."""
        ...

    async def get_by_period(
        self, company_id: UUID, statement_type: str, fiscal_period: str
    ) -> FinancialStatement | None:
        """Retrieve a unique statement by company, statement type, and fiscal period."""
        ...

    async def save(self, statement: FinancialStatement) -> FinancialStatement:
        """Save/persist a statement entity."""
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
