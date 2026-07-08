from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.env import load_project_env
from database.session import DEFAULT_DATABASE_URL
from tasks.handlers import run_crawl_task, run_import_existing_data_task, run_search_task
from tasks.runner import run_task

load_project_env()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run reusable lead-generation tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Run a search task")
    search.add_argument("--config", dest="config_path", default=None)
    search.add_argument("--output", dest="output_file", default=None)
    search.add_argument("--state-dir", default=None)
    search.add_argument("--engines", default=None)
    search.add_argument("--backend", choices=["requests", "browser"], default=None)
    search.add_argument("--max-pages", type=int, default=None)
    search.add_argument("--limit-keywords", type=int, default=None)
    search.add_argument("--keyword-delay", dest="keyword_delay_seconds", type=float, default=None)
    search.add_argument("--engine-request-delay", dest="engine_request_delay_seconds", type=float, default=None)
    search.add_argument("--retry-failed", action="store_true", default=False)
    search.add_argument("--database-url", default=None)
    search.add_argument("--no-persist-to-database", dest="persist_to_database", action="store_false", default=None)

    crawl = subparsers.add_parser("crawl", help="Run a crawl task")
    crawl.add_argument("--candidate-group-id", type=int, default=None)
    crawl.add_argument("--input", dest="input_file", default=None)
    crawl.add_argument("--output", dest="output_file", default=None)
    crawl.add_argument("--state-dir", default=None)
    crawl.add_argument("--backend", choices=["requests", "browser"], default=None)
    crawl.add_argument("--workers", type=int, default=None)
    crawl.add_argument("--max-depth", type=int, default=None)
    crawl.add_argument("--max-pages-per-site", type=int, default=None)
    crawl.add_argument("--profile-input-dir", default=None)
    crawl.add_argument("--profile-page-char-limit", type=int, default=None)
    crawl.add_argument("--max-retries", type=int, default=None)
    crawl.add_argument("--backoff-base", type=float, default=None)
    crawl.add_argument("--backoff-max", type=float, default=None)
    crawl.add_argument("--global-delay", type=float, default=None)
    crawl.add_argument("--domain-delay", type=float, default=None)
    crawl.add_argument("--proxy", default=None)
    crawl.add_argument("--no-system-proxy", dest="use_system_proxy", action="store_false", default=None)
    crawl.add_argument("--headless", dest="headless", action="store_true", default=None)
    crawl.add_argument("--headed", dest="headless", action="store_false")
    crawl.add_argument("--browser-max-pages", type=int, default=None)
    crawl.add_argument("--browser-timeout-ms", type=int, default=None)
    crawl.add_argument("--browser-wait-ms", type=int, default=None)
    crawl.add_argument("--no-robots", dest="respect_robots", action="store_false", default=None)
    crawl.add_argument("--retry-failed", action="store_true", default=False)
    crawl.add_argument("--database-url", default=None)
    crawl.add_argument("--no-persist-to-database", dest="persist_to_database", action="store_false", default=None)

    import_data = subparsers.add_parser("import-existing-data", help="Import existing CSV/profile files")
    import_data.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
    import_data.add_argument("--search-csv", action="append", default=None)
    import_data.add_argument("--crawl-csv", action="append", default=None)
    import_data.add_argument("--profile-dir", action="append", default=None)
    import_data.add_argument("--no-create-tables", action="store_true")
    return parser


def params_from_args(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    if args.command == "search":
        return "search", compact_params(vars(args), exclude={"command"})
    if args.command == "crawl":
        return "crawl", compact_params(vars(args), exclude={"command"})
    if args.command == "import-existing-data":
        return (
            "import_existing_data",
            {
                "database_url": args.database_url,
                "search_csvs": args.search_csv,
                "crawl_csvs": args.crawl_csv,
                "profile_dirs": args.profile_dir,
                "create_tables": not args.no_create_tables,
            },
        )
    raise ValueError(f"Unsupported task command: {args.command}")


def compact_params(values: dict[str, Any], exclude: set[str]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if key not in exclude and value is not None}


def handler_for_task(task_type: str):
    if task_type == "search":
        return run_search_task
    if task_type == "crawl":
        return run_crawl_task
    if task_type == "import_existing_data":
        return run_import_existing_data_task
    raise ValueError(f"Unsupported task type: {task_type}")


def main() -> None:
    args = build_parser().parse_args()
    task_type, params = params_from_args(args)
    result = run_task(task_type, handler_for_task(task_type), params)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.status == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
