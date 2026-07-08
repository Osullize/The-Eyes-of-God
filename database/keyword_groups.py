from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config.keywords import KeywordSpec, load_keyword_config
from database.models import KeywordGroup


DEFAULT_STRUCTURED_SEARCH_TEMPLATES = (
    "{product} {role} {country}",
    "{product} {role} in {country}",
)


def list_keyword_groups(session: Session, include_inactive: bool = True) -> list[dict[str, Any]]:
    stmt = select(KeywordGroup).order_by(KeywordGroup.name)
    if not include_inactive:
        stmt = stmt.where(KeywordGroup.is_active.is_(True))
    return [serialize_keyword_group(group) for group in session.scalars(stmt).all()]


def get_keyword_group(session: Session, group_id: int) -> KeywordGroup | None:
    return session.get(KeywordGroup, group_id)


def create_keyword_group(session: Session, values: dict[str, Any]) -> KeywordGroup:
    group = KeywordGroup()
    apply_keyword_group_values(group, values)
    session.add(group)
    session.flush()
    return group


def update_keyword_group(session: Session, group_id: int, values: dict[str, Any]) -> dict[str, Any]:
    group = session.get(KeywordGroup, group_id)
    if group is None:
        raise ValueError(f"Keyword group not found: {group_id}")
    apply_keyword_group_values(group, values, partial=True)
    session.flush()
    return serialize_keyword_group(group)


def delete_keyword_group(session: Session, group_id: int) -> bool:
    group = session.get(KeywordGroup, group_id)
    if group is None:
        return False
    session.delete(group)
    return True


def generate_keyword_specs(session: Session, group_id: int) -> list[KeywordSpec]:
    group = session.get(KeywordGroup, group_id)
    if group is None:
        raise ValueError(f"Keyword group not found: {group_id}")
    if not group.is_active:
        raise ValueError(f"Keyword group is inactive: {group_id}")

    return build_keyword_specs_from_group(group)


def build_keyword_specs_from_group(group: KeywordGroup) -> list[KeywordSpec]:
    country_terms = split_terms(group.country_terms)
    if not country_terms:
        raise ValueError("Keyword group must define country terms")

    keyword_terms = split_terms(group.keyword_terms)
    product_terms = split_terms(group.product_terms)
    role_terms = split_terms(group.role_terms)
    search_templates = split_terms(group.search_templates)
    if not keyword_terms and not product_terms:
        raise ValueError("Keyword group must define keyword terms or product terms")

    specs: list[KeywordSpec] = []
    seen_keywords: set[str] = set()

    for keyword_term in keyword_terms:
        for country_term in country_terms:
            append_keyword_spec(
                specs,
                seen_keywords,
                keyword=normalize_spaces(f"{keyword_term} {country_term}"),
                country=group.country,
                country_term=country_term,
                industry=group.name,
                industry_term=keyword_term,
            )

    if product_terms:
        active_templates = search_templates or list(DEFAULT_STRUCTURED_SEARCH_TEMPLATES)
        active_roles = role_terms or [""]
        for product_term in product_terms:
            for role_term in active_roles:
                industry_term = normalize_spaces(f"{product_term} {role_term}")
                for country_term in country_terms:
                    for template in active_templates:
                        keyword = render_search_template(
                            template,
                            product=product_term,
                            role=role_term,
                            country=country_term,
                            keyword=industry_term,
                        )
                        append_keyword_spec(
                            specs,
                            seen_keywords,
                            keyword=keyword,
                            country=group.country,
                            country_term=country_term,
                            industry=group.name,
                            industry_term=industry_term,
                        )
    return specs


def append_keyword_spec(
    specs: list[KeywordSpec],
    seen_keywords: set[str],
    *,
    keyword: str,
    country: str,
    country_term: str,
    industry: str,
    industry_term: str,
) -> None:
    normalized_keyword = normalize_spaces(keyword)
    if not normalized_keyword or normalized_keyword in seen_keywords:
        return
    seen_keywords.add(normalized_keyword)
    specs.append(
        KeywordSpec(
            keyword=normalized_keyword,
            country=country,
            country_term=country_term,
            industry=industry,
            industry_term=industry_term,
        )
    )


def render_search_template(
    template: str,
    *,
    product: str,
    role: str,
    country: str,
    keyword: str,
) -> str:
    rendered = template
    values = {
        "product": product,
        "role": role,
        "country": country,
        "country_term": country,
        "keyword": keyword,
    }
    for name, value in values.items():
        rendered = rendered.replace("{" + name + "}", value)
    return normalize_spaces(rendered)


def normalize_spaces(value: str) -> str:
    return " ".join(value.split())


def import_keyword_group_from_yaml(session: Session, path: str | Path, name: str | None = None) -> KeywordGroup:
    source_path = Path(path)
    config = load_keyword_config(source_path)
    countries = config.get("countries", {})
    industries = config.get("industries", {})
    if not isinstance(countries, dict) or not countries:
        raise ValueError(f"Keyword YAML has no countries: {source_path}")
    if not isinstance(industries, dict) or not industries:
        raise ValueError(f"Keyword YAML has no industries: {source_path}")

    country_name = str(next(iter(countries.keys())))
    country_terms: list[str] = []
    for country_node in countries.values():
        country_terms.extend(terms_from_config_node(country_node))

    keyword_terms: list[str] = []
    for industry_node in industries.values():
        keyword_terms.extend(terms_from_config_node(industry_node))

    group_name = name or source_path.stem
    group = session.scalar(select(KeywordGroup).where(KeywordGroup.name == group_name))
    values = {
        "name": group_name,
        "country": country_name,
        "country_terms": join_unique_terms(country_terms),
        "keyword_terms": join_unique_terms(keyword_terms),
        "product_terms": "",
        "role_terms": "",
        "search_templates": "",
        "notes": f"Imported from {source_path}",
        "is_active": True,
    }
    if group is None:
        group = create_keyword_group(session, values)
    else:
        apply_keyword_group_values(group, values)
        session.flush()
    return group


def serialize_keyword_group(group: KeywordGroup) -> dict[str, Any]:
    return {
        "id": group.id,
        "name": group.name,
        "country": group.country,
        "country_terms": group.country_terms,
        "keyword_terms": group.keyword_terms,
        "product_terms": group.product_terms,
        "role_terms": group.role_terms,
        "search_templates": group.search_templates,
        "notes": group.notes,
        "is_active": group.is_active,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "updated_at": group.updated_at.isoformat() if group.updated_at else None,
        "keyword_count": keyword_count_for_group(group),
    }


def apply_keyword_group_values(group: KeywordGroup, values: dict[str, Any], partial: bool = False) -> None:
    required_fields = ["name", "country", "country_terms"]
    if not partial:
        missing = [field for field in required_fields if not clean(values.get(field))]
        if missing:
            raise ValueError(f"Missing keyword group fields: {', '.join(missing)}")
        if not clean(values.get("keyword_terms")) and not clean(values.get("product_terms")):
            raise ValueError("Missing keyword group fields: keyword_terms or product_terms")

    for field in ["name", "country", "country_terms", "keyword_terms", "product_terms", "role_terms", "search_templates", "notes"]:
        if field in values:
            setattr(group, field, clean(values.get(field)))
    if "is_active" in values:
        group.is_active = bool(values.get("is_active"))


def keyword_count_for_group(group: KeywordGroup) -> int:
    try:
        return len(build_keyword_specs_from_group(group))
    except ValueError:
        return 0


def terms_from_config_node(node: Any) -> list[str]:
    if isinstance(node, str):
        return [node.strip()] if node.strip() else []
    if isinstance(node, list):
        return [str(item).strip() for item in node if str(item).strip()]
    if isinstance(node, dict):
        terms: list[str] = []
        for key in ("terms", "synonyms"):
            values = node.get(key, [])
            if isinstance(values, str):
                values = [values]
            terms.extend(str(item).strip() for item in values if str(item).strip())
        return terms
    return []


def split_terms(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def join_unique_terms(values: list[str]) -> str:
    terms: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in terms:
            terms.append(cleaned)
    return "\n".join(terms)


def clean(value: Any) -> str:
    return str(value or "").strip()
