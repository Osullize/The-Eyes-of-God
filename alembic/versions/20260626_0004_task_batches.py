"""task batches

Revision ID: 20260626_0004
Revises: 20260626_0003
Create Date: 2026-06-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260626_0004"
down_revision = "20260626_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("params_json", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_runs_created_at", "task_runs", ["created_at"], unique=False)
    op.create_index("ix_task_runs_status", "task_runs", ["status"], unique=False)
    op.create_index("ix_task_runs_task_type", "task_runs", ["task_type"], unique=False)

    op.create_table(
        "task_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_run_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("item_key", sa.Text(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_run_id", "item_type", "item_key", name="uq_task_items_run_type_key"),
    )
    op.create_index("ix_task_items_domain_id", "task_items", ["domain_id"], unique=False)
    op.create_index("ix_task_items_status", "task_items", ["status"], unique=False)
    op.create_index("ix_task_items_task_run_id", "task_items", ["task_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_task_items_task_run_id", table_name="task_items")
    op.drop_index("ix_task_items_status", table_name="task_items")
    op.drop_index("ix_task_items_domain_id", table_name="task_items")
    op.drop_table("task_items")
    op.drop_index("ix_task_runs_task_type", table_name="task_runs")
    op.drop_index("ix_task_runs_status", table_name="task_runs")
    op.drop_index("ix_task_runs_created_at", table_name="task_runs")
    op.drop_table("task_runs")
