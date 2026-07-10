"""
Domain entities and value objects for the Financial Intelligence Engine.
"""

from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.recommendation import RecommendationType
from app.domain.value_objects.fiscal_period import FiscalPeriod


class RatioCategory(StrEnum):
    """Categories grouping financial ratios."""

    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"
    PROFITABILITY = "profitability"
    EFFICIENCY = "efficiency"
    CASH_FLOW = "cash_flow"


class SeverityLevel(StrEnum):
    """Severity ratings for deterministic risks."""

    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"


class TrendState(StrEnum):
    """Categorized status states of financial trends over multiple periods."""

    ACCELERATING = "accelerating"  # Growth is positive and rate is increasing
    DECELERATING = "decelerating"  # Growth is positive but rate is decreasing
    RECOVERY = "recovery"  # Growth is positive after being negative
    DECLINE = "decline"  # Growth is negative
    STABLE = "stable"  # Growth is flat within a narrow band
    VOLATILE = "volatile"  # Erratic changes across multiple periods


class RatioDefinition(BaseModel):
    """Registry definition details for a financial ratio calculation."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str = Field(min_length=1, description="Unique metric key of the ratio")
    category: RatioCategory = Field(description="Target ratio classification category")
    formula: str = Field(
        min_length=1, description="String representation of the formula"
    )
    required_line_items: list[str] = Field(
        description="Keys of normalized line items required as inputs"
    )
    calculate_fn: Callable[[dict[str, float]], float] = Field(
        description="Pure function performing calculations"
    )
    assumptions: str = Field(
        min_length=1, description="Logical assumptions for math operations"
    )
    validation_rules: list[Callable[[float], bool]] = Field(
        default_factory=list,
        description="List of boolean validator check rules for calculated results",
    )


class RatioCalculationResult(BaseModel):
    """Computed result of a single financial ratio calculation."""

    model_config = ConfigDict(frozen=True)

    ratio_name: str = Field(min_length=1, description="Target ratio metric key")
    category: RatioCategory = Field(description="Assigned category of the ratio")
    value: float | None = Field(default=None, description="Calculated ratio value")
    is_valid: bool = Field(
        description="Flag confirming ratio succeeded validation rules"
    )
    error_message: str | None = Field(
        default=None, description="Reason if calculation failed"
    )
    formula: str = Field(min_length=1, description="Tracked formula logic string")
    line_items_used: dict[str, float] = Field(
        default_factory=dict, description="Raw items consumed in calculation"
    )
    ratio_engine_version: str = Field(min_length=1, description="Tracked version index")


class RecommendationPolicy(BaseModel):
    """Thresholds and criteria governing rules-based recommendation ratings."""

    model_config = ConfigDict(frozen=True)

    policy_id: UUID = Field(description="Unique policy database identifier")
    policy_name: str = Field(min_length=1, description="Unique semantic name")
    policy_version: str = Field(min_length=1, description="Semantic version of policy")
    health_score_thresholds: dict[str, float] = Field(
        description="Health score limits per recommendation rating key"
    )
    max_severe_risks_allowed: dict[str, int] = Field(
        description="Upper limit of Severe risks allowed per rating category"
    )
    requires_positive_growth: list[str] = Field(
        description="Recommendation rating keys requiring positive growth checks"
    )
    is_active: bool = Field(default=True, description="Active status indicator")


class FinancialHealthScore(BaseModel):
    """Calculated overall and category-level health scores."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique health score record identifier")
    company_id: UUID = Field(description="Associated company identifier")
    fiscal_period: FiscalPeriod = Field(description="Target reporting period")
    overall_score: float = Field(ge=0.0, le=10.0, description="Overall weighted score")
    category_scores: dict[str, float] = Field(
        description="Breakdown scores (0.0 to 10.0) per category"
    )
    weights: dict[str, float] = Field(description="Weights configuration applied")
    score_explanation: list[str] = Field(
        default_factory=list, description="Reasoning statements explaining scores"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Calculations completeness indicator"
    )
    percentile: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Percentile rank relative to peers"
    )
    ratio_engine_version: str = Field(
        min_length=1, description="Ratio engine version context"
    )
    confidence_breakdown: dict[str, float] = Field(
        default_factory=dict, description="Detailed scoring confidence breakdown"
    )
    computed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Calculation timestamp"
    )


class RiskAssessment(BaseModel):
    """Detected risk flag rating for a company and period."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique risk record identifier")
    company_id: UUID = Field(description="Associated company identifier")
    fiscal_period: FiscalPeriod = Field(description="Target reporting period")
    risk_category: str = Field(min_length=1, description="Target metric domain label")
    severity: SeverityLevel = Field(description="Calculated severity tier")
    confidence: float = Field(ge=0.0, le=1.0, description="Risk scoring confidence")
    supporting_evidence: str = Field(
        min_length=1, description="Data points supporting findings"
    )
    ratio_engine_version: str = Field(min_length=1, description="Engine version code")
    computed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Calculation timestamp"
    )


class RecommendationHistory(BaseModel):
    """Historical audit trail entry tracking policy decisions."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique history record identifier")
    recommendation_id: UUID = Field(description="Reference recommendation UUID")
    company_id: UUID = Field(description="Associated company identifier")
    fiscal_period: FiscalPeriod = Field(description="Target reporting period")
    rating: RecommendationType = Field(description="Historical recommendation value")
    policy_id: UUID = Field(description="Used recommendation policy ID")
    policy_version: str = Field(min_length=1, description="Used policy version string")
    composite_score: float = Field(
        ge=0.0, le=10.0, description="Applied composite score value"
    )
    reasoning_steps: list[str] = Field(
        default_factory=list, description="Reasoning logs of logic transitions"
    )
    triggered_by: UUID | None = Field(
        default=None, description="Initiating user database identifier"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
