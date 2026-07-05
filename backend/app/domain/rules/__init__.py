"""
Rules package containing mathematical and business rules for financial computations.
"""

from app.domain.rules.dcf_math import calculate_dcf
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
from app.domain.rules.scoring_rubric import calculate_composite_score

__all__ = [
    "apply_normalization_adjustments",
    "calculate_composite_score",
    "calculate_current_ratio",
    "calculate_dcf",
    "calculate_debt_to_equity",
    "calculate_ev_to_ebitda",
    "calculate_gross_margin",
    "calculate_net_margin",
    "calculate_operating_margin",
    "calculate_pe_ratio",
    "calculate_price_to_book",
    "calculate_quick_ratio",
    "calculate_return_on_assets",
    "calculate_return_on_equity",
    "detect_line_item_swings",
]
