"""Build JSON input packages for downstream profile analysis."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup


SCHEMA_VERSION = "1.0"
PAGE_CATEGORY_PRIORITY = {
    "home": 0,
    "product": 1,
    "service": 2,
    "about": 3,
    "contact": 4,
    "team": 5,
    "news": 6,
    "other": 20,
}


def _value(source: Any, key: str, default: str = "") -> str:
    if source is None:
        return default
    if isinstance(source, Mapping):
        value = source.get(key, default)
    else:
        value = getattr(source, key, default)
    if value is None:
        return default
    return str(value)


def _list_value(source: Any, key: str) -> list[str]:
    value = source.get(key, []) if isinstance(source, Mapping) else getattr(source, key, [])
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if item is not None]


def _dict_value(source: Any, key: str) -> dict[str, str]:
    value = source.get(key, {}) if isinstance(source, Mapping) else getattr(source, key, {})
    if not isinstance(value, Mapping):
        return {}
    return {str(item_key): str(item_value) for item_key, item_value in value.items() if item_value is not None}


def _trim_text(text: str, limit: int) -> str:
    if limit < 1:
        raise ValueError("page_char_limit must be >= 1")
    if len(text) <= limit:
        return text
    trimmed = text[:limit].rstrip()
    if " " in trimmed:
        return trimmed.rsplit(" ", 1)[0]
    return trimmed


def visible_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "title"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def page_title_from_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    if soup.title and soup.title.string:
        return " ".join(soup.title.string.split())
    return ""


def safe_package_filename(domain: str) -> str:
    safe_domain = (domain or "").strip().lower()
    if safe_domain.startswith("www."):
        safe_domain = safe_domain[4:]
    safe_domain = re.sub(r"[^a-z0-9.-]+", "-", safe_domain).strip(".-")
    if not safe_domain:
        safe_domain = "unknown"
    return f"{safe_domain}.json"


def _contact_people(profile: Any) -> list[dict[str, str]]:
    contacts = profile.get("contacts", []) if isinstance(profile, Mapping) else getattr(profile, "contacts", [])
    people = []
    for contact in contacts or []:
        person = {
            "name": _value(contact, "name"),
            "title": _value(contact, "title"),
            "email": _value(contact, "email"),
        }
        if any(person.values()):
            people.append(person)
    return people


def _page_sort_key(record: Any) -> tuple[int, str]:
    category = _value(record, "category", "other").lower() or "other"
    return (PAGE_CATEGORY_PRIORITY.get(category, PAGE_CATEGORY_PRIORITY["other"]), _value(record, "final_url"))


def _page_payloads(records: list[Any], max_pages: int, page_char_limit: int) -> list[dict[str, str]]:
    if max_pages < 1:
        raise ValueError("max_pages must be >= 1")

    pages = []
    for record in sorted(records, key=_page_sort_key):
        html = _value(record, "html")
        if not html:
            continue
        text = visible_text_from_html(html)
        if not text:
            continue
        pages.append(
            {
                "url": _value(record, "final_url") or _value(record, "requested_url"),
                "category": _value(record, "category", "other") or "other",
                "title": page_title_from_html(html),
                "text": _trim_text(text, page_char_limit),
            }
        )
        if len(pages) >= max_pages:
            break
    return pages


def build_profile_input_package(
    company: Any,
    profile: Any,
    records: list[Any],
    status: str,
    errors: list[str] | None = None,
    crawl_time: str | None = None,
    max_pages: int = 12,
    page_char_limit: int = 8000,
) -> dict[str, Any]:
    record_list = list(records)
    return {
        "schema_version": SCHEMA_VERSION,
        "company": {
            "domain": _value(company, "domain"),
            "website": _value(company, "website"),
            "company_name": _value(profile, "company_name") or _value(company, "title"),
            "country": _value(company, "country"),
            "industry": _value(company, "industry"),
            "source_keyword": _value(company, "keyword"),
            "matched_keywords": _value(company, "matched_keywords") or _value(company, "keyword"),
            "matched_countries": _value(company, "matched_countries") or _value(company, "country"),
            "matched_industries": _value(company, "matched_industries") or _value(company, "industry"),
            "matched_industry_terms": _value(company, "matched_industry_terms"),
        },
        "contacts": {
            "emails": _list_value(profile, "emails"),
            "phones": _list_value(profile, "phones"),
            "social_links": _dict_value(profile, "social_links"),
            "people": _contact_people(profile),
        },
        "pages": _page_payloads(record_list, max_pages, page_char_limit),
        "crawl_metadata": {
            "crawled_pages": len(record_list),
            "status": status,
            "errors": errors or [],
            "crawl_time": crawl_time or datetime.now(timezone.utc).isoformat(),
        },
    }


def write_profile_input_package(package: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = safe_package_filename(package.get("company", {}).get("domain", ""))
    path = output_dir / filename
    path.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
