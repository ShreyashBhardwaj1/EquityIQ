from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class FinancialStatementORM(Base):
    """
    SQLAlchemy mapping for the 'financial_statements' database table.
    """

    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "fiscal_period",
            "statement_type",
            name="uq_statements_company_period_type",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    statement_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # e.g., 'income', 'balance', 'cashflow'
    fiscal_period: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # e.g., 'Q1-2024', 'FY-2024'
    line_items: Mapped[dict[str, float]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )
    normalization_adjustments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    normalized_line_items: Mapped[dict[str, float]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )
    extraction_confidence: Mapped[dict[str, float] | None] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True
    )
