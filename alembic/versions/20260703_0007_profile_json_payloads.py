"""profile json payloads

Revision ID: 20260703_0007
Revises: 20260703_0006
Create Date: 2026-07-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260703_0007"
down_revision = "20260703_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profile_packages", sa.Column("candidate_group_id", sa.Integer(), nullable=True))
    op.add_column("profile_packages", sa.Column("crawl_task_run_id", sa.Integer(), nullable=True))
    op.add_column("profile_packages", sa.Column("crawl_result_id", sa.Integer(), nullable=True))
    op.add_column("profile_packages", sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("profile_packages", sa.Column("content_hash", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("profile_packages", sa.Column("source_mtime", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        "fk_profile_packages_candidate_group_id_candidate_groups",
        "profile_packages",
        "candidate_groups",
        ["candidate_group_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_profile_packages_crawl_task_run_id_task_runs",
        "profile_packages",
        "task_runs",
        ["crawl_task_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_profile_packages_crawl_result_id_crawl_results",
        "profile_packages",
        "crawl_results",
        ["crawl_result_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index("ix_profile_packages_candidate_group_id", "profile_packages", ["candidate_group_id"], unique=False)
    op.create_index("ix_profile_packages_crawl_task_run_id", "profile_packages", ["crawl_task_run_id"], unique=False)

    op.alter_column("profile_packages", "payload_json", server_default=None)
    op.alter_column("profile_packages", "content_hash", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_profile_packages_crawl_task_run_id", table_name="profile_packages")
    op.drop_index("ix_profile_packages_candidate_group_id", table_name="profile_packages")
    op.drop_constraint("fk_profile_packages_crawl_result_id_crawl_results", "profile_packages", type_="foreignkey")
    op.drop_constraint("fk_profile_packages_crawl_task_run_id_task_runs", "profile_packages", type_="foreignkey")
    op.drop_constraint("fk_profile_packages_candidate_group_id_candidate_groups", "profile_packages", type_="foreignkey")
    op.drop_column("profile_packages", "source_mtime")
    op.drop_column("profile_packages", "content_hash")
    op.drop_column("profile_packages", "payload_json")
    op.drop_column("profile_packages", "crawl_result_id")
    op.drop_column("profile_packages", "crawl_task_run_id")
    op.drop_column("profile_packages", "candidate_group_id")
