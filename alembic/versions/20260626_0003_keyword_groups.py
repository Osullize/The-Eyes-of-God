"""keyword groups

Revision ID: 20260626_0003
Revises: 20260626_0002
Create Date: 2026-06-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260626_0003"
down_revision = "20260626_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "keyword_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("country_terms", sa.Text(), nullable=False),
        sa.Column("keyword_terms", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_keyword_groups_name"),
    )
    op.create_index("ix_keyword_groups_country", "keyword_groups", ["country"], unique=False)
    op.create_index("ix_keyword_groups_is_active", "keyword_groups", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_keyword_groups_is_active", table_name="keyword_groups")
    op.drop_index("ix_keyword_groups_country", table_name="keyword_groups")
    op.drop_table("keyword_groups")
