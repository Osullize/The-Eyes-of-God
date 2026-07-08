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
from database.keyword_groups import import_keyword_group_from_yaml, serialize_keyword_group
from database.session import DEFAULT_DATABASE_URL, create_all, create_engine_from_url, create_session_factory

load_project_env()


DEFAULT_KEYWORD_FILES = [
    ROOT / "config" / "keywords_france.yaml",
    ROOT / "config" / "keywords_france_complement.yaml",
    ROOT / "config" / "keywords_uk.yaml",
    ROOT / "config" / "keywords_uk_complement.yaml",
]


def import_keyword_groups(
    database_url: str = DEFAULT_DATABASE_URL,
    paths: list[str | Path] | None = None,
    create_tables: bool = True,
) -> dict[str, Any]:
    engine = create_engine_from_url(database_url)
    if create_tables:
        create_all(engine)
    Session = create_session_factory(engine)
    source_paths = [Path(path) for path in (paths or DEFAULT_KEYWORD_FILES)]
    try:
        with Session() as session:
            groups = []
            for path in source_paths:
                group = import_keyword_group_from_yaml(session, path)
                groups.append(serialize_keyword_group(group))
            session.commit()
            return {
                "database": database_url,
                "imported": len(groups),
                "groups": groups,
            }
    finally:
        engine.dispose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import YAML keyword files into database keyword groups.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--keyword-file", action="append", default=None)
    parser.add_argument("--no-create-tables", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = import_keyword_groups(
        database_url=args.database_url,
        paths=args.keyword_file,
        create_tables=not args.no_create_tables,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
