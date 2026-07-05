"""
Scoring Rubric Domain Rules.
Computes a composite investment score and rating.
"""

from typing import Any

from app.domain.entities.recommendation import RecommendationType


def calculate_composite_score(
    intrinsic_value: float,
    current_price: float,
    pe_ratio: float,
    industry_pe_median: float,
    debt_to_equity: float,
    sentiment_score: float,  # Between -1.0 (bearish) and 1.0 (bullish)
    risk_flags_count: int,
) -> dict[str, Any]:
    """
    Computes a composite financial rating (0.0 to 10.0) based on:
    - Valuation Upside (W: 40%)
    - Relative Valuation (W: 20%)
    - Financial Leverage/Health (W: 20%)
    - News/Sentiment (W: 20%)
    - Risk Flags Penalty (subtracts 1.0 per flag, max penalty 3.0)
    """
    # 1. Valuation Score (Upside to DCF)
    if current_price <= 0.0:
        val_score = 0.0
        upside = 0.0
    else:
        upside = (intrinsic_value - current_price) / current_price
        if upside >= 0.30:  # 30% or more upside
            val_score = 10.0
        elif upside <= -0.10:  # Overvalued
            val_score = 0.0
        else:
            # Linear scaling between -10% and +30%
            val_score = ((upside + 0.10) / 0.40) * 10.0

    # 2. Relative Valuation Score (P/E comparison)
    if pe_ratio <= 0.0 or industry_pe_median <= 0.0:
        rel_score = 5.0  # Neutral fallback
    else:
        pe_ratio_fraction = pe_ratio / industry_pe_median
        if pe_ratio_fraction <= 0.5:
            rel_score = 10.0
        elif pe_ratio_fraction >= 1.5:
            rel_score = 0.0
        else:
            rel_score = (1.5 - pe_ratio_fraction) * 10.0

    # 3. Financial Health Score (Debt to Equity)
    if debt_to_equity <= 0.5:
        health_score = 10.0
    elif debt_to_equity >= 2.5:
        health_score = 0.0
    else:
        health_score = ((2.5 - debt_to_equity) / 2.0) * 10.0

    # 4. Sentiment Score (Map -1.0 -> 1.0 to 0 -> 10)
    clamped_sentiment = max(-1.0, min(1.0, sentiment_score))
    sentiment_rating = (clamped_sentiment + 1.0) * 5.0

    # 5. Combine Weighted Score
    base_score = (
        (val_score * 0.4)
        + (rel_score * 0.2)
        + (health_score * 0.2)
        + (sentiment_rating * 0.2)
    )

    # 6. Apply Risk Penalty (Max penalty of 3.0 points)
    penalty = min(3.0, float(max(0, risk_flags_count)) * 1.0)
    composite_score = max(0.0, min(10.0, base_score - penalty))

    # 7. Convert score to recommendation category
    if composite_score >= 7.5:
        rec_type = RecommendationType.BUY
    elif composite_score >= 4.5:
        rec_type = RecommendationType.HOLD
    else:
        rec_type = RecommendationType.SELL

    return {
        "valuation_score": val_score,
        "valuation_upside": upside,
        "relative_valuation_score": rel_score,
        "financial_health_score": health_score,
        "sentiment_score_mapped": sentiment_rating,
        "base_score": base_score,
        "risk_penalty": penalty,
        "composite_score": composite_score,
        "recommendation": rec_type,
    }
