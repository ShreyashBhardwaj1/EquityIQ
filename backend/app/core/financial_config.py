"""
Centralized Financial Intelligence configuration.
Defines version indices, thresholds, weights, and scoring boundaries.
"""

from pydantic import BaseModel, Field


class FinancialIntelligenceConfig(BaseModel):
    """
    Configuration model for the Financial Intelligence & Recommendation Engine.
    """

    # Engine and policy versions
    ratio_engine_version: str = "1.0.0"
    recommendation_policy_version: str = "1.0.0-default"
    health_score_version: str = "1.0.0"
    risk_engine_version: str = "1.0.0"

    # Default category weights for health score (must sum to 1.0)
    default_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "liquidity": 0.15,
            "profitability": 0.25,
            "leverage": 0.20,
            "cash_flow": 0.20,
            "growth": 0.10,
            "efficiency": 0.10,
        }
    )

    # Trend detection thresholds
    trend_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "stable_band": 0.01,  # +/- 1% for stable
            "significant_growth": 0.05,  # > 5% growth
            "significant_decline": -0.05,  # < -5% growth
        }
    )

    # Scoring boundaries
    scoring_boundaries: dict[str, float] = Field(
        default_factory=lambda: {
            "current_ratio_high": 2.0,
            "current_ratio_low": 1.0,
            "quick_ratio_high": 1.5,
            "quick_ratio_low": 0.8,
            "cash_ratio_high": 1.0,
            "cash_ratio_low": 0.2,
            "debt_to_equity_high": 2.5,
            "debt_to_equity_low": 0.5,
            "debt_ratio_high": 0.8,
            "debt_ratio_low": 0.3,
            "interest_coverage_high": 5.0,
            "interest_coverage_low": 1.5,
            "net_margin_high": 0.20,
            "net_margin_low": 0.0,
            "operating_margin_high": 0.15,
            "operating_margin_low": 0.0,
            "gross_margin_high": 0.40,
            "gross_margin_low": 0.10,
            "roa_high": 0.08,
            "roa_low": 0.0,
            "roe_high": 0.15,
            "roe_low": 0.0,
            "asset_turnover_high": 1.0,
            "asset_turnover_low": 0.2,
            "operating_cf_margin_high": 0.20,
            "operating_cf_margin_low": 0.0,
        }
    )


# Global financial configuration instance
financial_config = FinancialIntelligenceConfig()
