"""candidate groups

Revision ID: 20260629_0005
Revises: 20260626_0004
Create Date: 2026-06-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260629_0005"
down_revision = "20260626_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("group_type", sa.String(length=50), nullable=False),
        sa.Column("source_task_run_id", sa.Integer(), nullable=True),
        sa.Column("keyword_group_id", sa.Integer(), nullable=True),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("params_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["keyword_group_id"], ["keyword_groups.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_task_run_id"], ["task_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_groups_country", "candidate_groups", ["country"], unique=False)
    op.create_index("ix_candidate_groups_group_type", "candidate_groups", ["group_type"], unique=False)
    op.create_index("ix_candidate_groups_keyword_group_id", "candidate_groups", ["keyword_group_id"], unique=False)
    op.create_index("ix_candidate_groups_source_task_run_id", "candidate_groups", ["source_task_run_id"], unique=False)
    op.create_index("ix_candidate_groups_status", "candidate_groups", ["status"], unique=False)

    op.create_table(
        "candidate_group_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("search_result_id", sa.Integer(), nullable=True),
        sa.Column("source_task_item_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["candidate_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["search_result_id"], ["search_results.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_task_item_id"], ["task_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "domain_id", name="uq_candidate_group_items_group_domain"),
    )
    op.create_index("ix_candidate_group_items_domain_id", "candidate_group_items", ["domain_id"], unique=False)
    op.create_index("ix_candidate_group_items_group_id", "candidate_group_items", ["group_id"], unique=False)
    op.create_index(
        "ix_candidate_group_items_search_result_id",
        "candidate_group_items",
        ["search_result_id"],
        unique=False,
    )
    op.create_index("ix_candidate_group_items_status", "candidate_group_items", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_candidate_group_items_status", table_name="candidate_group_items")
    op.drop_index("ix_candidate_group_items_search_result_id", table_name="candidate_group_items")
    op.drop_index("ix_candidate_group_items_group_id", table_name="candidate_group_items")
    op.drop_index("ix_candidate_group_items_domain_id", table_name="candidate_group_items")
    op.drop_table("candidate_group_items")
    op.drop_index("ix_candidate_groups_status", table_name="candidate_groups")
    op.drop_index("ix_candidate_groups_source_task_run_id", table_name="candidate_groups")
    op.drop_index("ix_candidate_groups_keyword_group_id", table_name="candidate_groups")
    op.drop_index("ix_candidate_groups_group_type", table_name="candidate_groups")
    op.drop_index("ix_candidate_groups_country", table_name="candidate_groups")
    op.drop_table("candidate_groups")
