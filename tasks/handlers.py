from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import exists, or_, select

import run_crawl as crawl_module
import run_search as search_module
from ai.lead_profile_prompt import DEFAULT_PROMPT_VERSION
from ai.model_api_client import (
    DEFAULT_API_BASE_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_PROVIDER,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
    ModelAPIClient,
)
from database.ai_profiles import sync_stage_c_from_ai_profile_result, upsert_ai_profile_result
from database.candidate_groups import (
    create_candidate_group_from_search_rows,
    select_candidate_group_companies,
)
from database.importers import ImportSummary
from database.keyword_groups import generate_keyword_specs
from database.models import CountrySignal, CrawlResult, Domain, KeywordGroup, ProfilePackage, SearchResult, TaskRun
from database.session import DEFAULT_DATABASE_URL, create_all, create_engine_from_url, create_session_factory
from database.stage_persistence import (
    persist_crawl_rows_to_database,
    persist_search_rows_to_database,
    resolve_database_url,
)
from database.task_batches import (
    cancel_unfinished_task_items,
    count_task_items_by_status,
    create_task_items,
    create_task_run,
    finish_task_item,
    finish_task_run,
    is_task_run_cancel_requested,
    start_task_item,
    start_task_run,
)
from tasks.importing import PROJECT_ROOT, import_sources, import_summary_to_dict, resolve_sources


SearchRunner = Callable[..., list[dict[str, Any]]]
CrawlRunner = Callable[..., list[dict[str, Any]]]
ImportSourcesFunc = Callable[..., Any]
AIProfileAnalyzer = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


def run_search_task(params: dict[str, Any], search_runner: SearchRunner = search_module.run_search) -> dict[str, Any]:
    database_url = resolve_database_url(params.get("database_url"), params.get("persist_to_database"))
    output_file = str(params["output_file"]) if params.get("output_file") else ""
    if not output_file and not database_url:
        output_file = search_module.OUTPUT_FILE
    explicit_state_dir = optional_non_blank_str(params.get("state_dir"))
    state_dir = explicit_state_dir if explicit_state_dir is not None else (None if database_url else search_module.STATE_DIR)
    keyword_specs = None
    if params.get("keyword_group_id") is not None:
        if not database_url:
            raise ValueError("database_url or DATABASE_URL is required when keyword_group_id is used")
        keyword_specs = load_keyword_specs_from_database(database_url, int(params["keyword_group_id"]))
    task_run_id, keyword_item_ids = create_search_task_batch(
        database_url=database_url,
        params=params,
        keyword_specs=keyword_specs,
    )
    on_keyword_done = build_keyword_progress_callback(database_url, keyword_item_ids)
    should_cancel = build_task_cancel_checker(database_url, task_run_id)
    rows = search_runner(
        config_path=params.get("config_path") or search_module.DEFAULT_KEYWORDS_PATH,
        output_file=output_file or None,
        engine_names=parse_engines(params.get("engines") or params.get("engine_names")),
        max_pages=int(params.get("max_pages", 2)),
        limit_keywords=optional_int(params.get("limit_keywords")),
        state_dir=state_dir,
        retry_failed_only=bool(params.get("retry_failed", False)),
        keyword_delay_seconds=float(params.get("keyword_delay_seconds", 30.0)),
        engine_request_delay_seconds=float(params.get("engine_request_delay_seconds", 10.0)),
        max_retries=int(params.get("max_retries", 3)),
        backoff_base_seconds=float(params.get("backoff_base_seconds", 20.0)),
        backoff_max_seconds=float(params.get("backoff_max_seconds", 180.0)),
        proxy_url=str(params.get("proxy_url") or ""),
        use_system_proxy=bool(params.get("use_system_proxy", True)),
        backend=str(params.get("backend") or "browser"),
        headless=bool(params.get("headless", True)),
        browser_max_pages=int(params.get("browser_max_pages", 1)),
        keyword_specs=keyword_specs,
        on_keyword_done=on_keyword_done,
        should_cancel=should_cancel,
    )
    search_source_name = output_file or task_source_name("search", task_run_id)
    database_summary = persist_search_rows_to_database(
        rows,
        database_url=database_url,
        source_name=search_source_name,
    )
    candidate_group_id = create_search_candidate_group(
        database_url=database_url,
        rows=rows,
        source_name=search_source_name,
        params=params,
        task_run_id=task_run_id,
    )
    finish_database_task_batch(database_url, task_run_id)
    result: dict[str, Any] = {
        "rows": len(rows),
        "output_file": output_file,
        "task_run_id": task_run_id,
        "candidate_group_id": candidate_group_id,
        "database_persisted": database_summary is not None,
        "database_import": import_summary_to_dict(database_summary or ImportSummary()),
    }
    task_status = get_database_task_status(database_url, task_run_id)
    if task_status:
        result["task_run_status"] = task_status
    if state_dir is not None:
        result["state_dir"] = str(state_dir)
    return result


def run_crawl_task(params: dict[str, Any], crawl_runner: CrawlRunner = crawl_module.run_crawl) -> dict[str, Any]:
    database_url = resolve_database_url(params.get("database_url"), params.get("persist_to_database"))
    input_file = str(params["input_file"]) if params.get("input_file") else ""
    output_file = str(params["output_file"]) if params.get("output_file") else ""
    explicit_state_dir = optional_non_blank_str(params.get("state_dir"))
    state_dir = explicit_state_dir if explicit_state_dir is not None else (None if database_url else crawl_module.STATE_DIR)
    max_retries = int(params.get("max_retries", 3))
    backoff_base = float(params.get("backoff_base", 1.0))
    backoff_max = float(params.get("backoff_max", 30.0))
    domain_delay = float(params.get("domain_delay", 1.0))
    fetcher_config = crawl_module.FetcherConfig(
        max_retries=max_retries,
        backoff_base_seconds=backoff_base,
        backoff_max_seconds=backoff_max,
        global_min_interval_seconds=float(params.get("global_delay", 0.2)),
        domain_min_interval_seconds=domain_delay,
        use_system_proxy=bool(params.get("use_system_proxy", True)),
        proxy_url=str(params.get("proxy") or ""),
        respect_robots=bool(params.get("respect_robots", True)),
    )
    browser_fetch_config = crawl_module.BrowserFetchConfig(
        headless=bool(params.get("headless", True)),
        network_idle=True,
        proxy=str(params.get("proxy") or ""),
        timeout_ms=int(params.get("browser_timeout_ms", 30000)),
        wait_ms=int(params.get("browser_wait_ms", 0)),
        max_pages=int(params.get("browser_max_pages", 1)),
        max_retries=max_retries,
        backoff_base_seconds=backoff_base,
        backoff_max_seconds=backoff_max,
        request_interval_seconds=domain_delay,
        respect_robots=bool(params.get("respect_robots", True)),
    )
    companies = None
    candidate_group_id = optional_int(params.get("candidate_group_id"))
    if not input_file and database_url:
        if candidate_group_id is not None:
            companies = select_crawl_candidates_from_candidate_group(
                database_url=database_url,
                candidate_group_id=candidate_group_id,
                limit=optional_int(params.get("candidate_limit")) or 50,
                recrawl_existing=bool(params.get("recrawl_existing", False)),
            )
        else:
            companies = select_crawl_candidates_from_database(
                database_url=database_url,
                country=str(params.get("candidate_country") or ""),
                query=str(params.get("candidate_query") or ""),
                limit=optional_int(params.get("candidate_limit")) or 50,
                recrawl_existing=bool(params.get("recrawl_existing", False)),
            )
    elif not input_file:
        input_file = crawl_module.INPUT_FILE
        output_file = output_file or crawl_module.OUTPUT_FILE

    task_run_id, domain_item_ids = create_crawl_task_batch(
        database_url=database_url,
        params=params,
        companies=companies,
    )
    on_domain_done = build_domain_progress_callback(database_url, domain_item_ids)
    should_cancel = build_task_cancel_checker(database_url, task_run_id)
    rows = crawl_runner(
        input_file=input_file or crawl_module.INPUT_FILE,
        output_file=output_file or None,
        state_dir=state_dir,
        workers=optional_int(params.get("workers")),
        max_depth=int(params.get("max_depth", 2)),
        max_pages_per_site=int(params.get("max_pages_per_site", 12)),
        retry_failed_only=bool(params.get("retry_failed", False)),
        fetcher_config=fetcher_config,
        browser_fetch_config=browser_fetch_config,
        backend=str(params.get("backend") or "requests"),
        profile_input_dir=optional_non_blank_str(params.get("profile_input_dir")),
        profile_page_char_limit=int(params.get("profile_page_char_limit", 8000)),
        companies=companies,
        on_domain_done=on_domain_done,
        should_cancel=should_cancel,
    )
    status_counts = Counter(str(row.get("status", "")) for row in rows)
    profile_input_dir = optional_non_blank_str(params.get("profile_input_dir"))
    database_summary = persist_crawl_rows_to_database(
        rows,
        database_url=database_url,
        source_name=output_file or task_source_name("crawl", task_run_id),
        profile_input_dir=profile_input_dir,
        candidate_group_id=candidate_group_id,
        crawl_task_run_id=task_run_id,
    )
    finish_database_task_batch(database_url, task_run_id)
    result: dict[str, Any] = {
        "rows": len(rows),
        "status_counts": dict(status_counts),
        "input_file": input_file,
        "output_file": output_file,
        "selected_from_database": companies is not None,
        "selected_from_candidate_group": candidate_group_id is not None,
        "selected_companies": len(companies) if companies is not None else None,
        "task_run_id": task_run_id,
        "candidate_group_id": candidate_group_id,
        "database_persisted": database_summary is not None,
        "database_import": import_summary_to_dict(database_summary or ImportSummary()),
    }
    task_status = get_database_task_status(database_url, task_run_id)
    if task_status:
        result["task_run_status"] = task_status
    if state_dir is not None:
        result["state_dir"] = str(state_dir)
    return result


def run_import_existing_data_task(
    params: dict[str, Any],
    root: Path = PROJECT_ROOT,
    import_sources_func: ImportSourcesFunc = import_sources,
) -> dict[str, Any]:
    search_csvs, crawl_csvs, profile_dirs = resolve_sources(
        root=root,
        search_csvs=params.get("search_csvs"),
        crawl_csvs=params.get("crawl_csvs"),
        profile_dirs=params.get("profile_dirs"),
    )
    summary = import_sources_func(
        database_url=str(params.get("database_url") or DEFAULT_DATABASE_URL),
        search_csvs=search_csvs,
        crawl_csvs=crawl_csvs,
        profile_dirs=profile_dirs,
        create_tables=bool(params.get("create_tables", True)),
    )
    return import_summary_to_dict(summary)


def run_ai_profile_task(
    params: dict[str, Any],
    analyzer: AIProfileAnalyzer | None = None,
) -> dict[str, Any]:
    database_url = resolve_database_url(params.get("database_url"), params.get("persist_to_database")) or DEFAULT_DATABASE_URL
    if not database_url:
        raise ValueError("database_url or DATABASE_URL is required for AI profile tasks")

    profile_source_group_id = optional_int(params.get("profile_source_group_id"))
    profile_package_ids = parse_int_list(params.get("profile_package_ids"))
    if profile_source_group_id is not None:
        profile_package_ids = select_profile_package_ids_from_source_group(
            database_url=database_url,
            profile_source_group_id=profile_source_group_id,
        )
    if not profile_package_ids:
        raise ValueError("profile_package_ids or profile_source_group_id is required")

    model_provider = str(params.get("model_provider") or DEFAULT_MODEL_PROVIDER)
    model_name = str(params.get("model_name") or DEFAULT_MODEL_NAME)
    prompt_version = DEFAULT_PROMPT_VERSION
    api_base_url = str(params.get("api_base_url") or DEFAULT_API_BASE_URL)
    api_key = str(params.get("api_key") or "")
    temperature = float(params.get("temperature") if params.get("temperature") is not None else DEFAULT_TEMPERATURE)
    timeout_seconds = float(params.get("timeout_seconds") if params.get("timeout_seconds") is not None else DEFAULT_TIMEOUT_SECONDS)
    task_run_id, item_ids = create_ai_profile_task_batch(
        database_url=database_url,
        params=params,
        profile_package_ids=profile_package_ids,
    )
    should_cancel = build_task_cancel_checker(database_url, task_run_id)
    created_count = 0
    updated_count = 0
    failed_count = 0

    if analyzer is None:
        client = ModelAPIClient(
            api_key=api_key,
            base_url=api_base_url,
            model=model_name,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )

        def analyzer(payload: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
            ai_result = client.analyze_profile(payload)
            return {**ai_result.content, "_raw_response": ai_result.raw_response}

    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            packages = session.scalars(
                select(ProfilePackage)
                .where(ProfilePackage.id.in_(profile_package_ids))
                .order_by(ProfilePackage.id)
            ).all()
            packages_by_id = {package.id: package for package in packages}
            for package_id in profile_package_ids:
                item_id = item_ids.get(str(package_id))
                if should_cancel():
                    break
                package = packages_by_id.get(package_id)
                if package is None:
                    if item_id is not None:
                        start_task_item(session, item_id)
                        finish_task_item(session, item_id, status="failed", error=f"Profile package not found: {package_id}")
                        failed_count += 1
                        session.commit()
                    continue
                if item_id is not None:
                    start_task_item(session, item_id)
                    session.commit()
                try:
                    result = analyzer(
                        package.payload_json,
                        {
                            "model_provider": model_provider,
                            "model_name": model_name,
                            "prompt_version": prompt_version,
                            "api_base_url": api_base_url,
                            "temperature": temperature,
                            "timeout_seconds": timeout_seconds,
                            "profile_package_id": package.id,
                        },
                    )
                    ai_profile_result, created = upsert_ai_profile_result(
                        session,
                        profile_package=package,
                        result=result,
                        model_provider=model_provider,
                        model_name=model_name,
                        prompt_version=prompt_version,
                        task_run_id=task_run_id,
                        task_item_id=item_id,
                    )
                    promoted_to_qualified_lead = sync_stage_c_from_ai_profile_result(session, ai_profile_result)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    if item_id is not None:
                        finish_task_item(
                            session,
                            item_id,
                            status="success",
                            result={
                                "profile_package_id": package.id,
                                "domain_id": package.domain_id,
                                "customer_priority": result.get("customer_priority", ""),
                                "score_total": result.get("score_total", 0),
                                "promoted_to_qualified_lead": promoted_to_qualified_lead,
                            },
                        )
                    session.commit()
                except Exception as error:
                    failed_count += 1
                    session.rollback()
                    if item_id is not None:
                        finish_task_item(session, item_id, status="failed", error=f"{error.__class__.__name__}: {error}")
                    session.commit()
    finally:
        engine.dispose()

    finish_database_task_batch(database_url, task_run_id)
    result = {
        "profile_packages": len(profile_package_ids),
        "results_created": created_count,
        "results_updated": updated_count,
        "failed": failed_count,
        "task_run_id": task_run_id,
        "profile_source_group_id": profile_source_group_id,
        "model_provider": model_provider,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "api_base_url": api_base_url,
    }
    task_status = get_database_task_status(database_url, task_run_id)
    if task_status:
        result["task_run_status"] = task_status
    return result


def parse_engines(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def optional_int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    return int(value)


def optional_non_blank_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_int_list(value: Any) -> list[int]:
    if value is None:
        return []
    raw_values = value.replace("\n", ",").split(",") if isinstance(value, str) else list(value)
    parsed: list[int] = []
    seen: set[int] = set()
    for raw in raw_values:
        text = str(raw).strip()
        if not text:
            continue
        number = int(text)
        if number in seen:
            continue
        seen.add(number)
        parsed.append(number)
    return parsed


def load_keyword_specs_from_database(database_url: str, keyword_group_id: int) -> list[search_module.KeywordSpec]:
    engine = create_engine_from_url(database_url)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            return generate_keyword_specs(session, keyword_group_id)
    finally:
        engine.dispose()


def create_search_candidate_group(
    *,
    database_url: str,
    rows: list[dict[str, str]],
    source_name: str,
    params: dict[str, Any],
    task_run_id: int | None,
) -> int | None:
    if not database_url or not rows:
        return None
    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            keyword_group_id = optional_int(params.get("keyword_group_id"))
            keyword_group = session.get(KeywordGroup, keyword_group_id) if keyword_group_id is not None else None
            country = keyword_group.country if keyword_group is not None else first_non_empty(row.get("country") for row in rows)
            name = str(params.get("candidate_group_name") or "").strip()
            if not name:
                if keyword_group is not None:
                    name = f"{keyword_group.name} search #{task_run_id}"
                elif task_run_id is not None:
                    name = f"Search task #{task_run_id} candidates"
                else:
                    name = "Search candidates"
            candidate_group = create_candidate_group_from_search_rows(
                session,
                rows=rows,
                source_name=source_name,
                name=name,
                source_task_run_id=task_run_id,
                keyword_group_id=keyword_group_id,
                country=country,
                params=safe_task_params(params),
            )
            session.commit()
            return candidate_group.id if candidate_group is not None else None
    finally:
        engine.dispose()


def select_crawl_candidates_from_candidate_group(
    *,
    database_url: str,
    candidate_group_id: int,
    limit: int = 50,
    recrawl_existing: bool = False,
) -> list[crawl_module.CompanyInput]:
    engine = create_engine_from_url(database_url)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            return select_candidate_group_companies(
                session,
                candidate_group_id,
                limit=limit,
                recrawl_existing=recrawl_existing,
            )
    finally:
        engine.dispose()


def task_source_name(task_type: str, task_run_id: int | None) -> str:
    return f"task:{task_type}:{task_run_id}" if task_run_id is not None else f"task:{task_type}:database"


def first_non_empty(values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def create_search_task_batch(
    *,
    database_url: str,
    params: dict[str, Any],
    keyword_specs: list[search_module.KeywordSpec] | None,
) -> tuple[int | None, dict[str, int]]:
    if not database_url:
        return None, {}
    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            task_run = create_task_run(
                session,
                task_type="search",
                name=str(params.get("name") or "Search task"),
                params=safe_task_params(params),
            )
            specs = keyword_specs or []
            limit = optional_int(params.get("limit_keywords"))
            if limit is not None:
                specs = specs[:limit]
            items = create_task_items(
                session,
                task_run,
                [
                    {
                        "item_type": "keyword",
                        "item_key": spec.keyword,
                    }
                    for spec in specs
                ],
            )
            start_task_run(session, task_run.id)
            session.commit()
            return task_run.id, {item.item_key: item.id for item in items}
    finally:
        engine.dispose()


def create_crawl_task_batch(
    *,
    database_url: str,
    params: dict[str, Any],
    companies: list[crawl_module.CompanyInput] | None,
) -> tuple[int | None, dict[str, int]]:
    if not database_url:
        return None, {}
    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            task_run = create_task_run(
                session,
                task_type="crawl",
                name=str(params.get("name") or "Crawl task"),
                params=safe_task_params(params),
            )
            domain_ids = {}
            for domain in session.scalars(select(Domain)).all():
                domain_ids[domain.domain] = domain.id
            items = create_task_items(
                session,
                task_run,
                [
                    {
                        "item_type": "domain",
                        "item_key": company.domain,
                        "domain_id": domain_ids.get(company.domain),
                    }
                    for company in (companies or [])
                ],
            )
            start_task_run(session, task_run.id)
            session.commit()
            return task_run.id, {item.item_key: item.id for item in items}
    finally:
        engine.dispose()


def create_ai_profile_task_batch(
    *,
    database_url: str,
    params: dict[str, Any],
    profile_package_ids: list[int],
) -> tuple[int | None, dict[str, int]]:
    if not database_url:
        return None, {}
    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            domain_ids = {
                package.id: package.domain_id
                for package in session.scalars(select(ProfilePackage).where(ProfilePackage.id.in_(profile_package_ids))).all()
            }
            task_run = create_task_run(
                session,
                task_type="ai_profile",
                name=str(params.get("name") or "AI profile task"),
                params=safe_task_params(params),
            )
            items = create_task_items(
                session,
                task_run,
                [
                    {
                        "item_type": "profile_package",
                        "item_key": str(profile_package_id),
                        "domain_id": domain_ids.get(profile_package_id),
                    }
                    for profile_package_id in profile_package_ids
                ],
            )
            start_task_run(session, task_run.id)
            session.commit()
            return task_run.id, {item.item_key: item.id for item in items}
    finally:
        engine.dispose()


def select_profile_package_ids_from_source_group(*, database_url: str, profile_source_group_id: int) -> list[int]:
    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            return list(
                session.scalars(
                    select(ProfilePackage.id)
                    .where(ProfilePackage.crawl_task_run_id == profile_source_group_id)
                    .order_by(ProfilePackage.id)
                ).all()
            )
    finally:
        engine.dispose()


def build_keyword_progress_callback(
    database_url: str,
    keyword_item_ids: dict[str, int],
) -> Callable[[dict[str, Any]], None] | None:
    if not database_url or not keyword_item_ids:
        return None

    def callback(event: dict[str, Any]) -> None:
        item_id = keyword_item_ids.get(str(event.get("keyword") or ""))
        if item_id is None:
            return
        update_task_item_from_event(database_url, item_id, event)

    return callback


def build_domain_progress_callback(
    database_url: str,
    domain_item_ids: dict[str, int],
) -> Callable[[dict[str, Any]], None] | None:
    if not database_url or not domain_item_ids:
        return None

    def callback(event: dict[str, Any]) -> None:
        item_id = domain_item_ids.get(str(event.get("domain") or ""))
        if item_id is None:
            return
        update_task_item_from_event(database_url, item_id, event)

    return callback


def update_task_item_from_event(database_url: str, item_id: int, event: dict[str, Any]) -> None:
    engine = create_engine_from_url(database_url)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            start_task_item(session, item_id)
            finish_task_item(
                session,
                item_id,
                status=str(event.get("status") or "success"),
                error=str(event.get("error") or ""),
                result=dict(event),
            )
            session.commit()
    finally:
        engine.dispose()


def build_task_cancel_checker(database_url: str, task_run_id: int | None) -> Callable[[], bool]:
    if not database_url or task_run_id is None:
        return lambda: False

    def should_cancel() -> bool:
        engine = create_engine_from_url(database_url)
        Session = create_session_factory(engine)
        try:
            with Session() as session:
                return is_task_run_cancel_requested(session, task_run_id)
        finally:
            engine.dispose()

    return should_cancel


def finish_database_task_batch(database_url: str, task_run_id: int | None) -> None:
    if not database_url or task_run_id is None:
        return
    engine = create_engine_from_url(database_url)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            if is_task_run_cancel_requested(session, task_run_id):
                cancel_unfinished_task_items(session, task_run_id)
                counts = count_task_items_by_status(session, task_run_id)
                finish_task_run(session, task_run_id, status="cancelled", summary=counts)
                session.commit()
                return
            counts = count_task_items_by_status(session, task_run_id)
            failed = counts.get("failed", 0) + counts.get("error", 0)
            success = counts.get("success", 0)
            if failed and success:
                status = "partial_failed"
            elif failed:
                status = "failed"
            else:
                status = "success"
            finish_task_run(session, task_run_id, status=status, summary=counts)
            session.commit()
    finally:
        engine.dispose()


def get_database_task_status(database_url: str, task_run_id: int | None) -> str:
    if not database_url or task_run_id is None:
        return ""
    engine = create_engine_from_url(database_url)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            task_run = session.get(TaskRun, task_run_id)
            return str(task_run.status) if task_run is not None else ""
    finally:
        engine.dispose()


def safe_task_params(params: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in params.items():
        if key == "database_url":
            safe[key] = "<configured>"
        elif key == "api_key":
            safe["api_key_configured"] = bool(str(value or "").strip())
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)
    return safe


def select_crawl_candidates_from_database(
    *,
    database_url: str,
    country: str = "",
    query: str = "",
    limit: int = 50,
    recrawl_existing: bool = False,
) -> list[crawl_module.CompanyInput]:
    engine = create_engine_from_url(database_url)
    Session = create_session_factory(engine)
    safe_limit = min(max(limit, 1), 500)
    try:
        with Session() as session:
            stmt = (
                select(Domain, SearchResult)
                .join(SearchResult, SearchResult.domain_id == Domain.id)
                .where(SearchResult.website != "")
            )
            if not recrawl_existing:
                stmt = stmt.where(~exists().where(CrawlResult.domain_id == Domain.id))

            country_text = country.strip()
            if country_text:
                country_pattern = f"%{country_text}%"
                stmt = stmt.where(
                    exists().where(
                        CountrySignal.domain_id == Domain.id,
                        CountrySignal.country.ilike(country_pattern),
                    )
                )

            query_text = query.strip()
            if query_text:
                query_pattern = f"%{query_text}%"
                stmt = stmt.where(
                    or_(
                        Domain.domain.ilike(query_pattern),
                        Domain.website.ilike(query_pattern),
                        Domain.display_name.ilike(query_pattern),
                        SearchResult.keyword.ilike(query_pattern),
                        SearchResult.title.ilike(query_pattern),
                        SearchResult.website.ilike(query_pattern),
                    )
                )

            rows = session.execute(
                stmt.order_by(Domain.domain, SearchResult.created_at.desc()).limit(safe_limit * 3)
            ).all()
            candidates: list[crawl_module.CompanyInput] = []
            seen_domains: set[str] = set()
            for domain, search_result in rows:
                if domain.domain in seen_domains:
                    continue
                website = search_result.website or domain.website
                if not website:
                    continue
                seen_domains.add(domain.domain)
                candidates.append(
                    crawl_module.CompanyInput(
                        keyword=search_result.keyword,
                        title=search_result.title or domain.display_name,
                        website=website,
                        domain=domain.domain,
                        country=search_result.country,
                        industry=search_result.industry,
                        matched_keywords=search_result.matched_keywords or search_result.keyword,
                        matched_countries=search_result.matched_countries or search_result.country,
                        matched_industries=search_result.matched_industries or search_result.industry,
                        matched_industry_terms=search_result.matched_industry_terms,
                    )
                )
                if len(candidates) >= safe_limit:
                    break
            return candidates
    finally:
        engine.dispose()
