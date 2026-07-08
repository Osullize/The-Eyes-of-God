from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
import time
from typing import Any, Callable

from config.keywords import DEFAULT_KEYWORDS_PATH, KeywordSpec, build_keywords_from_config
from config.search import DEFAULT_SEARCH_CONFIG_PATH, SearchRuntimeConfig, load_search_config
from crawl.browser_fetcher import BrowserFetchConfig, BrowserFetcher
from database.stage_persistence import persist_search_rows_to_database, resolve_database_url
from pipeline.csv_writer import append_deduped_rows
from pipeline.search_state import SearchState
from search.aggregator import SearchAggregator
from search.base import SearchEngine, SearchResult
from search.engines import BingEngine, DuckDuckGoEngine


OUTPUT_FILE = "company_websites.csv"
STATE_DIR = ".search_state"


FIELDNAMES = [
    "keyword",
    "title",
    "website",
    "domain",
    "source_url",
    "engine",
    "country",
    "country_term",
    "industry",
    "industry_term",
    "matched_keywords",
    "matched_countries",
    "matched_industries",
    "matched_industry_terms",
]


def build_engines(
    engine_names: list[str],
    max_pages: int,
    engine_request_delay_seconds: float,
    max_retries: int,
    backoff_base_seconds: float,
    backoff_max_seconds: float,
    proxy_url: str = "",
    use_system_proxy: bool = True,
    backend: str = "browser",
    headless: bool = True,
    browser_max_pages: int = 1,
) -> list[SearchEngine]:
    engines: list[SearchEngine] = []
    browser_fetcher: BrowserFetcher | None = None
    if backend == "browser":
        browser_fetcher = BrowserFetcher(
            BrowserFetchConfig(
                headless=headless,
                network_idle=True,
                proxy=proxy_url,
                max_pages=browser_max_pages,
                max_retries=max_retries,
                backoff_base_seconds=backoff_base_seconds,
                backoff_max_seconds=backoff_max_seconds,
                request_interval_seconds=engine_request_delay_seconds,
                respect_robots=False,
            )
        )
    elif backend != "requests":
        raise ValueError(f"Unsupported search backend: {backend}")

    for name in engine_names:
        normalized = name.strip().lower()
        if normalized == "duckduckgo":
            engines.append(
                DuckDuckGoEngine(
                    max_pages=max_pages,
                    request_interval_seconds=engine_request_delay_seconds,
                    max_retries=max_retries,
                    backoff_base_seconds=backoff_base_seconds,
                    backoff_max_seconds=backoff_max_seconds,
                    proxy_url=proxy_url,
                    use_system_proxy=use_system_proxy,
                    fetcher=browser_fetcher,
                )
            )
        elif normalized == "bing":
            engines.append(
                BingEngine(
                    max_pages=max_pages,
                    request_interval_seconds=engine_request_delay_seconds,
                    max_retries=max_retries,
                    backoff_base_seconds=backoff_base_seconds,
                    backoff_max_seconds=backoff_max_seconds,
                    proxy_url=proxy_url,
                    use_system_proxy=use_system_proxy,
                    fetcher=browser_fetcher,
                )
            )
        elif normalized:
            raise ValueError(f"Unsupported search engine: {name}")
    return engines


def result_to_row(result: SearchResult, spec: KeywordSpec) -> dict[str, str]:
    row = asdict(result)
    row.update(
        {
            "country": spec.country,
            "country_term": spec.country_term,
            "industry": spec.industry,
            "industry_term": spec.industry_term,
        }
    )
    return {field: str(row.get(field, "")) for field in FIELDNAMES}


def append_unique_value(row: dict[str, str], field: str, value: str) -> None:
    if not value:
        return
    current = [item.strip() for item in row.get(field, "").split(";") if item.strip()]
    if value not in current:
        current.append(value)
    row[field] = "; ".join(current)


def aggregate_domain_rows(
    rows_by_domain: dict[str, dict[str, str]],
    result: SearchResult,
    spec: KeywordSpec,
) -> None:
    row = rows_by_domain.get(result.domain)
    if row is None:
        row = result_to_row(result, spec)
        row["matched_keywords"] = ""
        row["matched_countries"] = ""
        row["matched_industries"] = ""
        row["matched_industry_terms"] = ""
        rows_by_domain[result.domain] = row
    else:
        append_unique_value(row, "source_url", result.source_url)
        append_unique_value(row, "engine", result.engine)

    append_unique_value(row, "matched_keywords", spec.keyword)
    append_unique_value(row, "matched_countries", spec.country)
    append_unique_value(row, "matched_industries", spec.industry)
    append_unique_value(row, "matched_industry_terms", spec.industry_term)


def load_existing_output_rows(output_file: str | Path) -> dict[str, dict[str, str]]:
    output_path = Path(output_file)
    if not output_path.exists() or output_path.stat().st_size == 0:
        return {}

    rows_by_domain: dict[str, dict[str, str]] = {}
    with output_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            domain = (row.get("domain") or "").strip().lower()
            if not domain:
                continue
            rows_by_domain[domain] = {field: str(row.get(field, "")) for field in FIELDNAMES}
    return rows_by_domain


def run_search(
    config_path: str | Path = DEFAULT_KEYWORDS_PATH,
    output_file: str | Path | None = OUTPUT_FILE,
    engine_names: list[str] | None = None,
    engines: list[SearchEngine] | None = None,
    max_pages: int = 2,
    limit_keywords: int | None = None,
    state_dir: str | Path | None = STATE_DIR,
    retry_failed_only: bool = False,
    keyword_delay_seconds: float = 30.0,
    engine_request_delay_seconds: float = 10.0,
    max_retries: int = 3,
    backoff_base_seconds: float = 20.0,
    backoff_max_seconds: float = 180.0,
    proxy_url: str = "",
    use_system_proxy: bool = True,
    backend: str = "browser",
    headless: bool = True,
    browser_max_pages: int = 1,
    keyword_specs: list[KeywordSpec] | None = None,
    on_keyword_done: Callable[[dict[str, Any]], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> list[dict[str, str]]:
    active_keyword_specs = keyword_specs if keyword_specs is not None else build_keywords_from_config(config_path)
    if limit_keywords is not None:
        active_keyword_specs = active_keyword_specs[:limit_keywords]

    search_state = SearchState(state_dir) if state_dir is not None else None
    if retry_failed_only:
        failed_keywords = set(search_state.failed_keywords()) if search_state is not None else set()
        active_keyword_specs = [spec for spec in active_keyword_specs if spec.keyword in failed_keywords]
    elif search_state is not None:
        active_keyword_specs = [spec for spec in active_keyword_specs if not search_state.is_completed(spec.keyword)]

    active_engines = engines or build_engines(
        engine_names or ["duckduckgo"],
        max_pages=max_pages,
        engine_request_delay_seconds=engine_request_delay_seconds,
        max_retries=max_retries,
        backoff_base_seconds=backoff_base_seconds,
        backoff_max_seconds=backoff_max_seconds,
        proxy_url=proxy_url,
        use_system_proxy=use_system_proxy,
        backend=backend,
        headless=headless,
        browser_max_pages=browser_max_pages,
    )
    aggregator_workers = 1 if backend == "browser" else len(active_engines)
    aggregator = SearchAggregator(engines=active_engines, max_workers=aggregator_workers)

    rows_by_domain = load_existing_output_rows(output_file) if output_file else {}
    changed_domains: set[str] = set()
    try:
        for index, spec in enumerate(active_keyword_specs, start=1):
            if is_cancel_requested(should_cancel):
                print("Search cancelled before next keyword.")
                break
            print(f"[{index}/{len(active_keyword_specs)}] Searching: {spec.keyword}")
            batch = aggregator.search_keyword(spec.keyword)
            for engine_name, error in batch.errors.items():
                print(f"  Engine blocked/failed: {engine_name}: {error}")

            before_count = len(rows_by_domain)
            added = 0
            for result in batch.results:
                aggregate_domain_rows(rows_by_domain, result, spec)
                changed_domains.add(result.domain)
                if len(rows_by_domain) > before_count:
                    added += 1
                    before_count = len(rows_by_domain)

            if output_file and changed_domains:
                append_deduped_rows(
                    output_file,
                    [rows_by_domain[domain] for domain in sorted(changed_domains)],
                    fieldnames=FIELDNAMES,
                    key_field="domain",
                )
                changed_domains.clear()

            status = "failed" if batch.errors else "success"
            error_text = "; ".join(f"{name}: {error}" for name, error in batch.errors.items())
            if batch.errors and search_state is not None:
                search_state.mark_failed(
                    spec.keyword,
                    error_text,
                )
            elif search_state is not None:
                search_state.mark_completed(spec.keyword)

            if on_keyword_done is not None:
                on_keyword_done(
                    {
                        "keyword": spec.keyword,
                        "status": status,
                        "error": error_text,
                        "added": added,
                        "result_count": len(batch.results),
                        "total_unique_domains": len(rows_by_domain),
                    }
                )

            print(f"  Added {added}; total unique domains: {len(rows_by_domain)}")
            if is_cancel_requested(should_cancel):
                print("Search cancelled after keyword.")
                break
            if index < len(active_keyword_specs) and keyword_delay_seconds > 0:
                if sleep_until_done_or_cancelled(keyword_delay_seconds, should_cancel):
                    print("Search cancelled during keyword delay.")
                    break
    finally:
        for engine in active_engines:
            fetcher = getattr(engine, "fetcher", None)
            close = getattr(fetcher, "close", None)
            if callable(close):
                close()

    rows = list(rows_by_domain.values())
    return rows


def is_cancel_requested(should_cancel: Callable[[], bool] | None) -> bool:
    return bool(should_cancel and should_cancel())


def sleep_until_done_or_cancelled(seconds: float, should_cancel: Callable[[], bool] | None) -> bool:
    deadline = time.monotonic() + seconds
    while True:
        if is_cancel_requested(should_cancel):
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return is_cancel_requested(should_cancel)
        time.sleep(min(remaining, 0.5))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search company websites from configured keyword combinations.")

    # 输入/输出参数：这些参数决定关键词配置从哪里读、官网搜索结果写到哪里、
    # 以及断点续跑/失败重试的状态文件保存到哪里。
    parser.add_argument("--search-config", default=str(DEFAULT_SEARCH_CONFIG_PATH), help="Path to config/search.yaml")
    parser.add_argument("--config", default=None, help="Path to config/keywords.yaml")
    parser.add_argument("--output", default=None, help="CSV output path")
    parser.add_argument("--state-dir", default=None, help="Directory for completed and failed search keyword state")

    # 搜索范围参数：这些参数直接影响“信息源覆盖面”。
    # 想多找官网时，优先增加 --max-pages；测试时用 --limit-keywords 限制关键词数量。
    parser.add_argument("--backend", choices=["requests", "browser"], default=None, help="Fetch backend")
    parser.add_argument("--engines", default=None, help="Comma-separated engines: duckduckgo,bing")
    parser.add_argument("--max-pages", type=int, default=None, help="Pages per search engine")
    parser.add_argument("--limit-keywords", type=int, default=None, help="Limit keyword count for smoke tests")

    # 失败恢复和限速参数：这些参数用于断点续跑、失败关键词重试、
    # HTTP 重试退避，以及降低被搜索引擎限流/阻断的概率。
    parser.add_argument("--retry-failed", action="store_true", default=None, help="Only retry keywords in failed search queue")
    parser.add_argument("--keyword-delay", type=float, default=None, help="Minimum seconds between keywords")
    parser.add_argument("--engine-request-delay", type=float, default=None, help="Minimum seconds between requests to one engine")
    parser.add_argument("--max-retries", type=int, default=None, help="Search HTTP attempts per page")
    parser.add_argument("--backoff-base", type=float, default=None, help="Base seconds for search exponential backoff")
    parser.add_argument("--backoff-max", type=float, default=None, help="Maximum seconds for search backoff")

    # 网络参数：用于显式指定代理，或决定是否读取当前终端/系统环境里的代理变量。
    parser.add_argument("--proxy", default=None, help="Optional HTTP/HTTPS proxy URL")
    parser.add_argument(
        "--system-proxy",
        dest="use_system_proxy",
        action="store_true",
        default=None,
        help="Use system proxy environment variables",
    )
    parser.add_argument(
        "--no-system-proxy",
        dest="use_system_proxy",
        action="store_false",
        default=None,
        help="Ignore system proxy environment variables",
    )

    # 浏览器模式参数：仅在 --backend browser 时生效，需要安装 scrapling。
    # 搜索引擎页面被 requests 阻断时，browser 后端通常更接近真实浏览器访问。
    parser.add_argument("--headless", dest="headless", action="store_true", default=None, help="Run browser hidden")
    parser.add_argument("--headed", dest="headless", action="store_false", help="Run browser visibly")
    parser.add_argument("--browser-max-pages", type=int, default=None, help="Maximum pages in the browser session pool")

    # 数据库参数：配置 DATABASE_URL 或传入 --database-url 后，搜索阶段产出的官网候选会写入数据库。
    parser.add_argument("--database-url", default=None, help="Optional SQLAlchemy database URL for stage persistence")
    parser.add_argument(
        "--no-persist-to-database",
        dest="persist_to_database",
        action="store_false",
        default=None,
        help="Do not persist this search run to the database even when DATABASE_URL is set",
    )
    return parser


def _arg_or_config(value: Any, fallback: Any) -> Any:
    return fallback if value is None else value


def resolve_search_run_config(args: argparse.Namespace) -> SearchRuntimeConfig:
    base_config = load_search_config(args.search_config) if args.search_config else SearchRuntimeConfig()

    return SearchRuntimeConfig(
        keyword_config=str(_arg_or_config(args.config, base_config.keyword_config)),
        output=str(_arg_or_config(args.output, base_config.output)),
        state_dir=str(_arg_or_config(args.state_dir, base_config.state_dir)),
        backend=str(_arg_or_config(args.backend, base_config.backend)),
        engines=(
            tuple(item.strip() for item in args.engines.split(",") if item.strip())
            if args.engines is not None
            else base_config.engines
        ),
        max_pages=int(_arg_or_config(args.max_pages, base_config.max_pages)),
        limit_keywords=_arg_or_config(args.limit_keywords, base_config.limit_keywords),
        retry_failed=bool(_arg_or_config(args.retry_failed, base_config.retry_failed)),
        keyword_delay=float(_arg_or_config(args.keyword_delay, base_config.keyword_delay)),
        engine_request_delay=float(_arg_or_config(args.engine_request_delay, base_config.engine_request_delay)),
        max_retries=int(_arg_or_config(args.max_retries, base_config.max_retries)),
        backoff_base=float(_arg_or_config(args.backoff_base, base_config.backoff_base)),
        backoff_max=float(_arg_or_config(args.backoff_max, base_config.backoff_max)),
        proxy=str(_arg_or_config(args.proxy, base_config.proxy) or ""),
        use_system_proxy=bool(_arg_or_config(args.use_system_proxy, base_config.use_system_proxy)),
        headless=bool(_arg_or_config(args.headless, base_config.headless)),
        browser_max_pages=int(_arg_or_config(args.browser_max_pages, base_config.browser_max_pages)),
    )


def parse_args() -> argparse.Namespace:
    parser = build_parser()
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = resolve_search_run_config(args)
    rows = run_search(
        config_path=config.keyword_config,
        output_file=config.output,
        engine_names=list(config.engines),
        max_pages=config.max_pages,
        limit_keywords=config.limit_keywords,
        state_dir=config.state_dir,
        retry_failed_only=config.retry_failed,
        keyword_delay_seconds=config.keyword_delay,
        engine_request_delay_seconds=config.engine_request_delay,
        max_retries=config.max_retries,
        backoff_base_seconds=config.backoff_base,
        backoff_max_seconds=config.backoff_max,
        proxy_url=config.proxy,
        use_system_proxy=config.use_system_proxy,
        backend=config.backend,
        headless=config.headless,
        browser_max_pages=config.browser_max_pages,
    )
    database_summary = persist_search_rows_to_database(
        rows,
        database_url=resolve_database_url(args.database_url, args.persist_to_database),
        source_name=config.output,
    )
    print(f"Done. Saved {len(rows)} unique websites to {config.output}")
    if database_summary is not None:
        print(
            "Database persisted: "
            f"{database_summary.domains_created} domains created, "
            f"{database_summary.domains_updated} domains updated, "
            f"{database_summary.search_results_created} search results created, "
            f"{database_summary.country_signals_created} country signals created."
        )


if __name__ == "__main__":
    main()
