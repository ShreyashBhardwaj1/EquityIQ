"""
Trend Analysis Engine.
Calculates growth rates and categorizes trend states into advanced states.
"""

from app.domain.entities.financial_intelligence import TrendState


def calculate_growth_rate(v_prev: float, v_curr: float) -> float:
    """
    Helper to calculate percentage growth between two values.
    """
    if v_prev == 0.0:
        return 0.0 if v_curr == 0.0 else 1.0  # Handle zero division
    return (v_curr - v_prev) / abs(v_prev)


def classify_trend(values: list[float], stable_band: float = 0.01) -> TrendState:
    """
    Categorizes the trend state of a sequence of chronological float values.
    Expects values in chronological order, e.g., [oldest, ..., newest].
    """
    if len(values) < 2:
        return TrendState.STABLE

    # 1. Simple 2-point sequence
    if len(values) == 2:
        v1, v2 = values[0], values[1]
        g = calculate_growth_rate(v1, v2)
        if abs(g) <= stable_band:
            return TrendState.STABLE
        return TrendState.DECLINE if g < 0.0 else TrendState.ACCELERATING

    # 2. Check for volatility (more than one change in sign of growth)
    growths = [calculate_growth_rate(values[i-1], values[i]) for i in range(1, len(values))]
    sign_changes = 0
    for i in range(1, len(growths)):
        # Sign change occurs if one growth is positive/negative and the other is opposite
        g_prev, g_curr = growths[i-1], growths[i]
        if (g_prev > stable_band and g_curr < -stable_band) or (g_prev < -stable_band and g_curr > stable_band):
            sign_changes += 1

    if sign_changes >= 2:
        return TrendState.VOLATILE

    # 3. 3-point sequence analysis (using the last three points)
    v1, v2, v3 = values[-3], values[-2], values[-1]
    g1 = calculate_growth_rate(v1, v2)
    g2 = calculate_growth_rate(v2, v3)

    # Stable if the most recent change is within the stable band
    if abs(g2) <= stable_band:
        return TrendState.STABLE

    # Decline
    if g2 < -stable_band:
        return TrendState.DECLINE

    # Positive growth
    if g2 > stable_band:
        # Recovery (was negative, now positive)
        if g1 < -stable_band:
            return TrendState.RECOVERY
        # Accelerating (both positive, growth is increasing)
        elif g2 > g1 > stable_band:
            return TrendState.ACCELERATING
        # Decelerating (both positive, growth is decreasing)
        elif stable_band < g2 < g1:
            return TrendState.DECELERATING

    return TrendState.STABLE
