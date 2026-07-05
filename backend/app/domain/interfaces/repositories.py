"""
Repository Interfaces (Protocols) for data access abstraction.
"""

from typing import Protocol
from uuid import UUID

from app.domain.entities.company import Company
from app.domain.entities.document import Document
from app.domain.entities.financial_statement import FinancialStatement


class CompanyRepository(Protocol):
    """Abstract interface for Company data persistence operations."""

    async def get_by_id(self, company_id: UUID) -> Company | None:
        """Retrieve a company by its unique ID."""
        ...

    async def get_by_ticker(self, ticker: str) -> Company | None:
        """Retrieve a company by its unique ticker symbol."""
        ...

    async def save(self, company: Company) -> Company:
        """Save/persist a company entity."""
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
