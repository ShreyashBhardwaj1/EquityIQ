"""
Financial Intelligence API Router.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.application.services.dashboard_service import DashboardService
from app.application.services.explainability_service import ExplainabilityService
from app.application.services.financial_intelligence_service import (
    FinancialIntelligenceService,
)
from app.core.dependencies import (
    get_company_repository,
    get_current_user,
    get_current_workspace_id,
    get_dashboard_service,
    get_explainability_service,
    get_financial_intelligence_service,
)
from app.domain.entities.user import User
from app.infrastructure.db.repositories.company_repo import SQLAlchemyCompanyRepository

router = APIRouter(prefix="/companies", tags=["Financial Intelligence"])


class CalculateResponse(BaseModel):
    """
    Response model for computation runs.
    """

    company_id: UUID
    fiscal_period: str
    overall_score: float
    recommendation: str
    risk_status: str
    portfolio_signal: dict[str, Any]
    ratio_engine_version: str
    health_engine_version: str
    risk_engine_version: str
    recommendation_policy_version: str
    financial_intelligence_version: str


@router.post(
    "/{company_id}/calculate",
    response_model=CalculateResponse,
    status_code=status.HTTP_200_OK,
)
async def calculate_financial_intelligence(
    company_id: UUID,
    fiscal_period: str = Query(
        ..., description="Target reporting period, e.g. FY-2024"
    ),
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    fi_service: FinancialIntelligenceService = Depends(
        get_financial_intelligence_service
    ),
) -> CalculateResponse:
    """
    Triggers the calculation pipeline for ratios, health scores, risks, and recommendation ratings.
    Enforces tenant/workspace-level access isolation.
    """
    # Verify company exists within user's active workspace
    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace context.",
        )

    try:
        result = await fi_service.run_analysis(
            company_id=company_id,
            fiscal_period=fiscal_period,
            user_id=current_user.id,
        )

        port_signal = result["portfolio_signal"]
        port_signal["ticker"] = company.ticker.symbol

        return CalculateResponse(
            company_id=company_id,
            fiscal_period=fiscal_period,
            overall_score=result["health_score"].overall_score,
            recommendation=result["recommendation"].recommendation.value,
            risk_status=port_signal["risk_status"],
            portfolio_signal=port_signal,
            ratio_engine_version=result["health_score"].ratio_engine_version,
            health_engine_version=result["health_score"].ratio_engine_version,
            risk_engine_version=result["health_score"].ratio_engine_version,
            recommendation_policy_version=result["history"].policy_version,
            financial_intelligence_version="1.0.0",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{company_id}/explainability", status_code=status.HTTP_200_OK)
async def get_explainability(
    company_id: UUID,
    fiscal_period: str = Query(
        ..., description="Target reporting period, e.g. FY-2024"
    ),
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    explain_service: ExplainabilityService = Depends(get_explainability_service),
) -> dict[str, Any]:
    """
    Retrieves the sequential logic checks, policy boundaries, and audit reasoning trails.
    Enforces tenant/workspace-level access isolation.
    """
    # Verify company exists within user's active workspace
    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace context.",
        )

    return await explain_service.get_explainability(company_id, fiscal_period)


@router.get("/{company_id}/dashboard", status_code=status.HTTP_200_OK)
async def get_dashboard(
    company_id: UUID,
    fiscal_period: str = Query(
        ..., description="Target reporting period, e.g. FY-2024"
    ),
    active_workspace_id: UUID = Depends(get_current_workspace_id),
    company_repo: SQLAlchemyCompanyRepository = Depends(get_company_repository),
    dash_service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, Any]:
    """
    Assembles a consolidated layout containing health scores, active ratings, detected risks,
    growth trends, and metric confidence.
    Enforces tenant/workspace-level access isolation.
    """
    # Verify company exists within user's active workspace
    company = await company_repo.get_by_id(active_workspace_id, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found in active workspace context.",
        )

    res = await dash_service.get_dashboard(company_id, fiscal_period)
    res["ticker"] = company.ticker.symbol
    return res
