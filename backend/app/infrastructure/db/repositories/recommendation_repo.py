"""
SQLAlchemy repository adapter for Recommendation, RecommendationPolicy, and RecommendationHistory.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.financial_intelligence import (
    RecommendationHistory,
    RecommendationPolicy,
)
from app.domain.entities.recommendation import Recommendation, RecommendationType
from app.domain.interfaces.repositories import RecommendationRepository
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.recommendation import (
    RecommendationORM,
    RecommendationPolicyORM,
)
from app.infrastructure.db.models.recommendation_history import RecommendationHistoryORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyRecommendationRepository(BaseRepository[RecommendationORM], RecommendationRepository):
    """
    SQLAlchemy-backed implementation of the RecommendationRepository interface.
    """

    def _to_domain(self, orm: RecommendationORM) -> Recommendation:
        """Translates ORM model to Domain Entity."""
        parts = orm.fiscal_period.split("-")
        fp = FiscalPeriod(parts[0], int(parts[1]))
        return Recommendation(
            id=orm.id,
            company_id=orm.company_id,
            recommendation=RecommendationType(orm.rating),
            composite_score=orm.overall_score,
            rationale=", ".join(orm.rules_applied),
            fiscal_period=fp,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: Recommendation) -> RecommendationORM:
        """Translates Domain Entity to ORM model."""
        fiscal_period_val = str(domain.fiscal_period) if domain.fiscal_period else "unknown"
        return RecommendationORM(
            id=domain.id,
            company_id=domain.company_id,
            fiscal_period=fiscal_period_val,
            rating=str(domain.recommendation),
            overall_score=domain.composite_score,
            rules_applied=[domain.rationale],
            recommendation_policy_version="1.0.0-default",
        )

    def _policy_to_domain(self, orm: RecommendationPolicyORM) -> RecommendationPolicy:
        """Translates Policy ORM model to Policy Domain Entity."""
        return RecommendationPolicy(
            policy_id=orm.id,
            policy_name=orm.policy_name,
            policy_version=orm.policy_version,
            health_score_thresholds=orm.health_score_thresholds,
            max_severe_risks_allowed=orm.max_severe_risks_allowed,
            requires_positive_growth=orm.requires_positive_growth,
            is_active=orm.is_active,
        )

    def _policy_to_orm(self, domain: RecommendationPolicy) -> RecommendationPolicyORM:
        """Translates Policy Domain Entity to Policy ORM model."""
        return RecommendationPolicyORM(
            id=domain.policy_id,
            policy_name=domain.policy_name,
            policy_version=domain.policy_version,
            health_score_thresholds=domain.health_score_thresholds,
            max_severe_risks_allowed=domain.max_severe_risks_allowed,
            requires_positive_growth=domain.requires_positive_growth,
            is_active=domain.is_active,
        )

    def _history_to_domain(self, orm: RecommendationHistoryORM) -> RecommendationHistory:
        """Translates History ORM model to History Domain Entity."""
        parts = orm.fiscal_period.split("-")
        fp = FiscalPeriod(parts[0], int(parts[1]))
        return RecommendationHistory(
            id=orm.id,
            recommendation_id=orm.recommendation_id,
            company_id=orm.company_id,
            fiscal_period=fp,
            rating=RecommendationType(orm.rating),
            policy_id=orm.policy_id,
            policy_version=orm.policy_version,
            composite_score=orm.composite_score,
            reasoning_steps=orm.reasoning_steps,
            triggered_by=orm.triggered_by,
            created_at=orm.created_at,
        )

    def _history_to_orm(self, domain: RecommendationHistory) -> RecommendationHistoryORM:
        """Translates History Domain Entity to History ORM model."""
        return RecommendationHistoryORM(
            id=domain.id,
            recommendation_id=domain.recommendation_id,
            company_id=domain.company_id,
            fiscal_period=str(domain.fiscal_period),
            rating=str(domain.rating),
            policy_id=domain.policy_id,
            policy_version=domain.policy_version,
            composite_score=domain.composite_score,
            reasoning_steps=domain.reasoning_steps,
            triggered_by=domain.triggered_by,
        )

    async def get(
        self, company_id: UUID, fiscal_period: str, workspace_id: UUID | None = None
    ) -> Recommendation | None:
        """
        Retrieve active recommendation rating for a company in a period.
        """
        query = select(RecommendationORM).where(
            RecommendationORM.company_id == company_id,
            RecommendationORM.fiscal_period == fiscal_period,
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, recommendation: Recommendation) -> Recommendation:
        """
        Save active recommendation rating record.
        """
        existing = await self.session.get(RecommendationORM, recommendation.id)
        orm = self._to_orm(recommendation)

        if existing:
            existing.rating = orm.rating
            existing.overall_score = orm.overall_score
            existing.rules_applied = orm.rules_applied
            existing.recommendation_policy_version = orm.recommendation_policy_version
            await self.session.flush()
            return self._to_domain(existing)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def delete(self, company_id: UUID, fiscal_period: str) -> None:
        """
        Delete active recommendation record.
        """
        query = delete(RecommendationORM).where(
            RecommendationORM.company_id == company_id,
            RecommendationORM.fiscal_period == fiscal_period,
        )
        await self.session.execute(query)
        await self.session.flush()

    async def save_history(self, history: RecommendationHistory) -> None:
        """
        Save a recommendation audit history record.
        """
        orm = self._history_to_orm(history)
        self.session.add(orm)
        await self.session.flush()

    async def list_history(
        self, company_id: UUID, fiscal_period: str
    ) -> list[RecommendationHistory]:
        """
        List historical recommendation change logs for audit trails.
        """
        query = select(RecommendationHistoryORM).where(
            RecommendationHistoryORM.company_id == company_id,
            RecommendationHistoryORM.fiscal_period == fiscal_period,
        ).order_by(RecommendationHistoryORM.created_at.desc())
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._history_to_domain(orm) for orm in orms]

    async def get_active_policy(self) -> RecommendationPolicy | None:
        """
        Retrieve currently active recommendation policy settings.
        """
        query = select(RecommendationPolicyORM).where(
            RecommendationPolicyORM.is_active
        ).limit(1)
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._policy_to_domain(orm) if orm else None

    async def save_policy(self, policy: RecommendationPolicy) -> RecommendationPolicy:
        """
        Save or register a recommendation policy.
        """
        existing = await self.session.get(RecommendationPolicyORM, policy.policy_id)
        orm = self._policy_to_orm(policy)

        if existing:
            existing.policy_name = orm.policy_name
            existing.policy_version = orm.policy_version
            existing.health_score_thresholds = orm.health_score_thresholds
            existing.max_severe_risks_allowed = orm.max_severe_risks_allowed
            existing.requires_positive_growth = orm.requires_positive_growth
            existing.is_active = orm.is_active
            await self.session.flush()
            return self._policy_to_domain(existing)
        else:
            self.session.add(orm)
            await self.session.flush()
            return self._policy_to_domain(orm)
