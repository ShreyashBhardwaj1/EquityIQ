"""
SQLAlchemy repository adapter for financial Ratio.
"""

from uuid import UUID

from sqlalchemy import delete, select

from app.domain.entities.ratio import Ratio
from app.domain.interfaces.repositories import RatioRepository
from app.domain.rules.ratio_registry import RatioRegistry
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.infrastructure.db.models.ratio import RatioORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyRatioRepository(BaseRepository[RatioORM], RatioRepository):
    """
    SQLAlchemy-backed implementation of the RatioRepository interface.
    """

    def _to_domain(self, orm: RatioORM) -> Ratio:
        """Translates ORM model to Domain Entity."""
        parts = orm.fiscal_period.split("-")
        fp = FiscalPeriod(parts[0], int(parts[1]))
        return Ratio(
            id=orm.id,
            company_id=orm.company_id,
            fiscal_period=fp,
            ratio_name=orm.ratio_name,
            value=orm.value if orm.value is not None else 0.0,
            formula_version=orm.ratio_engine_version,
            computed_at=orm.created_at,
        )

    def _to_orm(self, domain: Ratio) -> RatioORM:
        """Translates Domain Entity to ORM model."""
        defn = RatioRegistry.DEFINITIONS.get(domain.ratio_name)
        category = defn.category if defn else "unknown"
        formula = defn.formula if defn else "unknown"

        return RatioORM(
            id=domain.id,
            company_id=domain.company_id,
            fiscal_period=str(domain.fiscal_period),
            ratio_name=domain.ratio_name,
            category=category,
            value=domain.value,
            is_valid=True,
            error_message=None,
            formula=formula,
            line_items_used={},
            ratio_engine_version=domain.formula_version,
        )

    async def get_by_period(
        self, company_id: UUID, fiscal_period: str, workspace_id: UUID | None = None
    ) -> list[Ratio]:
        """
        Retrieve computed ratios for a company in a fiscal period.
        """
        # Note: Scoping workspace_id can be done by joining on companies if workspace_id is provided,
        # but to keep it simple and correct, we filter by company_id and fiscal_period.
        query = select(RatioORM).where(
            RatioORM.company_id == company_id,
            RatioORM.fiscal_period == fiscal_period,
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def save_batch(self, ratios: list[Ratio]) -> None:
        """
        Batch save computed ratio records.
        """
        for ratio in ratios:
            # Check if it already exists by ID
            existing = await self.session.get(RatioORM, ratio.id)
            orm = self._to_orm(ratio)
            if existing:
                existing.value = orm.value
                existing.ratio_engine_version = orm.ratio_engine_version
            else:
                self._add(orm)
        await self.session.flush()

    async def delete_by_period(self, company_id: UUID, fiscal_period: str) -> None:
        """
        Delete ratios associated with a specific period.
        """
        query = delete(RatioORM).where(
            RatioORM.company_id == company_id,
            RatioORM.fiscal_period == fiscal_period,
        )
        await self.session.execute(query)
        await self.session.flush()
