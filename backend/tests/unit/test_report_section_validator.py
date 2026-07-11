"""
Unit tests for ReportSectionValidator service.
"""

from uuid import uuid4

import pytest

from app.application.services.report_context_assembler import ReportContext
from app.application.services.report_section_validator import (
    ReportSectionValidator,
    SectionValidationError,
)


def _make_context(**overrides: object) -> ReportContext:
    """Build a minimal ReportContext for testing."""
    defaults: dict[str, object] = {
        "company_id": uuid4(),
        "fiscal_period": "FY-2024",
        "company_name": "Acme Corp",
        "ticker": "ACME",
        "overall_score": 7.42,
        "category_scores": {"liquidity": 8.0, "profitability": 7.0},
        "score_explanation": ["Strong liquidity"],
        "health_confidence": 0.85,
        "confidence_breakdown": {"overall_confidence": 0.85},
        "ratios": {"current_ratio": 1.8},
        "ratio_statuses": {"current_ratio": "Healthy"},
        "risks": [
            {
                "category": "Leverage Risk",
                "severity": "moderate",
                "confidence": 0.75,
                "evidence": "Debt/Equity above threshold",
            }
        ],
        "severe_risk_count": 0,
        "recommendation_rating": "BUY",
        "recommendation_rationale": "Strong health score with moderate leverage.",
        "recommendation_policy_version": "1.0.0",
        "trends": {"revenue": "ACCELERATING"},
        "ratio_engine_version": "1.0.0",
        "financial_engine_version": "1.0.0",
    }
    defaults.update(overrides)
    return ReportContext(**defaults)  # type: ignore[arg-type]


class TestReportSectionValidator:
    @pytest.fixture
    def validator(self) -> ReportSectionValidator:
        return ReportSectionValidator()

    @pytest.fixture
    def ctx(self) -> ReportContext:
        return _make_context()

    # --- Executive Summary ---

    def test_exec_summary_valid_with_rating(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = (
            "## Executive Summary\n\nAcme Corp has a BUY recommendation "
            "based on its strong financial health score of 7.42."
        )
        validator.validate_executive_summary(content, ctx)  # Should not raise

    def test_exec_summary_missing_rating_raises(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = "## Executive Summary\n\nAcme Corp is doing well overall."
        with pytest.raises(SectionValidationError, match="recommendation rating"):
            validator.validate_executive_summary(content, ctx)

    def test_exec_summary_case_insensitive_match(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = "The rating is buy and the score supports this."
        validator.validate_executive_summary(content, ctx)  # Should pass

    # --- Financial Health ---

    def test_financial_health_valid_with_score(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = "## Financial Health\n\nOverall score: 7.4 indicates strong financial position."
        validator.validate_financial_health(content, ctx)

    def test_financial_health_missing_score_raises(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = (
            "## Financial Health\n\nThe company shows solid performance across metrics."
        )
        with pytest.raises(SectionValidationError, match="overall score"):
            validator.validate_financial_health(content, ctx)

    # --- Risk Assessment ---

    def test_risk_assessment_with_no_risks_passes(
        self, validator: ReportSectionValidator
    ) -> None:
        ctx = _make_context(risks=[], severe_risk_count=0)
        content = "## Risk Assessment\n\nNo significant risks detected."
        validator.validate_risk_assessment(content, ctx)  # Should not raise

    def test_risk_assessment_references_actual_category(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = (
            "## Risk Assessment\n\nLeverage Risk is detected at moderate severity."
        )
        validator.validate_risk_assessment(content, ctx)

    def test_risk_assessment_missing_categories_raises(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = "## Risk Assessment\n\nThe company has liquidity concerns and currency exposure."
        with pytest.raises(SectionValidationError, match="risk categories"):
            validator.validate_risk_assessment(content, ctx)

    # --- Recommendation ---

    def test_recommendation_valid_with_rating(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = "## Recommendation\n\nRating: **BUY**\n\nStrong health score supports a BUY rating."
        validator.validate_recommendation(content, ctx)

    def test_recommendation_wrong_rating_raises(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        content = (
            "## Recommendation\n\nThe rating for this company is HOLD based on risks."
        )
        with pytest.raises(SectionValidationError, match="rating"):
            validator.validate_recommendation(content, ctx)

    def test_recommendation_strong_buy_underscore_flexible(
        self, validator: ReportSectionValidator
    ) -> None:
        ctx = _make_context(recommendation_rating="STRONG_BUY")
        content = (
            "## Recommendation\n\nRating: STRONG BUY based on exceptional metrics."
        )
        validator.validate_recommendation(content, ctx)  # Should pass

    # --- validate_all ---

    def test_validate_all_returns_empty_on_success(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        sections = {
            "executive_summary": "Acme Corp receives a BUY rating.",
            "financial_health": "Health score is 7.4 out of 10.",
            "risk_assessment": "Leverage Risk is moderate.",
            "recommendation": "Rating: BUY is supported by data.",
        }
        failures = validator.validate_all(sections, ctx)
        assert failures == []

    def test_validate_all_skips_empty_sections(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        sections = {
            "executive_summary": "",
            "recommendation": "Rating: BUY",
        }
        failures = validator.validate_all(sections, ctx)
        assert failures == []

    def test_validate_all_collects_failures(
        self, validator: ReportSectionValidator, ctx: ReportContext
    ) -> None:
        sections = {
            "executive_summary": "Some generic summary without the rating.",
            "recommendation": "Some generic recommendation without the rating.",
        }
        failures = validator.validate_all(sections, ctx)
        assert len(failures) == 2
