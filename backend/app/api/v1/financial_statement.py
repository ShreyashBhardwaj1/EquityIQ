"""
Financial Statement API Router.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.financial_statement_service import (
    FinancialStatementService,
)
from app.core.dependencies import (
    get_current_user,
    get_current_workspace_id,
    get_statement_service,
)
from app.domain.entities.financial_statement import NormalizationAdjustment
from app.domain.entities.user import User
from app.domain.exceptions import EntityValidationError
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/financial-statements", tags=["Financial Statements"])


# Input schemas
class NormalizationAdjustmentInput(BaseModel):
    line_item: str = Field(..., min_length=1, description="Target statement field key")
    adjustment: float = Field(..., description="Numerical revision (+/-)")
    reason: str = Field(..., min_length=1, description="Justification explanation")
    source_document_id: UUID = Field(..., description="Provenance source file UUID")
    source_page: int = Field(..., ge=1, description="Page number where the adjustment is sourced")


class StatementCreate(BaseModel):
    company_id: UUID = Field(..., description="Associated company ID")
    document_id: UUID = Field(..., description="Associated source document ID")
    statement_type: str = Field(..., description="Statement category: income, balance, cashflow")
    fiscal_period: str = Field(..., description="Reporting fiscal period (e.g. Q1-2024)")
    line_items: dict[str, float] = Field(..., description="As-reported raw line items")


class StatementPatch(BaseModel):
    line_items: dict[str, float] | None = Field(None, description="Updated raw line items")
    adjustments: list[NormalizationAdjustmentInput] | None = Field(None, description="Adjustments list")
    change_reason: str = Field(..., min_length=1, description="Reason for statement changes")


# Response schemas
class AdjustmentResponse(BaseModel):
    line_item: str
    adjustment: float
    reason: str
    source_document_id: UUID
    source_page: int


class StatementResponse(BaseModel):
    id: UUID
    company_id: UUID
    document_id: UUID
    statement_type: str
    fiscal_period: str
    line_items: dict[str, float]
    normalization_adjustments: list[AdjustmentResponse]
    normalized_line_items: dict[str, float]
    created_at: datetime


class StatementVersionResponse(BaseModel):
    id: UUID
    statement_id: UUID
    version: int
    line_items: dict[str, float]
    normalization_adjustments: list[AdjustmentResponse]
    normalized_line_items: dict[str, float]
    changed_by: UUID
    change_reason: str
    created_at: datetime


class ComparisonItem(BaseModel):
    as_reported: float | None = None
    normalized: float | None = None
    difference: float = 0.0


class ComparisonReportResponse(BaseModel):
    statement_id: UUID
    company_id: UUID
    statement_type: str
    fiscal_period: str
    comparison: dict[str, ComparisonItem]


@router.post("", response_model=StatementResponse, status_code=status.HTTP_201_CREATED)
async def create_statement(
    payload: StatementCreate,
    workspace_id: UUID = Depends(get_current_workspace_id),
    statement_service: FinancialStatementService = Depends(get_statement_service),
    db: AsyncSession = Depends(get_db_session),
) -> StatementResponse:
    """
    Register a new financial statement, performing validation guards and normalization mappings.
    """
    try:
        statement = await statement_service.create_statement(
            workspace_id=workspace_id,
            company_id=payload.company_id,
            document_id=payload.document_id,
            statement_type_str=payload.statement_type,
            fiscal_period_str=payload.fiscal_period,
            line_items=payload.line_items,
        )
        await db.commit()
        return StatementResponse(
            id=statement.id,
            company_id=statement.company_id,
            document_id=statement.document_id,
            statement_type=statement.statement_type.value,
            fiscal_period=f"{statement.fiscal_period.period}-{statement.fiscal_period.year}",
            line_items=statement.line_items,
            normalization_adjustments=[
                AdjustmentResponse(
                    line_item=adj.line_item,
                    adjustment=adj.adjustment,
                    reason=adj.reason,
                    source_document_id=adj.source_document_id,
                    source_page=adj.source_page,
                )
                for adj in statement.normalization_adjustments
            ],
            normalized_line_items=statement.normalized_line_items,
            created_at=statement.created_at,
        )
    except EntityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[StatementResponse])
async def list_statements(
    company_id: UUID = Query(...),
    workspace_id: UUID = Depends(get_current_workspace_id),
    statement_service: FinancialStatementService = Depends(get_statement_service),
) -> list[StatementResponse]:
    """
    List all financial statements associated with a company in the active workspace.
    """
    statements = await statement_service.list_company_statements(workspace_id, company_id)
    return [
        StatementResponse(
            id=s.id,
            company_id=s.company_id,
            document_id=s.document_id,
            statement_type=s.statement_type.value,
            fiscal_period=f"{s.fiscal_period.period}-{s.fiscal_period.year}",
            line_items=s.line_items,
            normalization_adjustments=[
                AdjustmentResponse(
                    line_item=adj.line_item,
                    adjustment=adj.adjustment,
                    reason=adj.reason,
                    source_document_id=adj.source_document_id,
                    source_page=adj.source_page,
                )
                for adj in s.normalization_adjustments
            ],
            normalized_line_items=s.normalized_line_items,
            created_at=s.created_at,
        )
        for s in statements
    ]


@router.get("/history", response_model=list[StatementVersionResponse])
async def get_statement_history(
    statement_id: UUID = Query(..., description="Target statement ID"),
    workspace_id: UUID = Depends(get_current_workspace_id),
    statement_service: FinancialStatementService = Depends(get_statement_service),
) -> list[StatementVersionResponse]:
    """
    Retrieve historical revision version audits for a statement.
    """
    versions = await statement_service.list_statement_versions(workspace_id, statement_id)
    return [
        StatementVersionResponse(
            id=v.id,
            statement_id=v.statement_id,
            version=v.version,
            line_items=v.line_items,
            normalization_adjustments=[
                AdjustmentResponse(
                    line_item=adj.line_item,
                    adjustment=adj.adjustment,
                    reason=adj.reason,
                    source_document_id=adj.source_document_id,
                    source_page=adj.source_page,
                )
                for adj in v.normalization_adjustments
            ],
            normalized_line_items=v.normalized_line_items,
            changed_by=v.changed_by,
            change_reason=v.change_reason,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/{statement_id}", response_model=StatementResponse)
async def get_statement(
    statement_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    statement_service: FinancialStatementService = Depends(get_statement_service),
) -> StatementResponse:
    """
    Retrieve details for a specific statement.
    """
    statement = await statement_service.get_statement(workspace_id, statement_id)
    return StatementResponse(
        id=statement.id,
        company_id=statement.company_id,
        document_id=statement.document_id,
        statement_type=statement.statement_type.value,
        fiscal_period=f"{statement.fiscal_period.period}-{statement.fiscal_period.year}",
        line_items=statement.line_items,
        normalization_adjustments=[
            AdjustmentResponse(
                line_item=adj.line_item,
                adjustment=adj.adjustment,
                reason=adj.reason,
                source_document_id=adj.source_document_id,
                source_page=adj.source_page,
            )
            for adj in statement.normalization_adjustments
        ],
        normalized_line_items=statement.normalized_line_items,
        created_at=statement.created_at,
    )


@router.patch("/{statement_id}", response_model=StatementResponse)
async def patch_statement(
    statement_id: UUID,
    payload: StatementPatch,
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    statement_service: FinancialStatementService = Depends(get_statement_service),
    db: AsyncSession = Depends(get_db_session),
) -> StatementResponse:
    """
    Partially update statement raw line items or normalization adjustments, tracking version changes.
    """
    try:
        # Convert adjustments input if present
        domain_adjustments = None
        if payload.adjustments is not None:
            domain_adjustments = [
                NormalizationAdjustment(
                    line_item=adj.line_item,
                    adjustment=adj.adjustment,
                    reason=adj.reason,
                    source_document_id=adj.source_document_id,
                    source_page=adj.source_page,
                )
                for adj in payload.adjustments
            ]

        statement = await statement_service.update_statement(
            workspace_id=workspace_id,
            statement_id=statement_id,
            changed_by=current_user.id,
            change_reason=payload.change_reason,
            line_items=payload.line_items,
            adjustments=domain_adjustments,
        )
        await db.commit()

        return StatementResponse(
            id=statement.id,
            company_id=statement.company_id,
            document_id=statement.document_id,
            statement_type=statement.statement_type.value,
            fiscal_period=f"{statement.fiscal_period.period}-{statement.fiscal_period.year}",
            line_items=statement.line_items,
            normalization_adjustments=[
                AdjustmentResponse(
                    line_item=adj.line_item,
                    adjustment=adj.adjustment,
                    reason=adj.reason,
                    source_document_id=adj.source_document_id,
                    source_page=adj.source_page,
                )
                for adj in statement.normalization_adjustments
            ],
            normalized_line_items=statement.normalized_line_items,
            created_at=statement.created_at,
        )
    except EntityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{statement_id}/compare", response_model=ComparisonReportResponse)
async def compare_statement(
    statement_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    statement_service: FinancialStatementService = Depends(get_statement_service),
) -> ComparisonReportResponse:
    """
    Compare raw line items side-by-side with normalized line items.
    """
    s = await statement_service.get_statement(workspace_id, statement_id)

    # Merge all unique keys across line_items and normalized_line_items
    all_keys = set(s.line_items.keys()) | set(s.normalized_line_items.keys())
    comparison: dict[str, ComparisonItem] = {}

    for k in all_keys:
        raw_val = s.line_items.get(k)
        norm_val = s.normalized_line_items.get(k)
        diff = (norm_val or 0.0) - (raw_val or 0.0)
        comparison[k] = ComparisonItem(
            as_reported=raw_val,
            normalized=norm_val,
            difference=diff,
        )

    return ComparisonReportResponse(
        statement_id=s.id,
        company_id=s.company_id,
        statement_type=s.statement_type.value,
        fiscal_period=f"{s.fiscal_period.period}-{s.fiscal_period.year}",
        comparison=comparison,
    )
