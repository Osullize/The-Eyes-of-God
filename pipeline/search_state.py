from __future__ import annotations

import csv
import threading
from pathlib import Path


class SearchState:
    def __init__(self, state_dir: str | Path = ".search_state") -> None:
        self.state_dir = Path(state_dir)
        self.completed_file = self.state_dir / "completed_keywords.txt"
        self.failed_file = self.state_dir / "failed_keywords.csv"
        self._lock = threading.RLock()
        self._completed = self._load_completed()
        self._failures = self._load_failures()

    def _load_completed(self) -> set[str]:
        if not self.completed_file.exists():
            return set()
        return {
            line.strip()
            for line in self.completed_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    def _load_failures(self) -> dict[str, str]:
        if not self.failed_file.exists():
            return {}
        with self.failed_file.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            return {
                (row.get("keyword") or "").strip(): row.get("reason", "")
                for row in reader
                if (row.get("keyword") or "").strip()
            }

    def _write_completed(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.completed_file.write_text(
            "".join(f"{keyword}\n" for keyword in sorted(self._completed)),
            encoding="utf-8",
        )

    def _write_failures(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.failed_file.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["keyword", "reason"])
            writer.writeheader()
            for keyword in sorted(self._failures):
                writer.writerow({"keyword": keyword, "reason": self._failures[keyword]})

    def is_completed(self, keyword: str) -> bool:
        with self._lock:
            return keyword.strip() in self._completed

    def mark_completed(self, keyword: str) -> None:
        normalized = keyword.strip()
        if not normalized:
            return
        with self._lock:
            self._completed.add(normalized)
            self._failures.pop(normalized, None)
            self._write_completed()
            self._write_failures()

    def mark_failed(self, keyword: str, reason: str) -> None:
        normalized = keyword.strip()
        if not normalized:
            return
        with self._lock:
            if normalized not in self._completed:
                self._failures[normalized] = reason
                self._write_failures()

    def failed_keywords(self) -> list[str]:
        with self._lock:
            return sorted(self._failures)

    def failure_reason(self, keyword: str) -> str:
        with self._lock:
            return self._failures.get(keyword.strip(), "")
