"""
Valuation entity representing valuation calculations (DCF, Comps).
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ValuationMethod(StrEnum):
    """Supported valuation methods."""

    DCF = "dcf"
    COMPS = "comps"


class DCFAssumptions(BaseModel):
    """Assumptions model specifically for Discounted Cash Flow valuation."""

    model_config = ConfigDict(frozen=True)

    wacc: float = Field(gt=0.0, description="Weighted Average Cost of Capital")
    terminal_growth: float = Field(ge=0.0, description="Perpetual growth rate")
    projection_years: int = Field(gt=0, description="Forecast period length")
    net_debt: float = Field(description="Total Debt minus Cash")
    shares_outstanding: float = Field(gt=0.0, description="Current shares outstanding")


class ComparableCompanyAssumptions(BaseModel):
    """Assumptions model specifically for multiples-based valuation."""

    model_config = ConfigDict(frozen=True)

    peers: list[str] = Field(description="List of peer ticker symbols")
    multiples: list[str] = Field(
        description="Multiples to compare (e.g., EV/EBITDA, P/E)"
    )


class Valuation(BaseModel):
    """
    Valuation domain entity representing calculated valuation (DCF model or Multiples Comps).
    Tracks assumptions and logs conflicts between sources.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique identifier for the valuation record")
    company_id: UUID = Field(description="Associated company identifier")
    method: ValuationMethod = Field(description="Valuation methodology used")
    assumptions: DCFAssumptions | ComparableCompanyAssumptions | dict[str, Any] = Field(
        description="Input parameters and assumptions model"
    )
    data_source_log: dict[str, Any] = Field(
        default_factory=dict,
        description="Records which source was authoritative for conflict fields",
    )
    result: dict[str, Any] = Field(
        default_factory=dict, description="Calculated results and sensitivity grids"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Valuation creation timestamp"
    )
