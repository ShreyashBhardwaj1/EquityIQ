"""
Company API Router.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.company_service import CompanyService
from app.core.dependencies import get_company_service, get_current_workspace_id
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/companies", tags=["Companies"])


class CompanyCreate(BaseModel):
    """
    Company creation request payload.
    """

    ticker: str = Field(
        ..., min_length=1, max_length=10, description="Stock ticker symbol"
    )
    exchange: str = Field(
        ..., min_length=1, max_length=15, description="Listing exchange code"
    )
    name: str = Field(..., min_length=1, description="Official company name")
    sector: str = Field(..., min_length=1, description="Macro economic sector")
    industry: str = Field(..., min_length=1, description="Micro industry name")
    country: str = Field(
        ..., min_length=2, description="Listing country of the company"
    )
    fiscal_year_end: str = Field(
        ...,
        pattern=r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$",
        description="Fiscal year end date in MM-DD format",
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Reporting currency code (ISO 4217)",
    )


class CompanyPatch(BaseModel):
    """
    Company partial update request payload.
    """

    name: str | None = Field(None, min_length=1, description="Official company name")
    sector: str | None = Field(None, min_length=1, description="Macro economic sector")
    industry: str | None = Field(None, min_length=1, description="Micro industry name")
    country: str | None = Field(
        None, min_length=2, description="Listing country of the company"
    )
    fiscal_year_end: str | None = Field(
        None,
        pattern=r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$",
        description="Fiscal year end date in MM-DD format",
    )
    currency: str | None = Field(
        None,
        min_length=3,
        max_length=3,
        description="Reporting currency code (ISO 4217)",
    )


class CompanyResponse(BaseModel):
    """
    Company response model.
    """

    id: UUID
    workspace_id: UUID
    ticker: str
    exchange: str
    name: str
    sector: str
    industry: str
    country: str
    fiscal_year_end: str
    currency: str


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    request: CompanyCreate,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_db_session),
) -> CompanyResponse:
    """
    Creates a new company in the active workspace. Checks for duplicates and restores soft-deleted entries.
    """
    company = await company_service.create_company(
        workspace_id=active_workspace_id,
        ticker=request.ticker,
        exchange=request.exchange,
        name=request.name,
        sector=request.sector,
        industry=request.industry,
        country=request.country,
        fiscal_year_end=request.fiscal_year_end,
        currency=request.currency,
    )
    await session.commit()
    return CompanyResponse(
        id=company.id,
        workspace_id=company.workspace_id,
        ticker=company.ticker.symbol,
        exchange=company.exchange.name,
        name=company.name,
        sector=company.sector,
        industry=company.industry,
        country=company.country,
        fiscal_year_end=company.fiscal_year_end,
        currency=company.currency,
    )


@router.get("", response_model=list[CompanyResponse])
async def list_companies(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str | None = Query(
        None, description="Field to sort by (ticker, exchange, sector, industry)"
    ),
    sort_order: str | None = Query(None, description="Order of sorting (asc, desc)"),
    exchange: str | None = Query(None, description="Filter by exchange code"),
    sector: str | None = Query(None, description="Filter by sector name"),
    industry: str | None = Query(None, description="Filter by industry classification"),
    country: str | None = Query(None, description="Filter by listing country"),
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_service: CompanyService = Depends(get_company_service),
) -> list[CompanyResponse]:
    """
    Lists companies in the active workspace with filtering, pagination, and sorting.
    """
    companies = await company_service.list_companies(
        workspace_id=active_workspace_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        exchange=exchange,
        sector=sector,
        industry=industry,
        country=country,
    )
    return [
        CompanyResponse(
            id=c.id,
            workspace_id=c.workspace_id,
            ticker=c.ticker.symbol,
            exchange=c.exchange.name,
            name=c.name,
            sector=c.sector,
            industry=c.industry,
            country=c.country,
            fiscal_year_end=c.fiscal_year_end,
            currency=c.currency,
        )
        for c in companies
    ]


@router.get("/search", response_model=list[CompanyResponse])
async def search_companies(
    query: str = Query(..., min_length=1, description="Search query string"),
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_service: CompanyService = Depends(get_company_service),
) -> list[CompanyResponse]:
    """
    Searches companies in active workspace by name, ticker, exchange, or sector (case-insensitive).
    """
    companies = await company_service.search_companies(
        workspace_id=active_workspace_id, query_str=query
    )
    return [
        CompanyResponse(
            id=c.id,
            workspace_id=c.workspace_id,
            ticker=c.ticker.symbol,
            exchange=c.exchange.name,
            name=c.name,
            sector=c.sector,
            industry=c.industry,
            country=c.country,
            fiscal_year_end=c.fiscal_year_end,
            currency=c.currency,
        )
        for c in companies
    ]


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyResponse:
    """
    Retrieves details of a specific company scoped to the active workspace.
    """
    company = await company_service.get_company(
        workspace_id=active_workspace_id, company_id=company_id
    )
    return CompanyResponse(
        id=company.id,
        workspace_id=company.workspace_id,
        ticker=company.ticker.symbol,
        exchange=company.exchange.name,
        name=company.name,
        sector=company.sector,
        industry=company.industry,
        country=company.country,
        fiscal_year_end=company.fiscal_year_end,
        currency=company.currency,
    )


@router.patch("/{company_id}", response_model=CompanyResponse)
async def patch_company(
    company_id: UUID,
    request: CompanyPatch,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_db_session),
) -> CompanyResponse:
    """
    Partially updates company settings inside the active workspace.
    """
    company = await company_service.update_company(
        workspace_id=active_workspace_id,
        company_id=company_id,
        name=request.name,
        sector=request.sector,
        industry=request.industry,
        country=request.country,
        fiscal_year_end=request.fiscal_year_end,
        currency=request.currency,
    )
    await session.commit()
    return CompanyResponse(
        id=company.id,
        workspace_id=company.workspace_id,
        ticker=company.ticker.symbol,
        exchange=company.exchange.name,
        name=company.name,
        sector=company.sector,
        industry=company.industry,
        country=company.country,
        fiscal_year_end=company.fiscal_year_end,
        currency=company.currency,
    )


@router.delete("/{company_id}", status_code=status.HTTP_200_OK)
async def delete_company(
    company_id: UUID,
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_service: CompanyService = Depends(get_company_service),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Soft-deletes a company from the active workspace.
    """
    await company_service.delete_company(
        workspace_id=active_workspace_id, company_id=company_id
    )
    await session.commit()
    return {"detail": "Company archived successfully."}
