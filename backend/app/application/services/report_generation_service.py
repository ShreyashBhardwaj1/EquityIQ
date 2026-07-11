"""
ReportGenerationService — orchestrates the full report generation pipeline.

Pipeline:
  Context Assembly → Prompt Building → LLM Section Generation →
  Markdown Validation → Section Validation → Storage → Version Snapshot

IMPORTANT: This service NEVER recalculates financial metrics. It consumes
pre-computed Milestone 8 deterministic outputs exclusively through
ReportContextAssembler.
"""

import logging
import time
from datetime import datetime
from uuid import UUID, uuid4

from app.application.services.report_context_assembler import (
    ReportContext,
    ReportContextAssembler,
)
from app.application.services.report_markdown_validator import (
    MarkdownValidationError,
    MarkdownValidator,
)
from app.application.services.report_prompt_builder import ReportPromptBuilder
from app.application.services.report_section_validator import ReportSectionValidator
from app.core.config import settings
from app.domain.entities.report import (
    REPORT_TEMPLATE_VERSION,
    FinancialReport,
    FinancialReportVersion,
    ReportStatus,
)
from app.domain.interfaces.providers import LLMProvider
from app.domain.interfaces.repositories import ReportRepository

logger = logging.getLogger("equityiq.application.report_generation_service")

# Report sections in generation order
REPORT_SECTIONS: list[tuple[str, str]] = [
    ("executive_summary", "Executive Summary"),
    ("financial_health", "Financial Health Assessment"),
    ("ratio_analysis", "Ratio Analysis"),
    ("trend_analysis", "Trend Analysis"),
    ("risk_assessment", "Risk Assessment"),
    ("recommendation", "Investment Recommendation"),
    ("appendix", "Appendix"),
]


class ReportGenerationService:
    """
    Orchestrates the end-to-end report generation pipeline:

    1. Assemble deterministic context from Milestone 8 outputs.
    2. Build section prompts.
    3. Generate each section via LLM (with system safety constraints).
    4. Validate each section's markdown structure.
    5. Validate each section against domain boundary rules.
    6. Assemble the full report.
    7. Save the report to the repository.
    8. Optionally save a version snapshot.
    """

    def __init__(
        self,
        context_assembler: ReportContextAssembler,
        prompt_builder: ReportPromptBuilder,
        markdown_validator: MarkdownValidator,
        section_validator: ReportSectionValidator,
        llm_provider: LLMProvider,
        report_repo: ReportRepository,
    ) -> None:
        self.context_assembler = context_assembler
        self.prompt_builder = prompt_builder
        self.markdown_validator = markdown_validator
        self.section_validator = section_validator
        self.llm_provider = llm_provider
        self.report_repo = report_repo

    async def generate_report(
        self,
        report: FinancialReport,
        company_name: str,
        ticker: str,
    ) -> FinancialReport:
        """
        Execute the full report generation pipeline for the given report entity.

        Updates the report entity's status, content, model_name, and timing.
        Returns the saved, completed FinancialReport domain entity.

        Args:
            report: Pre-persisted report entity with PENDING status.
            company_name: Human-readable company name for prompt binding.
            ticker: Exchange ticker symbol for prompt binding.

        Raises:
            ValueError: When no financial health data exists (FI not run).
        """
        start_time = time.perf_counter()

        # Mark as GENERATING
        report = report.model_copy(update={"status": ReportStatus.GENERATING})
        report = await self.report_repo.save(report)

        try:
            # 1. Assemble deterministic context
            logger.info(
                f"Assembling report context for company={report.company_id} "
                f"period={report.fiscal_period}"
            )
            ctx: ReportContext = await self.context_assembler.assemble(
                company_id=report.company_id,
                fiscal_period=str(report.fiscal_period),
                company_name=company_name,
                ticker=ticker,
            )

            # 2. Build system prompt
            system_prompt = self.prompt_builder.build_system_prompt(ctx)

            # 3. Generate each section
            generated_sections: dict[str, str] = {}
            section_prompts = self._build_all_section_prompts(ctx, report)

            for section_key, section_label in REPORT_SECTIONS:
                prompt = section_prompts.get(section_key, "")
                if not prompt:
                    logger.warning(f"No prompt built for section: {section_key}")
                    generated_sections[section_key] = ""
                    continue

                logger.info(f"Generating section: {section_label}")
                full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"

                try:
                    response = await self.llm_provider.complete(full_prompt)
                    section_content = response.text.strip() if response.text else ""
                except Exception as e:
                    logger.warning(
                        f"LLM generation failed for section '{section_label}': {e}"
                    )
                    section_content = (
                        f"## {section_label}\n\n_Section generation failed: {e}_\n"
                    )

                # 4. Validate markdown structure (warn only — don't abort full report)
                try:
                    if section_content:
                        self.markdown_validator.validate(section_content, section_label)
                except MarkdownValidationError as e:
                    logger.warning(
                        f"Markdown validation warning [{section_label}]: {e}"
                    )

                generated_sections[section_key] = section_content

            # 5. Domain boundary validation (warn only — report still saved)
            validation_failures = self.section_validator.validate_all(
                generated_sections, ctx
            )
            if validation_failures:
                for failure in validation_failures:
                    logger.warning(f"Section boundary validation failed: {failure}")

            # 6. Assemble full report markdown
            full_content = self._assemble_full_report(ctx, generated_sections)

            # 7. Determine model name
            model_name = settings.PRIMARY_LLM_MODEL

            # 8. Save completed report
            duration = time.perf_counter() - start_time
            completed_report = report.model_copy(
                update={
                    "content": full_content,
                    "status": ReportStatus.COMPLETED,
                    "model_name": model_name,
                    "generation_duration": duration,
                    "generated_at": datetime.utcnow(),
                    "financial_engine_version": ctx.financial_engine_version,
                    "rag_version": "1.0.0",
                    "embedding_version": settings.EMBEDDING_MODEL_NAME,
                    "prompt_version": self.prompt_builder.get_version(),
                    "report_template_version": REPORT_TEMPLATE_VERSION,
                }
            )
            saved = await self.report_repo.save(completed_report)

            # 9. Save version snapshot
            existing_versions = await self.report_repo.get_versions(saved.id)
            version_number = len(existing_versions) + 1
            version = FinancialReportVersion(
                id=uuid4(),
                report_id=saved.id,
                version=version_number,
                content=full_content,
                changed_by_id=saved.generated_by,
                change_reason="Initial generation",
            )
            await self.report_repo.save_version(version)

            logger.info(
                f"Report {saved.id} generated successfully in {duration:.1f}s "
                f"({len(full_content)} chars)"
            )
            return saved

        except Exception as e:
            logger.exception(f"Report generation failed for report {report.id}: {e}")
            duration = time.perf_counter() - start_time
            failed_report = report.model_copy(
                update={
                    "status": ReportStatus.FAILED,
                    "error_message": str(e),
                    "generation_duration": duration,
                }
            )
            return await self.report_repo.save(failed_report)

    def _build_all_section_prompts(
        self, ctx: ReportContext, report: FinancialReport
    ) -> dict[str, str]:
        """Build the prompt string for each report section."""
        return {
            "executive_summary": self.prompt_builder.build_executive_summary_prompt(
                ctx
            ),
            "financial_health": self.prompt_builder.build_financial_health_prompt(ctx),
            "ratio_analysis": self.prompt_builder.build_ratio_analysis_prompt(ctx),
            "trend_analysis": self.prompt_builder.build_trend_analysis_prompt(ctx),
            "risk_assessment": self.prompt_builder.build_risk_assessment_prompt(ctx),
            "recommendation": self.prompt_builder.build_recommendation_prompt(ctx),
            "appendix": self.prompt_builder.build_appendix_prompt(
                ctx=ctx,
                model_name=settings.PRIMARY_LLM_MODEL,
                prompt_version=self.prompt_builder.get_version(),
                report_template_version=REPORT_TEMPLATE_VERSION,
                rag_version="1.0.0",
                embedding_version=settings.EMBEDDING_MODEL_NAME,
            ),
        }

    def _assemble_full_report(
        self,
        ctx: ReportContext,
        sections: dict[str, str],
    ) -> str:
        """
        Concatenate generated sections into a complete report markdown document.
        Prepends a title header.
        """
        title = (
            f"# EquityIQ Investment Research Report\n"
            f"## {ctx.company_name} ({ctx.ticker}) — {ctx.fiscal_period}\n\n"
            f"---\n\n"
        )

        section_texts: list[str] = [title]
        for section_key, _section_label in REPORT_SECTIONS:
            content = sections.get(section_key, "")
            if content:
                section_texts.append(content)
                section_texts.append("\n\n---\n\n")

        return "".join(section_texts)

    async def create_pending_report(
        self,
        company_id: UUID,
        workspace_id: UUID,
        fiscal_period: str,
        generated_by: UUID,
        company_name: str,
        ticker: str,
    ) -> FinancialReport:
        """
        Create and persist a new FinancialReport entity in PENDING status.
        Called by the API before dispatching the Celery task.
        """
        from app.domain.value_objects.fiscal_period import FiscalPeriod

        parts = fiscal_period.split("-")
        fp = FiscalPeriod(parts[0], int(parts[1]))

        report = FinancialReport(
            id=uuid4(),
            company_id=company_id,
            workspace_id=workspace_id,
            fiscal_period=fp,
            title=f"{company_name} ({ticker}) — {fiscal_period} Investment Research Report",
            content="",
            status=ReportStatus.PENDING,
            generated_by=generated_by,
            model_name=settings.PRIMARY_LLM_MODEL,
            prompt_version=self.prompt_builder.get_version(),
            report_template_version=REPORT_TEMPLATE_VERSION,
            financial_engine_version="1.0.0",
            rag_version="1.0.0",
            embedding_version=settings.EMBEDDING_MODEL_NAME,
        )
        return await self.report_repo.save(report)
