from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class FinancialStatementVersionORM(Base):
    """
    SQLAlchemy mapping for the 'financial_statement_versions' database table.
    """

    __tablename__ = "financial_statement_versions"

    statement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financial_statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
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
    changed_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_reason: Mapped[str] = mapped_column(String(512), nullable=False)
