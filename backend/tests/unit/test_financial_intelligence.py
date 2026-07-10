"""
Unit tests for Financial Intelligence rules engines and orchestrator services.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.financial_intelligence_service import (
    FinancialIntelligenceService,
)
from app.domain.entities.financial_intelligence import SeverityLevel, TrendState
from app.domain.entities.recommendation import RecommendationType
from app.domain.rules.health_scoring import (
    calculate_health_score,
    score_negative_ratio,
    score_positive_ratio,
)
from app.domain.rules.recommendation_engine import evaluate_recommendation
from app.domain.rules.risk_engine import evaluate_risks
from app.domain.rules.trend_engine import calculate_growth_rate, classify_trend
from app.domain.value_objects.fiscal_period import FiscalPeriod


def test_trend_engine_calculations() -> None:
    # Test growth rates
    assert calculate_growth_rate(100.0, 110.0) == 0.10
    assert calculate_growth_rate(100.0, 90.0) == -0.10
    assert calculate_growth_rate(0.0, 10.0) == 1.0
    assert calculate_growth_rate(0.0, 0.0) == 0.0

    # Test classifications
    # 1. 2-points
    assert classify_trend([100.0, 100.5]) == TrendState.STABLE
    assert classify_trend([100.0, 110.0]) == TrendState.ACCELERATING
    assert classify_trend([100.0, 90.0]) == TrendState.DECLINE

    # 2. 3-points or more
    # Accelerating: [100, 110, 125] -> growth 10% then 13.6%
    assert classify_trend([100.0, 110.0, 125.0]) == TrendState.ACCELERATING
    # Decelerating: [100, 115, 120] -> growth 15% then 4.3%
    assert classify_trend([100.0, 115.0, 120.0]) == TrendState.DECELERATING
    # Recovery: [100, 80, 90] -> growth -20% then +12.5%
    assert classify_trend([100.0, 80.0, 90.0]) == TrendState.RECOVERY
    # Decline: [100, 90, 80] -> growth negative
    assert classify_trend([100.0, 90.0, 80.0]) == TrendState.DECLINE
    # Volatile: sign changes
    assert classify_trend([100.0, 120.0, 90.0, 110.0]) == TrendState.VOLATILE


def test_health_scoring_rules() -> None:
    # Test positive ratio
    assert score_positive_ratio(1.5, 1.0, 2.0) == 5.0
    assert score_positive_ratio(2.5, 1.0, 2.0) == 10.0
    assert score_positive_ratio(0.5, 1.0, 2.0) == 0.0

    # Test negative ratio
    assert score_negative_ratio(1.5, 1.0, 2.0) == 5.0
    assert score_negative_ratio(0.5, 1.0, 2.0) == 10.0
    assert score_negative_ratio(2.5, 1.0, 2.0) == 0.0

    # Test overall health calculation
    ratios: dict[str, float | None] = {
        "current_ratio": 1.5,
        "debt_to_equity": 1.0,
        "gross_margin": 0.25,
        "asset_turnover": 0.6,
        "operating_cf_margin": 0.10,
    }
    growth = {"revenue": 0.08}
    score_payload = calculate_health_score(ratios, growth)

    assert "overall_score" in score_payload
    assert score_payload["overall_score"] >= 0.0
    assert score_payload["overall_score"] <= 10.0
    assert score_payload["confidence"] < 1.0  # Partially defined categories



def test_risk_assessment_engine() -> None:
    # Safe ratios
    ratios_safe: dict[str, float | None] = {
        "current_ratio": 2.0,
        "quick_ratio": 1.5,
        "debt_to_equity": 0.5,
        "interest_coverage": 10.0,
        "net_margin": 0.15,
        "operating_cf_margin": 0.20,
    }
    risks_safe = evaluate_risks(ratios_safe)
    assert len(risks_safe) == 0

    # Distress ratios
    ratios_distress: dict[str, float | None] = {
        "current_ratio": 0.5,  # Severe liquidity
        "debt_to_equity": 3.0,  # Severe leverage
        "net_margin": -0.10,  # Severe loss
        "operating_cf_margin": -0.15,  # Severe cash outflow
    }
    risks_distress = evaluate_risks(ratios_distress)
    assert len(risks_distress) == 4
    for r in risks_distress:
        assert r["severity"] == SeverityLevel.SEVERE


def test_recommendation_engine() -> None:
    from app.domain.entities.financial_intelligence import RecommendationPolicy
    policy = RecommendationPolicy(
        policy_id=uuid.uuid4(),
        policy_name="Test Policy",
        policy_version="1.0.0",
        health_score_thresholds={
            "strong_buy": 8.5,
            "buy": 7.0,
            "hold": 4.5,
            "sell": 2.0,
            "strong_sell": 0.0,
        },
        max_severe_risks_allowed={
            "strong_buy": 0,
            "buy": 1,
            "hold": 2,
            "sell": 3,
            "strong_sell": 99,
        },
        requires_positive_growth=["strong_buy", "buy"],
        is_active=True,
    )

    # Strong Buy match
    rating, _logs = evaluate_recommendation(
        health_score=9.0,
        severe_risks_count=0,
        growth_rates={"revenue": 0.05},
        policy=policy,
    )
    assert rating == RecommendationType.STRONG_BUY

    # Fails growth check for Buy
    rating, _logs = evaluate_recommendation(
        health_score=8.0,
        severe_risks_count=0,
        growth_rates={"revenue": -0.02},
        policy=policy,
    )
    assert rating == RecommendationType.HOLD

    # Severe risks pushes down to Hold
    rating, _logs = evaluate_recommendation(
        health_score=8.8,
        severe_risks_count=2,
        growth_rates={"revenue": 0.10},
        policy=policy,
    )
    assert rating == RecommendationType.HOLD



@pytest.mark.asyncio
async def test_financial_intelligence_service() -> None:
    # Setup mocks
    stmt_repo = MagicMock()
    ratio_repo = MagicMock()
    health_repo = MagicMock()
    risk_repo = MagicMock()
    rec_repo = MagicMock()

    # Stub repository methods with AsyncMock
    ratio_repo.delete_by_period = AsyncMock()
    ratio_repo.save_batch = AsyncMock()
    health_repo.delete = AsyncMock()
    health_repo.save = AsyncMock()
    risk_repo.delete_by_period = AsyncMock()
    risk_repo.save_batch = AsyncMock()
    rec_repo.delete = AsyncMock()
    rec_repo.save_history = AsyncMock()

    # Stub list_by_company statement data
    from app.domain.entities.financial_statement import (
        FinancialStatement,
        StatementType,
    )
    statement = FinancialStatement(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        statement_type=StatementType.INCOME,
        fiscal_period=FiscalPeriod("FY", 2024),
        normalized_line_items={"revenue": 100000.0, "net_income": 15000.0},
    )
    stmt_repo.list_by_company = AsyncMock(return_value=[statement])

    # Stub active policy lookup
    from app.domain.entities.financial_intelligence import RecommendationPolicy
    policy = RecommendationPolicy(
        policy_id=uuid.uuid4(),
        policy_name="Test Policy",
        policy_version="1.0.0",
        health_score_thresholds={"strong_buy": 8.0, "buy": 7.0, "hold": 4.5, "sell": 2.0, "strong_sell": 0.0},
        max_severe_risks_allowed={"strong_buy": 0, "buy": 1, "hold": 2, "sell": 3, "strong_sell": 99},
        requires_positive_growth=["buy"],
        is_active=True,
    )
    rec_repo.get_active_policy = AsyncMock(return_value=policy)
    rec_repo.save = AsyncMock(return_value=MagicMock(id=uuid.uuid4(), recommendation=RecommendationType.BUY))

    service = FinancialIntelligenceService(
        statement_repo=stmt_repo,
        ratio_repo=ratio_repo,
        health_repo=health_repo,
        risk_repo=risk_repo,
        rec_repo=rec_repo,
    )

    result = await service.run_analysis(company_id=statement.company_id, fiscal_period="FY-2024")
    assert "health_score" in result
    assert "recommendation" in result
    assert result["portfolio_signal"]["rating"] == "strong_sell"


