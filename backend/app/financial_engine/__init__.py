"""
Financial Engine Package.
Re-exports domain/rules for backwards compatibility with earlier systems.
"""

from app.domain.rules import (
    apply_normalization_adjustments,
    calculate_composite_score,
    calculate_current_ratio,
    calculate_dcf,
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
    detect_line_item_swings,
)

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
