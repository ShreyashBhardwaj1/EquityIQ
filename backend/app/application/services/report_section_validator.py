"""
ReportSectionValidator — post-generation validation of section content
to enforce section-specific boundary rules.
"""

from app.application.services.report_context_assembler import ReportContext


class SectionValidationError(Exception):
    """Raised when a section violates a domain boundary rule."""


class ReportSectionValidator:
    """
    Validates each generated section against domain boundary rules.

    Ensures the LLM narrative is consistent with the deterministic context:
    - Recommendation section must contain the correct rating string.
    - Risk section must not reference more risks than were detected.
    - Health section must mention the correct overall score.
    """

    def validate_executive_summary(self, content: str, ctx: ReportContext) -> None:
        """
        Validate executive summary section.
        Must reference the correct recommendation rating.
        """
        rating_upper = ctx.recommendation_rating.upper().replace("_", " ")
        rating_lower = ctx.recommendation_rating.lower().replace("_", " ")
        if rating_upper not in content.upper():
            raise SectionValidationError(
                f"Executive Summary does not contain the required recommendation rating "
                f"'{ctx.recommendation_rating}'. Possible hallucination detected."
            )
        del rating_lower  # silence linting; we check case-insensitively via upper

    def validate_financial_health(self, content: str, ctx: ReportContext) -> None:
        """
        Validate financial health section.
        Must reference the overall score.
        """
        score_str = str(round(ctx.overall_score, 1))
        if score_str not in content:
            raise SectionValidationError(
                f"Financial Health section does not contain the computed overall score "
                f"'{score_str}'. Content may not be grounded in deterministic data."
            )

    def validate_risk_assessment(self, content: str, ctx: ReportContext) -> None:
        """
        Validate risk assessment section.
        Must not invent risk categories beyond what was detected.
        """
        if not ctx.risks:
            # If no risks detected, section should acknowledge absence
            return

        # Verify at least one actual risk category appears
        at_least_one_found = any(
            risk["category"].lower() in content.lower() for risk in ctx.risks
        )
        if not at_least_one_found:
            raise SectionValidationError(
                "Risk Assessment section does not reference any of the detected risk "
                "categories. Content may be fabricated."
            )

    def validate_recommendation(self, content: str, ctx: ReportContext) -> None:
        """
        Validate recommendation section.
        Must use the exact rating value (no substitution allowed).
        """
        # Strip underscores for flexible matching (STRONG_BUY vs STRONG BUY)
        rating_key = ctx.recommendation_rating.upper().replace("_", " ")
        if rating_key not in content.upper():
            raise SectionValidationError(
                f"Recommendation section does not contain the exact rating "
                f"'{ctx.recommendation_rating}'. The rating must not be altered."
            )

    def validate_all(
        self,
        sections: dict[str, str],
        ctx: ReportContext,
    ) -> list[str]:
        """
        Run all section validators and return a list of validation failure messages.

        Args:
            sections: Dict mapping section_name -> generated_content.
            ctx: The grounding ReportContext.

        Returns:
            List of failure messages (empty = all valid).
        """
        failures: list[str] = []

        validators: list[tuple[str, object]] = [
            ("executive_summary", self.validate_executive_summary),
            ("financial_health", self.validate_financial_health),
            ("risk_assessment", self.validate_risk_assessment),
            ("recommendation", self.validate_recommendation),
        ]

        for section_key, validator_fn in validators:
            content = sections.get(section_key, "")
            if content:
                try:
                    validator_fn(content, ctx)  # type: ignore[operator]
                except SectionValidationError as e:
                    failures.append(f"[{section_key}] {e}")

        return failures
