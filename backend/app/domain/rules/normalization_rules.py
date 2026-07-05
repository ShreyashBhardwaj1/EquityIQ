"""
Normalization Rules Domain Logic.
Applies normalization adjustments and detects line item swing flags.
"""

from app.domain.entities.financial_statement import NormalizationAdjustment


def apply_normalization_adjustments(
    line_items: dict[str, float],
    adjustments: list[NormalizationAdjustment],
) -> dict[str, float]:
    """
    Applies a list of normalization adjustments to raw statement line items.
    Formula: Normalized Value = Raw Value + Adjustment
    """
    normalized_items = line_items.copy()

    for adj in adjustments:
        key = adj.line_item
        # If the item doesn't exist, we assume the baseline was 0.0
        current_val = normalized_items.get(key, 0.0)
        normalized_items[key] = current_val + adj.adjustment

    return normalized_items


def detect_line_item_swings(
    current_items: dict[str, float],
    prior_items: dict[str, float],
    threshold: float = 0.15,
) -> list[str]:
    """
    Scans two sets of line items (e.g. current vs. prior quarter) and returns
    a list of line item keys that swing by more than the threshold percentage.

    Threshold default is 0.15 (15%).
    """
    swung_items: list[str] = []

    for key, current_val in current_items.items():
        if key not in prior_items:
            # New line item that didn't exist prior represents a swing if non-zero
            if current_val != 0.0:
                swung_items.append(key)
            continue

        prior_val = prior_items[key]

        if prior_val == 0.0:
            if current_val != 0.0:
                swung_items.append(key)
            continue

        percent_change = abs(current_val - prior_val) / abs(prior_val)
        if percent_change > threshold:
            swung_items.append(key)

    return swung_items
