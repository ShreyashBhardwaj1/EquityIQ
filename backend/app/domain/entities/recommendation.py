from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects.fiscal_period import FiscalPeriod


class RecommendationType(StrEnum):
    """Investment recommendation ratings."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class Recommendation(BaseModel):
    """
    Recommendation domain entity representing the final investment decision
    with scoring metrics and narrative reasoning.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique identifier for the recommendation")
    company_id: UUID = Field(description="Associated company identifier")
    recommendation: RecommendationType = Field(
        description="Investment recommendation rating"
    )
    composite_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Score calculated based on financial scoring rubrics",
    )
    rationale: str = Field(min_length=1, description="Narrative reasoning explanation")
    fiscal_period: FiscalPeriod | None = Field(
        default=None, description="Target reporting fiscal period value object"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Recommendation creation timestamp"
    )

