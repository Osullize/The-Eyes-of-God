from __future__ import annotations

import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable


def _normalize_row(row: dict[str, str], fieldnames: list[str]) -> dict[str, str]:
    return {field: str(row.get(field, "")) for field in fieldnames}


def _read_existing_rows(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not file_path.exists() or file_path.stat().st_size == 0:
        return [], []

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            return [], []
        return list(reader.fieldnames), list(reader)


def _write_all_rows(file_path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8-sig",
        newline="",
        dir=str(file_path.parent or Path(".")),
        delete=False,
    ) as temp_file:
        writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(_normalize_row(row, fieldnames))
        temp_name = temp_file.name

    os.replace(temp_name, file_path)


def append_deduped_rows(
    file_path: str | Path,
    rows: Iterable[dict[str, str]],
    fieldnames: list[str],
    key_field: str = "domain",
) -> None:
    output_path = Path(file_path)
    new_rows = [_normalize_row(row, fieldnames) for row in rows if row.get(key_field)]
    if not new_rows:
        return

    existing_fieldnames, existing_rows = _read_existing_rows(output_path)
    needs_header_upgrade = existing_fieldnames != fieldnames

    existing_keys = {row.get(key_field, "") for row in existing_rows if row.get(key_field)}
    incoming_keys = [row[key_field] for row in new_rows]
    has_duplicate = any(key in existing_keys for key in incoming_keys) or len(set(incoming_keys)) != len(incoming_keys)

    if existing_rows and not needs_header_upgrade and not has_duplicate:
        with output_path.open("a", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            for row in new_rows:
                writer.writerow(row)
        return

    rows_by_key: dict[str, dict[str, str]] = {}
    key_order: list[str] = []

    for row in existing_rows:
        key = row.get(key_field, "")
        if not key:
            continue
        if key not in rows_by_key:
            key_order.append(key)
        rows_by_key[key] = _normalize_row(row, fieldnames)

    for row in new_rows:
        key = row[key_field]
        if key not in rows_by_key:
            key_order.append(key)
        rows_by_key[key] = row

    _write_all_rows(output_path, [rows_by_key[key] for key in key_order], fieldnames)
