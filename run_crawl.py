from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from crawl.browser_fetcher import BrowserFetchConfig, BrowserFetcher
from crawl.extractors import ContactPerson, extract_company_profile
from crawl.fetcher import FetcherConfig, WebFetcher
from crawl.link_explorer import LinkExplorer
from database.stage_persistence import persist_crawl_rows_to_database, resolve_database_url
from pipeline.csv_writer import append_deduped_rows
from pipeline.state import CrawlState
from profile_analysis.input_package import build_profile_input_package, write_profile_input_package
from search.url_utils import normalize_domain


INPUT_FILE = "company_websites.csv"
OUTPUT_FILE = "company_info.csv"
STATE_DIR = ".crawl_state"


CRAWL_FIELDNAMES = [
    "keyword",
    "company_name",
    "website",
    "domain",
    "emails",
    "phones",
    "possible_address",
    "description",
    "crawled_pages",
    "status",
    "error",
    "social_links",
    "contacts",
    "page_categories",
    "country",
    "industry",
    "matched_keywords",
    "matched_countries",
    "matched_industries",
    "matched_industry_terms",
]


@dataclass(frozen=True)
class CompanyInput:
    keyword: str
    title: str
    website: str
    domain: str
    country: str = ""
    industry: str = ""
    matched_keywords: str = ""
    matched_countries: str = ""
    matched_industries: str = ""
    matched_industry_terms: str = ""


class HtmlFetcher(Protocol):
    def fetch_html(self, url: str) -> tuple[str, str]:
        ...


def normalize_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return "https://" + value


def read_input_csv(file_path: str | Path) -> list[CompanyInput]:
    rows: list[CompanyInput] = []
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            website = normalize_url(row.get("website", ""))
            if not website:
                continue
            domain = (row.get("domain") or normalize_domain(website)).strip().lower()
            if not domain:
                continue
            rows.append(
                CompanyInput(
                    keyword=row.get("keyword", ""),
                    title=row.get("title", ""),
                    website=website,
                    domain=domain,
                    country=row.get("country", ""),
                    industry=row.get("industry", ""),
                    matched_keywords=row.get("matched_keywords", ""),
                    matched_countries=row.get("matched_countries", ""),
                    matched_industries=row.get("matched_industries", ""),
                    matched_industry_terms=row.get("matched_industry_terms", ""),
                )
            )
    return dedupe_companies_by_domain(rows)


def dedupe_companies_by_domain(companies: list[CompanyInput]) -> list[CompanyInput]:
    seen: set[str] = set()
    deduped: list[CompanyInput] = []
    for company in companies:
        if company.domain in seen:
            continue
        seen.add(company.domain)
        deduped.append(company)
    return deduped


def guess_country(company: CompanyInput) -> str:
    text = " ".join(
        [
            company.country,
            company.matched_countries,
            company.keyword,
            company.matched_keywords,
        ]
    ).lower()
    if "turkey" in text or "turkiye" in text:
        return "Turkey"
    if "germany" in text or "deutschland" in text:
        return "Germany"
    if "united arab emirates" in text or "uae" in text or "dubai" in text:
        return "United Arab Emirates"
    return ""


def format_social_links(links: dict[str, str]) -> str:
    return "; ".join(f"{name}:{url}" for name, url in sorted(links.items()))


def format_contacts(contacts: list[ContactPerson]) -> str:
    values: list[str] = []
    for contact in contacts:
        value = f"{contact.name} ({contact.title}) <{contact.email}>"
        if value not in values:
            values.append(value)
    return "; ".join(values)


def select_companies(
    companies: list[CompanyInput],
    state: CrawlState,
    retry_failed_only: bool = False,
) -> list[CompanyInput]:
    if retry_failed_only:
        failed = set(state.failed_domains())
        return [company for company in companies if company.domain in failed]
    return [company for company in companies if not state.is_completed(company.domain)]


def empty_result_row(company: CompanyInput, status: str, error: str) -> dict[str, str]:
    return {
        "keyword": company.keyword,
        "company_name": company.title or company.domain,
        "website": company.website,
        "domain": company.domain,
        "emails": "",
        "phones": "",
        "possible_address": "",
        "description": "",
        "crawled_pages": "",
        "status": status,
        "error": error,
        "social_links": "",
        "contacts": "",
        "page_categories": "",
        "country": company.country,
        "industry": company.industry,
        "matched_keywords": company.matched_keywords or company.keyword,
        "matched_countries": company.matched_countries or company.country,
        "matched_industries": company.matched_industries or company.industry,
        "matched_industry_terms": company.matched_industry_terms,
    }


def crawl_company(
    company: CompanyInput,
    fetcher: HtmlFetcher,
    max_depth: int,
    max_pages_per_site: int,
    profile_input_dir: str | Path | None = None,
    profile_page_char_limit: int = 8000,
    emit_profile_package: bool = True,
) -> dict[str, Any]:
    explorer = LinkExplorer(max_depth=max_depth, max_pages_per_site=max_pages_per_site)
    records = explorer.explore(company.website, company.domain, fetcher.fetch_html)
    pages = [(record.html, record.final_url) for record in records if record.html]
    if not pages:
        return empty_result_row(company, status="empty", error="no html pages crawled")

    profile = extract_company_profile(
        pages,
        fallback_title=company.title,
        domain=company.domain,
        country=guess_country(company),
    )
    crawled_urls = [record.final_url for record in records if record.html]
    page_categories = [
        f"{record.category}:{record.final_url}"
        for record in records
        if record.html
    ]

    row: dict[str, Any] = {
        "keyword": company.keyword,
        "company_name": profile.company_name,
        "website": company.website,
        "domain": company.domain,
        "emails": "; ".join(profile.emails[:10]),
        "phones": "; ".join(profile.phones[:10]),
        "possible_address": profile.possible_address,
        "description": profile.description,
        "crawled_pages": "; ".join(crawled_urls),
        "status": "success",
        "error": "",
        "social_links": format_social_links(profile.social_links),
        "contacts": format_contacts(profile.contacts),
        "page_categories": "; ".join(page_categories),
        "country": company.country,
        "industry": company.industry,
        "matched_keywords": company.matched_keywords or company.keyword,
        "matched_countries": company.matched_countries or company.country,
        "matched_industries": company.matched_industries or company.industry,
        "matched_industry_terms": company.matched_industry_terms,
    }
    if emit_profile_package or profile_input_dir is not None:
        try:
            package = build_profile_input_package(
                company=company,
                profile=profile,
                records=records,
                status="success",
                errors=[],
                max_pages=max_pages_per_site,
                page_char_limit=profile_page_char_limit,
            )
            if emit_profile_package:
                row["_profile_package"] = package
            if profile_input_dir is not None:
                write_profile_input_package(package, Path(profile_input_dir))
        except Exception as error:
            print(f"Warning: failed to build profile input package for {company.domain}: {error}")

    return row


def resolve_workers(backend: str, requested_workers: int | None) -> int:
    if backend == "browser":
        return 1
    if requested_workers is not None:
        return requested_workers
    return 1 if backend == "browser" else 4


def build_crawl_fetcher(
    backend: str,
    fetcher_config: FetcherConfig | None,
    browser_fetch_config: BrowserFetchConfig | None,
) -> HtmlFetcher:
    if backend == "requests":
        return WebFetcher(fetcher_config or FetcherConfig())
    if backend == "browser":
        return BrowserFetcher(browser_fetch_config or BrowserFetchConfig())
    raise ValueError(f"Unsupported crawl backend: {backend}")


def run_crawl(
    input_file: str | Path = INPUT_FILE,
    output_file: str | Path | None = OUTPUT_FILE,
    state_dir: str | Path | None = STATE_DIR,
    workers: int | None = None,
    max_depth: int = 2,
    max_pages_per_site: int = 12,
    retry_failed_only: bool = False,
    fetcher_config: FetcherConfig | None = None,
    browser_fetch_config: BrowserFetchConfig | None = None,
    backend: str = "requests",
    fetcher: HtmlFetcher | None = None,
    profile_input_dir: str | Path | None = None,
    profile_page_char_limit: int = 8000,
    emit_profile_package: bool = True,
    companies: list[CompanyInput] | None = None,
    on_domain_done: Callable[[dict[str, Any]], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> list[dict[str, Any]]:
    workers = resolve_workers(backend, workers)
    if workers < 1:
        raise ValueError("workers must be >= 1")
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    if max_pages_per_site < 1:
        raise ValueError("max_pages_per_site must be >= 1")
    if (emit_profile_package or profile_input_dir is not None) and profile_page_char_limit < 1:
        raise ValueError("profile_page_char_limit must be >= 1")

    companies = companies if companies is not None else read_input_csv(input_file)
    state = CrawlState(state_dir) if state_dir is not None else None
    if state is None:
        selected = [] if retry_failed_only else companies
    else:
        selected = select_companies(companies, state, retry_failed_only=retry_failed_only)
    active_fetcher = fetcher or build_crawl_fetcher(backend, fetcher_config, browser_fetch_config)
    results: list[dict[str, Any]] = []

    print(f"Loaded {len(companies)} domains; selected {len(selected)} for crawl.")
    if not selected:
        close = getattr(active_fetcher, "close", None)
        if callable(close):
            close()
        return results

    try:
        if workers <= 1:
            for index, company in enumerate(selected, start=1):
                if is_cancel_requested(should_cancel):
                    print("Crawl cancelled before next domain.")
                    break
                try:
                    row = crawl_company(
                        company,
                        active_fetcher,
                        max_depth,
                        max_pages_per_site,
                        profile_input_dir=profile_input_dir,
                        profile_page_char_limit=profile_page_char_limit,
                        emit_profile_package=emit_profile_package,
                    )
                except Exception as error:
                    row = empty_result_row(company, status="error", error=str(error))

                if output_file:
                    append_deduped_rows(output_file, [row], fieldnames=CRAWL_FIELDNAMES, key_field="domain")
                if row["status"] == "success" and state is not None:
                    state.mark_completed(company.domain)
                elif state is not None:
                    state.mark_failed(company.domain, row["error"] or row["status"])

                if on_domain_done is not None:
                    on_domain_done(
                        {
                            "domain": company.domain,
                            "status": row["status"],
                            "error": row["error"],
                            "company_name": row["company_name"],
                        }
                    )

                results.append(row)
                print(f"[{index}/{len(selected)}] {company.domain}: {row['status']}")
                if is_cancel_requested(should_cancel):
                    print("Crawl cancelled after domain.")
                    break
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                selected_iter = iter(selected)
                future_to_company = {}

                def submit_next() -> bool:
                    if is_cancel_requested(should_cancel):
                        return False
                    try:
                        company = next(selected_iter)
                    except StopIteration:
                        return False
                    future = executor.submit(
                        crawl_company,
                        company,
                        active_fetcher,
                        max_depth,
                        max_pages_per_site,
                        profile_input_dir=profile_input_dir,
                        profile_page_char_limit=profile_page_char_limit,
                        emit_profile_package=emit_profile_package,
                    )
                    future_to_company[future] = company
                    return True

                for _ in range(workers):
                    if not submit_next():
                        break

                index = 0
                while future_to_company:
                    for future in as_completed(list(future_to_company)):
                        break
                    company = future_to_company[future]
                    del future_to_company[future]
                    index += 1
                    try:
                        row = future.result()
                    except Exception as error:
                        row = empty_result_row(company, status="error", error=str(error))

                    if output_file:
                        append_deduped_rows(output_file, [row], fieldnames=CRAWL_FIELDNAMES, key_field="domain")
                    if row["status"] == "success" and state is not None:
                        state.mark_completed(company.domain)
                    elif state is not None:
                        state.mark_failed(company.domain, row["error"] or row["status"])

                    if on_domain_done is not None:
                        on_domain_done(
                            {
                                "domain": company.domain,
                                "status": row["status"],
                                "error": row["error"],
                                "company_name": row["company_name"],
                            }
                        )

                    results.append(row)
                    print(f"[{index}/{len(selected)}] {company.domain}: {row['status']}")
                    if not is_cancel_requested(should_cancel):
                        submit_next()
    finally:
        close = getattr(active_fetcher, "close", None)
        if callable(close):
            close()

    return results


def is_cancel_requested(should_cancel: Callable[[], bool] | None) -> bool:
    return bool(should_cancel and should_cancel())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl company websites and append extracted public info to CSV.")

    # 输入/输出参数：这些参数决定从哪个官网列表开始抓取、结果 CSV 写到哪里、
    # 是否额外导出给画像分析 Agent 使用的 JSON 输入包。
    parser.add_argument("--input", default=INPUT_FILE, help="Input CSV from run_search.py")
    parser.add_argument("--output", default=OUTPUT_FILE, help="Output CSV path")
    parser.add_argument(
        "--profile-input-dir",
        default="",
        help="Optional legacy directory for per-company JSON files; profile JSON is persisted to database when enabled",
    )
    parser.add_argument(
        "--profile-page-char-limit",
        type=int,
        default=8000,
        help="Maximum visible text characters per crawled page in profile-analysis input packages",
    )
    parser.add_argument("--state-dir", default=STATE_DIR, help="Directory for completed and failed crawl state")

    # 抓取范围参数：这些参数直接影响“每家公司抓多少信息”。
    # 想提高画像信息量时，优先调大 --max-depth 和 --max-pages-per-site。
    parser.add_argument("--backend", choices=["requests", "browser"], default="browser", help="Fetch backend")
    parser.add_argument("--workers", type=int, default=None, help="Maximum concurrent company crawls")
    parser.add_argument("--max-depth", type=int, default=2, help="BFS link depth per website")
    parser.add_argument("--max-pages-per-site", type=int, default=12, help="Maximum pages per website")

    # 失败恢复和限速参数：这些参数控制失败重试和请求节奏。
    # workers/delay 设得太激进时更容易被网站限流；正式跑建议保守一点。
    parser.add_argument("--retry-failed", action="store_true", help="Only retry domains in the failed queue")
    parser.add_argument("--max-retries", type=int, default=3, help="HTTP attempts per URL")
    parser.add_argument("--backoff-base", type=float, default=1.0, help="Base seconds for exponential backoff")
    parser.add_argument("--backoff-max", type=float, default=30.0, help="Maximum backoff seconds")
    parser.add_argument("--global-delay", type=float, default=0.2, help="Minimum seconds between any two requests")
    parser.add_argument("--domain-delay", type=float, default=1.0, help="Minimum seconds between requests to one domain")

    # 网络参数：用于显式指定代理，或忽略当前终端/系统环境里的代理变量。
    parser.add_argument("--proxy", default="", help="Optional HTTP/HTTPS proxy URL")
    parser.add_argument("--no-system-proxy", action="store_true", help="Ignore system proxy environment variables")

    # 浏览器模式参数：仅在 --backend browser 时生效。
    # 遇到动态渲染网站、requests 抓不到正文时，再切换到 browser 后端。
    parser.add_argument("--headless", dest="headless", action="store_true", default=True, help="Run browser hidden")
    parser.add_argument("--headed", dest="headless", action="store_false", help="Run browser visibly")
    parser.add_argument("--browser-max-pages", type=int, default=1, help="Maximum pages in the browser session pool")
    parser.add_argument("--browser-timeout-ms", type=int, default=30000, help="Browser operation timeout in milliseconds")
    parser.add_argument("--browser-wait-ms", type=int, default=0, help="Extra browser wait after page stability in milliseconds")

    # robots.txt 开关：默认尊重网站 robots.txt；必要时可用 --no-robots 关闭。
    parser.add_argument(
        "--no-robots",
        dest="respect_robots",
        action="store_false",
        default=True,
        help="Disable robots.txt checks",
    )
    # 数据库参数：配置 DATABASE_URL 或传入 --database-url 后，抓取阶段产出会写入数据库。
    parser.add_argument("--database-url", default=None, help="Optional SQLAlchemy database URL for stage persistence")
    parser.add_argument(
        "--no-persist-to-database",
        dest="persist_to_database",
        action="store_false",
        default=None,
        help="Do not persist this crawl run to the database even when DATABASE_URL is set",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = FetcherConfig(
        max_retries=args.max_retries,
        backoff_base_seconds=args.backoff_base,
        backoff_max_seconds=args.backoff_max,
        global_min_interval_seconds=args.global_delay,
        domain_min_interval_seconds=args.domain_delay,
        use_system_proxy=not args.no_system_proxy,
        proxy_url=args.proxy,
        respect_robots=args.respect_robots,
    )
    browser_config = BrowserFetchConfig(
        headless=args.headless,
        network_idle=True,
        proxy=args.proxy,
        timeout_ms=args.browser_timeout_ms,
        wait_ms=args.browser_wait_ms,
        max_pages=args.browser_max_pages,
        max_retries=args.max_retries,
        backoff_base_seconds=args.backoff_base,
        backoff_max_seconds=args.backoff_max,
        request_interval_seconds=args.domain_delay,
        respect_robots=args.respect_robots,
    )
    rows = run_crawl(
        input_file=args.input,
        output_file=args.output,
        state_dir=args.state_dir,
        workers=resolve_workers(args.backend, args.workers),
        max_depth=args.max_depth,
        max_pages_per_site=args.max_pages_per_site,
        retry_failed_only=args.retry_failed,
        fetcher_config=config,
        browser_fetch_config=browser_config,
        backend=args.backend,
        profile_input_dir=args.profile_input_dir or None,
        profile_page_char_limit=args.profile_page_char_limit,
    )
    database_summary = persist_crawl_rows_to_database(
        rows,
        database_url=resolve_database_url(args.database_url, args.persist_to_database),
        source_name=args.output,
        profile_input_dir=args.profile_input_dir,
    )
    print(f"Done. Wrote {len(rows)} crawl results to {args.output}")
    if database_summary is not None:
        print(
            "Database persisted: "
            f"{database_summary.domains_created} domains created, "
            f"{database_summary.domains_updated} domains updated, "
            f"{database_summary.crawl_results_created} crawl results created, "
            f"{database_summary.contacts_created} contacts created, "
            f"{database_summary.profile_packages_created} profile packages created, "
            f"{database_summary.country_signals_created} country signals created."
        )


if __name__ == "__main__":
    main()
