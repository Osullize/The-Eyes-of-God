from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

import run_crawl
from database.importers import clean, normalize_domain_value
from database.models import CandidateGroup, CandidateGroupItem, CrawlResult, Domain, SearchResult


def create_candidate_group_from_search_rows(
    session: Session,
    *,
    rows: Iterable[dict[str, Any]],
    source_name: str,
    name: str = "",
    source_task_run_id: int | None = None,
    keyword_group_id: int | None = None,
    country: str = "",
    params: dict[str, Any] | None = None,
) -> CandidateGroup | None:
    ranked_results = find_search_results_for_rows(session, rows, source_name)
    if not ranked_results:
        return None

    candidate_group = CandidateGroup(
        name=name or default_group_name(country),
        group_type="search_output",
        source_task_run_id=source_task_run_id,
        keyword_group_id=keyword_group_id,
        country=country,
        status="active",
        params_json=params or {},
    )
    session.add(candidate_group)
    session.flush()

    seen_domain_ids: set[int] = set()
    rank = 1
    for search_result in ranked_results:
        if search_result.domain_id in seen_domain_ids:
            continue
        seen_domain_ids.add(search_result.domain_id)
        session.add(
            CandidateGroupItem(
                group_id=candidate_group.id,
                domain_id=search_result.domain_id,
                search_result_id=search_result.id,
                status="active",
                rank=rank,
            )
        )
        rank += 1
    session.flush()
    return candidate_group


def list_candidate_groups(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str = "active",
) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)
    stmt = select(CandidateGroup)
    if status.strip():
        stmt = stmt.where(CandidateGroup.status == status.strip())
    total = int(session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    groups = session.scalars(
        stmt.order_by(CandidateGroup.created_at.desc(), CandidateGroup.id.desc()).offset(safe_offset).limit(safe_limit)
    ).all()
    return {
        "items": [serialize_candidate_group(session, group, include_items=False) for group in groups],
        "count": len(groups),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def get_candidate_group_detail(session: Session, group_id: int) -> dict[str, Any] | None:
    group = session.scalar(
        select(CandidateGroup)
        .where(CandidateGroup.id == group_id)
        .options(
            selectinload(CandidateGroup.items).selectinload(CandidateGroupItem.domain_record),
            selectinload(CandidateGroup.items).selectinload(CandidateGroupItem.search_result),
        )
    )
    if group is None:
        return None
    return serialize_candidate_group(session, group, include_items=True)


def select_candidate_group_companies(
    session: Session,
    group_id: int,
    *,
    limit: int = 50,
    recrawl_existing: bool = False,
) -> list[run_crawl.CompanyInput]:
    if session.get(CandidateGroup, group_id) is None:
        raise ValueError(f"Candidate group not found: {group_id}")
    safe_limit = min(max(limit, 1), 500)
    stmt = (
        select(CandidateGroupItem)
        .where(CandidateGroupItem.group_id == group_id, CandidateGroupItem.status == "active")
        .options(selectinload(CandidateGroupItem.domain_record), selectinload(CandidateGroupItem.search_result))
        .order_by(CandidateGroupItem.rank, CandidateGroupItem.id)
    )
    if not recrawl_existing:
        stmt = stmt.where(~exists().where(CrawlResult.domain_id == CandidateGroupItem.domain_id))

    items = session.scalars(stmt.limit(safe_limit)).all()
    companies: list[run_crawl.CompanyInput] = []
    for item in items:
        domain = item.domain_record
        search_result = item.search_result
        website = (search_result.website if search_result is not None else "") or domain.website
        if not website:
            continue
        companies.append(
            run_crawl.CompanyInput(
                keyword=search_result.keyword if search_result is not None else "",
                title=(search_result.title if search_result is not None else "") or domain.display_name,
                website=website,
                domain=domain.domain,
                country=search_result.country if search_result is not None else "",
                industry=search_result.industry if search_result is not None else "",
                matched_keywords=(
                    search_result.matched_keywords or search_result.keyword if search_result is not None else ""
                ),
                matched_countries=(
                    search_result.matched_countries or search_result.country if search_result is not None else ""
                ),
                matched_industries=(
                    search_result.matched_industries or search_result.industry if search_result is not None else ""
                ),
                matched_industry_terms=search_result.matched_industry_terms if search_result is not None else "",
            )
        )
    return companies


def find_search_results_for_rows(
    session: Session,
    rows: Iterable[dict[str, Any]],
    source_name: str,
) -> list[SearchResult]:
    results: list[SearchResult] = []
    for row in rows:
        domain_name = normalize_domain_value(row.get("domain", ""), row.get("website", ""))
        if not domain_name:
            continue
        search_result = session.scalar(
            select(SearchResult)
            .join(Domain, Domain.id == SearchResult.domain_id)
            .where(
                Domain.domain == domain_name,
                SearchResult.keyword == clean(row.get("keyword")),
                SearchResult.website == clean(row.get("website")),
                SearchResult.source_file == source_name,
            )
            .order_by(SearchResult.id.desc())
        )
        if search_result is not None:
            results.append(search_result)
    return results


def serialize_candidate_group(
    session: Session,
    group: CandidateGroup,
    *,
    include_items: bool,
) -> dict[str, Any]:
    counts = count_group_items(session, group.id)
    result: dict[str, Any] = {
        "id": group.id,
        "name": group.name,
        "group_type": group.group_type,
        "source_task_run_id": group.source_task_run_id,
        "keyword_group_id": group.keyword_group_id,
        "country": group.country,
        "status": group.status,
        "params_json": group.params_json or {},
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "updated_at": group.updated_at.isoformat() if group.updated_at else None,
        **counts,
    }
    if include_items:
        items = sorted(group.items, key=lambda item: (item.rank, item.id or 0))
        result["items"] = [serialize_candidate_group_item(session, item) for item in items]
    return result


def serialize_candidate_group_item(session: Session, item: CandidateGroupItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "group_id": item.group_id,
        "domain": serialize_domain(item.domain_record),
        "search_result": serialize_search_result(item.search_result),
        "status": item.status,
        "rank": item.rank,
        "has_crawl_result": has_crawl_result(session, item.domain_id),
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def count_group_items(session: Session, group_id: int) -> dict[str, int]:
    item_count = int(
        session.scalar(
            select(func.count())
            .select_from(CandidateGroupItem)
            .where(CandidateGroupItem.group_id == group_id, CandidateGroupItem.status == "active")
        )
        or 0
    )
    crawled_count = int(
        session.scalar(
            select(func.count())
            .select_from(CandidateGroupItem)
            .where(
                CandidateGroupItem.group_id == group_id,
                CandidateGroupItem.status == "active",
                exists().where(CrawlResult.domain_id == CandidateGroupItem.domain_id),
            )
        )
        or 0
    )
    return {
        "item_count": item_count,
        "crawled_count": crawled_count,
        "uncrawled_count": max(item_count - crawled_count, 0),
    }


def has_crawl_result(session: Session, domain_id: int) -> bool:
    return bool(session.scalar(select(exists().where(CrawlResult.domain_id == domain_id))))


def serialize_domain(domain: Domain | None) -> dict[str, Any]:
    if domain is None:
        return {}
    return {
        "id": domain.id,
        "domain": domain.domain,
        "website": domain.website,
        "display_name": domain.display_name,
        "latest_status": domain.latest_status,
    }


def serialize_search_result(search_result: SearchResult | None) -> dict[str, Any]:
    if search_result is None:
        return {}
    return {
        "id": search_result.id,
        "keyword": search_result.keyword,
        "title": search_result.title,
        "website": search_result.website,
        "engine": search_result.engine,
        "country": search_result.country,
    }


def default_group_name(country: str) -> str:
    country_text = country.strip()
    return f"{country_text} search candidates" if country_text else "Search candidates"
