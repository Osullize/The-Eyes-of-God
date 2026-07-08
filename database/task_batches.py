from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from database.models import TaskItem, TaskRun


ACTIVE_TASK_STATUSES = {"pending", "running", "cancelling"}
CANCEL_REQUESTED_STATUSES = {"cancelling", "cancelled"}
TERMINAL_TASK_STATUSES = {"success", "partial_failed", "failed", "cancelled", "error"}


def create_task_run(
    session: Session,
    *,
    task_type: str,
    name: str = "",
    params: dict[str, Any] | None = None,
    status: str = "pending",
    created_by: str = "",
) -> TaskRun:
    task_run = TaskRun(
        task_type=task_type,
        name=name,
        status=status,
        params_json=params or {},
        summary_json={},
        created_by=created_by,
    )
    session.add(task_run)
    session.flush()
    return task_run


def start_task_run(session: Session, task_run_id: int) -> TaskRun:
    task_run = require_task_run(session, task_run_id)
    task_run.status = "running"
    task_run.started_at = task_run.started_at or utc_now()
    session.flush()
    return task_run


def finish_task_run(
    session: Session,
    task_run_id: int,
    *,
    status: str,
    summary: dict[str, Any] | None = None,
) -> TaskRun:
    task_run = require_task_run(session, task_run_id)
    task_run.status = status
    task_run.finished_at = utc_now()
    task_run.summary_json = summary if summary is not None else count_task_items_by_status(session, task_run_id)
    session.flush()
    return task_run


def create_task_items(
    session: Session,
    task_run: TaskRun,
    items: Iterable[dict[str, Any]],
) -> list[TaskItem]:
    created: list[TaskItem] = []
    for item in items:
        task_item = TaskItem(
            task_run_id=task_run.id,
            item_type=str(item["item_type"]),
            item_key=str(item["item_key"]),
            domain_id=item.get("domain_id"),
            status=str(item.get("status") or "pending"),
            result_json=item.get("result_json") or {},
        )
        session.add(task_item)
        created.append(task_item)
    session.flush()
    return created


def start_task_item(session: Session, task_item_id: int) -> TaskItem:
    task_item = require_task_item(session, task_item_id)
    if task_item.status == "cancelled":
        return task_item
    task_item.status = "running"
    task_item.attempt_count += 1
    task_item.started_at = utc_now()
    task_item.error = ""
    session.flush()
    return task_item


def finish_task_item(
    session: Session,
    task_item_id: int,
    *,
    status: str,
    error: str = "",
    result: dict[str, Any] | None = None,
) -> TaskItem:
    task_item = require_task_item(session, task_item_id)
    if task_item.status == "cancelled":
        return task_item
    task_item.status = status
    task_item.error = error
    task_item.result_json = result or {}
    task_item.finished_at = utc_now()
    session.flush()
    return task_item


def request_task_run_cancel(session: Session, task_run_id: int) -> dict[str, Any]:
    task_run = require_task_run(session, task_run_id)
    if task_run.status in TERMINAL_TASK_STATUSES:
        return serialize_task_run(session, task_run, include_items=True)

    task_run.status = "cancelling"
    task_run.started_at = task_run.started_at or utc_now()
    cancel_task_items_by_status(session, task_run_id, statuses={"pending"})
    session.flush()
    return serialize_task_run(session, task_run, include_items=True)


def is_task_run_cancel_requested(session: Session, task_run_id: int) -> bool:
    task_run = session.get(TaskRun, task_run_id)
    return bool(task_run and task_run.status in CANCEL_REQUESTED_STATUSES)


def cancel_unfinished_task_items(session: Session, task_run_id: int) -> None:
    cancel_task_items_by_status(session, task_run_id, statuses={"pending", "running"})


def cancel_task_items_by_status(session: Session, task_run_id: int, *, statuses: set[str]) -> None:
    now = utc_now()
    items = session.scalars(
        select(TaskItem).where(
            TaskItem.task_run_id == task_run_id,
            TaskItem.status.in_(statuses),
        )
    ).all()
    for item in items:
        item.status = "cancelled"
        item.error = item.error or "cancelled by user"
        item.finished_at = item.finished_at or now
        item.updated_at = now
    session.flush()


def list_task_runs(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    task_type: str = "",
    status: str = "",
) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)
    stmt = select(TaskRun)
    if task_type.strip():
        stmt = stmt.where(TaskRun.task_type == task_type.strip())
    if status.strip():
        stmt = stmt.where(TaskRun.status == status.strip())

    total = int(session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    runs = session.scalars(stmt.order_by(TaskRun.created_at.desc(), TaskRun.id.desc()).offset(safe_offset).limit(safe_limit)).all()
    return {
        "items": [serialize_task_run(session, run, include_items=False) for run in runs],
        "count": len(runs),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def get_task_run_detail(session: Session, task_run_id: int) -> dict[str, Any] | None:
    task_run = session.scalar(
        select(TaskRun)
        .where(TaskRun.id == task_run_id)
        .options(selectinload(TaskRun.items))
    )
    if task_run is None:
        return None
    return serialize_task_run(session, task_run, include_items=True)


def count_task_items_by_status(session: Session, task_run_id: int) -> dict[str, int]:
    statuses = session.execute(
        select(TaskItem.status, func.count())
        .where(TaskItem.task_run_id == task_run_id)
        .group_by(TaskItem.status)
        .order_by(TaskItem.status)
    ).all()
    return {str(status): int(count) for status, count in statuses}


def serialize_task_run(session: Session, task_run: TaskRun, *, include_items: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": task_run.id,
        "task_type": task_run.task_type,
        "name": task_run.name,
        "status": task_run.status,
        "params_json": task_run.params_json or {},
        "summary_json": task_run.summary_json or {},
        "created_by": task_run.created_by,
        "created_at": isoformat(task_run.created_at),
        "started_at": isoformat(task_run.started_at),
        "finished_at": isoformat(task_run.finished_at),
        "item_counts": count_task_items_by_status(session, task_run.id),
    }
    if include_items:
        items = sorted(task_run.items, key=lambda item: (item.id or 0))
        result["items"] = [serialize_task_item(item) for item in items]
    return result


def serialize_task_item(task_item: TaskItem) -> dict[str, Any]:
    return {
        "id": task_item.id,
        "task_run_id": task_item.task_run_id,
        "item_type": task_item.item_type,
        "item_key": task_item.item_key,
        "domain_id": task_item.domain_id,
        "status": task_item.status,
        "attempt_count": task_item.attempt_count,
        "error": task_item.error,
        "result_json": task_item.result_json or {},
        "created_at": isoformat(task_item.created_at),
        "updated_at": isoformat(task_item.updated_at),
        "started_at": isoformat(task_item.started_at),
        "finished_at": isoformat(task_item.finished_at),
    }


def require_task_run(session: Session, task_run_id: int) -> TaskRun:
    task_run = session.get(TaskRun, task_run_id)
    if task_run is None:
        raise ValueError(f"Task run not found: {task_run_id}")
    return task_run


def require_task_item(session: Session, task_item_id: int) -> TaskItem:
    task_item = session.get(TaskItem, task_item_id)
    if task_item is None:
        raise ValueError(f"Task item not found: {task_item_id}")
    return task_item


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
