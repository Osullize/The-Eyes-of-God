"""allow long ai product fit text

Revision ID: 20260704_0010
Revises: 20260704_0009
Create Date: 2026-07-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260704_0010"
down_revision = "20260704_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ai_profile_results",
        "product_fit",
        existing_type=sa.String(length=50),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "ai_profile_results",
        "product_fit",
        existing_type=sa.Text(),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
