"""
Policy-driven Recommendation Engine.
Maps composite health scores, severe risks, and growth states against configurable policy rules.
"""

from app.domain.entities.financial_intelligence import RecommendationPolicy
from app.domain.entities.recommendation import RecommendationType


def evaluate_recommendation(
    health_score: float,
    severe_risks_count: int,
    growth_rates: dict[str, float] | None,
    policy: RecommendationPolicy,
) -> tuple[RecommendationType, list[str]]:
    """
    Evaluates policy-driven rules to assign an investment recommendation.
    Returns a tuple of (RecommendationType, reasoning_steps).
    """
    reasoning_steps = []
    reasoning_steps.append(
        f"Evaluating policy '{policy.policy_name}' (v{policy.policy_version}) "
        f"for Health Score: {health_score:.2f}, Severe Risks: {severe_risks_count}."
    )

    # 1. Growth validation
    has_positive_growth = True
    if growth_rates:
        for metric, growth in growth_rates.items():
            if growth < 0.0:
                has_positive_growth = False
                reasoning_steps.append(
                    f"Negative growth detected in {metric}: {growth * 100:.1f}%."
                )

    # Define execution checks in descending rating order
    ratings_hierarchy = [
        RecommendationType.STRONG_BUY,
        RecommendationType.BUY,
        RecommendationType.HOLD,
        RecommendationType.SELL,
        RecommendationType.STRONG_SELL,
    ]

    for rating in ratings_hierarchy:
        score_thresh = policy.health_score_thresholds.get(rating, 0.0)
        risk_limit = policy.max_severe_risks_allowed.get(rating, 99)
        needs_growth = rating in policy.requires_positive_growth

        reasoning_steps.append(
            f"Checking threshold for {rating.upper()}: "
            f"Health Score >= {score_thresh}, Max Severe Risks <= {risk_limit}, Requires Growth: {needs_growth}."
        )

        # Validate score limit
        if health_score < score_thresh:
            reasoning_steps.append(
                f"Failed {rating.upper()} score check (score {health_score:.2f} < threshold {score_thresh})."
            )
            continue

        # Validate severe risks limit
        if severe_risks_count > risk_limit:
            reasoning_steps.append(
                f"Failed {rating.upper()} risk check (severe risk count {severe_risks_count} > limit {risk_limit})."
            )
            continue

        # Validate positive growth requirement
        if needs_growth and not has_positive_growth:
            reasoning_steps.append(
                f"Failed {rating.upper()} growth check (requires positive growth on designated metrics)."
            )
            continue

        # All checks passed for this rating
        reasoning_steps.append(f"Recommendation policy matched: {rating.upper()}.")
        return rating, reasoning_steps

    # Fallback default
    reasoning_steps.append("Default fallback matched: STRONG_SELL.")
    return RecommendationType.STRONG_SELL, reasoning_steps
