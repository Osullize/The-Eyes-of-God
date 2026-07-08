"""structured keyword groups

Revision ID: 20260703_0006
Revises: 20260629_0005
Create Date: 2026-07-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260703_0006"
down_revision = "20260629_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("keyword_groups", sa.Column("product_terms", sa.Text(), nullable=False, server_default=""))
    op.add_column("keyword_groups", sa.Column("role_terms", sa.Text(), nullable=False, server_default=""))
    op.add_column("keyword_groups", sa.Column("search_templates", sa.Text(), nullable=False, server_default=""))
    op.alter_column("keyword_groups", "product_terms", server_default=None)
    op.alter_column("keyword_groups", "role_terms", server_default=None)
    op.alter_column("keyword_groups", "search_templates", server_default=None)


def downgrade() -> None:
    op.drop_column("keyword_groups", "search_templates")
    op.drop_column("keyword_groups", "role_terms")
    op.drop_column("keyword_groups", "product_terms")
