"""
Ratio entity representing computed financial ratios.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects.fiscal_period import FiscalPeriod


class Ratio(BaseModel):
    """
    Ratio domain entity representing a computed financial metric (e.g., Debt-to-Equity, PE).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique identifier for the ratio record")
    company_id: UUID = Field(description="Associated company identifier")
    fiscal_period: FiscalPeriod = Field(
        description="Associated fiscal period value object"
    )
    ratio_name: str = Field(min_length=1, description="Financial ratio metric key")
    value: float = Field(description="Calculated ratio value")
    formula_version: str = Field(
        min_length=1, description="Tracked formula version used in computation"
    )
    computed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Computation timestamp"
    )

    @property
    def status(self) -> str:
        """Determines qualitative classification (Excellent, Healthy, Watch, etc.)"""
        from app.domain.rules.ratio_registry import classify_ratio_status
        return classify_ratio_status(self.ratio_name, self.value)

