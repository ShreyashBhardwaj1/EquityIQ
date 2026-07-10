"""
Financial Health Score ORM model representation.
"""

from uuid import UUID

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class FinancialHealthScoreORM(Base):
    """
    SQLAlchemy mapping for the 'health_scores' database table.
    """

    __tablename__ = "health_scores"

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    category_scores: Mapped[dict[str, float]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )
    weights: Mapped[dict[str, float]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )
    score_explanation: Mapped[list[str]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    ratio_engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
