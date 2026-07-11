"""Add financial report tables

Revision ID: f1a2b3c4d5e6
Revises: 89ee9532b883
Create Date: 2026-07-11 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "89ee9532b883"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema — create financial_reports and financial_report_versions tables."""
    op.create_table(
        "financial_reports",
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("fiscal_period", sa.String(length=10), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="PENDING"
        ),
        sa.Column("generated_by", sa.UUID(), nullable=False),
        sa.Column(
            "model_name", sa.String(length=100), nullable=False, server_default=""
        ),
        sa.Column(
            "prompt_version",
            sa.String(length=32),
            nullable=False,
            server_default="1.0.0",
        ),
        sa.Column(
            "report_template_version",
            sa.String(length=32),
            nullable=False,
            server_default="1.0.0",
        ),
        sa.Column(
            "financial_engine_version",
            sa.String(length=32),
            nullable=False,
            server_default="1.0.0",
        ),
        sa.Column(
            "rag_version", sa.String(length=32), nullable=False, server_default="1.0.0"
        ),
        sa.Column(
            "embedding_version",
            sa.String(length=100),
            nullable=False,
            server_default="all-MiniLM-L6-v2",
        ),
        sa.Column(
            "generation_duration", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_financial_reports_company_id"),
        "financial_reports",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_reports_workspace_id"),
        "financial_reports",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_reports_status"),
        "financial_reports",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_reports_fiscal_period"),
        "financial_reports",
        ["fiscal_period"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_reports_celery_task_id"),
        "financial_reports",
        ["celery_task_id"],
        unique=False,
    )

    op.create_table(
        "financial_report_versions",
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("changed_by_id", sa.UUID(), nullable=False),
        sa.Column("change_reason", sa.String(length=500), nullable=True),
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
            ["report_id"], ["financial_reports.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_financial_report_versions_report_id"),
        "financial_report_versions",
        ["report_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema — drop financial report tables."""
    op.drop_index(
        op.f("ix_financial_report_versions_report_id"),
        table_name="financial_report_versions",
    )
    op.drop_table("financial_report_versions")
    op.drop_index(
        op.f("ix_financial_reports_celery_task_id"),
        table_name="financial_reports",
    )
    op.drop_index(
        op.f("ix_financial_reports_fiscal_period"),
        table_name="financial_reports",
    )
    op.drop_index(
        op.f("ix_financial_reports_status"),
        table_name="financial_reports",
    )
    op.drop_index(
        op.f("ix_financial_reports_workspace_id"),
        table_name="financial_reports",
    )
    op.drop_index(
        op.f("ix_financial_reports_company_id"),
        table_name="financial_reports",
    )
    op.drop_table("financial_reports")
