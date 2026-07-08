"""profile packages database first

Revision ID: 20260703_0008
Revises: 20260703_0007
Create Date: 2026-07-03
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from alembic import op
import sqlalchemy as sa


revision = "20260703_0008"
down_revision = "20260703_0007"
branch_labels = None
depends_on = None


profile_packages = sa.table(
    "profile_packages",
    sa.column("id", sa.Integer()),
    sa.column("path", sa.Text()),
    sa.column("schema_version", sa.String(length=50)),
    sa.column("crawl_status", sa.String(length=50)),
    sa.column("page_count", sa.Integer()),
    sa.column("crawl_time", sa.DateTime(timezone=True)),
    sa.column("payload_json", sa.JSON()),
    sa.column("content_hash", sa.String(length=64)),
)


def upgrade() -> None:
    bind = op.get_bind()
    root = Path(__file__).resolve().parents[2]
    rows = bind.execute(
        sa.select(
            profile_packages.c.id,
            profile_packages.c.path,
            profile_packages.c.payload_json,
            profile_packages.c.content_hash,
        )
    ).mappings()

    unresolved_empty_ids: list[int] = []
    for row in rows:
        payload = _payload_dict(row["payload_json"])
        if not payload:
            payload = _load_payload_from_legacy_path(root, row["path"])
        if not payload:
            unresolved_empty_ids.append(int(row["id"]))
            continue

        metadata = payload.get("crawl_metadata") or {}
        pages = payload.get("pages") or []
        bind.execute(
            profile_packages.update()
            .where(profile_packages.c.id == row["id"])
            .values(
                schema_version=_clean(payload.get("schema_version")),
                crawl_status=_clean(metadata.get("status")),
                page_count=len(pages) if isinstance(pages, list) else 0,
                crawl_time=_parse_datetime(metadata.get("crawl_time")),
                payload_json=payload,
                content_hash=_content_hash(payload),
            )
        )

    if unresolved_empty_ids:
        bind.execute(profile_packages.delete().where(profile_packages.c.id.in_(unresolved_empty_ids)))

    duplicate_ids = _duplicate_content_hash_ids(bind)
    if duplicate_ids:
        bind.execute(profile_packages.delete().where(profile_packages.c.id.in_(duplicate_ids)))

    dialect = bind.dialect.name
    if dialect != "sqlite":
        op.drop_constraint("uq_profile_packages_path", "profile_packages", type_="unique")

    with op.batch_alter_table("profile_packages") as batch_op:
        batch_op.drop_column("path")
        batch_op.drop_column("source_dir")
        batch_op.drop_column("source_mtime")

    op.create_index(
        "uq_profile_packages_content_hash",
        "profile_packages",
        ["content_hash"],
        unique=True,
        postgresql_where=sa.text("content_hash <> ''"),
        sqlite_where=sa.text("content_hash <> ''"),
    )


def downgrade() -> None:
    op.drop_index("uq_profile_packages_content_hash", table_name="profile_packages")

    with op.batch_alter_table("profile_packages") as batch_op:
        batch_op.add_column(sa.Column("path", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("source_dir", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("source_mtime", sa.DateTime(timezone=True), nullable=True))

    bind = op.get_bind()
    bind.execute(sa.text("update profile_packages set path = 'profile_package:' || id where path is null or path = ''"))
    if bind.dialect.name != "sqlite":
        op.alter_column("profile_packages", "path", nullable=False)
        op.create_unique_constraint("uq_profile_packages_path", "profile_packages", ["path"])


def _payload_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _load_payload_from_legacy_path(root: Path, value: Any) -> dict[str, Any]:
    path_text = _clean(value)
    if not path_text:
        return {}
    candidates = [Path(path_text)]
    if not candidates[0].is_absolute():
        candidates.append(root / path_text)
        candidates.append(Path.cwd() / path_text)
    for candidate in candidates:
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _content_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _duplicate_content_hash_ids(bind: sa.Connection) -> list[int]:
    rows = bind.execute(
        sa.select(profile_packages.c.id, profile_packages.c.payload_json, profile_packages.c.content_hash)
        .where(profile_packages.c.content_hash != "")
        .order_by(profile_packages.c.content_hash, profile_packages.c.id)
    ).mappings()
    seen: set[str] = set()
    duplicates: list[int] = []
    for row in rows:
        content_hash = str(row["content_hash"])
        if content_hash in seen:
            duplicates.append(int(row["id"]))
        else:
            seen.add(content_hash)
    return duplicates


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_datetime(value: Any) -> datetime | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
