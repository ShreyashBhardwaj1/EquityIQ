"""
FinancialReport and FinancialReportVersion ORM model representations.
"""

from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class FinancialReportORM(Base):
    """
    SQLAlchemy mapping for the 'financial_reports' database table.

    Stores metadata and completed markdown content for each generated report.
    """

    __tablename__ = "financial_reports"

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    fiscal_period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", index=True
    )
    generated_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="1.0.0"
    )
    report_template_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="1.0.0"
    )
    financial_engine_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="1.0.0"
    )
    rag_version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="1.0.0"
    )
    embedding_version: Mapped[str] = mapped_column(
        String(100), nullable=False, default="all-MiniLM-L6-v2"
    )
    generation_duration: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )


class FinancialReportVersionORM(Base):
    """
    SQLAlchemy mapping for the 'financial_report_versions' database table.

    Preserves point-in-time snapshots of report content for audit trails.
    """

    __tablename__ = "financial_report_versions"

    report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financial_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
