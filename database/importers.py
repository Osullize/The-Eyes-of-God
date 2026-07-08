from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from database.models import Contact, CountrySignal, CrawlResult, Domain, ProfilePackage, SearchResult
from search.url_utils import normalize_domain as normalize_domain_from_url


@dataclass
class ImportSummary:
    domains_created: int = 0
    domains_updated: int = 0
    search_results_created: int = 0
    crawl_results_created: int = 0
    contacts_created: int = 0
    profile_packages_created: int = 0
    profile_packages_updated: int = 0
    country_signals_created: int = 0
    files_scanned: int = 0

    def merge(self, other: ImportSummary) -> None:
        self.domains_created += other.domains_created
        self.domains_updated += other.domains_updated
        self.search_results_created += other.search_results_created
        self.crawl_results_created += other.crawl_results_created
        self.contacts_created += other.contacts_created
        self.profile_packages_created += other.profile_packages_created
        self.profile_packages_updated += other.profile_packages_updated
        self.country_signals_created += other.country_signals_created
        self.files_scanned += other.files_scanned


def import_search_csv(session: Session, path: str | Path) -> ImportSummary:
    source_path = Path(path)
    with source_path.open("r", encoding="utf-8-sig", newline="") as file:
        return import_search_rows(session, csv.DictReader(file), source_name=str(source_path), files_scanned=1)


def import_search_rows(
    session: Session,
    rows: Any,
    source_name: str,
    files_scanned: int = 0,
) -> ImportSummary:
    summary = ImportSummary(files_scanned=files_scanned)
    for row in rows:
        import_search_row(session, dict(row), source_name=source_name, summary=summary)
    return summary


def import_search_row(session: Session, row: dict[str, Any], source_name: str, summary: ImportSummary) -> None:
    domain_name = normalize_domain_value(row.get("domain", ""), row.get("website", ""))
    if not domain_name:
        return
    domain = upsert_domain(
        session,
        domain_name=domain_name,
        website=row.get("website", ""),
        display_name=row.get("title", ""),
        summary=summary,
    )
    search_result = (
        session.query(SearchResult)
        .filter(
            SearchResult.domain_id == domain.id,
            SearchResult.keyword == clean(row.get("keyword")),
            SearchResult.website == clean(row.get("website")),
            SearchResult.source_file == source_name,
        )
        .one_or_none()
    )
    if search_result is None:
        session.add(
            SearchResult(
                domain_id=domain.id,
                keyword=clean(row.get("keyword")),
                title=clean(row.get("title")),
                website=clean(row.get("website")),
                source_url=clean(row.get("source_url")),
                engine=clean(row.get("engine")),
                country=clean(row.get("country")),
                country_term=clean(row.get("country_term")),
                industry=clean(row.get("industry")),
                industry_term=clean(row.get("industry_term")),
                matched_keywords=clean(row.get("matched_keywords")),
                matched_countries=clean(row.get("matched_countries")),
                matched_industries=clean(row.get("matched_industries")),
                matched_industry_terms=clean(row.get("matched_industry_terms")),
                source_file=source_name,
            )
        )
        summary.search_results_created += 1
    for country in unique_values([row.get("country", ""), row.get("matched_countries", "")]):
        if add_country_signal(
            session,
            domain=domain,
            country=country,
            signal_type="search_country",
            confidence=0.4,
            evidence=clean(row.get("keyword")),
            source=source_name,
        ):
            summary.country_signals_created += 1


def import_crawl_csv(session: Session, path: str | Path) -> ImportSummary:
    source_path = Path(path)
    with source_path.open("r", encoding="utf-8-sig", newline="") as file:
        return import_crawl_rows(session, csv.DictReader(file), source_name=str(source_path), files_scanned=1)


def import_crawl_rows(
    session: Session,
    rows: Any,
    source_name: str,
    files_scanned: int = 0,
    candidate_group_id: int | None = None,
    crawl_task_run_id: int | None = None,
) -> ImportSummary:
    summary = ImportSummary(files_scanned=files_scanned)
    for row in rows:
        import_crawl_row(
            session,
            dict(row),
            source_name=source_name,
            summary=summary,
            candidate_group_id=candidate_group_id,
            crawl_task_run_id=crawl_task_run_id,
        )
    return summary


def import_crawl_row(
    session: Session,
    row: dict[str, Any],
    source_name: str,
    summary: ImportSummary,
    candidate_group_id: int | None = None,
    crawl_task_run_id: int | None = None,
) -> None:
    domain_name = normalize_domain_value(row.get("domain", ""), row.get("website", ""))
    if not domain_name:
        return
    domain = upsert_domain(
        session,
        domain_name=domain_name,
        website=row.get("website", ""),
        display_name=row.get("company_name", ""),
        description=row.get("description", ""),
        latest_status=row.get("status", ""),
        summary=summary,
    )
    crawl_result = (
        session.query(CrawlResult)
        .filter(
            CrawlResult.domain_id == domain.id,
            CrawlResult.source_file == source_name,
        )
        .one_or_none()
    )
    if crawl_result is None:
        crawl_result = CrawlResult(
            domain_id=domain.id,
            keyword=clean(row.get("keyword")),
            company_name=clean(row.get("company_name")),
            website=clean(row.get("website")),
            emails=clean(row.get("emails")),
            phones=clean(row.get("phones")),
            possible_address=clean(row.get("possible_address")),
            description=clean(row.get("description")),
            crawled_pages=clean(row.get("crawled_pages")),
            status=clean(row.get("status")),
            error=clean(row.get("error")),
            social_links=clean(row.get("social_links")),
            contacts=clean(row.get("contacts")),
            page_categories=clean(row.get("page_categories")),
            country=clean(row.get("country")),
            industry=clean(row.get("industry")),
            matched_keywords=clean(row.get("matched_keywords")),
            matched_countries=clean(row.get("matched_countries")),
            matched_industries=clean(row.get("matched_industries")),
            matched_industry_terms=clean(row.get("matched_industry_terms")),
            source_file=source_name,
        )
        session.add(crawl_result)
        session.flush()
        summary.crawl_results_created += 1
    summary.contacts_created += add_contacts_from_crawl_row(session, domain, row)
    profile_package = row.get("_profile_package")
    if isinstance(profile_package, dict):
        import_profile_package(
            session,
            profile_package,
            summary=summary,
            candidate_group_id=candidate_group_id,
            crawl_task_run_id=crawl_task_run_id,
            crawl_result_id=crawl_result.id,
            signal_source=source_name,
        )
    for country in unique_values([row.get("country", ""), row.get("matched_countries", "")]):
        if add_country_signal(
            session,
            domain=domain,
            country=country,
            signal_type="crawl_country",
            confidence=0.6,
            evidence=clean(row.get("possible_address")) or clean(row.get("matched_countries")),
            source=source_name,
        ):
            summary.country_signals_created += 1


def import_profile_dir(
    session: Session,
    path: str | Path,
    candidate_group_id: int | None = None,
    crawl_task_run_id: int | None = None,
) -> ImportSummary:
    summary = ImportSummary()
    profile_dir = Path(path)
    if not profile_dir.exists():
        return summary

    for package_path in sorted(profile_dir.glob("*.json")):
        summary.files_scanned += 1
        package_text = package_path.read_text(encoding="utf-8")
        package = json.loads(package_text)
        import_profile_package(
            session,
            package,
            summary=summary,
            candidate_group_id=candidate_group_id,
            crawl_task_run_id=crawl_task_run_id,
            signal_source="profile_json",
        )
    return summary


def import_profile_package(
    session: Session,
    package: dict[str, Any],
    summary: ImportSummary,
    candidate_group_id: int | None = None,
    crawl_task_run_id: int | None = None,
    crawl_result_id: int | None = None,
    signal_source: str = "profile_json",
) -> ProfilePackage | None:
    company = package.get("company") or {}
    contacts = package.get("contacts") or {}
    crawl_metadata = package.get("crawl_metadata") or {}
    pages = package.get("pages") or []
    domain_name = normalize_domain_value(company.get("domain", ""), company.get("website", ""))
    if not domain_name:
        return None

    domain = upsert_domain(
        session,
        domain_name=domain_name,
        website=company.get("website", ""),
        display_name=company.get("company_name", ""),
        latest_status=crawl_metadata.get("status", ""),
        summary=summary,
    )
    content_hash = profile_package_content_hash(package)
    profile_package = session.query(ProfilePackage).filter(ProfilePackage.content_hash == content_hash).one_or_none()
    if profile_package is None:
        profile_package = ProfilePackage(domain_id=domain.id, content_hash=content_hash)
        session.add(profile_package)
        summary.profile_packages_created += 1
    else:
        summary.profile_packages_updated += 1

    profile_package.domain_id = domain.id
    if candidate_group_id is not None:
        profile_package.candidate_group_id = candidate_group_id
    if crawl_task_run_id is not None:
        profile_package.crawl_task_run_id = crawl_task_run_id
    if crawl_result_id is not None:
        profile_package.crawl_result_id = crawl_result_id
    profile_package.schema_version = clean(package.get("schema_version"))
    profile_package.crawl_status = clean(crawl_metadata.get("status"))
    profile_package.page_count = len(pages)
    profile_package.crawl_time = parse_datetime(crawl_metadata.get("crawl_time"))
    profile_package.payload_json = package
    profile_package.content_hash = content_hash

    summary.contacts_created += add_contacts_from_profile(session, domain, contacts)
    for country in unique_values([company.get("country", ""), company.get("matched_countries", "")]):
        if add_country_signal(
            session,
            domain=domain,
            country=country,
            signal_type="profile_country",
            confidence=0.7,
            evidence=clean(company.get("company_name")),
            source=signal_source,
        ):
            summary.country_signals_created += 1
    return profile_package


def profile_package_content_hash(package: dict[str, Any]) -> str:
    canonical = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def upsert_domain(
    session: Session,
    domain_name: str,
    website: Any = "",
    display_name: Any = "",
    description: Any = "",
    latest_status: Any = "",
    summary: ImportSummary | None = None,
) -> Domain:
    normalized = normalize_domain_value(domain_name, website)
    if not normalized:
        raise ValueError("domain_name or website must contain a valid domain")
    domain = session.query(Domain).filter(Domain.domain == normalized).one_or_none()
    created = False
    if domain is None:
        domain = Domain(domain=normalized)
        session.add(domain)
        session.flush()
        created = True

    changed = False
    for field, value in {
        "website": clean(website),
        "display_name": clean(display_name),
        "description": clean(description),
        "latest_status": clean(latest_status),
    }.items():
        if value and getattr(domain, field) != value:
            setattr(domain, field, value)
            changed = True

    if summary is not None:
        if created:
            summary.domains_created += 1
        elif changed:
            summary.domains_updated += 1
    return domain


def add_contacts_from_crawl_row(session: Session, domain: Domain, row: dict[str, Any]) -> int:
    created = 0
    for email in split_values(row.get("emails")):
        created += add_contact(session, domain, "email", email, source="crawl_csv")
    for phone in split_values(row.get("phones")):
        created += add_contact(session, domain, "phone", phone, source="crawl_csv")
    for label, value in parse_social_links(row.get("social_links")):
        created += add_contact(session, domain, "social", value, label=label, source="crawl_csv")
    return created


def add_contacts_from_profile(session: Session, domain: Domain, contacts: dict[str, Any]) -> int:
    created = 0
    for email in contacts.get("emails") or []:
        created += add_contact(session, domain, "email", email, source="profile_json")
    for phone in contacts.get("phones") or []:
        created += add_contact(session, domain, "phone", phone, source="profile_json")
    for label, value in (contacts.get("social_links") or {}).items():
        created += add_contact(session, domain, "social", value, label=label, source="profile_json")
    for person in contacts.get("people") or []:
        name = clean(person.get("name"))
        title = clean(person.get("title"))
        email = clean(person.get("email"))
        value = email or name
        label = " | ".join(part for part in [name, title] if part)
        created += add_contact(session, domain, "person", value, label=label, source="profile_json")
    return created


def add_contact(
    session: Session,
    domain: Domain,
    kind: str,
    value: Any,
    label: Any = "",
    source: str = "",
) -> int:
    cleaned_value = clean(value)
    if not cleaned_value:
        return 0
    existing = (
        session.query(Contact)
        .filter(
            Contact.domain_id == domain.id,
            Contact.kind == kind,
            Contact.value == cleaned_value,
            Contact.source == source,
        )
        .one_or_none()
    )
    if existing is not None:
        if label and not existing.label:
            existing.label = clean(label)
        return 0
    session.add(
        Contact(
            domain_id=domain.id,
            kind=kind,
            value=cleaned_value,
            label=clean(label),
            source=source,
        )
    )
    return 1


def add_country_signal(
    session: Session,
    domain: Domain,
    country: Any,
    signal_type: str,
    confidence: float,
    evidence: Any,
    source: str,
) -> bool:
    cleaned_country = clean(country)
    if not cleaned_country:
        return False
    existing = (
        session.query(CountrySignal)
        .filter(
            CountrySignal.domain_id == domain.id,
            CountrySignal.country == cleaned_country,
            CountrySignal.signal_type == signal_type,
            CountrySignal.source == source,
        )
        .one_or_none()
    )
    if existing is not None:
        return False
    session.add(
        CountrySignal(
            domain_id=domain.id,
            country=cleaned_country,
            signal_type=signal_type,
            confidence=confidence,
            evidence=clean(evidence),
            source=source,
        )
    )
    return True


def normalize_domain_value(domain: Any, website: Any = "") -> str:
    value = clean(domain).lower()
    if value.startswith(("http://", "https://")):
        value = normalize_domain_from_url(value)
    elif value:
        value = value.split("/", 1)[0].split(":", 1)[0].strip()
        if value.startswith("www."):
            value = value[4:]
    if value and "." in value:
        return value

    website_value = clean(website)
    if website_value:
        parsed = urlparse(website_value if "://" in website_value else f"https://{website_value}")
        parsed_domain = parsed.netloc.lower().split(":", 1)[0]
        if parsed_domain.startswith("www."):
            parsed_domain = parsed_domain[4:]
        return parsed_domain
    return ""


def split_values(value: Any) -> list[str]:
    return [item.strip() for item in clean(value).split(";") if item.strip()]


def unique_values(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        for item in split_values(value):
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def parse_social_links(value: Any) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for item in split_values(value):
        if ":" in item:
            label, url = item.split(":", 1)
            links.append((label.strip(), url.strip()))
        else:
            links.append(("", item))
    return links


def parse_datetime(value: Any) -> datetime | None:
    text = clean(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
