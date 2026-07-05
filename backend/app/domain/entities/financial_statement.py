"""
FinancialStatement entity representing balance, income, or cash flow reports.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.exceptions import EntityValidationError
from app.domain.value_objects.fiscal_period import FiscalPeriod


class StatementType(StrEnum):
    """Types of financial statements."""

    INCOME = "income"
    BALANCE = "balance"
    CASHFLOW = "cashflow"


class NormalizationAdjustment(BaseModel):
    """
    Represents a specific revision applied to an as-reported figure
    to arrive at the normalized figure (e.g., stripping one-off legal fees).
    """

    model_config = ConfigDict(frozen=True)

    line_item: str = Field(min_length=1, description="Target statement field key")
    adjustment: float = Field(description="Numerical revision (+/-)")
    reason: str = Field(min_length=1, description="Justification explanation")
    source_document_id: UUID = Field(description="Provenance source file UUID")
    source_page: int = Field(
        ge=1, description="Page number where the adjustment is sourced"
    )


class FinancialStatement(BaseModel):
    """
    FinancialStatement domain entity representing a statement for a company
    containing raw, normalized, and audit trail data.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique identifier for this statement")
    company_id: UUID = Field(description="Associated company identifier")
    document_id: UUID = Field(description="Associated provenance document")
    statement_type: StatementType = Field(description="Category of the statement")
    fiscal_period: FiscalPeriod = Field(description="Reporting fiscal period")
    line_items: dict[str, float] = Field(
        default_factory=dict, description="As-reported line item raw figures"
    )
    normalization_adjustments: list[NormalizationAdjustment] = Field(
        default_factory=list,
        description="Itemized adjustments applied to raw statement",
    )
    normalized_line_items: dict[str, float] = Field(
        default_factory=dict, description="Reconciled figures after adjustments"
    )
    extraction_confidence: dict[str, float] = Field(
        default_factory=dict, description="Confidence per-field mapping (0.0 to 1.0)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )

    def validate_accounting_identity(self) -> None:
        """
        Validates accounting identity constraints for the statement:
        - Balance Sheet: Assets = Liabilities + Equity (using normalized values if available)
        """
        if self.statement_type != StatementType.BALANCE:
            return

        # Use normalized items if present, fallback to raw items
        items = (
            self.normalized_line_items
            if self.normalized_line_items
            else self.line_items
        )

        assets = items.get("total_assets")
        liabilities = items.get("total_liabilities")
        equity = items.get("total_equity")

        if assets is None or liabilities is None or equity is None:
            # Check for generic/alternative naming conventions
            assets = items.get("assets")
            liabilities = items.get("liabilities")
            equity = items.get("equity")

        if assets is None or liabilities is None or equity is None:
            raise EntityValidationError(
                "Missing assets, liabilities, or equity for accounting identity check"
            )

        diff = abs(assets - (liabilities + equity))
        # Small tolerance (1.0 in case of rounding errors in millions/thousands)
        if diff > 1.0:
            raise EntityValidationError(
                f"Balance sheet identity violation (Assets != Liabilities + Equity): "
                f"Assets={assets}, Liabilities={liabilities}, Equity={equity} (Diff={diff})"
            )
