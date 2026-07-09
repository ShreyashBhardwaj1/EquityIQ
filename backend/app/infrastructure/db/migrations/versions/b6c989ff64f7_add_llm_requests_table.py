"""add_llm_requests_table

Revision ID: b6c989ff64f7
Revises: ecb5cb5c0198
Create Date: 2026-07-09 13:25:57.896548

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6c989ff64f7"
down_revision: str | Sequence[str] | None = "ecb5cb5c0198"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "llm_requests",
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("embedding_version", sa.String(length=100), nullable=False),
        sa.Column("parser_version", sa.String(length=50), nullable=False),
        sa.Column("vector_index_version", sa.String(length=50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("retrieval_latency_ms", sa.Float(), nullable=False),
        sa.Column("generation_latency_ms", sa.Float(), nullable=False),
        sa.Column("total_latency_ms", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("grounding_score", sa.Float(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_llm_requests_conversation_id"),
        "llm_requests",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_llm_requests_workspace_id"),
        "llm_requests",
        ["workspace_id"],
        unique=False,
    )

    # Add extended explainability metadata fields to citations table
    op.add_column(
        "citations", sa.Column("rank", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column("citations", sa.Column("semantic_score", sa.Float(), nullable=True))
    op.add_column("citations", sa.Column("keyword_score", sa.Float(), nullable=True))
    op.add_column(
        "citations",
        sa.Column("hybrid_score", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "citations",
        sa.Column(
            "retrieval_method",
            sa.String(length=50),
            nullable=False,
            server_default="hybrid",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("citations", "retrieval_method")
    op.drop_column("citations", "hybrid_score")
    op.drop_column("citations", "keyword_score")
    op.drop_column("citations", "semantic_score")
    op.drop_column("citations", "rank")

    op.drop_index(op.f("ix_llm_requests_workspace_id"), table_name="llm_requests")
    op.drop_index(op.f("ix_llm_requests_conversation_id"), table_name="llm_requests")
    op.drop_table("llm_requests")

    # ### end Alembic commands ###
