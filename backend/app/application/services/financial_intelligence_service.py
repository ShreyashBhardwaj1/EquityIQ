"""
FinancialIntelligenceService orchestrator service.
"""

import logging
import uuid
from typing import Any
from uuid import UUID

from app.core.financial_config import financial_config
from app.domain.entities.financial_intelligence import (
    FinancialHealthScore,
    RecommendationHistory,
    RecommendationPolicy,
    RiskAssessment,
)
from app.domain.entities.ratio import Ratio
from app.domain.entities.recommendation import Recommendation, RecommendationType
from app.domain.interfaces.repositories import (
    FinancialStatementRepository,
    HealthScoreRepository,
    RatioRepository,
    RecommendationRepository,
    RiskAssessmentRepository,
)
from app.domain.rules.health_scoring import calculate_health_score
from app.domain.rules.ratio_registry import RatioRegistry
from app.domain.rules.recommendation_engine import evaluate_recommendation
from app.domain.rules.risk_engine import evaluate_risks
from app.domain.rules.trend_engine import calculate_growth_rate
from app.domain.value_objects.fiscal_period import FiscalPeriod

logger = logging.getLogger("equityiq.application.financial_intelligence_service")


def get_previous_period(period: str) -> str:
    """Gets previous chronological reporting period key."""
    if period.startswith("FY-"):
        try:
            yr = int(period.split("-")[1])
            return f"FY-{yr - 1}"
        except ValueError:
            pass
    elif period.startswith("Q"):
        try:
            parts = period.split("-")
            q = int(parts[0][1])
            yr = int(parts[1])
            if q == 1:
                return f"Q4-{yr - 1}"
            else:
                return f"Q{q - 1}-{yr}"
        except (ValueError, IndexError):
            pass
    return ""


def get_yoy_period(period: str) -> str:
    """Gets YoY reporting period key (quarter of previous year)."""
    if period.startswith("Q"):
        try:
            parts = period.split("-")
            q_str = parts[0]
            yr = int(parts[1])
            return f"{q_str}-{yr - 1}"
        except (ValueError, IndexError):
            pass
    elif period.startswith("FY-"):
        return get_previous_period(period)
    return ""


def make_fiscal_period(val: str) -> FiscalPeriod:
    """Helper to construct a FiscalPeriod from string 'PERIOD-YEAR'."""
    parts = val.split("-")
    if len(parts) == 2:
        return FiscalPeriod(parts[0], int(parts[1]))
    raise ValueError(f"Invalid period format: {val}")


class FinancialIntelligenceService:
    """
    Orchestrates the deterministic financial metrics, risk assessment, health scoring,
    and policy-driven recommendation pipeline.
    """

    def __init__(
        self,
        statement_repo: FinancialStatementRepository,
        ratio_repo: RatioRepository,
        health_repo: HealthScoreRepository,
        risk_repo: RiskAssessmentRepository,
        rec_repo: RecommendationRepository,
    ) -> None:
        self.statement_repo = statement_repo
        self.ratio_repo = ratio_repo
        self.health_repo = health_repo
        self.risk_repo = risk_repo
        self.rec_repo = rec_repo

    async def get_or_create_active_policy(self) -> RecommendationPolicy:
        """Helper to get active policy or seed default active policy if none exists."""
        policy = await self.rec_repo.get_active_policy()
        if not policy:
            # Build default active recommendation policy
            health_thresholds = {
                RecommendationType.STRONG_BUY.value: 8.5,
                RecommendationType.BUY.value: 7.0,
                RecommendationType.HOLD.value: 4.5,
                RecommendationType.SELL.value: 2.0,
                RecommendationType.STRONG_SELL.value: 0.0,
            }
            max_risks = {
                RecommendationType.STRONG_BUY.value: 0,
                RecommendationType.BUY.value: 1,
                RecommendationType.HOLD.value: 2,
                RecommendationType.SELL.value: 3,
                RecommendationType.STRONG_SELL.value: 99,
            }
            policy = RecommendationPolicy(
                policy_id=uuid.uuid4(),
                policy_name="Standard Evaluation Policy",
                policy_version=financial_config.recommendation_policy_version,
                health_score_thresholds=health_thresholds,
                max_severe_risks_allowed=max_risks,
                requires_positive_growth=[
                    RecommendationType.STRONG_BUY.value,
                    RecommendationType.BUY.value,
                ],
                is_active=True,
            )
            await self.rec_repo.save_policy(policy)
        return policy

    async def run_analysis(
        self, company_id: UUID, fiscal_period: str, user_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Runs the full deterministic analysis for a company and period.
        """
        # 1. Fetch current statements
        all_statements = await self.statement_repo.list_by_company(company_id)
        curr_statements = [s for s in all_statements if str(s.fiscal_period) == fiscal_period]

        if not curr_statements:
            raise ValueError(f"No financial statements found for period {fiscal_period}")

        # Flat dictionary of line items
        curr_line_items: dict[str, float] = {}
        for s in curr_statements:
            curr_line_items.update(s.normalized_line_items)

        # 2. Fetch past periods for growth/trend analysis
        prev_period_key = get_previous_period(fiscal_period)
        yoy_period_key = get_yoy_period(fiscal_period)

        prev_statements = [s for s in all_statements if str(s.fiscal_period) == prev_period_key]
        yoy_statements = [s for s in all_statements if str(s.fiscal_period) == yoy_period_key]

        prev_line_items: dict[str, float] = {}
        for s in prev_statements:
            prev_line_items.update(s.normalized_line_items)

        yoy_line_items: dict[str, float] = {}
        for s in yoy_statements:
            yoy_line_items.update(s.normalized_line_items)

        # Compute growth rates for key items (YoY or QoQ based on period type)
        comparison_line_items = yoy_line_items if fiscal_period.startswith("Q") else prev_line_items
        growth_rates: dict[str, float] = {}
        for key in ["revenue", "net_income", "operating_cash_flow"]:
            if key in curr_line_items and key in comparison_line_items:
                growth_rates[key] = calculate_growth_rate(comparison_line_items[key], curr_line_items[key])

        # 3. Calculate financial ratios
        ratios_dict = RatioRegistry.calculate_ratios(curr_line_items)
        ratio_entities: list[Ratio] = []
        for name, value in ratios_dict.items():
            ratio_entities.append(
                Ratio(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    fiscal_period=make_fiscal_period(fiscal_period),
                    ratio_name=name,
                    value=value if value is not None else 0.0,
                    formula_version=financial_config.ratio_engine_version,
                )
            )

        # Delete previous run if exists, then batch save new ratios
        await self.ratio_repo.delete_by_period(company_id, fiscal_period)
        await self.ratio_repo.save_batch(ratio_entities)

        # 4. Evaluate risk assessments
        risk_results = evaluate_risks(ratios_dict)
        risk_entities: list[RiskAssessment] = []
        for r in risk_results:
            risk_entities.append(
                RiskAssessment(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    fiscal_period=make_fiscal_period(fiscal_period),
                    risk_category=r["risk_category"],
                    severity=r["severity"],
                    confidence=r["confidence"],
                    supporting_evidence=r["supporting_evidence"],
                    ratio_engine_version=financial_config.ratio_engine_version,
                )
            )

        await self.risk_repo.delete_by_period(company_id, fiscal_period)
        await self.risk_repo.save_batch(risk_entities)

        # 5. Evaluate overall health score
        health_payload = calculate_health_score(ratios_dict, growth_rates)
        health_entity = FinancialHealthScore(
            id=uuid.uuid4(),
            company_id=company_id,
            fiscal_period=make_fiscal_period(fiscal_period),
            overall_score=health_payload["overall_score"],
            category_scores=health_payload["category_scores"],
            weights=health_payload["weights"],
            score_explanation=health_payload["score_explanation"],
            confidence=health_payload["confidence"],
            confidence_breakdown=health_payload["confidence_breakdown"],
            percentile=None,  # Placeholder percentile
            ratio_engine_version=financial_config.ratio_engine_version,
        )

        await self.health_repo.delete(company_id, fiscal_period)
        await self.health_repo.save(health_entity)

        # 6. Evaluate recommendation rating
        policy = await self.get_or_create_active_policy()
        severe_risks_count = sum(1 for r in risk_entities if r.severity.value == "severe")

        rating, reasoning_steps = evaluate_recommendation(
            health_score=health_entity.overall_score,
            severe_risks_count=severe_risks_count,
            growth_rates=growth_rates,
            policy=policy,
        )

        rec_entity = Recommendation(
            id=uuid.uuid4(),
            company_id=company_id,
            recommendation=rating,
            composite_score=health_entity.overall_score,
            rationale=", ".join(reasoning_steps),
            fiscal_period=make_fiscal_period(fiscal_period),
        )

        await self.rec_repo.delete(company_id, fiscal_period)
        saved_rec = await self.rec_repo.save(rec_entity)

        # Save to RecommendationHistory for audit logs
        history_entity = RecommendationHistory(
            id=uuid.uuid4(),
            recommendation_id=saved_rec.id,
            company_id=company_id,
            fiscal_period=make_fiscal_period(fiscal_period),
            rating=rating,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            composite_score=health_entity.overall_score,
            reasoning_steps=reasoning_steps,
            triggered_by=user_id,
        )
        await self.rec_repo.save_history(history_entity)

        # Define lightweight portfolio signal placeholder block
        portfolio_signal = {
            "company_id": str(company_id),
            "ticker": "UNKNOWN",  # Will resolve ticker in API
            "rating": rating.value,
            "score": health_entity.overall_score,
            "risk_status": "HIGH" if severe_risks_count > 0 else "LOW",
        }

        return {
            "ratios": ratio_entities,
            "health_score": health_entity,
            "risks": risk_entities,
            "recommendation": saved_rec,
            "history": history_entity,
            "portfolio_signal": portfolio_signal,
        }

