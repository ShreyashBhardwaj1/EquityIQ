"""
SQLAlchemy repository adapter for FinancialReport and FinancialReportVersion.
"""

from uuid import UUID

from sqlalchemy import select

from app.domain.entities.report import (
    FinancialReport,
    FinancialReportVersion,
    ReportStatus,
)
from app.domain.interfaces.repositories import ReportRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.report import (
    FinancialReportORM,
    FinancialReportVersionORM,
)
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyReportRepository(BaseRepository[FinancialReportORM], ReportRepository):
    """
    SQLAlchemy-backed implementation of the ReportRepository interface.
    """

    # ─── Mapping Helpers ─────────────────────────────────────────────────────

    def _to_domain(self, orm: FinancialReportORM) -> FinancialReport:
        """Translates ORM model to FinancialReport domain entity."""
        parts = orm.fiscal_period.split("-")
        fp = FiscalPeriod(parts[0], int(parts[1]))
        return FinancialReport(
            id=orm.id,
            company_id=orm.company_id,
            workspace_id=orm.workspace_id,
            fiscal_period=fp,
            title=orm.title,
            content=orm.content,
            status=ReportStatus(orm.status),
            generated_by=orm.generated_by,
            model_name=orm.model_name,
            prompt_version=orm.prompt_version,
            report_template_version=orm.report_template_version,
            financial_engine_version=orm.financial_engine_version,
            rag_version=orm.rag_version,
            embedding_version=orm.embedding_version,
            generated_at=orm.updated_at if orm.status == "COMPLETED" else None,
            generation_duration=orm.generation_duration,
            error_message=orm.error_message,
            celery_task_id=orm.celery_task_id,
        )

    def _to_orm(self, domain: FinancialReport) -> FinancialReportORM:
        """Translates FinancialReport domain entity to ORM model."""
        return FinancialReportORM(
            id=domain.id,
            company_id=domain.company_id,
            workspace_id=domain.workspace_id,
            fiscal_period=str(domain.fiscal_period),
            title=domain.title,
            content=domain.content,
            status=domain.status.value,
            generated_by=domain.generated_by,
            model_name=domain.model_name,
            prompt_version=domain.prompt_version,
            report_template_version=domain.report_template_version,
            financial_engine_version=domain.financial_engine_version,
            rag_version=domain.rag_version,
            embedding_version=domain.embedding_version,
            generation_duration=domain.generation_duration,
            error_message=domain.error_message,
            celery_task_id=domain.celery_task_id,
        )

    def _version_to_domain(
        self, orm: FinancialReportVersionORM
    ) -> FinancialReportVersion:
        """Translates ORM version model to domain entity."""
        return FinancialReportVersion(
            id=orm.id,
            report_id=orm.report_id,
            version=orm.version,
            content=orm.content,
            changed_by_id=orm.changed_by_id,
            changed_at=orm.created_at,
            change_reason=orm.change_reason,
        )

    # ─── Interface Methods ────────────────────────────────────────────────────

    async def get(self, report_id: UUID, workspace_id: UUID) -> FinancialReport | None:
        """
        Retrieve a report by its unique ID and workspace scoping.
        """
        query = select(FinancialReportORM).where(
            FinancialReportORM.id == report_id,
            FinancialReportORM.workspace_id == workspace_id,
            FinancialReportORM.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def list_by_company(
        self, company_id: UUID, workspace_id: UUID
    ) -> list[FinancialReport]:
        """
        List all non-deleted reports for a company scoped to a workspace.
        """
        query = (
            select(FinancialReportORM)
            .where(
                FinancialReportORM.company_id == company_id,
                FinancialReportORM.workspace_id == workspace_id,
                FinancialReportORM.deleted_at.is_(None),
            )
            .order_by(FinancialReportORM.created_at.desc())
        )
        result = await self.session.execute(query)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def save(self, report: FinancialReport) -> FinancialReport:
        """
        Upsert a FinancialReport entity.
        """
        existing = await self.session.get(FinancialReportORM, report.id)
        if existing:
            existing.title = report.title
            existing.content = report.content
            existing.status = report.status.value
            existing.model_name = report.model_name
            existing.generation_duration = report.generation_duration
            existing.error_message = report.error_message
            existing.celery_task_id = report.celery_task_id
            existing.financial_engine_version = report.financial_engine_version
            existing.rag_version = report.rag_version
            existing.embedding_version = report.embedding_version
            existing.prompt_version = report.prompt_version
            existing.report_template_version = report.report_template_version
            # Track generation timestamp via updated_at (auto-updated)
            await self.session.flush()
            return self._to_domain(existing)
        else:
            orm = self._to_orm(report)
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def save_version(self, version: FinancialReportVersion) -> None:
        """
        Persist a new point-in-time content snapshot for a report.
        """
        orm = FinancialReportVersionORM(
            id=version.id,
            report_id=version.report_id,
            version=version.version,
            content=version.content,
            changed_by_id=version.changed_by_id,
            change_reason=version.change_reason,
        )
        self.session.add(orm)
        await self.session.flush()

    async def get_versions(self, report_id: UUID) -> list[FinancialReportVersion]:
        """
        List all historical version snapshots of a report ordered newest first.
        """
        query = (
            select(FinancialReportVersionORM)
            .where(FinancialReportVersionORM.report_id == report_id)
            .order_by(FinancialReportVersionORM.version.desc())
        )
        result = await self.session.execute(query)
        return [self._version_to_domain(row) for row in result.scalars().all()]

    async def get_version_count(self, report_id: UUID) -> int:
        """
        Return the current version count for a report (used to compute next version number).
        """
        versions = await self.get_versions(report_id)
        return len(versions)
