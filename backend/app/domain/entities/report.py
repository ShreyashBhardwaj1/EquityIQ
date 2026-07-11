"""
Domain entities for the Report Generation Engine.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects.fiscal_period import FiscalPeriod


class ReportStatus(StrEnum):
    """Lifecycle status values for a FinancialReport."""

    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Semantic version for the report generation template
REPORT_TEMPLATE_VERSION = "1.0.0"


class FinancialReport(BaseModel):
    """
    Domain entity representing a generated financial analysis report.

    The content is markdown text assembled from deterministic Milestone 8 outputs.
    LLM narrative wraps pre-computed values; no metrics are invented by the model.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID = Field(description="Unique report identifier")
    company_id: UUID = Field(description="Associated company identifier")
    workspace_id: UUID = Field(description="Owning workspace identifier for isolation")
    fiscal_period: FiscalPeriod = Field(description="Target reporting period")
    title: str = Field(min_length=1, description="Human-readable report title")
    content: str = Field(default="", description="Full markdown report text")
    status: ReportStatus = Field(
        default=ReportStatus.PENDING, description="Current lifecycle status"
    )
    generated_by: UUID = Field(description="User UUID who triggered generation")
    model_name: str = Field(
        default="", description="LLM model used for narrative generation"
    )
    prompt_version: str = Field(
        default=REPORT_TEMPLATE_VERSION, description="Prompt template version tag"
    )
    report_template_version: str = Field(
        default=REPORT_TEMPLATE_VERSION, description="Report template schema version"
    )
    financial_engine_version: str = Field(
        default="1.0.0", description="Financial intelligence engine version tag"
    )
    rag_version: str = Field(default="1.0.0", description="RAG pipeline version tag")
    embedding_version: str = Field(
        default="all-MiniLM-L6-v2", description="Embedding model identifier"
    )
    generated_at: datetime | None = Field(
        default=None, description="UTC timestamp when generation completed"
    )
    generation_duration: float = Field(
        default=0.0, ge=0.0, description="Total wall-clock generation time in seconds"
    )
    error_message: str | None = Field(
        default=None, description="Error description when status is FAILED"
    )
    celery_task_id: str | None = Field(
        default=None, description="Celery task ID for async tracking"
    )


class FinancialReportVersion(BaseModel):
    """
    Domain entity preserving a point-in-time snapshot of report content.

    Saved whenever a report is regenerated or manually edited.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID = Field(description="Unique version record identifier")
    report_id: UUID = Field(description="Parent FinancialReport identifier")
    version: int = Field(ge=1, description="Monotonically increasing version number")
    content: str = Field(description="Full markdown report text at this revision")
    changed_by_id: UUID = Field(description="User UUID who created this revision")
    changed_at: datetime = Field(
        default_factory=datetime.utcnow, description="UTC timestamp of this revision"
    )
    change_reason: str | None = Field(
        default=None, description="Optional reason for this revision"
    )
