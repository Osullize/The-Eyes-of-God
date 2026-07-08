from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class Domain(TimestampMixin, Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    website: Mapped[str] = mapped_column(Text, default="", nullable=False)
    display_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    latest_status: Mapped[str] = mapped_column(String(50), default="", nullable=False)

    search_results: Mapped[list[SearchResult]] = relationship(back_populates="domain_record", cascade="all, delete-orphan")
    crawl_results: Mapped[list[CrawlResult]] = relationship(back_populates="domain_record", cascade="all, delete-orphan")
    contacts: Mapped[list[Contact]] = relationship(back_populates="domain_record", cascade="all, delete-orphan")
    profile_packages: Mapped[list[ProfilePackage]] = relationship(
        back_populates="domain_record",
        cascade="all, delete-orphan",
    )
    country_signals: Mapped[list[CountrySignal]] = relationship(
        back_populates="domain_record",
        cascade="all, delete-orphan",
    )
    qualified_leads: Mapped[list[QualifiedLead]] = relationship(
        back_populates="domain_record",
        cascade="all, delete-orphan",
    )
    company_profiles: Mapped[list[CompanyProfile]] = relationship(
        back_populates="domain_record",
        cascade="all, delete-orphan",
    )
    lead_scores: Mapped[list[LeadScore]] = relationship(back_populates="domain_record", cascade="all, delete-orphan")
    ai_profile_results: Mapped[list[AIProfileResult]] = relationship(back_populates="domain_record", cascade="all, delete-orphan")
    task_items: Mapped[list[TaskItem]] = relationship(back_populates="domain_record")
    candidate_group_items: Mapped[list[CandidateGroupItem]] = relationship(back_populates="domain_record")


class SearchResult(Base):
    __tablename__ = "search_results"
    __table_args__ = (
        UniqueConstraint("domain_id", "keyword", "website", "source_file", name="uq_search_result_source_row"),
        Index("ix_search_results_domain_id", "domain_id"),
        Index("ix_search_results_country", "country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    keyword: Mapped[str] = mapped_column(Text, default="", nullable=False)
    title: Mapped[str] = mapped_column(Text, default="", nullable=False)
    website: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_url: Mapped[str] = mapped_column(Text, default="", nullable=False)
    engine: Mapped[str] = mapped_column(Text, default="", nullable=False)
    country: Mapped[str] = mapped_column(Text, default="", nullable=False)
    country_term: Mapped[str] = mapped_column(Text, default="", nullable=False)
    industry: Mapped[str] = mapped_column(Text, default="", nullable=False)
    industry_term: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_keywords: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_countries: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_industries: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_industry_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_file: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="search_results")
    candidate_group_items: Mapped[list[CandidateGroupItem]] = relationship(back_populates="search_result")


class CrawlResult(Base):
    __tablename__ = "crawl_results"
    __table_args__ = (
        UniqueConstraint("domain_id", "source_file", name="uq_crawl_result_source_row"),
        Index("ix_crawl_results_domain_id", "domain_id"),
        Index("ix_crawl_results_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    keyword: Mapped[str] = mapped_column(Text, default="", nullable=False)
    company_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    website: Mapped[str] = mapped_column(Text, default="", nullable=False)
    emails: Mapped[str] = mapped_column(Text, default="", nullable=False)
    phones: Mapped[str] = mapped_column(Text, default="", nullable=False)
    possible_address: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    crawled_pages: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    social_links: Mapped[str] = mapped_column(Text, default="", nullable=False)
    contacts: Mapped[str] = mapped_column(Text, default="", nullable=False)
    page_categories: Mapped[str] = mapped_column(Text, default="", nullable=False)
    country: Mapped[str] = mapped_column(Text, default="", nullable=False)
    industry: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_keywords: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_countries: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_industries: Mapped[str] = mapped_column(Text, default="", nullable=False)
    matched_industry_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_file: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="crawl_results")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("domain_id", "kind", "value", "source", name="uq_contacts_domain_kind_value_source"),
        Index("ix_contacts_domain_id", "domain_id"),
        Index("ix_contacts_kind", "kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="contacts")


class ProfilePackage(TimestampMixin, Base):
    __tablename__ = "profile_packages"
    __table_args__ = (
        Index(
            "uq_profile_packages_content_hash",
            "content_hash",
            unique=True,
            sqlite_where=text("content_hash <> ''"),
            postgresql_where=text("content_hash <> ''"),
        ),
        Index("ix_profile_packages_domain_id", "domain_id"),
        Index("ix_profile_packages_candidate_group_id", "candidate_group_id"),
        Index("ix_profile_packages_crawl_task_run_id", "crawl_task_run_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    candidate_group_id: Mapped[int | None] = mapped_column(ForeignKey("candidate_groups.id", ondelete="SET NULL"), nullable=True)
    crawl_task_run_id: Mapped[int | None] = mapped_column(ForeignKey("task_runs.id", ondelete="SET NULL"), nullable=True)
    crawl_result_id: Mapped[int | None] = mapped_column(ForeignKey("crawl_results.id", ondelete="SET NULL"), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    crawl_status: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    crawl_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="profile_packages")


class CountrySignal(Base):
    __tablename__ = "country_signals"
    __table_args__ = (
        UniqueConstraint("domain_id", "country", "signal_type", "source", name="uq_country_signal_source"),
        Index("ix_country_signals_domain_id", "domain_id"),
        Index("ix_country_signals_country", "country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="country_signals")


class KeywordGroup(TimestampMixin, Base):
    __tablename__ = "keyword_groups"
    __table_args__ = (
        UniqueConstraint("name", name="uq_keyword_groups_name"),
        Index("ix_keyword_groups_country", "country"),
        Index("ix_keyword_groups_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(Text, default="", nullable=False)
    country_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    keyword_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    product_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    role_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    search_templates: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    candidate_groups: Mapped[list[CandidateGroup]] = relationship(back_populates="keyword_group")


class TaskRun(Base):
    __tablename__ = "task_runs"
    __table_args__ = (
        Index("ix_task_runs_task_type", "task_type"),
        Index("ix_task_runs_status", "status"),
        Index("ix_task_runs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    params_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_by: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list[TaskItem]] = relationship(back_populates="task_run", cascade="all, delete-orphan")
    candidate_groups: Mapped[list[CandidateGroup]] = relationship(back_populates="source_task_run")


class TaskItem(TimestampMixin, Base):
    __tablename__ = "task_items"
    __table_args__ = (
        UniqueConstraint("task_run_id", "item_type", "item_key", name="uq_task_items_run_type_key"),
        Index("ix_task_items_task_run_id", "task_run_id"),
        Index("ix_task_items_domain_id", "domain_id"),
        Index("ix_task_items_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_run_id: Mapped[int] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_key: Mapped[str] = mapped_column(Text, nullable=False)
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domains.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task_run: Mapped[TaskRun] = relationship(back_populates="items")
    domain_record: Mapped[Domain | None] = relationship(back_populates="task_items")
    candidate_group_items: Mapped[list[CandidateGroupItem]] = relationship(back_populates="source_task_item")


class CandidateGroup(TimestampMixin, Base):
    __tablename__ = "candidate_groups"
    __table_args__ = (
        Index("ix_candidate_groups_group_type", "group_type"),
        Index("ix_candidate_groups_status", "status"),
        Index("ix_candidate_groups_source_task_run_id", "source_task_run_id"),
        Index("ix_candidate_groups_keyword_group_id", "keyword_group_id"),
        Index("ix_candidate_groups_country", "country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    group_type: Mapped[str] = mapped_column(String(50), default="search_output", nullable=False)
    source_task_run_id: Mapped[int | None] = mapped_column(ForeignKey("task_runs.id", ondelete="SET NULL"), nullable=True)
    keyword_group_id: Mapped[int | None] = mapped_column(ForeignKey("keyword_groups.id", ondelete="SET NULL"), nullable=True)
    country: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    params_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    source_task_run: Mapped[TaskRun | None] = relationship(back_populates="candidate_groups")
    keyword_group: Mapped[KeywordGroup | None] = relationship(back_populates="candidate_groups")
    items: Mapped[list[CandidateGroupItem]] = relationship(back_populates="group", cascade="all, delete-orphan")


class CandidateGroupItem(TimestampMixin, Base):
    __tablename__ = "candidate_group_items"
    __table_args__ = (
        UniqueConstraint("group_id", "domain_id", name="uq_candidate_group_items_group_domain"),
        Index("ix_candidate_group_items_group_id", "group_id"),
        Index("ix_candidate_group_items_domain_id", "domain_id"),
        Index("ix_candidate_group_items_search_result_id", "search_result_id"),
        Index("ix_candidate_group_items_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("candidate_groups.id", ondelete="CASCADE"), nullable=False)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    search_result_id: Mapped[int | None] = mapped_column(ForeignKey("search_results.id", ondelete="SET NULL"), nullable=True)
    source_task_item_id: Mapped[int | None] = mapped_column(ForeignKey("task_items.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    group: Mapped[CandidateGroup] = relationship(back_populates="items")
    domain_record: Mapped[Domain] = relationship(back_populates="candidate_group_items")
    search_result: Mapped[SearchResult | None] = relationship(back_populates="candidate_group_items")
    source_task_item: Mapped[TaskItem | None] = relationship(back_populates="candidate_group_items")


class QualifiedLead(TimestampMixin, Base):
    __tablename__ = "qualified_leads"
    __table_args__ = (
        UniqueConstraint("domain_id", "source", name="uq_qualified_leads_domain_source"),
        Index("ix_qualified_leads_domain_id", "domain_id"),
        Index("ix_qualified_leads_priority", "priority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="new", nullable=False)
    segment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="qualified_leads")


class CompanyProfile(TimestampMixin, Base):
    __tablename__ = "company_profiles"
    __table_args__ = (
        UniqueConstraint("domain_id", "source", name="uq_company_profiles_domain_source"),
        Index("ix_company_profiles_domain_id", "domain_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    business_type: Mapped[str] = mapped_column(Text, default="", nullable=False)
    product_fit: Mapped[str] = mapped_column(Text, default="", nullable=False)
    market_role: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[str] = mapped_column(Text, default="", nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="company_profiles")


class LeadScore(Base):
    __tablename__ = "lead_scores"
    __table_args__ = (
        UniqueConstraint("domain_id", "score_name", "source", name="uq_lead_scores_domain_name_source"),
        Index("ix_lead_scores_domain_id", "domain_id"),
        Index("ix_lead_scores_score_name", "score_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    score_name: Mapped[str] = mapped_column(String(80), nullable=False)
    score_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="lead_scores")


class AIProfileResult(TimestampMixin, Base):
    __tablename__ = "ai_profile_results"
    __table_args__ = (
        UniqueConstraint(
            "profile_package_id",
            "prompt_version",
            "model_provider",
            "model_name",
            name="uq_ai_profile_results_input_prompt_model",
        ),
        Index("ix_ai_profile_results_domain_id", "domain_id"),
        Index("ix_ai_profile_results_profile_package_id", "profile_package_id"),
        Index("ix_ai_profile_results_task_run_id", "task_run_id"),
        Index("ix_ai_profile_results_priority", "customer_priority"),
        Index("ix_ai_profile_results_score_total", "score_total"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    profile_package_id: Mapped[int] = mapped_column(ForeignKey("profile_packages.id", ondelete="CASCADE"), nullable=False)
    task_run_id: Mapped[int | None] = mapped_column(ForeignKey("task_runs.id", ondelete="SET NULL"), nullable=True)
    task_item_id: Mapped[int | None] = mapped_column(ForeignKey("task_items.id", ondelete="SET NULL"), nullable=True)
    model_provider: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    company_name: Mapped[str] = mapped_column(Text, default="", nullable=False)
    profile_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    business_type: Mapped[str] = mapped_column(Text, default="", nullable=False)
    market_role: Mapped[str] = mapped_column(Text, default="", nullable=False)
    product_fit: Mapped[str] = mapped_column(Text, default="", nullable=False)
    customer_priority: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    score_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_breakdown_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evidence_json: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    risk_flags_json: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, default="", nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    raw_response_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)

    domain_record: Mapped[Domain] = relationship(back_populates="ai_profile_results")
