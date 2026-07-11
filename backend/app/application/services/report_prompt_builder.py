"""
ReportPromptBuilder — loads prompt templates and binds ReportContext data
to produce section-level prompt strings for LLM generation.
"""

import logging
from pathlib import Path
from typing import Any

from app.application.services.report_context_assembler import ReportContext

logger = logging.getLogger("equityiq.application.report_prompt_builder")

REPORT_PROMPT_VERSION = "1.0.0"

# Path to the reports prompt directory (relative to this module's package root)
_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "reports"


def _load_template(filename: str) -> str:
    """Load a markdown prompt template file from the reports prompts directory."""
    path = _PROMPTS_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning(f"Prompt template not found: {path}")
        return ""


def _fmt_table(
    data: dict[str, Any], key_header: str = "Metric", val_header: str = "Value"
) -> str:
    """Format a dict as a markdown table string."""
    lines = [f"| {key_header} | {val_header} |", "|---|---|"]
    for k, v in data.items():
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def _fmt_risks_block(risks: list[dict[str, Any]]) -> str:
    """Format risk details as a markdown block."""
    if not risks:
        return "_No risks detected for this period._"
    lines: list[str] = []
    for r in risks:
        lines.append(
            f"**{r['category']}** — Severity: {r['severity'].upper()} "
            f"(Confidence: {r['confidence']:.2%})\n"
            f"> Evidence: _{r['evidence']}_\n"
        )
    return "\n".join(lines)


class ReportPromptBuilder:
    """
    Loads section markdown templates and binds ReportContext values to produce
    prompt strings passed to the LLM for each report section.

    The system prompt enforces strict rules preventing metric invention.
    """

    def __init__(self, prompt_version: str = REPORT_PROMPT_VERSION) -> None:
        self.prompt_version = prompt_version
        self._system_prompt = _load_template("report_system_prompt.md")

    def get_version(self) -> str:
        """Return the prompt template version."""
        return self.prompt_version

    def build_system_prompt(self, ctx: ReportContext) -> str:
        """Build the system-level safety/instruction prompt."""
        return self._system_prompt.replace(
            "{financial_engine_version}", ctx.financial_engine_version
        )

    def _base_vars(self, ctx: ReportContext) -> dict[str, str]:
        """Common template variables shared across all sections."""
        return {
            "{company_name}": ctx.company_name,
            "{ticker}": ctx.ticker,
            "{fiscal_period}": ctx.fiscal_period,
            "{overall_score}": str(round(ctx.overall_score, 2)),
            "{recommendation_rating}": ctx.recommendation_rating,
            "{recommendation_rationale}": ctx.recommendation_rationale,
            "{severe_risk_count}": str(ctx.severe_risk_count),
            "{health_confidence}": f"{ctx.health_confidence:.1%}",
            "{financial_engine_version}": ctx.financial_engine_version,
            "{ratio_engine_version}": ctx.ratio_engine_version,
            "{recommendation_policy_version}": ctx.recommendation_policy_version,
        }

    def _apply_vars(
        self, template: str, ctx: ReportContext, extra: dict[str, str] | None = None
    ) -> str:
        """Substitute all template placeholders with context values."""
        result = template
        for k, v in self._base_vars(ctx).items():
            result = result.replace(k, v)
        if extra:
            for k, v in extra.items():
                result = result.replace(k, v)
        return result

    def build_executive_summary_prompt(self, ctx: ReportContext) -> str:
        """Assemble the executive summary section prompt."""
        template = _load_template("executive_summary.md")
        return self._apply_vars(template, ctx)

    def build_financial_health_prompt(self, ctx: ReportContext) -> str:
        """Assemble the financial health section prompt."""
        template = _load_template("financial_health.md")
        cat_table = _fmt_table(
            {k: round(v, 2) for k, v in ctx.category_scores.items()},
            "Category",
            "Score",
        )
        conf_table = _fmt_table(
            {k: round(v, 4) for k, v in ctx.confidence_breakdown.items()},
            "Dimension",
            "Confidence",
        )
        explanation_list = "\n".join(f"- {e}" for e in ctx.score_explanation)
        extra = {
            "{category_scores_table}": cat_table,
            "{confidence_breakdown_table}": conf_table,
            "{score_explanation_list}": explanation_list,
        }
        return self._apply_vars(template, ctx, extra)

    def build_ratio_analysis_prompt(self, ctx: ReportContext) -> str:
        """Assemble the ratio analysis section prompt."""
        template = _load_template("ratio_analysis.md")
        rows = []
        for ratio_name, value in ctx.ratios.items():
            status = ctx.ratio_statuses.get(ratio_name, "—")
            rows.append(f"| {ratio_name} | {value:.4f} | {status} |")
        ratios_table = "| Ratio | Value | Status |\n|---|---|---|\n" + "\n".join(rows)
        return self._apply_vars(template, ctx, {"{ratios_table}": ratios_table})

    def build_trend_analysis_prompt(self, ctx: ReportContext) -> str:
        """Assemble the trend analysis section prompt."""
        template = _load_template("trend_analysis.md")
        extra = {
            "{trend_revenue}": ctx.trends.get("revenue", "stable"),
            "{trend_net_income}": ctx.trends.get("net_income", "stable"),
            "{trend_ocf}": ctx.trends.get("operating_cash_flow", "stable"),
        }
        return self._apply_vars(template, ctx, extra)

    def build_risk_assessment_prompt(self, ctx: ReportContext) -> str:
        """Assemble the risk assessment section prompt."""
        template = _load_template("risk_assessment.md")
        risks_block = _fmt_risks_block(ctx.risks)
        extra = {
            "{total_risk_count}": str(len(ctx.risks)),
            "{risks_detail_block}": risks_block,
        }
        return self._apply_vars(template, ctx, extra)

    def build_recommendation_prompt(self, ctx: ReportContext) -> str:
        """Assemble the investment recommendation section prompt."""
        template = _load_template("recommendation.md")
        return self._apply_vars(template, ctx)

    def build_appendix_prompt(
        self,
        ctx: ReportContext,
        model_name: str,
        prompt_version: str,
        report_template_version: str,
        rag_version: str,
        embedding_version: str,
    ) -> str:
        """Assemble the appendix section prompt with all engine metadata."""
        template = _load_template("appendix.md")
        conf_table = _fmt_table(
            {k: round(v, 4) for k, v in ctx.confidence_breakdown.items()},
            "Dimension",
            "Confidence",
        )
        extra = {
            "{model_name}": model_name,
            "{prompt_version}": prompt_version,
            "{report_template_version}": report_template_version,
            "{rag_version}": rag_version,
            "{embedding_version}": embedding_version,
            "{confidence_breakdown_table}": conf_table,
        }
        return self._apply_vars(template, ctx, extra)
