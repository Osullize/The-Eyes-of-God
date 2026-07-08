from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.env import load_project_env
from database.session import DEFAULT_DATABASE_URL


load_project_env()


@dataclass(frozen=True)
class CleanupTarget:
    search_task_id: int
    candidate_group_id: int
    crawl_task_ids: tuple[int, ...]

    @property
    def search_source(self) -> str:
        return f"task:search:{self.search_task_id}"

    @property
    def crawl_sources(self) -> tuple[str, ...]:
        return tuple(f"task:crawl:{task_id}" for task_id in self.crawl_task_ids)

    @property
    def task_ids(self) -> tuple[int, ...]:
        return (self.search_task_id, *self.crawl_task_ids)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remove one search/crawl task chain from the lead database. Defaults target the Italy heating run."
    )
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--search-task-id", type=int, default=19)
    parser.add_argument("--candidate-group-id", type=int, default=3)
    parser.add_argument("--crawl-task-id", type=int, action="append", default=[20, 21, 22])
    parser.add_argument("--execute", action="store_true", help="Actually delete records. Without this, only prints a dry-run.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    target = CleanupTarget(
        search_task_id=args.search_task_id,
        candidate_group_id=args.candidate_group_id,
        crawl_task_ids=tuple(args.crawl_task_id),
    )
    engine = create_engine(args.database_url)
    try:
        with engine.begin() as conn:
            plan = collect_cleanup_plan(conn, target)
            print_plan(plan, target, execute=args.execute)
            if not args.execute:
                print("\nDRY RUN ONLY. Add --execute to delete these records.")
                return
            execute_cleanup(conn, plan, target)
            print("\nCleanup committed.")
    finally:
        engine.dispose()


def collect_cleanup_plan(conn: Any, target: CleanupTarget) -> dict[str, Any]:
    search_result_ids = fetch_ids(
        conn,
        "select id from search_results where source_file = :source",
        {"source": target.search_source},
    )
    crawl_result_ids = fetch_ids(
        conn,
        "select id from crawl_results where source_file = any(:sources)",
        {"sources": list(target.crawl_sources)},
    )
    profile_package_ids = fetch_ids(
        conn,
        """
        select id
        from profile_packages
        where crawl_task_run_id = any(:crawl_task_ids)
           or candidate_group_id = :candidate_group_id
           or crawl_result_id = any(:crawl_result_ids)
        """,
        {
            "crawl_task_ids": list(target.crawl_task_ids),
            "candidate_group_id": target.candidate_group_id,
            "crawl_result_ids": list(crawl_result_ids) or [-1],
        },
    )
    candidate_group_item_ids = fetch_ids(
        conn,
        "select id from candidate_group_items where group_id = :candidate_group_id",
        {"candidate_group_id": target.candidate_group_id},
    )
    target_domain_ids = fetch_ids(
        conn,
        """
        select distinct domain_id from search_results where id = any(:search_result_ids)
        union
        select distinct domain_id from crawl_results where id = any(:crawl_result_ids)
        union
        select distinct domain_id from profile_packages where id = any(:profile_package_ids)
        union
        select distinct domain_id from candidate_group_items where id = any(:candidate_group_item_ids)
        """,
        {
            "search_result_ids": list(search_result_ids) or [-1],
            "crawl_result_ids": list(crawl_result_ids) or [-1],
            "profile_package_ids": list(profile_package_ids) or [-1],
            "candidate_group_item_ids": list(candidate_group_item_ids) or [-1],
        },
    )
    ai_profile_rows = fetch_rows(
        conn,
        """
        select id,
               domain_id,
               'ai_profile:' ||
               coalesce(nullif(prompt_version, ''), 'unknown_prompt') || ':' ||
               coalesce(nullif(model_provider, ''), 'unknown_provider') || ':' ||
               coalesce(nullif(model_name, ''), 'unknown_model') as stage_c_source
        from ai_profile_results
        where profile_package_id = any(:profile_package_ids)
        """,
        {"profile_package_ids": list(profile_package_ids) or [-1]},
    )
    ai_profile_result_ids = {int(row["id"]) for row in ai_profile_rows}
    safe_stage_c_pairs = collect_safe_stage_c_pairs(conn, ai_profile_rows, profile_package_ids)
    orphan_domain_ids = collect_orphan_domain_ids(
        conn,
        target_domain_ids=target_domain_ids,
        search_result_ids=search_result_ids,
        crawl_result_ids=crawl_result_ids,
        profile_package_ids=profile_package_ids,
        ai_profile_result_ids=ai_profile_result_ids,
        candidate_group_item_ids=candidate_group_item_ids,
    )
    country_signal_ids = fetch_ids(
        conn,
        """
        select id
        from country_signals
        where domain_id = any(:domain_ids)
          and source = any(:sources)
        """,
        {
            "domain_ids": list(target_domain_ids) or [-1],
            "sources": [target.search_source, *target.crawl_sources, "profile_json"],
        },
    )
    task_item_ids = fetch_ids(
        conn,
        "select id from task_items where task_run_id = any(:task_ids)",
        {"task_ids": list(target.task_ids)},
    )

    return {
        "search_result_ids": search_result_ids,
        "crawl_result_ids": crawl_result_ids,
        "profile_package_ids": profile_package_ids,
        "candidate_group_item_ids": candidate_group_item_ids,
        "target_domain_ids": target_domain_ids,
        "ai_profile_result_ids": ai_profile_result_ids,
        "safe_stage_c_pairs": safe_stage_c_pairs,
        "orphan_domain_ids": orphan_domain_ids,
        "country_signal_ids": country_signal_ids,
        "task_item_ids": task_item_ids,
    }


def collect_safe_stage_c_pairs(conn: Any, ai_profile_rows: list[dict[str, Any]], profile_package_ids: set[int]) -> set[tuple[int, str]]:
    safe_pairs: set[tuple[int, str]] = set()
    for row in ai_profile_rows:
        domain_id = int(row["domain_id"])
        source = str(row["stage_c_source"])
        other_count = conn.execute(
            text(
                """
                select count(*)
                from ai_profile_results
                where domain_id = :domain_id
                  and profile_package_id <> all(:profile_package_ids)
                  and 'ai_profile:' ||
                      coalesce(nullif(prompt_version, ''), 'unknown_prompt') || ':' ||
                      coalesce(nullif(model_provider, ''), 'unknown_provider') || ':' ||
                      coalesce(nullif(model_name, ''), 'unknown_model') = :source
                """
            ),
            {"domain_id": domain_id, "profile_package_ids": list(profile_package_ids) or [-1], "source": source},
        ).scalar_one()
        if int(other_count) == 0:
            safe_pairs.add((domain_id, source))
    return safe_pairs


def collect_orphan_domain_ids(
    conn: Any,
    *,
    target_domain_ids: set[int],
    search_result_ids: set[int],
    crawl_result_ids: set[int],
    profile_package_ids: set[int],
    ai_profile_result_ids: set[int],
    candidate_group_item_ids: set[int],
) -> set[int]:
    orphan_domain_ids: set[int] = set()
    for domain_id in target_domain_ids:
        remaining_refs = conn.execute(
            text(
                """
                select
                  (select count(*) from search_results where domain_id = :domain_id and id <> all(:search_result_ids)) +
                  (select count(*) from crawl_results where domain_id = :domain_id and id <> all(:crawl_result_ids)) +
                  (select count(*) from profile_packages where domain_id = :domain_id and id <> all(:profile_package_ids)) +
                  (select count(*) from ai_profile_results where domain_id = :domain_id and id <> all(:ai_profile_result_ids)) +
                  (select count(*) from qualified_leads where domain_id = :domain_id) +
                  (select count(*) from company_profiles where domain_id = :domain_id) +
                  (select count(*) from lead_scores where domain_id = :domain_id) +
                  (select count(*) from candidate_group_items where domain_id = :domain_id and id <> all(:candidate_group_item_ids))
                """
            ),
            {
                "domain_id": domain_id,
                "search_result_ids": list(search_result_ids) or [-1],
                "crawl_result_ids": list(crawl_result_ids) or [-1],
                "profile_package_ids": list(profile_package_ids) or [-1],
                "ai_profile_result_ids": list(ai_profile_result_ids) or [-1],
                "candidate_group_item_ids": list(candidate_group_item_ids) or [-1],
            },
        ).scalar_one()
        if int(remaining_refs) == 0:
            orphan_domain_ids.add(domain_id)
    return orphan_domain_ids


def execute_cleanup(conn: Any, plan: dict[str, Any], target: CleanupTarget) -> None:
    for domain_id, source in plan["safe_stage_c_pairs"]:
        conn.execute(text("delete from qualified_leads where domain_id = :domain_id and source = :source"), {"domain_id": domain_id, "source": source})
        conn.execute(text("delete from company_profiles where domain_id = :domain_id and source = :source"), {"domain_id": domain_id, "source": source})
        conn.execute(text("delete from lead_scores where domain_id = :domain_id and source = :source"), {"domain_id": domain_id, "source": source})

    delete_by_ids(conn, "ai_profile_results", plan["ai_profile_result_ids"])
    delete_by_ids(conn, "profile_packages", plan["profile_package_ids"])
    delete_by_ids(conn, "country_signals", plan["country_signal_ids"])
    delete_by_ids(conn, "crawl_results", plan["crawl_result_ids"])
    delete_by_ids(conn, "candidate_group_items", plan["candidate_group_item_ids"])
    conn.execute(text("delete from candidate_groups where id = :id"), {"id": target.candidate_group_id})
    delete_by_ids(conn, "search_results", plan["search_result_ids"])
    delete_by_ids(conn, "task_items", plan["task_item_ids"])
    delete_by_ids(conn, "task_runs", set(target.task_ids))
    delete_by_ids(conn, "domains", plan["orphan_domain_ids"])


def delete_by_ids(conn: Any, table_name: str, ids: set[int]) -> None:
    if not ids:
        return
    conn.execute(text(f"delete from {table_name} where id = any(:ids)"), {"ids": list(ids)})


def fetch_ids(conn: Any, sql: str, params: dict[str, Any]) -> set[int]:
    rows = conn.execute(text(sql), params).fetchall()
    return {int(row[0]) for row in rows if row[0] is not None}


def fetch_rows(conn: Any, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    rows = conn.execute(text(sql), params).fetchall()
    return [dict(row._mapping) for row in rows]


def print_plan(plan: dict[str, Any], target: CleanupTarget, *, execute: bool) -> None:
    print("Target:")
    print(f"  search task: #{target.search_task_id} ({target.search_source})")
    print(f"  candidate group: #{target.candidate_group_id}")
    print(f"  crawl tasks: {', '.join(f'#{task_id}' for task_id in target.crawl_task_ids)}")
    print(f"  mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print("\nPlanned deletions:")
    print(f"  task_runs: {len(target.task_ids)}")
    print(f"  task_items: {len(plan['task_item_ids'])}")
    print(f"  candidate_group_items: {len(plan['candidate_group_item_ids'])}")
    print("  candidate_groups: 1")
    print(f"  search_results: {len(plan['search_result_ids'])}")
    print(f"  crawl_results: {len(plan['crawl_result_ids'])}")
    print(f"  profile_packages: {len(plan['profile_package_ids'])}")
    print(f"  ai_profile_results: {len(plan['ai_profile_result_ids'])}")
    print(f"  stage_c_domain_source_pairs: {len(plan['safe_stage_c_pairs'])}")
    print(f"  country_signals: {len(plan['country_signal_ids'])}")
    print(f"  orphan_domains: {len(plan['orphan_domain_ids'])}")


if __name__ == "__main__":
    main()
