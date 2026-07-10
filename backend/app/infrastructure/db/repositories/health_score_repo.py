"""
SQLAlchemy repository adapter for FinancialHealthScore.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.financial_intelligence import FinancialHealthScore
from app.domain.interfaces.repositories import HealthScoreRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.health_score import FinancialHealthScoreORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyHealthScoreRepository(
    BaseRepository[FinancialHealthScoreORM], HealthScoreRepository
):
    """
    SQLAlchemy-backed implementation of the HealthScoreRepository interface.
    """

    def _to_domain(self, orm: FinancialHealthScoreORM) -> FinancialHealthScore:
        """Translates ORM model to Domain Entity."""
        parts = orm.fiscal_period.split("-")
        fp = FiscalPeriod(parts[0], int(parts[1]))

        # Reconstruct confidence breakdown
        retrieval_confidence = 0.95
        financial_data_quality = orm.confidence
        if orm.category_scores:
            avg = sum(orm.category_scores.values()) / len(orm.category_scores)
            variance = sum((x - avg) ** 2 for x in orm.category_scores.values()) / len(
                orm.category_scores
            )
            std_dev = variance**0.5
            rule_agreement = max(0.0, min(1.0, 1.0 - (std_dev / 5.0)))
        else:
            rule_agreement = 1.0
        trend_consistency = 0.8

        confidence_breakdown = {
            "retrieval_confidence": round(retrieval_confidence, 2),
            "financial_data_quality": round(financial_data_quality, 2),
            "rule_agreement": round(rule_agreement, 2),
            "trend_consistency": round(trend_consistency, 2),
            "overall_confidence": round(orm.confidence, 2),
        }

        return FinancialHealthScore(
            id=orm.id,
            company_id=orm.company_id,
            fiscal_period=fp,
            overall_score=orm.overall_score,
            category_scores=orm.category_scores,
            weights=orm.weights,
            score_explanation=orm.score_explanation,
            confidence=orm.confidence,
            confidence_breakdown=confidence_breakdown,
            percentile=orm.percentile,
            ratio_engine_version=orm.ratio_engine_version,
            computed_at=orm.created_at,
        )

    def _to_orm(self, domain: FinancialHealthScore) -> FinancialHealthScoreORM:
        """Translates Domain Entity to ORM model."""
        return FinancialHealthScoreORM(
            id=domain.id,
            company_id=domain.company_id,
            fiscal_period=str(domain.fiscal_period),
            overall_score=domain.overall_score,
            category_scores=domain.category_scores,
            weights=domain.weights,
            score_explanation=domain.score_explanation,
            confidence=domain.confidence,
            percentile=domain.percentile,
            ratio_engine_version=domain.ratio_engine_version,
        )

    async def get(
        self, company_id: UUID, fiscal_period: str, workspace_id: UUID | None = None
    ) -> FinancialHealthScore | None:
        """
        Retrieve computed health score for a company in a period.
        """
        query = select(FinancialHealthScoreORM).where(
            FinancialHealthScoreORM.company_id == company_id,
            FinancialHealthScoreORM.fiscal_period == fiscal_period,
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, health_score: FinancialHealthScore) -> FinancialHealthScore:
        """
        Save a computed health score record.
        """
        existing = await self.session.get(FinancialHealthScoreORM, health_score.id)
        orm = self._to_orm(health_score)

        if existing:
            existing.overall_score = orm.overall_score
            existing.category_scores = orm.category_scores
            existing.weights = orm.weights
            existing.score_explanation = orm.score_explanation
            existing.confidence = orm.confidence
            existing.percentile = orm.percentile
            existing.ratio_engine_version = orm.ratio_engine_version
            await self.session.flush()
            return self._to_domain(existing)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def delete(self, company_id: UUID, fiscal_period: str) -> None:
        """
        Delete health score associated with a specific period.
        """
        query = delete(FinancialHealthScoreORM).where(
            FinancialHealthScoreORM.company_id == company_id,
            FinancialHealthScoreORM.fiscal_period == fiscal_period,
        )
        await self.session.execute(query)
        await self.session.flush()
