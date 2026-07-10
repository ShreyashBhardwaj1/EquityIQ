"""
Financial Health Scoring Engine.
Scores ratios based on configuration boundaries and aggregates them.
"""

from typing import Any

from app.core.financial_config import financial_config


def score_positive_ratio(val: float, low: float, high: float) -> float:
    """Higher is better."""
    if val >= high:
        return 10.0
    if val <= low:
        return 0.0
    return ((val - low) / (high - low)) * 10.0


def score_negative_ratio(val: float, low: float, high: float) -> float:
    """Lower is better (like debt-to-equity)."""
    if val <= low:
        return 10.0
    if val >= high:
        return 0.0
    return ((high - val) / (high - low)) * 10.0


def calculate_health_score(
    ratios: dict[str, float | None],
    growth_rates: dict[str, float] | None = None,
    weights_override: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Computes category health scores and overall weighted health score.
    """
    bounds = financial_config.scoring_boundaries
    weights = weights_override or financial_config.default_weights

    # Map ratios to their categories
    category_ratios: dict[str, list[float]] = {
        "liquidity": [],
        "leverage": [],
        "profitability": [],
        "efficiency": [],
        "cash_flow": [],
        "growth": [],
    }

    explanations: list[str] = []
    ratios_count = 0
    calculated_ratios_count = 0

    # 1. Score Liquidity
    liquidity_keys = ["current_ratio", "quick_ratio", "cash_ratio"]
    for key in liquidity_keys:
        ratios_count += 1
        val = ratios.get(key)
        if val is not None:
            calculated_ratios_count += 1
            low = bounds.get(f"{key}_low", 1.0)
            high = bounds.get(f"{key}_high", 2.0)
            score = score_positive_ratio(val, low, high)
            category_ratios["liquidity"].append(score)
            if score <= 3.0:
                explanations.append(
                    f"Weak liquidity indicated by low {key.replace('_', ' ')}: {val:.2f}"
                )

    # 2. Score Leverage
    leverage_keys = ["debt_to_equity", "debt_ratio", "interest_coverage"]
    for key in leverage_keys:
        ratios_count += 1
        val = ratios.get(key)
        if val is not None:
            calculated_ratios_count += 1
            low = bounds.get(f"{key}_low", 0.5)
            high = bounds.get(f"{key}_high", 2.5)
            if key == "interest_coverage":
                score = score_positive_ratio(val, low, high)
                if score <= 3.0:
                    explanations.append(f"Strained interest coverage: {val:.2f}")
            else:
                score = score_negative_ratio(val, low, high)
                if score <= 3.0:
                    explanations.append(
                        f"Elevated solvency risk from high {key.replace('_', ' ')}: {val:.2f}"
                    )
            category_ratios["leverage"].append(score)

    # 3. Score Profitability
    profit_keys = ["gross_margin", "operating_margin", "net_margin", "roa", "roe"]
    for key in profit_keys:
        ratios_count += 1
        val = ratios.get(key)
        if val is not None:
            calculated_ratios_count += 1
            low = bounds.get(f"{key}_low", 0.0)
            high = bounds.get(f"{key}_high", 0.20)
            score = score_positive_ratio(val, low, high)
            category_ratios["profitability"].append(score)
            if score <= 3.0:
                explanations.append(
                    f"Subdued profitability from low {key.replace('_', ' ')}: {val:.2f}"
                )

    # 4. Score Efficiency
    eff_keys = ["asset_turnover"]
    for key in eff_keys:
        ratios_count += 1
        val = ratios.get(key)
        if val is not None:
            calculated_ratios_count += 1
            low = bounds.get(f"{key}_low", 0.2)
            high = bounds.get(f"{key}_high", 1.0)
            score = score_positive_ratio(val, low, high)
            category_ratios["efficiency"].append(score)

    # 5. Score Cash Flow
    cf_keys = ["operating_cf_margin"]
    for key in cf_keys:
        ratios_count += 1
        val = ratios.get(key)
        if val is not None:
            calculated_ratios_count += 1
            low = bounds.get(f"{key}_low", 0.0)
            high = bounds.get(f"{key}_high", 0.20)
            score = score_positive_ratio(val, low, high)
            category_ratios["cash_flow"].append(score)

    # 6. Score Growth
    if growth_rates:
        for key, val in growth_rates.items():
            ratios_count += 1
            calculated_ratios_count += 1
            # Standard bounds: -0.05 (decline) to 0.10 (solid growth)
            score = score_positive_ratio(val, -0.05, 0.10)
            category_ratios["growth"].append(score)
            if val < 0:
                explanations.append(
                    f"Negative growth observed in {key.replace('_', ' ')}: {val * 100:.1f}%"
                )

    # Aggregate category scores
    category_scores: dict[str, float] = {}
    active_weights: dict[str, float] = {}
    total_active_weight = 0.0

    for cat_name, scores in category_ratios.items():
        if scores:
            cat_score = sum(scores) / len(scores)
            category_scores[cat_name] = cat_score
            cat_weight = weights.get(cat_name, 0.0)
            active_weights[cat_name] = cat_weight
            total_active_weight += cat_weight
        else:
            # Placeholder or fallback if no data for the category
            category_scores[cat_name] = 5.0  # Neutral fallback

    # Compute overall score
    overall_score = 0.0
    if total_active_weight > 0.0:
        for cat_name, cat_weight in active_weights.items():
            overall_score += category_scores[cat_name] * (
                cat_weight / total_active_weight
            )
    else:
        overall_score = 5.0  # Neutral fallback

    # Add general description to explanation
    if overall_score >= 7.5:
        explanations.insert(
            0, f"Strong overall financial position (Score: {overall_score:.2f})"
        )
    elif overall_score >= 4.5:
        explanations.insert(
            0, f"Moderate financial health (Score: {overall_score:.2f})"
        )
    else:
        explanations.insert(
            0, f"Caution: Weak financial health profile (Score: {overall_score:.2f})"
        )

    retrieval_confidence = 0.95
    financial_data_quality = calculated_ratios_count / max(1, ratios_count)

    if category_scores:
        avg = sum(category_scores.values()) / len(category_scores)
        variance = sum((x - avg) ** 2 for x in category_scores.values()) / len(
            category_scores
        )
        std_dev = variance**0.5
        rule_agreement = max(0.0, min(1.0, 1.0 - (std_dev / 5.0)))
    else:
        rule_agreement = 1.0

    trend_consistency = 1.0
    if growth_rates:
        vals = list(growth_rates.values())
        if vals:
            pos = sum(1 for v in vals if v > 0)
            neg = sum(1 for v in vals if v < 0)
            if pos == len(vals) or neg == len(vals):
                trend_consistency = 1.0
            elif pos > 0 and neg > 0:
                trend_consistency = 0.6
            else:
                trend_consistency = 0.8

    overall_confidence = (
        retrieval_confidence
        + financial_data_quality
        + rule_agreement
        + trend_consistency
    ) / 4.0

    confidence_breakdown = {
        "retrieval_confidence": round(retrieval_confidence, 2),
        "financial_data_quality": round(financial_data_quality, 2),
        "rule_agreement": round(rule_agreement, 2),
        "trend_consistency": round(trend_consistency, 2),
        "overall_confidence": round(overall_confidence, 2),
    }

    return {
        "overall_score": round(overall_score, 2),
        "category_scores": {k: round(v, 2) for k, v in category_scores.items()},
        "weights": weights,
        "score_explanation": explanations,
        "confidence": round(overall_confidence, 2),
        "confidence_breakdown": confidence_breakdown,
    }
