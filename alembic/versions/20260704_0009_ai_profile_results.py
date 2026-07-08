"""ai profile results

Revision ID: 20260704_0009
Revises: 20260703_0008
Create Date: 2026-07-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260704_0009"
down_revision = "20260703_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_profile_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("profile_package_id", sa.Integer(), nullable=False),
        sa.Column("task_run_id", sa.Integer(), nullable=True),
        sa.Column("task_item_id", sa.Integer(), nullable=True),
        sa.Column("model_provider", sa.String(length=80), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=120), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("profile_summary", sa.Text(), nullable=False),
        sa.Column("business_type", sa.Text(), nullable=False),
        sa.Column("market_role", sa.Text(), nullable=False),
        sa.Column("product_fit", sa.String(length=50), nullable=False),
        sa.Column("customer_priority", sa.String(length=50), nullable=False),
        sa.Column("score_total", sa.Float(), nullable=False),
        sa.Column("score_breakdown_json", sa.JSON(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("risk_flags_json", sa.JSON(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("raw_response_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_package_id"], ["profile_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_item_id"], ["task_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_package_id",
            "prompt_version",
            "model_provider",
            "model_name",
            name="uq_ai_profile_results_input_prompt_model",
        ),
    )
    op.create_index("ix_ai_profile_results_domain_id", "ai_profile_results", ["domain_id"], unique=False)
    op.create_index("ix_ai_profile_results_profile_package_id", "ai_profile_results", ["profile_package_id"], unique=False)
    op.create_index("ix_ai_profile_results_task_run_id", "ai_profile_results", ["task_run_id"], unique=False)
    op.create_index("ix_ai_profile_results_priority", "ai_profile_results", ["customer_priority"], unique=False)
    op.create_index("ix_ai_profile_results_score_total", "ai_profile_results", ["score_total"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_profile_results_score_total", table_name="ai_profile_results")
    op.drop_index("ix_ai_profile_results_priority", table_name="ai_profile_results")
    op.drop_index("ix_ai_profile_results_task_run_id", table_name="ai_profile_results")
    op.drop_index("ix_ai_profile_results_profile_package_id", table_name="ai_profile_results")
    op.drop_index("ix_ai_profile_results_domain_id", table_name="ai_profile_results")
    op.drop_table("ai_profile_results")
