from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from database.importers import ImportSummary, import_crawl_rows, import_profile_dir, import_search_rows
from database.session import create_all, create_engine_from_url, create_session_factory


def resolve_database_url(database_url: str | None = None, persist_to_database: bool | None = None) -> str:
    if persist_to_database is False:
        return ""
    return str(database_url or os.environ.get("DATABASE_URL") or "")


def persist_search_rows_to_database(
    rows: list[dict[str, Any]],
    database_url: str,
    source_name: str,
) -> ImportSummary | None:
    if not database_url:
        return None
    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    try:
        with Session() as session:
            summary = import_search_rows(session, rows, source_name=source_name)
            session.commit()
            return summary
    finally:
        engine.dispose()


def persist_crawl_rows_to_database(
    rows: list[dict[str, Any]],
    database_url: str,
    source_name: str,
    profile_input_dir: str | Path | None,
    candidate_group_id: int | None = None,
    crawl_task_run_id: int | None = None,
) -> ImportSummary | None:
    if not database_url:
        return None
    engine = create_engine_from_url(database_url)
    create_all(engine)
    Session = create_session_factory(engine)
    total = ImportSummary()
    try:
        with Session() as session:
            total.merge(
                import_crawl_rows(
                    session,
                    rows,
                    source_name=source_name,
                    candidate_group_id=candidate_group_id,
                    crawl_task_run_id=crawl_task_run_id,
                )
            )
            if profile_input_dir:
                total.merge(
                    import_profile_dir(
                        session,
                        profile_input_dir,
                        candidate_group_id=candidate_group_id,
                        crawl_task_run_id=crawl_task_run_id,
                    )
                )
            session.commit()
            return total
    finally:
        engine.dispose()
