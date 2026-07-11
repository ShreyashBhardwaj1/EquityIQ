"""
ReportContextAssembler — gathers deterministic Milestone 8 outputs to ground
the report generation prompt. Never recalculates metrics; only reads persisted data.
"""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.entities.financial_intelligence import (
    FinancialHealthScore,
    RiskAssessment,
    SeverityLevel,
    TrendState,
)
from app.domain.entities.ratio import Ratio
from app.domain.entities.recommendation import Recommendation
from app.domain.interfaces.repositories import (
    FinancialStatementRepository,
    HealthScoreRepository,
    RatioRepository,
    RecommendationRepository,
    RiskAssessmentRepository,
)
from app.domain.rules.trend_engine import classify_trend

logger = logging.getLogger("equityiq.application.report_context_assembler")


@dataclass(frozen=True)
class ReportContext:
    """
    Immutable container holding all deterministic data required to ground report generation.

    All values are sourced from Milestone 8 persisted outputs. The LLM narrative
    layer must reference these values verbatim — it must never invent metrics.
    """

    company_id: UUID
    fiscal_period: str
    company_name: str
    ticker: str

    # Health scoring
    overall_score: float
    category_scores: dict[str, float]
    score_explanation: list[str]
    health_confidence: float
    confidence_breakdown: dict[str, float]

    # Ratios
    ratios: dict[str, float]  # {ratio_name: value}
    ratio_statuses: dict[str, str]  # {ratio_name: status_label}

    # Risks
    risks: list[dict[str, Any]]  # [{category, severity, evidence}]
    severe_risk_count: int

    # Recommendation
    recommendation_rating: str
    recommendation_rationale: str
    recommendation_policy_version: str

    # Trends
    trends: dict[str, str]  # {metric_name: trend_state}

    # Engine versions (provenance tracking)
    ratio_engine_version: str
    financial_engine_version: str

    def to_prompt_dict(self) -> dict[str, Any]:
        """Return a flat dict suitable for prompt template interpolation."""
        return {
            "company_name": self.company_name,
            "ticker": self.ticker,
            "fiscal_period": self.fiscal_period,
            "overall_score": round(self.overall_score, 2),
            "category_scores": {
                k: round(v, 2) for k, v in self.category_scores.items()
            },
            "score_explanation": self.score_explanation,
            "health_confidence": round(self.health_confidence, 4),
            "confidence_breakdown": {
                k: round(v, 4) for k, v in self.confidence_breakdown.items()
            },
            "ratios": {k: round(v, 4) for k, v in self.ratios.items()},
            "ratio_statuses": self.ratio_statuses,
            "risks": self.risks,
            "severe_risk_count": self.severe_risk_count,
            "recommendation_rating": self.recommendation_rating,
            "recommendation_rationale": self.recommendation_rationale,
            "recommendation_policy_version": self.recommendation_policy_version,
            "trends": self.trends,
            "ratio_engine_version": self.ratio_engine_version,
            "financial_engine_version": self.financial_engine_version,
        }


class ReportContextAssembler:
    """
    Assembles a grounded ReportContext from pre-computed Milestone 8 outputs.

    IMPORTANT: This service is strictly read-only with respect to financial metrics.
    It must never recalculate or modify any stored values.
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

    async def assemble(
        self,
        company_id: UUID,
        fiscal_period: str,
        company_name: str,
        ticker: str,
    ) -> ReportContext:
        """
        Fetches and bundles deterministic data for a company and fiscal period.

        Raises ValueError if no health score data is available (signals FI not run).
        """
        # 1. Load health score (mandatory — must exist)
        health: FinancialHealthScore | None = await self.health_repo.get(
            company_id, fiscal_period
        )
        if not health:
            raise ValueError(
                f"No financial health data found for company {company_id} period "
                f"{fiscal_period}. Run financial intelligence calculation first."
            )

        # 2. Load computed ratios
        ratio_entities: list[Ratio] = await self.ratio_repo.get_by_period(
            company_id, fiscal_period
        )
        ratios_map: dict[str, float] = {r.ratio_name: r.value for r in ratio_entities}
        ratio_statuses_map: dict[str, str] = {
            r.ratio_name: r.status for r in ratio_entities
        }

        # 3. Load risk assessments
        risk_entities: list[RiskAssessment] = await self.risk_repo.list_by_period(
            company_id, fiscal_period
        )
        severity_order = {
            SeverityLevel.SEVERE: 3,
            SeverityLevel.MODERATE: 2,
            SeverityLevel.LOW: 1,
        }
        sorted_risks = sorted(
            risk_entities,
            key=lambda r: severity_order.get(r.severity, 0),
            reverse=True,
        )
        risks_payload = [
            {
                "category": r.risk_category,
                "severity": str(r.severity),
                "confidence": round(r.confidence, 4),
                "evidence": r.supporting_evidence,
            }
            for r in sorted_risks
        ]
        severe_risk_count = sum(
            1 for r in risk_entities if r.severity == SeverityLevel.SEVERE
        )

        # 4. Load recommendation
        rec: Recommendation | None = await self.rec_repo.get(company_id, fiscal_period)
        history_list = await self.rec_repo.list_history(company_id, fiscal_period)
        policy_version = "1.0.0-default"
        if history_list:
            policy_version = history_list[0].policy_version

        rec_rating = str(rec.recommendation) if rec else "HOLD"
        rec_rationale = (
            rec.rationale if rec else "Insufficient data for recommendation."
        )

        # 5. Compute simplified trends from historical statements
        all_statements = await self.statement_repo.list_by_company(company_id)
        period_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "FY": 5}
        sorted_stmts = sorted(
            all_statements,
            key=lambda s: (
                s.fiscal_period.year,
                period_order.get(s.fiscal_period.period, 0),
            ),
        )
        revenue_vals = [
            s.normalized_line_items["revenue"]
            for s in sorted_stmts
            if "revenue" in s.normalized_line_items
        ]
        income_vals = [
            s.normalized_line_items["net_income"]
            for s in sorted_stmts
            if "net_income" in s.normalized_line_items
        ]
        ocf_vals = [
            s.normalized_line_items["operating_cash_flow"]
            for s in sorted_stmts
            if "operating_cash_flow" in s.normalized_line_items
        ]
        trends: dict[str, str] = {
            "revenue": str(classify_trend(revenue_vals))
            if len(revenue_vals) > 1
            else str(TrendState.STABLE),
            "net_income": str(classify_trend(income_vals))
            if len(income_vals) > 1
            else str(TrendState.STABLE),
            "operating_cash_flow": str(classify_trend(ocf_vals))
            if len(ocf_vals) > 1
            else str(TrendState.STABLE),
        }

        return ReportContext(
            company_id=company_id,
            fiscal_period=fiscal_period,
            company_name=company_name,
            ticker=ticker,
            overall_score=health.overall_score,
            category_scores=health.category_scores,
            score_explanation=health.score_explanation,
            health_confidence=health.confidence,
            confidence_breakdown=health.confidence_breakdown,
            ratios=ratios_map,
            ratio_statuses=ratio_statuses_map,
            risks=risks_payload,
            severe_risk_count=severe_risk_count,
            recommendation_rating=rec_rating,
            recommendation_rationale=rec_rationale,
            recommendation_policy_version=policy_version,
            trends=trends,
            ratio_engine_version=health.ratio_engine_version,
            financial_engine_version="1.0.0",
        )
