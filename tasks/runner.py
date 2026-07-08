from __future__ import annotations

from typing import Any, Callable

from tasks.models import TaskResult, utc_now


TaskHandler = Callable[[dict[str, Any]], dict[str, Any]]


def run_task(task_type: str, handler: TaskHandler, params: dict[str, Any] | None = None) -> TaskResult:
    task_params = dict(params or {})
    started_at = utc_now()
    try:
        summary = handler(task_params)
    except Exception as error:
        return TaskResult(
            task_type=task_type,
            status="failed",
            params=task_params,
            summary={},
            error=f"{error.__class__.__name__}: {error}",
            started_at=started_at,
            finished_at=utc_now(),
        )

    result_status = str(summary.get("task_run_status") or "success")
    if result_status not in {"success", "partial_failed", "cancelled"}:
        result_status = "success"

    return TaskResult(
        task_type=task_type,
        status=result_status,
        params=task_params,
        summary=summary,
        error="",
        started_at=started_at,
        finished_at=utc_now(),
    )
