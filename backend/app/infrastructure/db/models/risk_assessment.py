"""
Risk Assessment ORM model representation.
"""

from uuid import UUID

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class RiskAssessmentORM(Base):
    """
    SQLAlchemy mapping for the 'risk_assessments' database table.
    """

    __tablename__ = "risk_assessments"

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_period: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    risk_category: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., 'low', 'moderate', 'severe'
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    supporting_evidence: Mapped[str] = mapped_column(String(1024), nullable=False)
    ratio_engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
