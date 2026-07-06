"""
Document ORM model representation.
"""

from uuid import UUID

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class DocumentORM(Base):
    """
    SQLAlchemy mapping for the 'documents' database table.
    """

    __tablename__ = "documents"

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    uploaded_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    doc_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # e.g., '10K', '10Q', 'news'
    fiscal_period: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # e.g., 'Q1-2024', 'FY-2024'
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    parsing_status: Mapped[str] = mapped_column(
        String(20), index=True, default="pending", nullable=False
    )  # e.g., 'pending', 'processing', 'completed', 'failed'
    parsing_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
