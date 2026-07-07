"""
SQLAlchemy repository adapter for Company.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select

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
            workspace_id=orm.workspace_id,
            ticker=Ticker(orm.ticker),
            exchange=Exchange(orm.exchange),
            name=orm.name,
            sector=orm.sector,
            industry=orm.industry,
            country=orm.country,
            fiscal_year_end=orm.fiscal_year_end,
            currency=orm.currency,
        )

    def _to_orm(self, domain: Company) -> CompanyORM:
        """Translates Domain Entity to ORM model."""
        return CompanyORM(
            id=domain.id,
            workspace_id=domain.workspace_id,
            ticker=domain.ticker.symbol,
            exchange=domain.exchange.name,
            name=domain.name,
            sector=domain.sector,
            industry=domain.industry,
            country=domain.country,
            fiscal_year_end=domain.fiscal_year_end,
            currency=domain.currency,
        )

    async def get_by_id(self, workspace_id: UUID, company_id: UUID) -> Company | None:
        """
        Retrieves a company by its ID inside a workspace (excluding soft-deleted).
        """
        query = select(CompanyORM).where(
            CompanyORM.workspace_id == workspace_id,
            CompanyORM.id == company_id,
            CompanyORM.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_ticker(
        self,
        workspace_id: UUID,
        ticker: str,
        exchange: str | None = None,
        include_deleted: bool = False,
    ) -> Company | None:
        """
        Retrieves a company by its unique ticker inside a workspace (optionally including soft-deleted).
        """
        query = select(CompanyORM).where(
            CompanyORM.workspace_id == workspace_id,
            CompanyORM.ticker == ticker.upper().strip(),
        )
        if exchange:
            query = query.where(CompanyORM.exchange == exchange.strip())
        if not include_deleted:
            query = query.where(CompanyORM.deleted_at.is_(None))

        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, company: Company) -> Company:
        """
        Persists a Company entity (restoring soft-deleted version if exists).
        """
        existing_orm = await self.session.get(CompanyORM, company.id)
        orm = self._to_orm(company)

        if existing_orm:
            existing_orm.workspace_id = orm.workspace_id
            existing_orm.ticker = orm.ticker
            existing_orm.exchange = orm.exchange
            existing_orm.name = orm.name
            existing_orm.sector = orm.sector
            existing_orm.industry = orm.industry
            existing_orm.country = orm.country
            existing_orm.fiscal_year_end = orm.fiscal_year_end
            existing_orm.currency = orm.currency
            existing_orm.deleted_at = None  # Restore if soft-deleted
            await self.session.flush()
            return self._to_domain(existing_orm)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def list_by_workspace(
        self,
        workspace_id: UUID,
        limit: int = 20,
        offset: int = 0,
        sort_by: str | None = None,
        sort_order: str | None = None,
        exchange: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        country: str | None = None,
    ) -> list[Company]:
        """
        Lists active companies under a workspace with filters, sorting, and pagination.
        """
        query = select(CompanyORM).where(
            CompanyORM.workspace_id == workspace_id,
            CompanyORM.deleted_at.is_(None),
        )

        # Apply Filters
        if exchange:
            query = query.where(CompanyORM.exchange == exchange.strip())
        if sector:
            query = query.where(CompanyORM.sector == sector.strip())
        if industry:
            query = query.where(CompanyORM.industry == industry.strip())
        if country:
            query = query.where(CompanyORM.country == country.strip())

        # Sorting: Default to created_at DESC
        sort_field: Any = CompanyORM.created_at
        is_desc = True

        if sort_by:
            by_val = sort_by.strip().lower()
            if by_val == "ticker":
                sort_field = CompanyORM.ticker
            elif by_val == "exchange":
                sort_field = CompanyORM.exchange
            elif by_val == "sector":
                sort_field = CompanyORM.sector
            elif by_val == "industry":
                sort_field = CompanyORM.industry

        if sort_order:
            order_val = sort_order.strip().lower()
            if order_val == "asc":
                is_desc = False
            elif order_val == "desc":
                is_desc = True

        if is_desc:
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def search_companies(
        self, workspace_id: UUID, query_str: str
    ) -> list[Company]:
        """
        Searches companies in workspace by name, ticker, exchange, or sector (case-insensitive).
        """
        q = f"%{query_str.strip()}%"
        query = (
            select(CompanyORM)
            .where(
                CompanyORM.workspace_id == workspace_id,
                CompanyORM.deleted_at.is_(None),
                (
                    CompanyORM.name.ilike(q)
                    | CompanyORM.ticker.ilike(q)
                    | CompanyORM.exchange.ilike(q)
                    | CompanyORM.sector.ilike(q)
                ),
            )
            .order_by(CompanyORM.ticker.asc())
        )

        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def delete(self, workspace_id: UUID, company_id: UUID) -> None:
        """
        Soft deletes a company from a workspace.
        """
        query = select(CompanyORM).where(
            CompanyORM.workspace_id == workspace_id,
            CompanyORM.id == company_id,
            CompanyORM.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        if orm:
            orm.deleted_at = func.now()
            await self.session.flush()
