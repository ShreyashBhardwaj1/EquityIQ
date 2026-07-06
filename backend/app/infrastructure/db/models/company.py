"""
Company ORM model representation.
"""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class CompanyORM(Base):
    """
    SQLAlchemy mapping for the 'companies' database table.
    """

    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("ticker", "exchange", name="uq_companies_ticker_exchange"),
    )

    ticker: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(15), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    fiscal_year_end: Mapped[str] = mapped_column(
        String(5), nullable=False
    )  # Format: MM-DD
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False
    )  # ISO 4217 Currency Code
