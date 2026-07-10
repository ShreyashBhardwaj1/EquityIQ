"""
Recommendation History/Audit ORM model representation.
"""

from uuid import UUID

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class RecommendationHistoryORM(Base):
    """
    SQLAlchemy mapping for the 'recommendation_histories' database table.
    """

    __tablename__ = "recommendation_histories"

    recommendation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning_steps: Mapped[list[str]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    triggered_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
