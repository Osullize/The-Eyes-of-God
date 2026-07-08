from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from database.models import (
    AIProfileResult,
    CandidateGroup,
    CompanyProfile,
    Contact,
    CountrySignal,
    CrawlResult,
    Domain,
    LeadScore,
    ProfilePackage,
    QualifiedLead,
    SearchResult,
    TaskRun,
)


def get_database_stats(session: Session) -> dict[str, int]:
    return {
        "domains": _count(session, Domain),
        "search_results": _count(session, SearchResult),
        "crawl_results": _count(session, CrawlResult),
        "contacts": _count(session, Contact),
        "profile_packages": _count(session, ProfilePackage),
        "country_signals": _count(session, CountrySignal),
    }


def get_company_library_stats(session: Session) -> dict[str, int]:
    return {
        "stage_a_companies": count_distinct_domains_with(session, SearchResult),
        "stage_b_companies": count_distinct_domains_with(session, CrawlResult),
        "stage_c_companies": count_distinct_domains_with(session, QualifiedLead),
        "search_results": _count(session, SearchResult),
        "crawl_results": _count(session, CrawlResult),
        "qualified_leads": _count(session, QualifiedLead),
    }


def list_stage_a_companies(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    country: str = "",
) -> dict[str, Any]:
    stmt = select(Domain).where(exists().where(SearchResult.domain_id == Domain.id))
    stmt = apply_domain_filters(stmt, q=q, country=country)
    domains, total, safe_limit, safe_offset = paginate_domains(session, stmt, limit=limit, offset=offset)
    return {
        "items": [serialize_stage_a_company(session, domain) for domain in domains],
        "count": len(domains),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def list_stage_b_companies(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    country: str = "",
    status: str = "",
) -> dict[str, Any]:
    stmt = select(Domain).where(exists().where(CrawlResult.domain_id == Domain.id))
    stmt = apply_domain_filters(stmt, q=q, country=country)
    status_text = status.strip()
    if status_text:
        stmt = stmt.where(exists().where(CrawlResult.domain_id == Domain.id, CrawlResult.status == status_text))
    domains, total, safe_limit, safe_offset = paginate_domains(session, stmt, limit=limit, offset=offset)
    return {
        "items": [serialize_stage_b_company(session, domain) for domain in domains],
        "count": len(domains),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def list_stage_c_companies(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    country: str = "",
) -> dict[str, Any]:
    stmt = select(Domain).where(exists().where(QualifiedLead.domain_id == Domain.id))
    stmt = apply_domain_filters(stmt, q=q, country=country)
    domains, total, safe_limit, safe_offset = paginate_domains(session, stmt, limit=limit, offset=offset)
    return {
        "items": [serialize_stage_c_company(session, domain) for domain in domains],
        "count": len(domains),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def list_profile_source_groups(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)
    stmt = (
        select(ProfilePackage.crawl_task_run_id)
        .where(ProfilePackage.crawl_task_run_id.is_not(None))
        .group_by(ProfilePackage.crawl_task_run_id)
        .order_by(func.max(ProfilePackage.updated_at).desc(), ProfilePackage.crawl_task_run_id.desc())
    )
    query_text = q.strip()
    if query_text:
        pattern = f"%{query_text}%"
        stmt = stmt.where(
            or_(
                exists().where(TaskRun.id == ProfilePackage.crawl_task_run_id, TaskRun.name.ilike(pattern)),
                exists().where(Domain.id == ProfilePackage.domain_id, Domain.domain.ilike(pattern)),
            )
        )
    group_ids = [int(group_id) for group_id in session.scalars(stmt).all() if group_id is not None]
    paged_group_ids = group_ids[safe_offset : safe_offset + safe_limit]
    return {
        "items": [serialize_profile_source_group(session, group_id) for group_id in paged_group_ids],
        "count": len(paged_group_ids),
        "total": len(group_ids),
        "limit": safe_limit,
        "offset": safe_offset,
    }


def get_profile_source_group(session: Session, crawl_task_run_id: int) -> dict[str, Any] | None:
    exists_package = session.scalar(
        select(ProfilePackage.id).where(ProfilePackage.crawl_task_run_id == crawl_task_run_id).limit(1)
    )
    if exists_package is None:
        return None
    return serialize_profile_source_group(session, crawl_task_run_id)


def list_domains(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    country: str = "",
    status: str = "",
) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)
    stmt = select(Domain)

    query_text = q.strip()
    if query_text:
        pattern = f"%{query_text}%"
        stmt = stmt.where(
            or_(
                Domain.domain.ilike(pattern),
                Domain.website.ilike(pattern),
                Domain.display_name.ilike(pattern),
                Domain.description.ilike(pattern),
            )
        )

    country_text = country.strip()
    if country_text:
        country_pattern = f"%{country_text}%"
        stmt = stmt.where(
            exists().where(
                CountrySignal.domain_id == Domain.id,
                CountrySignal.country.ilike(country_pattern),
            )
        )

    status_text = status.strip()
    if status_text:
        stmt = stmt.where(Domain.latest_status == status_text)

    total = int(session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    paged_stmt = stmt.order_by(Domain.domain).offset(safe_offset).limit(safe_limit)
    domains = session.scalars(paged_stmt).all()
    return {
        "items": [serialize_domain(domain) for domain in domains],
        "count": len(domains),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def list_raw_domains(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    status: str = "",
) -> dict[str, Any]:
    stmt = select(Domain)
    query_text = q.strip()
    if query_text:
        pattern = f"%{query_text}%"
        stmt = stmt.where(
            or_(
                Domain.domain.ilike(pattern),
                Domain.website.ilike(pattern),
                Domain.display_name.ilike(pattern),
                Domain.description.ilike(pattern),
            )
        )

    status_text = status.strip()
    if status_text:
        stmt = stmt.where(Domain.latest_status == status_text)

    return paginate_raw_rows(session, stmt, Domain, serialize_domain, limit=limit, offset=offset)


def list_raw_search_results(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    country: str = "",
    engine: str = "",
    keyword: str = "",
) -> dict[str, Any]:
    stmt = select(SearchResult).join(SearchResult.domain_record)
    query_text = q.strip()
    if query_text:
        pattern = f"%{query_text}%"
        stmt = stmt.where(
            or_(
                Domain.domain.ilike(pattern),
                SearchResult.keyword.ilike(pattern),
                SearchResult.title.ilike(pattern),
                SearchResult.website.ilike(pattern),
                SearchResult.source_url.ilike(pattern),
                SearchResult.engine.ilike(pattern),
                SearchResult.country.ilike(pattern),
                SearchResult.industry.ilike(pattern),
                SearchResult.source_file.ilike(pattern),
            )
        )

    country_text = country.strip()
    if country_text:
        stmt = stmt.where(SearchResult.country.ilike(f"%{country_text}%"))

    engine_text = engine.strip()
    if engine_text:
        stmt = stmt.where(SearchResult.engine.ilike(f"%{engine_text}%"))

    keyword_text = keyword.strip()
    if keyword_text:
        stmt = stmt.where(SearchResult.keyword.ilike(f"%{keyword_text}%"))

    return paginate_raw_rows(session, stmt, SearchResult, serialize_raw_search_result, limit=limit, offset=offset)


def list_raw_crawl_results(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    country: str = "",
    status: str = "",
    keyword: str = "",
) -> dict[str, Any]:
    stmt = select(CrawlResult).join(CrawlResult.domain_record)
    query_text = q.strip()
    if query_text:
        pattern = f"%{query_text}%"
        stmt = stmt.where(
            or_(
                Domain.domain.ilike(pattern),
                CrawlResult.keyword.ilike(pattern),
                CrawlResult.company_name.ilike(pattern),
                CrawlResult.website.ilike(pattern),
                CrawlResult.emails.ilike(pattern),
                CrawlResult.phones.ilike(pattern),
                CrawlResult.possible_address.ilike(pattern),
                CrawlResult.description.ilike(pattern),
                CrawlResult.country.ilike(pattern),
                CrawlResult.industry.ilike(pattern),
                CrawlResult.source_file.ilike(pattern),
            )
        )

    country_text = country.strip()
    if country_text:
        stmt = stmt.where(CrawlResult.country.ilike(f"%{country_text}%"))

    status_text = status.strip()
    if status_text:
        stmt = stmt.where(CrawlResult.status == status_text)

    keyword_text = keyword.strip()
    if keyword_text:
        stmt = stmt.where(CrawlResult.keyword.ilike(f"%{keyword_text}%"))

    return paginate_raw_rows(session, stmt, CrawlResult, serialize_raw_crawl_result, limit=limit, offset=offset)


def list_raw_ai_profile_results(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    status: str = "",
    priority: str = "",
    model_name: str = "",
    prompt_version: str = "",
) -> dict[str, Any]:
    stmt = select(AIProfileResult).join(AIProfileResult.domain_record)
    query_text = q.strip()
    if query_text:
        pattern = f"%{query_text}%"
        stmt = stmt.where(
            or_(
                Domain.domain.ilike(pattern),
                Domain.display_name.ilike(pattern),
                AIProfileResult.company_name.ilike(pattern),
                AIProfileResult.profile_summary.ilike(pattern),
                AIProfileResult.business_type.ilike(pattern),
                AIProfileResult.market_role.ilike(pattern),
                AIProfileResult.product_fit.ilike(pattern),
                AIProfileResult.recommended_action.ilike(pattern),
                AIProfileResult.model_provider.ilike(pattern),
                AIProfileResult.model_name.ilike(pattern),
                AIProfileResult.prompt_version.ilike(pattern),
                exists().where(CountrySignal.domain_id == AIProfileResult.domain_id, CountrySignal.country.ilike(pattern)),
            )
        )

    status_text = status.strip()
    if status_text:
        stmt = stmt.where(AIProfileResult.status == status_text)

    priority_text = priority.strip()
    if priority_text:
        stmt = stmt.where(AIProfileResult.customer_priority.ilike(f"%{priority_text}%"))

    model_text = model_name.strip()
    if model_text:
        stmt = stmt.where(AIProfileResult.model_name.ilike(f"%{model_text}%"))

    prompt_text = prompt_version.strip()
    if prompt_text:
        stmt = stmt.where(AIProfileResult.prompt_version.ilike(f"%{prompt_text}%"))

    return paginate_raw_rows(
        session,
        stmt,
        AIProfileResult,
        lambda result: serialize_raw_ai_profile_result(
            result,
            country=", ".join(countries_for_domain(session, result.domain_id)),
            contacts=contacts_for_domain(session, result.domain_id),
        ),
        limit=limit,
        offset=offset,
        max_limit=500,
    )


def get_domain_detail(session: Session, domain_name: str) -> dict[str, Any] | None:
    domain = session.scalar(select(Domain).where(Domain.domain == domain_name))
    if domain is None:
        return None

    contacts = session.scalars(
        select(Contact)
        .where(Contact.domain_id == domain.id)
        .order_by(Contact.kind, Contact.value, Contact.source)
    ).all()
    profile_packages = session.scalars(
        select(ProfilePackage)
        .where(ProfilePackage.domain_id == domain.id)
        .order_by(ProfilePackage.updated_at.desc(), ProfilePackage.id.desc())
    ).all()
    country_signals = session.scalars(
        select(CountrySignal)
        .where(CountrySignal.domain_id == domain.id)
        .order_by(CountrySignal.confidence.desc(), CountrySignal.country, CountrySignal.signal_type)
    ).all()

    return {
        "domain": serialize_domain(domain),
        "contacts": [serialize_contact(contact) for contact in contacts],
        "profile_packages": [serialize_profile_package(profile) for profile in profile_packages],
        "country_signals": [serialize_country_signal(signal) for signal in country_signals],
    }


def serialize_domain(domain: Domain) -> dict[str, Any]:
    return {
        "id": domain.id,
        "domain": domain.domain,
        "website": domain.website,
        "display_name": domain.display_name,
        "description": domain.description,
        "latest_status": domain.latest_status,
        "created_at": _isoformat(domain.created_at),
        "updated_at": _isoformat(domain.updated_at),
    }


def serialize_contact(contact: Contact) -> dict[str, Any]:
    return {
        "id": contact.id,
        "kind": contact.kind,
        "value": contact.value,
        "label": contact.label,
        "source": contact.source,
        "created_at": _isoformat(contact.created_at),
    }


def serialize_profile_package(profile: ProfilePackage) -> dict[str, Any]:
    return {
        "id": profile.id,
        "schema_version": profile.schema_version,
        "crawl_status": profile.crawl_status,
        "page_count": profile.page_count,
        "crawl_time": _isoformat(profile.crawl_time),
        "candidate_group_id": profile.candidate_group_id,
        "crawl_task_run_id": profile.crawl_task_run_id,
        "crawl_result_id": profile.crawl_result_id,
        "content_hash": profile.content_hash,
        "payload_stored": bool(profile.payload_json),
        "created_at": _isoformat(profile.created_at),
        "updated_at": _isoformat(profile.updated_at),
    }


def serialize_country_signal(signal: CountrySignal) -> dict[str, Any]:
    return {
        "id": signal.id,
        "country": signal.country,
        "signal_type": signal.signal_type,
        "confidence": signal.confidence,
        "evidence": signal.evidence,
        "source": signal.source,
        "created_at": _isoformat(signal.created_at),
    }


def serialize_search_result(result: SearchResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "keyword": result.keyword,
        "title": result.title,
        "website": result.website,
        "source_url": result.source_url,
        "engine": result.engine,
        "country": result.country,
        "industry": result.industry,
        "source_file": result.source_file,
        "created_at": _isoformat(result.created_at),
    }


def serialize_raw_search_result(result: SearchResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "domain_id": result.domain_id,
        "domain": result.domain_record.domain,
        "keyword": result.keyword,
        "title": result.title,
        "website": result.website,
        "source_url": result.source_url,
        "engine": result.engine,
        "country": result.country,
        "country_term": result.country_term,
        "industry": result.industry,
        "industry_term": result.industry_term,
        "matched_keywords": result.matched_keywords,
        "matched_countries": result.matched_countries,
        "matched_industries": result.matched_industries,
        "matched_industry_terms": result.matched_industry_terms,
        "source_file": result.source_file,
        "created_at": _isoformat(result.created_at),
    }


def serialize_crawl_result(result: CrawlResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "company_name": result.company_name,
        "website": result.website,
        "status": result.status,
        "description": result.description,
        "possible_address": result.possible_address,
        "country": result.country,
        "industry": result.industry,
        "source_file": result.source_file,
        "created_at": _isoformat(result.created_at),
    }


def serialize_raw_crawl_result(result: CrawlResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "domain_id": result.domain_id,
        "domain": result.domain_record.domain,
        "keyword": result.keyword,
        "company_name": result.company_name,
        "website": result.website,
        "emails": result.emails,
        "phones": result.phones,
        "possible_address": result.possible_address,
        "description": result.description,
        "crawled_pages": result.crawled_pages,
        "status": result.status,
        "error": result.error,
        "social_links": result.social_links,
        "contacts": result.contacts,
        "page_categories": result.page_categories,
        "country": result.country,
        "industry": result.industry,
        "matched_keywords": result.matched_keywords,
        "matched_countries": result.matched_countries,
        "matched_industries": result.matched_industries,
        "matched_industry_terms": result.matched_industry_terms,
        "source_file": result.source_file,
        "created_at": _isoformat(result.created_at),
    }


def serialize_raw_ai_profile_result(
    result: AIProfileResult,
    *,
    country: str = "",
    contacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": result.id,
        "domain_id": result.domain_id,
        "domain": result.domain_record.domain,
        "company_name": result.company_name,
        "country": country,
        "contacts": contacts or [],
        "profile_package_id": result.profile_package_id,
        "task_run_id": result.task_run_id,
        "task_item_id": result.task_item_id,
        "model_provider": result.model_provider,
        "model_name": result.model_name,
        "prompt_version": result.prompt_version,
        "input_hash": result.input_hash,
        "profile_summary": result.profile_summary,
        "business_type": result.business_type,
        "market_role": result.market_role,
        "product_fit": result.product_fit,
        "customer_priority": result.customer_priority,
        "score_total": result.score_total,
        "score_breakdown_json": result.score_breakdown_json,
        "evidence_json": result.evidence_json,
        "risk_flags_json": result.risk_flags_json,
        "recommended_action": result.recommended_action,
        "status": result.status,
        "error": result.error,
        "created_at": _isoformat(result.created_at),
        "updated_at": _isoformat(result.updated_at),
    }


def serialize_qualified_lead(lead: QualifiedLead) -> dict[str, Any]:
    return {
        "id": lead.id,
        "priority": lead.priority,
        "status": lead.status,
        "segment": lead.segment,
        "source": lead.source,
        "notes": lead.notes,
        "created_at": _isoformat(lead.created_at),
        "updated_at": _isoformat(lead.updated_at),
    }


def serialize_company_profile(profile: CompanyProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "business_type": profile.business_type,
        "product_fit": profile.product_fit,
        "market_role": profile.market_role,
        "summary": profile.summary,
        "evidence": profile.evidence,
        "source": profile.source,
        "created_at": _isoformat(profile.created_at),
        "updated_at": _isoformat(profile.updated_at),
    }


def serialize_lead_score(score: LeadScore) -> dict[str, Any]:
    return {
        "id": score.id,
        "score_name": score.score_name,
        "score_value": score.score_value,
        "reason": score.reason,
        "source": score.source,
        "created_at": _isoformat(score.created_at),
    }


def serialize_stage_a_company(session: Session, domain: Domain) -> dict[str, Any]:
    latest_search = session.scalars(
        select(SearchResult).where(SearchResult.domain_id == domain.id).order_by(SearchResult.created_at.desc())
    ).first()
    return {
        "domain": serialize_domain(domain),
        "search_result_count": count_rows_for_domain(session, SearchResult, domain.id),
        "latest_search": serialize_search_result(latest_search) if latest_search else None,
        "countries": countries_for_domain(session, domain.id),
    }


def serialize_stage_b_company(session: Session, domain: Domain) -> dict[str, Any]:
    latest_crawl = session.scalars(
        select(CrawlResult).where(CrawlResult.domain_id == domain.id).order_by(CrawlResult.created_at.desc())
    ).first()
    return {
        "domain": serialize_domain(domain),
        "latest_crawl": serialize_crawl_result(latest_crawl) if latest_crawl else None,
        "contact_count": count_rows_for_domain(session, Contact, domain.id),
        "profile_package_count": count_rows_for_domain(session, ProfilePackage, domain.id),
        "countries": countries_for_domain(session, domain.id),
    }


def serialize_stage_c_company(session: Session, domain: Domain) -> dict[str, Any]:
    lead = session.scalars(
        select(QualifiedLead).where(QualifiedLead.domain_id == domain.id).order_by(QualifiedLead.updated_at.desc())
    ).first()
    profile = session.scalars(
        select(CompanyProfile).where(CompanyProfile.domain_id == domain.id).order_by(CompanyProfile.updated_at.desc())
    ).first()
    scores = session.scalars(
        select(LeadScore).where(LeadScore.domain_id == domain.id).order_by(LeadScore.score_name)
    ).all()
    return {
        "domain": serialize_domain(domain),
        "qualified_lead": serialize_qualified_lead(lead) if lead else None,
        "company_profile": serialize_company_profile(profile) if profile else None,
        "scores": [serialize_lead_score(score) for score in scores],
    }


def serialize_profile_source_group(session: Session, crawl_task_run_id: int) -> dict[str, Any]:
    packages = session.scalars(
        select(ProfilePackage).where(ProfilePackage.crawl_task_run_id == crawl_task_run_id).order_by(ProfilePackage.id)
    ).all()
    package_ids = [package.id for package in packages]
    task_run = session.get(TaskRun, crawl_task_run_id)
    candidate_group_ids = sorted({package.candidate_group_id for package in packages if package.candidate_group_id is not None})
    candidate_group = session.get(CandidateGroup, candidate_group_ids[0]) if len(candidate_group_ids) == 1 else None
    analyzed_package_ids = set()
    if package_ids:
        analyzed_package_ids = set(
            session.scalars(
                select(AIProfileResult.profile_package_id)
                .where(AIProfileResult.profile_package_id.in_(package_ids), AIProfileResult.status == "success")
                .distinct()
            ).all()
        )
    latest_package_time = max((package.updated_at or package.created_at for package in packages), default=None)
    return {
        "id": crawl_task_run_id,
        "task_run_id": crawl_task_run_id,
        "name": task_run.name if task_run and task_run.name else f"抓官网任务 #{crawl_task_run_id}",
        "status": task_run.status if task_run else "",
        "created_at": _isoformat(task_run.created_at if task_run else None),
        "updated_at": _isoformat((task_run.finished_at if task_run else None) or latest_package_time),
        "candidate_group_id": candidate_group.id if candidate_group else None,
        "candidate_group_name": candidate_group.name if candidate_group else "",
        "country": candidate_group.country if candidate_group else "",
        "profile_package_count": len(package_ids),
        "ai_profile_count": len(analyzed_package_ids),
        "pending_profile_count": max(len(package_ids) - len(analyzed_package_ids), 0),
        "domain_count": len({package.domain_id for package in packages}),
        "profile_package_ids": package_ids,
    }


def apply_domain_filters(stmt: Any, *, q: str = "", country: str = "") -> Any:
    query_text = q.strip()
    if query_text:
        pattern = f"%{query_text}%"
        stmt = stmt.where(
            or_(
                Domain.domain.ilike(pattern),
                Domain.website.ilike(pattern),
                Domain.display_name.ilike(pattern),
                Domain.description.ilike(pattern),
            )
        )

    country_text = country.strip()
    if country_text:
        country_pattern = f"%{country_text}%"
        stmt = stmt.where(
            exists().where(
                CountrySignal.domain_id == Domain.id,
                CountrySignal.country.ilike(country_pattern),
            )
        )
    return stmt


def paginate_domains(
    session: Session,
    stmt: Any,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Domain], int, int, int]:
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)
    count_stmt = stmt.with_only_columns(Domain.id).order_by(None)
    total = int(session.scalar(select(func.count()).select_from(count_stmt.subquery())) or 0)
    id_stmt = stmt.with_only_columns(Domain.id).order_by(Domain.domain)
    domain_ids = list(session.scalars(id_stmt.offset(safe_offset).limit(safe_limit)))
    if not domain_ids:
        return [], total, safe_limit, safe_offset
    domains_by_id = {
        domain.id: domain
        for domain in session.scalars(select(Domain).where(Domain.id.in_(domain_ids))).all()
    }
    return [domains_by_id[domain_id] for domain_id in domain_ids if domain_id in domains_by_id], total, safe_limit, safe_offset


def paginate_raw_rows(
    session: Session,
    stmt: Any,
    model: type[Any],
    serializer: Callable[[Any], dict[str, Any]],
    *,
    limit: int,
    offset: int,
    max_limit: int = 200,
) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), max_limit)
    safe_offset = max(offset, 0)
    total = int(session.scalar(select(func.count()).select_from(stmt.with_only_columns(model.id).order_by(None).subquery())) or 0)
    rows = session.scalars(stmt.order_by(model.id.desc()).offset(safe_offset).limit(safe_limit)).all()
    return {
        "items": [serializer(row) for row in rows],
        "count": len(rows),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def count_distinct_domains_with(session: Session, model: type[Any]) -> int:
    return int(session.scalar(select(func.count(func.distinct(model.domain_id))).select_from(model)) or 0)


def count_rows_for_domain(session: Session, model: type[Any], domain_id: int) -> int:
    return int(session.scalar(select(func.count()).select_from(model).where(model.domain_id == domain_id)) or 0)


def countries_for_domain(session: Session, domain_id: int) -> list[str]:
    rows = session.scalars(
        select(CountrySignal.country)
        .where(CountrySignal.domain_id == domain_id, CountrySignal.country != "")
        .distinct()
        .order_by(CountrySignal.country)
    ).all()
    return [str(country) for country in rows]


def contacts_for_domain(session: Session, domain_id: int) -> list[dict[str, Any]]:
    contacts = session.scalars(
        select(Contact)
        .where(Contact.domain_id == domain_id)
        .order_by(Contact.kind, Contact.value, Contact.source)
    ).all()
    return [serialize_contact(contact) for contact in contacts]


def _count(session: Session, model: type[Any]) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
