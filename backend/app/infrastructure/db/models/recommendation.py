"""
Recommendation and RecommendationPolicy ORM model representation.
"""

from uuid import UUID

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class RecommendationPolicyORM(Base):
    """
    SQLAlchemy mapping for the 'recommendation_policies' database table.
    """

    __tablename__ = "recommendation_policies"

    policy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    health_score_thresholds: Mapped[dict[str, float]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )
    max_severe_risks_allowed: Mapped[dict[str, int]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
    )
    requires_positive_growth: Mapped[list[str]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RecommendationORM(Base):
    """
    SQLAlchemy mapping for the 'recommendations' database table.
    """

    __tablename__ = "recommendations"

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., 'buy', 'hold', 'sell'
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    rules_applied: Mapped[list[str]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    recommendation_policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
