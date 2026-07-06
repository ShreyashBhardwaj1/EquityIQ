"""Add foreign keys to documents table

Revision ID: c59e03532a27
Revises: 3767dcc294d4
Create Date: 2026-07-06 12:44:42.611343

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c59e03532a27"
down_revision: Union[str, Sequence[str], None] = "3767dcc294d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch_alter_table to support SQLite's table recreation workflow
    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "workspace_id", existing_type=sa.UUID(), nullable=False
        )
        batch_op.alter_column(
            "uploaded_by_id", existing_type=sa.UUID(), nullable=False
        )

        batch_op.create_index(
            batch_op.f("ix_documents_uploaded_by_id"),
            ["uploaded_by_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_documents_workspace_id"),
            ["workspace_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_documents_uploaded_by_id",
            "users",
            ["uploaded_by_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_documents_workspace_id",
            "workspaces",
            ["workspace_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_constraint(
            "fk_documents_uploaded_by_id", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_documents_workspace_id", type_="foreignkey"
        )

        batch_op.drop_index("ix_documents_workspace_id")
        batch_op.drop_index("ix_documents_uploaded_by_id")

        batch_op.alter_column(
            "uploaded_by_id", existing_type=sa.UUID(), nullable=True
        )
        batch_op.alter_column(
            "workspace_id", existing_type=sa.UUID(), nullable=True
        )
