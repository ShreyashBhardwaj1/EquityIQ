"""Add workspace_id and country to companies

Revision ID: 6e7ecded3645
Revises: c59e03532a27
Create Date: 2026-07-07 12:54:44.943136

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e7ecded3645"
down_revision: str | Sequence[str] | None = "c59e03532a27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("companies") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.UUID(), nullable=False))
        batch_op.add_column(sa.Column("country", sa.String(length=100), nullable=False))
        batch_op.drop_constraint("uq_companies_ticker_exchange", type_="unique")
        batch_op.create_index(
            "ix_companies_workspace_id", ["workspace_id"], unique=False
        )
        batch_op.create_unique_constraint(
            "uq_companies_workspace_ticker_exchange",
            ["workspace_id", "ticker", "exchange"],
        )
        batch_op.create_foreign_key(
            "fk_companies_workspace_id",
            "workspaces",
            ["workspace_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("companies") as batch_op:
        batch_op.drop_constraint("fk_companies_workspace_id", type_="foreignkey")
        batch_op.drop_constraint(
            "uq_companies_workspace_ticker_exchange", type_="unique"
        )
        batch_op.drop_index("ix_companies_workspace_id")
        batch_op.create_unique_constraint(
            "uq_companies_ticker_exchange", ["ticker", "exchange"]
        )
        batch_op.drop_column("country")
        batch_op.drop_column("workspace_id")
