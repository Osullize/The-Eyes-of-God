from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from database.models import AIProfileResult, CompanyProfile, LeadScore, ProfilePackage, QualifiedLead


def upsert_ai_profile_result(
    session: Session,
    *,
    profile_package: ProfilePackage,
    result: dict[str, Any],
    model_provider: str,
    model_name: str,
    prompt_version: str,
    task_run_id: int | None = None,
    task_item_id: int | None = None,
    input_hash: str | None = None,
) -> tuple[AIProfileResult, bool]:
    normalized = normalize_ai_profile_result(result)
    raw_response = normalized.pop("_raw_response", {})
    existing = (
        session.query(AIProfileResult)
        .filter(
            AIProfileResult.profile_package_id == profile_package.id,
            AIProfileResult.prompt_version == prompt_version,
            AIProfileResult.model_provider == model_provider,
            AIProfileResult.model_name == model_name,
        )
        .one_or_none()
    )
    created = existing is None
    record = existing or AIProfileResult(
        domain_id=profile_package.domain_id,
        profile_package_id=profile_package.id,
        prompt_version=prompt_version,
        model_provider=model_provider,
        model_name=model_name,
    )
    if created:
        session.add(record)

    record.domain_id = profile_package.domain_id
    record.task_run_id = task_run_id
    record.task_item_id = task_item_id
    record.input_hash = input_hash or profile_package.content_hash
    record.company_name = str(normalized.get("company_name") or fallback_company_name(profile_package))
    normalized["company_name"] = record.company_name
    record.profile_summary = str(normalized.get("profile_summary") or "")
    record.business_type = str(normalized.get("business_type") or "")
    record.market_role = str(normalized.get("market_role") or "")
    record.product_fit = str(normalized.get("product_fit") or "")
    record.customer_priority = str(normalized.get("customer_priority") or "")
    record.score_total = float(normalized.get("score_total") or 0.0)
    record.score_breakdown_json = dict(normalized.get("score_breakdown") or {})
    record.evidence_json = list(normalized.get("evidence") or [])
    record.risk_flags_json = list(normalized.get("risk_flags") or [])
    record.recommended_action = str(normalized.get("recommended_action") or "")
    record.result_json = normalized
    record.raw_response_json = raw_response if isinstance(raw_response, dict) else {"raw": raw_response}
    record.status = "success"
    record.error = ""
    session.flush()
    return record, created


def normalize_ai_profile_result(result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result)
    normalized.setdefault("company_name", "")
    normalized.setdefault("profile_summary", "")
    normalized.setdefault("business_type", "")
    normalized.setdefault("market_role", "")
    normalized.setdefault("product_fit", "")
    normalized.setdefault("customer_priority", "")
    normalized["score_total"] = clamp_score(normalized.get("score_total"))
    normalized.setdefault("score_breakdown", {})
    normalized.setdefault("contact_analysis", {})
    normalized.setdefault("evidence", [])
    normalized.setdefault("risk_flags", [])
    normalized.setdefault("recommended_action", "")
    if not isinstance(normalized["score_breakdown"], dict):
        normalized["score_breakdown"] = {}
    if not isinstance(normalized["contact_analysis"], dict):
        normalized["contact_analysis"] = {}
    if not isinstance(normalized["evidence"], list):
        normalized["evidence"] = [str(normalized["evidence"])]
    if not isinstance(normalized["risk_flags"], list):
        normalized["risk_flags"] = [str(normalized["risk_flags"])]
    return normalized


def fallback_company_name(profile_package: ProfilePackage) -> str:
    payload = profile_package.payload_json if isinstance(profile_package.payload_json, dict) else {}
    company = payload.get("company") if isinstance(payload.get("company"), dict) else {}
    company_name = str(company.get("company_name") or "").strip()
    if company_name:
        return company_name

    domain_record = profile_package.domain_record
    if domain_record is not None:
        display_name = str(domain_record.display_name or "").strip()
        if display_name:
            return display_name
        return str(domain_record.domain or "").strip()
    return ""


def clamp_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(score, 0.0), 100.0)


def sync_stage_c_from_ai_profile_result(session: Session, record: AIProfileResult) -> bool:
    source = stage_c_source_for_ai_result(record)
    if normalize_customer_priority(record.customer_priority) != "A":
        delete_stage_c_ai_source(session, domain_id=record.domain_id, source=source)
        return False

    upsert_qualified_lead(session, record, source)
    upsert_company_profile(session, record, source)
    upsert_lead_score(
        session,
        domain_id=record.domain_id,
        score_name="total",
        score_value=record.score_total,
        reason=record.recommended_action or record.profile_summary,
        source=source,
    )
    for score_name, score_value, reason in iter_score_breakdown(record.score_breakdown_json):
        upsert_lead_score(
            session,
            domain_id=record.domain_id,
            score_name=score_name,
            score_value=score_value,
            reason=reason,
            source=source,
        )
    return True


def stage_c_source_for_ai_result(record: AIProfileResult) -> str:
    prompt_version = record.prompt_version or "unknown_prompt"
    model_provider = record.model_provider or "unknown_provider"
    model_name = record.model_name or "unknown_model"
    return f"ai_profile:{prompt_version}:{model_provider}:{model_name}"


def normalize_customer_priority(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text.startswith("A"):
        return "A"
    if text.startswith("B"):
        return "B"
    if text.startswith("C"):
        return "C"
    if text.startswith("D"):
        return "D"
    return ""


def delete_stage_c_ai_source(session: Session, *, domain_id: int, source: str) -> None:
    session.query(QualifiedLead).filter(QualifiedLead.domain_id == domain_id, QualifiedLead.source == source).delete(
        synchronize_session=False
    )
    session.query(CompanyProfile).filter(CompanyProfile.domain_id == domain_id, CompanyProfile.source == source).delete(
        synchronize_session=False
    )
    session.query(LeadScore).filter(LeadScore.domain_id == domain_id, LeadScore.source == source).delete(
        synchronize_session=False
    )


def upsert_qualified_lead(session: Session, record: AIProfileResult, source: str) -> QualifiedLead:
    lead = (
        session.query(QualifiedLead)
        .filter(QualifiedLead.domain_id == record.domain_id, QualifiedLead.source == source)
        .one_or_none()
    )
    if lead is None:
        lead = QualifiedLead(domain_id=record.domain_id, source=source)
        session.add(lead)

    lead.priority = "A"
    lead.status = "new"
    lead.segment = record.market_role or record.business_type
    lead.notes = record.recommended_action or record.profile_summary
    return lead


def upsert_company_profile(session: Session, record: AIProfileResult, source: str) -> CompanyProfile:
    profile = (
        session.query(CompanyProfile)
        .filter(CompanyProfile.domain_id == record.domain_id, CompanyProfile.source == source)
        .one_or_none()
    )
    if profile is None:
        profile = CompanyProfile(domain_id=record.domain_id, source=source)
        session.add(profile)

    profile.business_type = record.business_type
    profile.product_fit = record.product_fit
    profile.market_role = record.market_role
    profile.summary = record.profile_summary
    profile.evidence = evidence_to_text(record.evidence_json)
    return profile


def upsert_lead_score(
    session: Session,
    *,
    domain_id: int,
    score_name: str,
    score_value: float,
    reason: str,
    source: str,
) -> LeadScore:
    normalized_score_name = score_name.strip()[:80] or "score"
    score = (
        session.query(LeadScore)
        .filter(
            LeadScore.domain_id == domain_id,
            LeadScore.score_name == normalized_score_name,
            LeadScore.source == source,
        )
        .one_or_none()
    )
    if score is None:
        score = LeadScore(domain_id=domain_id, score_name=normalized_score_name, source=source)
        session.add(score)

    score.score_value = float(score_value)
    score.reason = reason
    return score


def iter_score_breakdown(score_breakdown: dict[str, Any]) -> list[tuple[str, float, str]]:
    rows: list[tuple[str, float, str]] = []
    for key, value in score_breakdown.items():
        score_value, reason = parse_score_breakdown_value(value)
        if score_value is None:
            continue
        rows.append((str(key), score_value, reason))
    return rows


def parse_score_breakdown_value(value: Any) -> tuple[float | None, str]:
    reason = ""
    raw_value = value
    if isinstance(value, dict):
        reason = str(value.get("reason") or value.get("evidence") or "")
        raw_value = value.get("score", value.get("value", value.get("points")))
    try:
        return float(raw_value), reason
    except (TypeError, ValueError):
        return None, reason


def evidence_to_text(evidence: list[Any]) -> str:
    lines: list[str] = []
    for item in evidence:
        if isinstance(item, str):
            lines.append(item)
        else:
            lines.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
    return "\n".join(lines)
