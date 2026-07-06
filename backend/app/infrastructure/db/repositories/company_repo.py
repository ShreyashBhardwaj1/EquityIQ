"""
SQLAlchemy repository adapter for Company.
"""

from uuid import UUID

from sqlalchemy import select

from app.domain.entities.company import Company
from app.domain.interfaces.repositories import CompanyRepository
from app.domain.value_objects.exchange import Exchange
from app.domain.value_objects.ticker import Ticker
from app.infrastructure.db.models.company import CompanyORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyCompanyRepository(BaseRepository[CompanyORM], CompanyRepository):
    """
    SQLAlchemy-backed implementation of the CompanyRepository interface.
    """

    def _to_domain(self, orm: CompanyORM) -> Company:
        """Translates ORM model to Domain Entity."""
        return Company(
            id=orm.id,
            ticker=Ticker(orm.ticker),
            exchange=Exchange(orm.exchange),
            name=orm.name,
            sector=orm.sector,
            industry=orm.industry,
            fiscal_year_end=orm.fiscal_year_end,
            currency=orm.currency,
        )

    def _to_orm(self, domain: Company) -> CompanyORM:
        """Translates Domain Entity to ORM model."""
        return CompanyORM(
            id=domain.id,
            ticker=domain.ticker.symbol,
            exchange=domain.exchange.name,
            name=domain.name,
            sector=domain.sector,
            industry=domain.industry,
            fiscal_year_end=domain.fiscal_year_end,
            currency=domain.currency,
        )

    async def get_by_id(self, company_id: UUID) -> Company | None:
        """
        Retrieves a company by its ID.

        Args:
            company_id: The UUID company identifier.

        Returns:
            The Company domain entity, or None.
        """
        orm = await self._get(CompanyORM, company_id)
        return self._to_domain(orm) if orm else None

    async def get_by_ticker(self, ticker: str) -> Company | None:
        """
        Retrieves a company by its unique ticker symbol.

        Args:
            ticker: Stock ticker string.

        Returns:
            The Company domain entity, or None.
        """
        query = select(CompanyORM).where(CompanyORM.ticker == ticker.upper().strip())
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, company: Company) -> Company:
        """
        Persists a Company entity.

        Args:
            company: Company domain entity.

        Returns:
            The persisted Company entity.
        """
        existing_orm = await self.session.get(CompanyORM, company.id)
        orm = self._to_orm(company)

        if existing_orm:
            # Update fields directly
            existing_orm.ticker = orm.ticker
            existing_orm.exchange = orm.exchange
            existing_orm.name = orm.name
            existing_orm.sector = orm.sector
            existing_orm.industry = orm.industry
            existing_orm.fiscal_year_end = orm.fiscal_year_end
            existing_orm.currency = orm.currency
            await self.session.flush()
            return self._to_domain(existing_orm)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)
