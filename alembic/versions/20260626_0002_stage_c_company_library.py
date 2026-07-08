"""stage c company library

Revision ID: 20260626_0002
Revises: 20260625_0001
Create Date: 2026-06-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260626_0002"
down_revision = "20260625_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("business_type", sa.Text(), nullable=False),
        sa.Column("product_fit", sa.Text(), nullable=False),
        sa.Column("market_role", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "source", name="uq_company_profiles_domain_source"),
    )
    op.create_index("ix_company_profiles_domain_id", "company_profiles", ["domain_id"], unique=False)

    op.create_table(
        "qualified_leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("segment", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "source", name="uq_qualified_leads_domain_source"),
    )
    op.create_index("ix_qualified_leads_domain_id", "qualified_leads", ["domain_id"], unique=False)
    op.create_index("ix_qualified_leads_priority", "qualified_leads", ["priority"], unique=False)

    op.create_table(
        "lead_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("score_name", sa.String(length=80), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "score_name", "source", name="uq_lead_scores_domain_name_source"),
    )
    op.create_index("ix_lead_scores_domain_id", "lead_scores", ["domain_id"], unique=False)
    op.create_index("ix_lead_scores_score_name", "lead_scores", ["score_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lead_scores_score_name", table_name="lead_scores")
    op.drop_index("ix_lead_scores_domain_id", table_name="lead_scores")
    op.drop_table("lead_scores")
    op.drop_index("ix_qualified_leads_priority", table_name="qualified_leads")
    op.drop_index("ix_qualified_leads_domain_id", table_name="qualified_leads")
    op.drop_table("qualified_leads")
    op.drop_index("ix_company_profiles_domain_id", table_name="company_profiles")
    op.drop_table("company_profiles")
