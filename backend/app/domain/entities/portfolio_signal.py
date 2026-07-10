"""
Domain entity representing a portfolio allocation signal.
Prepares codebase for Milestone 9 portfolio optimization tasks.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.financial_intelligence import SeverityLevel
from app.domain.entities.recommendation import RecommendationType


class PortfolioSignal(BaseModel):
    """
    Placeholder domain model representing a generated asset allocation/rebalancing signal.
    """

    model_config = ConfigDict(frozen=True)

    company_id: UUID = Field(description="Target company identifier")
    ticker: str = Field(min_length=1, description="Company stock ticker symbol")
    recommendation: RecommendationType = Field(
        description="Rating recommendation value"
    )
    health_score: float = Field(
        ge=0.0, le=10.0, description="Weighted financial health score value"
    )
    overall_risk_rating: SeverityLevel = Field(
        description="Assigned overall risk severity rating"
    )
    allocation_weight_multiplier: float = Field(
        ge=0.0, description="Suggested allocation scaling weight factor"
    )
    suggested_action: str = Field(
        min_length=1,
        description="Suggested action tag (e.g. ACCUMULATE, EXIT, HOLD)",
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
