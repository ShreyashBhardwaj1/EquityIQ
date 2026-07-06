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
from app.domain.interfaces.repositories import FinancialStatementRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.financial_statement import FinancialStatementORM
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
        )

    async def get(self, statement_id: UUID) -> FinancialStatement | None:
        """
        Retrieves a financial statement by its ID.

        Args:
            statement_id: UUID statement identifier.

        Returns:
            The FinancialStatement domain entity, or None.
        """
        orm = await self._get(FinancialStatementORM, statement_id)
        return self._to_domain(orm) if orm else None

    async def get_by_period(
        self, company_id: UUID, statement_type: str, fiscal_period: str
    ) -> FinancialStatement | None:
        """
        Retrieves a unique statement by company, statement type, and fiscal period.

        Args:
            company_id: UUID company identifier.
            statement_type: e.g. income, balance, cashflow.
            fiscal_period: e.g. Q1-2024.

        Returns:
            The matching FinancialStatement domain entity, or None.
        """
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

        Args:
            statement: FinancialStatement domain entity.

        Returns:
            The persisted FinancialStatement entity.
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
