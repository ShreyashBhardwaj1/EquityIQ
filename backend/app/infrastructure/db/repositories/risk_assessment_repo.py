"""
SQLAlchemy repository adapter for RiskAssessment.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.financial_intelligence import RiskAssessment, SeverityLevel
from app.domain.interfaces.repositories import RiskAssessmentRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.risk_assessment import RiskAssessmentORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyRiskAssessmentRepository(BaseRepository[RiskAssessmentORM], RiskAssessmentRepository):
    """
    SQLAlchemy-backed implementation of the RiskAssessmentRepository interface.
    """

    def _to_domain(self, orm: RiskAssessmentORM) -> RiskAssessment:
        """Translates ORM model to Domain Entity."""
        parts = orm.fiscal_period.split("-")
        fp = FiscalPeriod(parts[0], int(parts[1]))
        return RiskAssessment(
            id=orm.id,
            company_id=orm.company_id,
            fiscal_period=fp,
            risk_category=orm.risk_category,
            severity=SeverityLevel(orm.severity),
            confidence=orm.confidence,
            supporting_evidence=orm.supporting_evidence,
            ratio_engine_version=orm.ratio_engine_version,
            computed_at=orm.created_at,
        )

    def _to_orm(self, domain: RiskAssessment) -> RiskAssessmentORM:
        """Translates Domain Entity to ORM model."""
        return RiskAssessmentORM(
            id=domain.id,
            company_id=domain.company_id,
            fiscal_period=str(domain.fiscal_period),
            risk_category=domain.risk_category,
            severity=str(domain.severity),
            confidence=domain.confidence,
            supporting_evidence=domain.supporting_evidence,
            ratio_engine_version=domain.ratio_engine_version,
        )


    async def list_by_period(
        self, company_id: UUID, fiscal_period: str, workspace_id: UUID | None = None
    ) -> list[RiskAssessment]:
        """
        List detected risks for a company in a period.
        """
        query = select(RiskAssessmentORM).where(
            RiskAssessmentORM.company_id == company_id,
            RiskAssessmentORM.fiscal_period == fiscal_period,
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def save_batch(self, risks: list[RiskAssessment]) -> None:
        """
        Batch save detected risk assessment records.
        """
        for risk in risks:
            existing = await self.session.get(RiskAssessmentORM, risk.id)
            orm = self._to_orm(risk)
            if existing:
                existing.severity = orm.severity
                existing.confidence = orm.confidence
                existing.supporting_evidence = orm.supporting_evidence
                existing.ratio_engine_version = orm.ratio_engine_version
            else:
                self._add(orm)
        await self.session.flush()

    async def delete_by_period(self, company_id: UUID, fiscal_period: str) -> None:
        """
        Delete risks associated with a specific period.
        """
        query = delete(RiskAssessmentORM).where(
            RiskAssessmentORM.company_id == company_id,
            RiskAssessmentORM.fiscal_period == fiscal_period,
        )
        await self.session.execute(query)
        await self.session.flush()
