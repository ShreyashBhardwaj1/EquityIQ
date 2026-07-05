"""
Unit tests for the Scoring Rubric.
"""

import pytest
from app.domain.entities.recommendation import RecommendationType
from app.domain.rules.scoring_rubric import calculate_composite_score


def test_calculate_composite_score_buy() -> None:
    """Test Buy recommendation triggers (undervalued, low leverage, positive sentiment)."""
    res = calculate_composite_score(
        intrinsic_value=130.0,
        current_price=100.0,  # 30% upside (val_score = 10.0)
        pe_ratio=10.0,
        industry_pe_median=20.0,  # 50% fraction (rel_score = 10.0)
        debt_to_equity=0.4,  # low debt (health_score = 10.0)
        sentiment_score=0.6,  # positive sentiment (mapped = 8.0)
        risk_flags_count=0,  # no penalty
    )

    # Weighted: (10 * 0.4) + (10 * 0.2) + (10 * 0.2) + (8 * 0.2) = 4.0 + 2.0 + 2.0 + 1.6 = 9.6
    assert res["composite_score"] == 9.6
    assert res["recommendation"] == RecommendationType.BUY


def test_calculate_composite_score_hold() -> None:
    """Test Hold recommendation triggers (neutral valuation, average sentiment)."""
    res = calculate_composite_score(
        intrinsic_value=100.0,
        current_price=100.0,  # 0% upside (val_score = 2.5)
        pe_ratio=15.0,
        industry_pe_median=15.0,  # 100% fraction (rel_score = 5.0)
        debt_to_equity=1.5,  # moderate debt (health_score = 5.0)
        sentiment_score=0.0,  # neutral sentiment (mapped = 5.0)
        risk_flags_count=0,
    )

    # Weighted: (2.5 * 0.4) + (5.0 * 0.2) + (5.0 * 0.2) + (5.0 * 0.2) = 1.0 + 1.0 + 1.0 + 1.0 = 4.0?
    # Wait, let's trace:
    # val_score: upside = 0.0. Linear scaling between -10% and +30%.
    # Formula: ((upside + 0.10) / 0.40) * 10 = (0.10 / 0.40) * 10 = 2.5. Correct!
    # rel_score: fraction = 1.0. (1.5 - 1.0) * 10 = 5.0. Correct!
    # health_score: debt_to_equity = 1.5. ((2.5 - 1.5) / 2) * 10 = (1 / 2) * 10 = 5.0. Correct!
    # sentiment: mapped = 5.0. Correct!
    # Total: 1.0 + 1.0 + 1.0 + 1.0 = 4.0.
    # Score 4.0 is SELL (< 4.5).
    # Let's adjust parameters to get a HOLD score (e.g. current_price = 90.0, which has ~11% upside).
    res = calculate_composite_score(
        intrinsic_value=110.0,
        current_price=100.0,  # 10% upside (val_score = 5.0)
        pe_ratio=15.0,
        industry_pe_median=15.0,  # rel_score = 5.0
        debt_to_equity=1.5,  # health_score = 5.0
        sentiment_score=0.0,  # mapped = 5.0
        risk_flags_count=0,
    )
    # Total: (5.0 * 0.4) + (5.0 * 0.2) + (5.0 * 0.2) + (5.0 * 0.2) = 2.0 + 1.0 + 1.0 + 1.0 = 5.0
    assert res["composite_score"] == 5.0
    assert res["recommendation"] == RecommendationType.HOLD


def test_calculate_composite_score_sell() -> None:
    """Test Sell recommendation triggers (overvalued, high debt, poor sentiment)."""
    res = calculate_composite_score(
        intrinsic_value=80.0,
        current_price=100.0,  # -20% downside (val_score = 0.0)
        pe_ratio=25.0,
        industry_pe_median=15.0,  # fraction = 1.67 >= 1.5 (rel_score = 0.0)
        debt_to_equity=2.6,  # high debt (health_score = 0.0)
        sentiment_score=-0.8,  # negative sentiment (mapped = 1.0)
        risk_flags_count=0,
    )

    # Weighted: (0.0 * 0.4) + (0.0 * 0.2) + (0.0 * 0.2) + (1.0 * 0.2) = 0.2
    assert res["composite_score"] == pytest.approx(0.2)
    assert res["recommendation"] == RecommendationType.SELL


def test_scoring_risk_penalties() -> None:
    """Test that risk flags subtract properly from the score."""
    # Base score without penalty is 9.6 (Buy)
    # 2 risk flags should subtract 2.0 points -> 7.6 (Buy)
    res_2_flags = calculate_composite_score(
        intrinsic_value=130.0,
        current_price=100.0,
        pe_ratio=10.0,
        industry_pe_median=20.0,
        debt_to_equity=0.4,
        sentiment_score=0.6,
        risk_flags_count=2,
    )
    assert res_2_flags["composite_score"] == 7.6

    # 4 risk flags should cap penalty at 3.0 points -> 6.6 (Hold)
    res_4_flags = calculate_composite_score(
        intrinsic_value=130.0,
        current_price=100.0,
        pe_ratio=10.0,
        industry_pe_median=20.0,
        debt_to_equity=0.4,
        sentiment_score=0.6,
        risk_flags_count=4,
    )
    assert res_4_flags["composite_score"] == 6.6
    assert res_4_flags["recommendation"] == RecommendationType.HOLD
