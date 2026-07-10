"""
ExplainabilityService application service.
"""

from typing import Any
from uuid import UUID

from app.domain.interfaces.repositories import (
    FinancialStatementRepository,
    HealthScoreRepository,
    RatioRepository,
    RecommendationRepository,
    RiskAssessmentRepository,
)


class ExplainabilityService:
    """
    Service responsible for assembling the explainability payload, detailing
    sequential reasoning steps, active policies, risks, and scoring weight distributions.
    """

    def __init__(
        self,
        health_repo: HealthScoreRepository,
        risk_repo: RiskAssessmentRepository,
        rec_repo: RecommendationRepository,
        statement_repo: FinancialStatementRepository,
        ratio_repo: RatioRepository,
    ) -> None:
        self.health_repo = health_repo
        self.risk_repo = risk_repo
        self.rec_repo = rec_repo
        self.statement_repo = statement_repo
        self.ratio_repo = ratio_repo

    async def get_explainability(
        self, company_id: UUID, fiscal_period: str
    ) -> dict[str, Any]:
        """
        Retrieves the deterministic reasoning breakdown and scoring checks.
        """
        # Fetch records
        health = await self.health_repo.get(company_id, fiscal_period)
        risks = await self.risk_repo.list_by_period(company_id, fiscal_period)
        rec = await self.rec_repo.get(company_id, fiscal_period)
        history_list = await self.rec_repo.list_history(company_id, fiscal_period)

        # Retrieve reasoning steps from audit log history if present
        reasoning_steps = []
        policy_info = {}
        policy_version = "1.0.0-default"
        policies_applied = []
        if history_list:
            latest_audit = history_list[0]
            reasoning_steps = latest_audit.reasoning_steps
            policy_version = latest_audit.policy_version
            policy_info = {
                "policy_id": str(latest_audit.policy_id),
                "policy_version": latest_audit.policy_version,
            }
            policies_applied.append(policy_info)
        elif rec:
            # Fallback parsing rules_applied if history is not accessible
            reasoning_steps = rec.rationale.split(", ")
            policy_info = {
                "policy_id": "unknown",
                "policy_version": policy_version,
            }
            policies_applied.append(policy_info)

        # Build positive and negative signals
        positive_signals = []
        negative_signals = []
        if health:
            for cat, score in health.category_scores.items():
                if score >= 7.0:
                    positive_signals.append(
                        f"Strong performance in {cat}: score {score}"
                    )
                elif score <= 4.0:
                    negative_signals.append(
                        f"Strained performance in {cat}: score {score}"
                    )
            for msg in health.score_explanation:
                if "Strong" in msg or "positive" in msg.lower():
                    positive_signals.append(msg)
                elif (
                    "Caution" in msg
                    or "Weak" in msg
                    or "negative" in msg.lower()
                    or "strained" in msg.lower()
                ):
                    negative_signals.append(msg)

        # Ratios influencing recommendation
        ratios = await self.ratio_repo.get_by_period(company_id, fiscal_period)
        ratios_influencing = []
        for ratio_item in ratios:
            status = ratio_item.status
            ratios_influencing.append(
                {
                    "ratio_name": ratio_item.ratio_name,
                    "value": ratio_item.value,
                    "status": status,
                }
            )
            if status in ["Excellent", "Healthy"]:
                positive_signals.append(
                    f"Ratio {ratio_item.ratio_name} is in a strong position ({status}: {ratio_item.value:.2f})"
                )
            elif status in ["Weak", "Critical"]:
                negative_signals.append(
                    f"Ratio {ratio_item.ratio_name} is in a strained position ({status}: {ratio_item.value:.2f})"
                )

        # Risk factors influencing recommendation
        risk_factors_influencing = []
        for risk_item in risks:
            sev_str = str(risk_item.severity)
            risk_factors_influencing.append(
                {
                    "category": risk_item.risk_category,
                    "severity": sev_str,
                    "supporting_evidence": risk_item.supporting_evidence,
                }
            )
            if sev_str == "severe":
                negative_signals.append(
                    f"Severe risk detected in {risk_item.risk_category}: {risk_item.supporting_evidence}"
                )
            elif sev_str == "moderate":
                negative_signals.append(
                    f"Moderate risk detected in {risk_item.risk_category}: {risk_item.supporting_evidence}"
                )

        # Trend factors influencing recommendation
        trend_factors_influencing = []
        statements = await self.statement_repo.list_by_company(company_id)
        period_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "FY": 5}
        sorted_statements = sorted(
            statements,
            key=lambda s: (
                s.fiscal_period.year,
                period_order.get(s.fiscal_period.period, 0),
            ),
        )

        from app.domain.rules.trend_engine import classify_trend

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

        if revenue_vals:
            rev_trend = str(classify_trend(revenue_vals))
            trend_factors_influencing.append({"metric": "revenue", "trend": rev_trend})
            if rev_trend in ["accelerating", "recovery"]:
                positive_signals.append(
                    f"Revenue is showing positive trend: {rev_trend}"
                )
            elif rev_trend in ["decline", "volatile"]:
                negative_signals.append(
                    f"Revenue is showing weak/volatile trend: {rev_trend}"
                )
        if income_vals:
            inc_trend = str(classify_trend(income_vals))
            trend_factors_influencing.append(
                {"metric": "net_income", "trend": inc_trend}
            )
            if inc_trend in ["accelerating", "recovery"]:
                positive_signals.append(
                    f"Net income is showing positive trend: {inc_trend}"
                )
            elif inc_trend in ["decline", "volatile"]:
                negative_signals.append(
                    f"Net income is showing weak/volatile trend: {inc_trend}"
                )

        # Filter rules triggered
        rules_triggered = []
        for step in reasoning_steps:
            if any(
                term in step.lower()
                for term in ["check", "passed", "failed", "requires", "risk"]
            ):
                rules_triggered.append(step)

        # Structure versions
        engine_versions = {
            "ratio_engine_version": health.ratio_engine_version if health else "1.0.0",
            "health_engine_version": health.ratio_engine_version if health else "1.0.0",
            "recommendation_policy_version": policy_version,
            "risk_engine_version": health.ratio_engine_version if health else "1.0.0",
            "financial_intelligence_version": "1.0.0",
        }

        # Deduplicate signals
        positive_signals = list(dict.fromkeys(positive_signals))
        negative_signals = list(dict.fromkeys(negative_signals))

        return {
            "company_id": str(company_id),
            "fiscal_period": fiscal_period,
            "recommendation_rating": str(rec.recommendation) if rec else None,
            "composite_score": health.overall_score if health else None,
            "confidence": health.confidence if health else 0.0,
            "confidence_breakdown": health.confidence_breakdown if health else {},
            "percentile": health.percentile if health else None,
            "reasoning_steps": reasoning_steps,
            "deterministic_reasoning_steps": reasoning_steps,
            "policy": policy_info,
            "policies_applied": policies_applied,
            "rules_triggered": rules_triggered,
            "positive_signals": positive_signals,
            "negative_signals": negative_signals,
            "ratios_influencing_recommendation": ratios_influencing,
            "risk_factors_influencing_recommendation": risk_factors_influencing,
            "trend_factors_influencing_recommendation": trend_factors_influencing,
            "health_score_details": {
                "category_scores": health.category_scores if health else {},
                "weights": health.weights if health else {},
                "explanations": health.score_explanation if health else [],
            },
            "risks_detected": [
                {
                    "category": r.risk_category,
                    "severity": str(r.severity),
                    "supporting_evidence": r.supporting_evidence,
                    "confidence": r.confidence,
                }
                for r in risks
            ],
            "engine_versions": engine_versions,
        }
