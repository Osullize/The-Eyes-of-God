from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


TaskStatus = Literal["success", "failed", "cancelled", "partial_failed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TaskResult:
    task_type: str
    status: TaskStatus
    params: dict[str, Any]
    summary: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: datetime = field(default_factory=utc_now)
    finished_at: datetime = field(default_factory=utc_now)

    @property
    def duration_seconds(self) -> float:
        return max((self.finished_at - self.started_at).total_seconds(), 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "status": self.status,
            "params": self.params,
            "summary": self.summary,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration_seconds": self.duration_seconds,
        }
