"""
Company application service.
"""

from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.domain.entities.company import Company
from app.domain.interfaces.repositories import CompanyRepository
from app.domain.value_objects.exchange import Exchange
from app.domain.value_objects.ticker import Ticker


class CompanyService:
    """
    Coordinates CRUD operations and validation rules for Company entities.
    """

    def __init__(self, company_repo: CompanyRepository) -> None:
        """
        Initializes CompanyService.
        """
        self.company_repo = company_repo

    async def create_company(
        self,
        workspace_id: UUID,
        ticker: str,
        exchange: str,
        name: str,
        sector: str,
        industry: str,
        country: str,
        fiscal_year_end: str,
        currency: str,
    ) -> Company:
        """
        Creates a new company inside a workspace, checking for duplicate active records
        and restoring soft-deleted matches if found.
        """
        ticker_clean = ticker.upper().strip()
        exchange_clean = exchange.strip()

        # Check if the company exists in the workspace (including soft-deleted)
        existing = await self.company_repo.get_by_ticker(
            workspace_id=workspace_id,
            ticker=ticker_clean,
            exchange=exchange_clean,
            include_deleted=True,
        )

        if existing:
            # Check if active or soft-deleted by seeing if we can query it actively
            active = await self.company_repo.get_by_ticker(
                workspace_id=workspace_id,
                ticker=ticker_clean,
                exchange=exchange_clean,
                include_deleted=False,
            )
            if active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Company with ticker '{ticker_clean}' on exchange '{exchange_clean}' already exists in this workspace.",
                )

            # If not active, it is soft-deleted. Restore and update it!
            restored = Company(
                id=existing.id,
                workspace_id=workspace_id,
                ticker=Ticker(ticker_clean),
                exchange=Exchange(exchange_clean),
                name=name,
                sector=sector,
                industry=industry,
                country=country,
                fiscal_year_end=fiscal_year_end,
                currency=currency,
            )
            return await self.company_repo.save(restored)

        # Create a new company
        company = Company(
            id=uuid4(),
            workspace_id=workspace_id,
            ticker=Ticker(ticker_clean),
            exchange=Exchange(exchange_clean),
            name=name,
            sector=sector,
            industry=industry,
            country=country,
            fiscal_year_end=fiscal_year_end,
            currency=currency,
        )
        return await self.company_repo.save(company)

    async def get_company(self, workspace_id: UUID, company_id: UUID) -> Company:
        """
        Retrieves a company inside a workspace.
        """
        company = await self.company_repo.get_by_id(
            workspace_id=workspace_id, company_id=company_id
        )
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found in this workspace.",
            )
        return company

    async def update_company(
        self,
        workspace_id: UUID,
        company_id: UUID,
        name: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        fiscal_year_end: str | None = None,
        currency: str | None = None,
    ) -> Company:
        """
        Partially updates company fields (PATCH) inside a workspace.
        """
        company = await self.get_company(
            workspace_id=workspace_id, company_id=company_id
        )

        updated = Company(
            id=company.id,
            workspace_id=company.workspace_id,
            ticker=company.ticker,
            exchange=company.exchange,
            name=name if name is not None else company.name,
            sector=sector if sector is not None else company.sector,
            industry=industry if industry is not None else company.industry,
            country=country if country is not None else company.country,
            fiscal_year_end=(
                fiscal_year_end
                if fiscal_year_end is not None
                else company.fiscal_year_end
            ),
            currency=currency if currency is not None else company.currency,
        )
        return await self.company_repo.save(updated)

    async def delete_company(self, workspace_id: UUID, company_id: UUID) -> None:
        """
        Soft deletes a company from a workspace.
        """
        # Ensure company exists in the workspace
        await self.get_company(workspace_id=workspace_id, company_id=company_id)
        await self.company_repo.delete(workspace_id=workspace_id, company_id=company_id)

    async def list_companies(
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
        """
        Lists companies in active workspace using filters, sorting, and pagination.
        """
        return await self.company_repo.list_by_workspace(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            exchange=exchange,
            sector=sector,
            industry=industry,
            country=country,
        )

    async def search_companies(
        self, workspace_id: UUID, query_str: str
    ) -> list[Company]:
        """
        Searches companies in active workspace.
        """
        if not query_str.strip():
            return []
        return await self.company_repo.search_companies(
            workspace_id=workspace_id, query_str=query_str
        )
