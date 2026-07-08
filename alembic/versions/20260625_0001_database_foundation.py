"""database foundation

Revision ID: 20260625_0001
Revises:
Create Date: 2026-06-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260625_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("website", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("latest_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_domains_domain"), "domains", ["domain"], unique=True)

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "kind", "value", "source", name="uq_contacts_domain_kind_value_source"),
    )
    op.create_index("ix_contacts_domain_id", "contacts", ["domain_id"], unique=False)
    op.create_index("ix_contacts_kind", "contacts", ["kind"], unique=False)

    op.create_table(
        "country_signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("signal_type", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "country", "signal_type", "source", name="uq_country_signal_source"),
    )
    op.create_index("ix_country_signals_country", "country_signals", ["country"], unique=False)
    op.create_index("ix_country_signals_domain_id", "country_signals", ["domain_id"], unique=False)

    op.create_table(
        "crawl_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("website", sa.Text(), nullable=False),
        sa.Column("emails", sa.Text(), nullable=False),
        sa.Column("phones", sa.Text(), nullable=False),
        sa.Column("possible_address", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("crawled_pages", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("social_links", sa.Text(), nullable=False),
        sa.Column("contacts", sa.Text(), nullable=False),
        sa.Column("page_categories", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=False),
        sa.Column("matched_keywords", sa.Text(), nullable=False),
        sa.Column("matched_countries", sa.Text(), nullable=False),
        sa.Column("matched_industries", sa.Text(), nullable=False),
        sa.Column("matched_industry_terms", sa.Text(), nullable=False),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "source_file", name="uq_crawl_result_source_row"),
    )
    op.create_index("ix_crawl_results_domain_id", "crawl_results", ["domain_id"], unique=False)
    op.create_index("ix_crawl_results_status", "crawl_results", ["status"], unique=False)

    op.create_table(
        "profile_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.String(length=50), nullable=False),
        sa.Column("crawl_status", sa.String(length=50), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("crawl_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_dir", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path", name="uq_profile_packages_path"),
    )
    op.create_index("ix_profile_packages_domain_id", "profile_packages", ["domain_id"], unique=False)

    op.create_table(
        "search_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("website", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("engine", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("country_term", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=False),
        sa.Column("industry_term", sa.Text(), nullable=False),
        sa.Column("matched_keywords", sa.Text(), nullable=False),
        sa.Column("matched_countries", sa.Text(), nullable=False),
        sa.Column("matched_industries", sa.Text(), nullable=False),
        sa.Column("matched_industry_terms", sa.Text(), nullable=False),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "keyword", "website", "source_file", name="uq_search_result_source_row"),
    )
    op.create_index("ix_search_results_country", "search_results", ["country"], unique=False)
    op.create_index("ix_search_results_domain_id", "search_results", ["domain_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_search_results_domain_id", table_name="search_results")
    op.drop_index("ix_search_results_country", table_name="search_results")
    op.drop_table("search_results")
    op.drop_index("ix_profile_packages_domain_id", table_name="profile_packages")
    op.drop_table("profile_packages")
    op.drop_index("ix_crawl_results_status", table_name="crawl_results")
    op.drop_index("ix_crawl_results_domain_id", table_name="crawl_results")
    op.drop_table("crawl_results")
    op.drop_index("ix_country_signals_domain_id", table_name="country_signals")
    op.drop_index("ix_country_signals_country", table_name="country_signals")
    op.drop_table("country_signals")
    op.drop_index("ix_contacts_kind", table_name="contacts")
    op.drop_index("ix_contacts_domain_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_index(op.f("ix_domains_domain"), table_name="domains")
    op.drop_table("domains")
