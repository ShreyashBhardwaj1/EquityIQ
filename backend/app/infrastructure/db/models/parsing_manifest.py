"""
ParsingManifest ORM model mapping.
"""

from uuid import UUID

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class ParsingManifestORM(Base):
    """
    SQLAlchemy mapping for the 'parsing_manifests' database table.
    """

    __tablename__ = "parsing_manifests"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False)
    chunk_strategy: Mapped[str] = mapped_column(String(32), nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    overlap: Mapped[int] = mapped_column(Integer, nullable=False)
    parse_duration: Mapped[float] = mapped_column(Float, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    table_count: Mapped[int] = mapped_column(Integer, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
    )
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=False)
