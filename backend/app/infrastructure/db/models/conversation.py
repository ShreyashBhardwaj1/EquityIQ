"""
SQLAlchemy ORM models for conversations, messages, and citations.
"""

from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class ConversationORM(Base):
    """
    SQLAlchemy mapping for the 'conversations' database table.
    """

    __tablename__ = "conversations"

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    messages: Mapped[list["ConversationMessageORM"]] = relationship(
        "ConversationMessageORM",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessageORM.created_at",
    )


class ConversationMessageORM(Base):
    """
    SQLAlchemy mapping for the 'conversation_messages' database table.
    """

    __tablename__ = "conversation_messages"

    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    conversation: Mapped[ConversationORM] = relationship(
        "ConversationORM", back_populates="messages"
    )
    citations: Mapped[list["CitationORM"]] = relationship(
        "CitationORM",
        back_populates="message",
        cascade="all, delete-orphan",
    )


class CitationORM(Base):
    """
    SQLAlchemy mapping for the 'citations' database table.
    """

    __tablename__ = "citations"

    message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_name: Mapped[str] = mapped_column(String(256), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section_heading: Mapped[str | None] = mapped_column(String(256), nullable=True)
    snippet_preview: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    keyword_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hybrid_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    retrieval_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="hybrid"
    )

    # Relationships
    message: Mapped[ConversationMessageORM] = relationship(
        "ConversationMessageORM", back_populates="citations"
    )


class LLMRequestORM(Base):
    """
    SQLAlchemy mapping for the 'llm_requests' database table tracking execution telemetry.
    """

    __tablename__ = "llm_requests"

    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(100), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(50), nullable=False)
    vector_index_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    retrieval_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    generation_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    total_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    grounding_score: Mapped[float] = mapped_column(Float, nullable=False)
