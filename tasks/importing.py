from __future__ import annotations

from pathlib import Path

from database.importers import ImportSummary, import_crawl_csv, import_profile_dir, import_search_csv
from database.session import create_all, create_engine_from_url, create_session_factory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PROFILE_DIR_NAMES = {".codex", "heat_pump_lead_analysis_outputs", "scripts"}


def default_search_csvs(root: Path = PROJECT_ROOT) -> list[Path]:
    return sorted(path for path in root.glob("company_websites*.csv") if path.is_file())


def default_crawl_csvs(root: Path = PROJECT_ROOT) -> list[Path]:
    return sorted(path for path in root.glob("company_info*.csv") if path.is_file())


def default_profile_dirs(root: Path = PROJECT_ROOT) -> list[Path]:
    profile_root = root / "profile_inputs"
    if not profile_root.is_dir():
        return []
    dirs = [profile_root]
    dirs.extend(
        sorted(
            path
            for path in profile_root.iterdir()
            if path.is_dir() and path.name not in EXCLUDED_PROFILE_DIR_NAMES
        )
    )
    return dirs


def resolve_sources(
    root: Path,
    search_csvs: list[str] | None = None,
    crawl_csvs: list[str] | None = None,
    profile_dirs: list[str] | None = None,
) -> tuple[list[Path], list[Path], list[Path]]:
    has_explicit_sources = bool(search_csvs or crawl_csvs or profile_dirs)
    resolved_search_csvs = [Path(path) for path in search_csvs] if search_csvs is not None else []
    resolved_crawl_csvs = [Path(path) for path in crawl_csvs] if crawl_csvs is not None else []
    resolved_profile_dirs = [Path(path) for path in profile_dirs] if profile_dirs is not None else []
    if not has_explicit_sources:
        resolved_search_csvs = default_search_csvs(root)
        resolved_crawl_csvs = default_crawl_csvs(root)
        resolved_profile_dirs = default_profile_dirs(root)
    return resolved_search_csvs, resolved_crawl_csvs, resolved_profile_dirs


def import_sources(
    database_url: str,
    search_csvs: list[Path],
    crawl_csvs: list[Path],
    profile_dirs: list[Path],
    create_tables: bool,
) -> ImportSummary:
    engine = create_engine_from_url(database_url)
    if create_tables:
        create_all(engine)
    Session = create_session_factory(engine)
    total = ImportSummary()
    try:
        with Session() as session:
            for path in search_csvs:
                if not path.exists():
                    print(f"skip missing search CSV: {path}")
                    continue
                summary = import_search_csv(session, path)
                session.commit()
                total.merge(summary)
                print(f"search {path}: {format_summary(summary)}")

            for path in crawl_csvs:
                if not path.exists():
                    print(f"skip missing crawl CSV: {path}")
                    continue
                summary = import_crawl_csv(session, path)
                session.commit()
                total.merge(summary)
                print(f"crawl {path}: {format_summary(summary)}")

            for path in profile_dirs:
                if not path.exists():
                    print(f"skip missing profile dir: {path}")
                    continue
                summary = import_profile_dir(session, path)
                session.commit()
                total.merge(summary)
                print(f"profile {path}: {format_summary(summary)}")
    finally:
        engine.dispose()
    return total


def import_summary_to_dict(summary: ImportSummary | dict[str, int]) -> dict[str, int]:
    if isinstance(summary, dict):
        return dict(summary)
    return {
        "domains_created": summary.domains_created,
        "domains_updated": summary.domains_updated,
        "search_results_created": summary.search_results_created,
        "crawl_results_created": summary.crawl_results_created,
        "contacts_created": summary.contacts_created,
        "profile_packages_created": summary.profile_packages_created,
        "profile_packages_updated": summary.profile_packages_updated,
        "country_signals_created": summary.country_signals_created,
        "files_scanned": summary.files_scanned,
    }


def format_summary(summary: ImportSummary | dict[str, int]) -> str:
    values = import_summary_to_dict(summary)
    return (
        f"domains +{values.get('domains_created', 0)}/~{values.get('domains_updated', 0)}, "
        f"search +{values.get('search_results_created', 0)}, "
        f"crawl +{values.get('crawl_results_created', 0)}, "
        f"contacts +{values.get('contacts_created', 0)}, "
        f"profiles +{values.get('profile_packages_created', 0)}/~{values.get('profile_packages_updated', 0)}, "
        f"country_signals +{values.get('country_signals_created', 0)}"
    )

