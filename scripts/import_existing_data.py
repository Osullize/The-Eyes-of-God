from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.env import load_project_env
from database.session import DEFAULT_DATABASE_URL
from tasks.importing import format_summary, import_sources, resolve_sources as resolve_import_sources

load_project_env()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import existing search/crawl/profile outputs into the lead database.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL), help="SQLAlchemy database URL")
    parser.add_argument("--search-csv", action="append", default=None, help="Search CSV path; can be repeated")
    parser.add_argument("--crawl-csv", action="append", default=None, help="Crawl CSV path; can be repeated")
    parser.add_argument("--profile-dir", action="append", default=None, help="Profile JSON directory; can be repeated")
    parser.add_argument("--no-create-tables", action="store_true", help="Do not create tables before importing")
    return parser


def resolve_sources(args: argparse.Namespace, root: Path) -> tuple[list[Path], list[Path], list[Path]]:
    return resolve_import_sources(
        root=root,
        search_csvs=args.search_csv,
        crawl_csvs=args.crawl_csv,
        profile_dirs=args.profile_dir,
    )


def main() -> None:
    args = build_parser().parse_args()
    search_csvs, crawl_csvs, profile_dirs = resolve_sources(args, ROOT)
    if not search_csvs and not crawl_csvs and not profile_dirs:
        print("No import sources found.")
        return

    print(f"database: {args.database_url}")
    total = import_sources(
        database_url=args.database_url,
        search_csvs=search_csvs,
        crawl_csvs=crawl_csvs,
        profile_dirs=profile_dirs,
        create_tables=not args.no_create_tables,
    )
    print(f"total: {format_summary(total)}")


if __name__ == "__main__":
    main()
