"""
Ratio ORM model representation.
"""

from uuid import UUID

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class RatioORM(Base):
    """
    SQLAlchemy mapping for the 'ratios' database table.
    """

    __tablename__ = "ratios"

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    ratio_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    formula: Mapped[str] = mapped_column(String(256), nullable=False)
    line_items_used: Mapped[dict[str, float]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )
    ratio_engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
