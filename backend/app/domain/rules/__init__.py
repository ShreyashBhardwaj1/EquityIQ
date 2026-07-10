"""
Rules package containing mathematical and business rules for financial computations.
"""

from app.domain.rules.chunk_validation import ChunkValidator
from app.domain.rules.dcf_math import calculate_dcf
from app.domain.rules.health_scoring import calculate_health_score
from app.domain.rules.normalization import NormalizationEngine, NormalizationRule
from app.domain.rules.normalization_rules import (
    apply_normalization_adjustments,
    detect_line_item_swings,
)
from app.domain.rules.ratio_formulas import (
    calculate_current_ratio,
    calculate_debt_to_equity,
    calculate_ev_to_ebitda,
    calculate_gross_margin,
    calculate_net_margin,
    calculate_operating_margin,
    calculate_pe_ratio,
    calculate_price_to_book,
    calculate_quick_ratio,
    calculate_return_on_assets,
    calculate_return_on_equity,
)
from app.domain.rules.ratio_registry import RatioRegistry
from app.domain.rules.recommendation_engine import evaluate_recommendation
from app.domain.rules.risk_engine import evaluate_risks
from app.domain.rules.scoring_rubric import calculate_composite_score
from app.domain.rules.trend_engine import classify_trend
from app.domain.rules.validation import ValidationContext, ValidationEngine

__all__ = [
    "ChunkValidator",
    "NormalizationEngine",
    "NormalizationRule",
    "RatioRegistry",
    "ValidationContext",
    "ValidationEngine",
    "apply_normalization_adjustments",
    "calculate_composite_score",
    "calculate_current_ratio",
    "calculate_dcf",
    "calculate_debt_to_equity",
    "calculate_ev_to_ebitda",
    "calculate_gross_margin",
    "calculate_health_score",
    "calculate_net_margin",
    "calculate_operating_margin",
    "calculate_pe_ratio",
    "calculate_price_to_book",
    "calculate_quick_ratio",
    "calculate_return_on_assets",
    "calculate_return_on_equity",
    "classify_trend",
    "detect_line_item_swings",
    "evaluate_recommendation",
    "evaluate_risks",
]
