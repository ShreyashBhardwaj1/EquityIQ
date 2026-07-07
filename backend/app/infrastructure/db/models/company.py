"""
Company ORM model representation.
"""

from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class CompanyORM(Base):
    """
    SQLAlchemy mapping for the 'companies' database table.
    """

    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "ticker",
            "exchange",
            name="uq_companies_workspace_ticker_exchange",
        ),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticker: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(15), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    fiscal_year_end: Mapped[str] = mapped_column(
        String(5), nullable=False
    )  # Format: MM-DD
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False
    )  # ISO 4217 Currency Code
