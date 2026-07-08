"""add ai profile company name

Revision ID: 20260706_0011
Revises: 20260704_0010
Create Date: 2026-07-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260706_0011"
down_revision = "20260704_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_profile_results",
        sa.Column("company_name", sa.Text(), nullable=False, server_default=""),
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            UPDATE ai_profile_results AS result
            SET company_name = COALESCE(
                NULLIF(result.result_json->>'company_name', ''),
                NULLIF(package.payload_json #>> '{company,company_name}', ''),
                NULLIF(domain.display_name, ''),
                domain.domain,
                ''
            )
            FROM profile_packages AS package
            JOIN domains AS domain ON domain.id = package.domain_id
            WHERE package.id = result.profile_package_id
            """
        )
        op.execute(
            """
            UPDATE ai_profile_results
            SET result_json = jsonb_set(result_json::jsonb, '{company_name}', to_jsonb(company_name), true)::json
            WHERE company_name <> ''
              AND COALESCE(result_json->>'company_name', '') = ''
            """
        )
    else:
        op.execute(
            """
            UPDATE ai_profile_results
            SET company_name = COALESCE(
                NULLIF((SELECT domains.display_name FROM domains WHERE domains.id = ai_profile_results.domain_id), ''),
                (SELECT domains.domain FROM domains WHERE domains.id = ai_profile_results.domain_id),
                ''
            )
            """
        )
    op.alter_column("ai_profile_results", "company_name", server_default=None)


def downgrade() -> None:
    op.drop_column("ai_profile_results", "company_name")
