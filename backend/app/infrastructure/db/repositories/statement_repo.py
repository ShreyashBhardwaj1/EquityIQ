"""
SQLAlchemy repository adapter for FinancialStatement.
"""

from uuid import UUID

from sqlalchemy import select

from app.domain.entities.financial_statement import (
    FinancialStatement,
    NormalizationAdjustment,
    StatementType,
)
from app.domain.entities.financial_statement_version import (
    FinancialStatementVersion,
)
from app.domain.interfaces.repositories import FinancialStatementRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.company import CompanyORM
from app.infrastructure.db.models.financial_statement import FinancialStatementORM
from app.infrastructure.db.models.financial_statement_version import (
    FinancialStatementVersionORM,
)
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyFinancialStatementRepository(
    BaseRepository[FinancialStatementORM], FinancialStatementRepository
):
    """
    SQLAlchemy-backed implementation of the FinancialStatementRepository interface.
    """

    def _to_domain(self, orm: FinancialStatementORM) -> FinancialStatement:
        """Translates ORM model to Domain Entity."""
        parts = orm.fiscal_period.split("-")
        period = parts[0]
        year = int(parts[1]) if len(parts) > 1 else 2000

        # Translate nested adjustments from dict representations back into Domain objects
        adjustments = [
            NormalizationAdjustment(
                line_item=adj["line_item"],
                adjustment=adj["adjustment"],
                reason=adj["reason"],
                source_document_id=UUID(adj["source_document_id"]),
                source_page=adj["source_page"],
            )
            for adj in orm.normalization_adjustments
        ]

        return FinancialStatement(
            id=orm.id,
            company_id=orm.company_id,
            document_id=orm.document_id,
            statement_type=StatementType(orm.statement_type),
            fiscal_period=FiscalPeriod(period, year),
            line_items=(
                {str(k): float(v) for k, v in orm.line_items.items()}
                if orm.line_items
                else {}
            ),
            normalization_adjustments=adjustments,
            normalized_line_items=(
                {str(k): float(v) for k, v in orm.normalized_line_items.items()}
                if orm.normalized_line_items
                else {}
            ),
            extraction_confidence=(
                {str(k): float(v) for k, v in orm.extraction_confidence.items()}
                if orm.extraction_confidence
                else {}
            ),
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: FinancialStatement) -> FinancialStatementORM:
        """Translates Domain Entity to ORM model."""
        fp_str = f"{domain.fiscal_period.period}-{domain.fiscal_period.year}"

        # Serialize adjustments back to plain dictionary structures for storage
        adjustments = [
            {
                "line_item": adj.line_item,
                "adjustment": adj.adjustment,
                "reason": adj.reason,
                "source_document_id": str(adj.source_document_id),
                "source_page": adj.source_page,
            }
            for adj in domain.normalization_adjustments
        ]

        return FinancialStatementORM(
            id=domain.id,
            company_id=domain.company_id,
            document_id=domain.document_id,
            statement_type=domain.statement_type.value,
            fiscal_period=fp_str,
            line_items=domain.line_items,
            normalization_adjustments=adjustments,
            normalized_line_items=domain.normalized_line_items,
            extraction_confidence=domain.extraction_confidence,
            created_at=domain.created_at,
        )

    def _version_to_domain(
        self, orm: FinancialStatementVersionORM
    ) -> FinancialStatementVersion:
        """Translates ORM version model to Domain Entity."""
        adjustments = [
            NormalizationAdjustment(
                line_item=adj["line_item"],
                adjustment=adj["adjustment"],
                reason=adj["reason"],
                source_document_id=UUID(adj["source_document_id"]),
                source_page=adj["source_page"],
            )
            for adj in orm.normalization_adjustments
        ]
        return FinancialStatementVersion(
            id=orm.id,
            statement_id=orm.statement_id,
            version=orm.version,
            line_items=(
                {str(k): float(v) for k, v in orm.line_items.items()}
                if orm.line_items
                else {}
            ),
            normalized_line_items=(
                {str(k): float(v) for k, v in orm.normalized_line_items.items()}
                if orm.normalized_line_items
                else {}
            ),
            normalization_adjustments=adjustments,
            changed_by=orm.changed_by,
            change_reason=orm.change_reason,
            created_at=orm.created_at,
        )

    def _version_to_orm(
        self, domain: FinancialStatementVersion
    ) -> FinancialStatementVersionORM:
        """Translates version Domain Entity to ORM model."""
        adjustments = [
            {
                "line_item": adj.line_item,
                "adjustment": adj.adjustment,
                "reason": adj.reason,
                "source_document_id": str(adj.source_document_id),
                "source_page": adj.source_page,
            }
            for adj in domain.normalization_adjustments
        ]
        return FinancialStatementVersionORM(
            id=domain.id,
            statement_id=domain.statement_id,
            version=domain.version,
            line_items=domain.line_items,
            normalized_line_items=domain.normalized_line_items,
            normalization_adjustments=adjustments,
            changed_by=domain.changed_by,
            change_reason=domain.change_reason,
            created_at=domain.created_at,
        )

    async def get(
        self, statement_id: UUID, workspace_id: UUID | None = None
    ) -> FinancialStatement | None:
        """
        Retrieves a financial statement by its ID, with optional workspace scoping.
        """
        if workspace_id:
            query = (
                select(FinancialStatementORM)
                .join(CompanyORM, FinancialStatementORM.company_id == CompanyORM.id)
                .where(
                    CompanyORM.workspace_id == workspace_id,
                    FinancialStatementORM.id == statement_id,
                )
            )
        else:
            query = select(FinancialStatementORM).where(
                FinancialStatementORM.id == statement_id
            )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_period(
        self,
        company_id: UUID,
        statement_type: str,
        fiscal_period: str,
        workspace_id: UUID | None = None,
    ) -> FinancialStatement | None:
        """
        Retrieves a unique statement by company, type, period, and optional workspace scoping.
        """
        if workspace_id:
            query = (
                select(FinancialStatementORM)
                .join(CompanyORM, FinancialStatementORM.company_id == CompanyORM.id)
                .where(
                    CompanyORM.workspace_id == workspace_id,
                    CompanyORM.id == company_id,
                    FinancialStatementORM.statement_type
                    == statement_type.lower().strip(),
                    FinancialStatementORM.fiscal_period == fiscal_period.strip(),
                )
            )
        else:
            query = select(FinancialStatementORM).where(
                FinancialStatementORM.company_id == company_id,
                FinancialStatementORM.statement_type == statement_type.lower().strip(),
                FinancialStatementORM.fiscal_period == fiscal_period.strip(),
            )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, statement: FinancialStatement) -> FinancialStatement:
        """
        Persists a FinancialStatement entity.
        """
        existing_orm = await self.session.get(FinancialStatementORM, statement.id)
        orm = self._to_orm(statement)

        if existing_orm:
            existing_orm.company_id = orm.company_id
            existing_orm.document_id = orm.document_id
            existing_orm.statement_type = orm.statement_type
            existing_orm.fiscal_period = orm.fiscal_period
            existing_orm.line_items = orm.line_items
            existing_orm.normalization_adjustments = orm.normalization_adjustments
            existing_orm.normalized_line_items = orm.normalized_line_items
            existing_orm.extraction_confidence = orm.extraction_confidence
            await self.session.flush()
            return self._to_domain(existing_orm)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def list_by_company(
        self, company_id: UUID, workspace_id: UUID | None = None
    ) -> list[FinancialStatement]:
        """
        Lists all statements associated with a company, with optional workspace scoping.
        """
        if workspace_id:
            query = (
                select(FinancialStatementORM)
                .join(CompanyORM, FinancialStatementORM.company_id == CompanyORM.id)
                .where(
                    CompanyORM.workspace_id == workspace_id,
                    CompanyORM.id == company_id,
                )
            )
        else:
            query = select(FinancialStatementORM).where(
                FinancialStatementORM.company_id == company_id
            )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def delete(
        self, statement_id: UUID, workspace_id: UUID | None = None
    ) -> None:
        """
        Deletes a statement, with optional workspace scoping context.
        """
        existing = await self.get(statement_id, workspace_id)
        if existing:
            orm = await self.session.get(FinancialStatementORM, statement_id)
            if orm:
                await self.session.delete(orm)
                await self.session.flush()

    async def save_version(self, version: FinancialStatementVersion) -> None:
        """
        Persists a FinancialStatementVersion ORM record.
        """
        orm = self._version_to_orm(version)
        self.session.add(orm)
        await self.session.flush()

    async def list_versions(
        self, statement_id: UUID
    ) -> list[FinancialStatementVersion]:
        """
        Lists all historical revision versions for a statement.
        """
        query = (
            select(FinancialStatementVersionORM)
            .where(FinancialStatementVersionORM.statement_id == statement_id)
            .order_by(FinancialStatementVersionORM.version.asc())
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._version_to_domain(orm) for orm in orms]
