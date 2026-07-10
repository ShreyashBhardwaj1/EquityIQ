"""
DashboardService application service.
"""

import logging
from typing import Any
from uuid import UUID

from app.domain.interfaces.repositories import (
    FinancialStatementRepository,
    HealthScoreRepository,
    RatioRepository,
    RecommendationRepository,
    RiskAssessmentRepository,
)
from app.domain.rules.trend_engine import classify_trend

logger = logging.getLogger("equityiq.application.dashboard_service")


class DashboardService:
    """
    Assembles a unified dashboard payload containing health scores, recommendations,
    risk profiles, trend states, and completeness confidence metrics.
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

    async def get_dashboard(
        self, company_id: UUID, fiscal_period: str
    ) -> dict[str, Any]:
        """
        Assembles and returns a consolidated dashboard for a company and reporting period.
        """
        # Fetch entities
        health = await self.health_repo.get(company_id, fiscal_period)
        risks = await self.risk_repo.list_by_period(company_id, fiscal_period)
        rec = await self.rec_repo.get(company_id, fiscal_period)
        ratios = await self.ratio_repo.get_by_period(company_id, fiscal_period)

        # 1. Compile Trend analysis
        # Fetch statements to get values across chronological periods
        statements = await self.statement_repo.list_by_company(company_id)
        # Sort statements chronologically by year and period segment (Q1, Q2, Q3, Q4, FY)
        period_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "FY": 5}
        sorted_statements = sorted(
            statements,
            key=lambda s: (
                s.fiscal_period.year,
                period_order.get(s.fiscal_period.period, 0),
            ),
        )

        # Extract values for revenue, net_income, and operating_cash_flow
        revenue_vals = []
        income_vals = []
        ocf_vals = []

        for s in sorted_statements:
            norm_items = s.normalized_line_items
            if "revenue" in norm_items:
                revenue_vals.append(norm_items["revenue"])
            if "net_income" in norm_items:
                income_vals.append(norm_items["net_income"])
            if "operating_cash_flow" in norm_items:
                ocf_vals.append(norm_items["operating_cash_flow"])

        trends = {
            "revenue": str(classify_trend(revenue_vals)) if revenue_vals else "stable",
            "net_income": str(classify_trend(income_vals)) if income_vals else "stable",
            "operating_cash_flow": str(classify_trend(ocf_vals))
            if ocf_vals
            else "stable",
        }

        # Determine strongest and weakest trends
        growth_rates = {}
        if len(sorted_statements) >= 2:
            curr = sorted_statements[-1].normalized_line_items
            prev = sorted_statements[-2].normalized_line_items
            for key in ["revenue", "net_income", "operating_cash_flow"]:
                if key in curr and key in prev and prev[key] != 0.0:
                    growth_rates[key] = (curr[key] - prev[key]) / abs(prev[key])

        strongest_positive_trend = "Stable"
        weakest_trend = "Stable"
        if growth_rates:
            sorted_growth = sorted(
                growth_rates.items(), key=lambda x: x[1], reverse=True
            )
            if sorted_growth[0][1] > 0.0:
                strongest_positive_trend = (
                    f"{sorted_growth[0][0]} (+{sorted_growth[0][1] * 100:.1f}%)"
                )
            else:
                strongest_positive_trend = (
                    f"{sorted_growth[0][0]} ({sorted_growth[0][1] * 100:.1f}%)"
                )
            weakest_trend = (
                f"{sorted_growth[-1][0]} ({sorted_growth[-1][1] * 100:.1f}%)"
            )

        # 2. Extract reasoning steps from audit log history
        history_list = await self.rec_repo.list_history(company_id, fiscal_period)
        reasoning_steps = []
        policy_version = "1.0.0-default"
        if history_list:
            reasoning_steps = history_list[0].reasoning_steps
            policy_version = history_list[0].policy_version
        elif rec:
            reasoning_steps = rec.rationale.split(", ")

        # 3. Sort top 5 ratios by qualitative status strength
        status_rank = {
            "Excellent": 5,
            "Healthy": 4,
            "Watch": 3,
            "Weak": 2,
            "Critical": 1,
        }
        sorted_ratios = sorted(
            ratios, key=lambda r: status_rank.get(r.status, 0), reverse=True
        )
        top_5_ratios = [
            {"ratio_name": r.ratio_name, "value": round(r.value, 4), "status": r.status}
            for r in sorted_ratios[:5]
        ]

        # 4. Sort top 3 risks by severity
        severity_rank = {"severe": 3, "moderate": 2, "low": 1}
        sorted_risks = sorted(
            risks, key=lambda r: severity_rank.get(str(r.severity), 0), reverse=True
        )
        top_3_risks = [
            {
                "category": r.risk_category,
                "severity": str(r.severity),
                "evidence": r.supporting_evidence,
            }
            for r in sorted_risks[:3]
        ]

        # Engine Versions
        engine_versions = {
            "ratio_engine_version": health.ratio_engine_version if health else "1.0.0",
            "health_engine_version": health.ratio_engine_version if health else "1.0.0",
            "recommendation_policy_version": policy_version,
            "risk_engine_version": health.ratio_engine_version if health else "1.0.0",
            "financial_intelligence_version": "1.0.0",
        }

        return {
            "company_id": str(company_id),
            "fiscal_period": fiscal_period,
            "overall_score": health.overall_score if health else 5.0,
            "category_scores": health.category_scores
            if health
            else {
                "liquidity": 5.0,
                "profitability": 5.0,
                "leverage": 5.0,
                "efficiency": 5.0,
                "cash_flow": 5.0,
                "growth": 5.0,
            },
            "top_5_ratios": top_5_ratios,
            "top_3_risks": top_3_risks,
            "strongest_positive_trend": strongest_positive_trend,
            "weakest_trend": weakest_trend,
            "final_recommendation": str(rec.recommendation) if rec else "HOLD",
            "recommendation_confidence": health.confidence if health else 0.0,
            "confidence_breakdown": health.confidence_breakdown if health else {},
            "engine_versions": engine_versions,
            # Maintain backward compatibility
            "health": {
                "overall_score": health.overall_score if health else None,
                "category_scores": health.category_scores if health else {},
                "explanations": health.score_explanation if health else [],
            },
            "recommendation": {
                "rating": str(rec.recommendation) if rec else None,
                "rationale": rec.rationale if rec else None,
                "reasoning_steps": reasoning_steps,
            },
            "risks": {
                "severe_count": sum(1 for r in risks if str(r.severity) == "severe"),
                "moderate_count": sum(
                    1 for r in risks if str(r.severity) == "moderate"
                ),
                "list": [
                    {
                        "category": r.risk_category,
                        "severity": str(r.severity),
                        "evidence": r.supporting_evidence,
                    }
                    for r in risks
                ],
            },
            "trends": trends,
            "confidence": health.confidence if health else 0.0,
            "ratios": {r.ratio_name: r.value for r in ratios},
        }
