"""
Unit tests for ReportPromptBuilder — verifies template loading and variable substitution.
"""

from uuid import uuid4

import pytest

from app.application.services.report_context_assembler import ReportContext
from app.application.services.report_prompt_builder import (
    ReportPromptBuilder,
    _fmt_risks_block,
    _fmt_table,
)


def _make_context(**overrides: object) -> ReportContext:
    defaults: dict[str, object] = {
        "company_id": uuid4(),
        "fiscal_period": "FY-2024",
        "company_name": "Acme Corp",
        "ticker": "ACME",
        "overall_score": 7.42,
        "category_scores": {"liquidity": 8.0, "profitability": 7.0},
        "score_explanation": ["Strong liquidity", "Positive growth trend"],
        "health_confidence": 0.85,
        "confidence_breakdown": {"overall_confidence": 0.85, "rule_agreement": 0.90},
        "ratios": {"current_ratio": 1.8, "return_on_equity": 0.12},
        "ratio_statuses": {"current_ratio": "Healthy", "return_on_equity": "Watch"},
        "risks": [
            {
                "category": "Leverage Risk",
                "severity": "moderate",
                "confidence": 0.75,
                "evidence": "D/E above 2.0",
            }
        ],
        "severe_risk_count": 0,
        "recommendation_rating": "BUY",
        "recommendation_rationale": "Score above threshold with low risks.",
        "recommendation_policy_version": "1.0.0",
        "trends": {
            "revenue": "ACCELERATING",
            "net_income": "STABLE",
            "operating_cash_flow": "DECELERATING",
        },
        "ratio_engine_version": "1.0.0",
        "financial_engine_version": "1.0.0",
    }
    defaults.update(overrides)
    return ReportContext(**defaults)  # type: ignore[arg-type]


class TestFmtTable:
    def test_basic_table(self) -> None:
        result = _fmt_table({"Revenue": "1000", "Net Income": "200"})
        assert "Revenue" in result
        assert "Net Income" in result
        assert "|---|---|" in result

    def test_custom_headers(self) -> None:
        result = _fmt_table({"Q1": "100"}, key_header="Period", val_header="Amount")
        assert "Period" in result
        assert "Amount" in result


class TestFmtRisksBlock:
    def test_empty_risks(self) -> None:
        result = _fmt_risks_block([])
        assert "No risks detected" in result

    def test_single_risk(self) -> None:
        risks = [
            {
                "category": "Leverage Risk",
                "severity": "moderate",
                "confidence": 0.75,
                "evidence": "D/E ratio exceeds threshold",
            }
        ]
        result = _fmt_risks_block(risks)
        assert "Leverage Risk" in result
        assert "MODERATE" in result
        assert "D/E ratio exceeds threshold" in result


class TestReportPromptBuilder:
    @pytest.fixture
    def builder(self) -> ReportPromptBuilder:
        return ReportPromptBuilder()

    @pytest.fixture
    def ctx(self) -> ReportContext:
        return _make_context()

    def test_get_version(self, builder: ReportPromptBuilder) -> None:
        assert builder.get_version() == "1.0.0"

    def test_base_vars_contain_company_name(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        base = builder._base_vars(ctx)
        assert "{company_name}" in base
        assert base["{company_name}"] == "Acme Corp"

    def test_build_executive_summary_prompt_substitutes_score(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_executive_summary_prompt(ctx)
        # Template variables for company_name should be substituted
        assert "Acme Corp" in result
        assert "{company_name}" not in result

    def test_build_financial_health_prompt_contains_category_table(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_financial_health_prompt(ctx)
        # Should contain the category table format
        assert "liquidity" in result.lower() or "Category" in result

    def test_build_ratio_analysis_prompt_contains_ratio_values(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_ratio_analysis_prompt(ctx)
        # current_ratio should appear
        assert "current_ratio" in result

    def test_build_trend_prompt_contains_trends(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_trend_analysis_prompt(ctx)
        assert "ACCELERATING" in result or "STABLE" in result

    def test_build_risk_prompt_contains_risk(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_risk_assessment_prompt(ctx)
        assert "Leverage Risk" in result

    def test_build_recommendation_prompt_contains_rating(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_recommendation_prompt(ctx)
        assert "BUY" in result

    def test_build_appendix_prompt_contains_model_name(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_appendix_prompt(
            ctx=ctx,
            model_name="gemini-2.5-pro",
            prompt_version="1.0.0",
            report_template_version="1.0.0",
            rag_version="1.0.0",
            embedding_version="all-MiniLM-L6-v2",
        )
        assert "gemini-2.5-pro" in result

    def test_system_prompt_contains_financial_engine_version(
        self, builder: ReportPromptBuilder, ctx: ReportContext
    ) -> None:
        result = builder.build_system_prompt(ctx)
        assert "1.0.0" in result
