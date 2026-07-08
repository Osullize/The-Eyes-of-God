from __future__ import annotations

from typing import Any, Callable

from tasks.celery_app import celery_app
from tasks.handlers import run_ai_profile_task, run_crawl_task, run_import_existing_data_task, run_search_task
from tasks.runner import run_task


TaskHandler = Callable[[dict[str, Any]], dict[str, Any]]


DEFAULT_HANDLERS: dict[str, TaskHandler] = {
    "search": run_search_task,
    "crawl": run_crawl_task,
    "ai_profile": run_ai_profile_task,
    "import_existing_data": run_import_existing_data_task,
}


@celery_app.task(name="lead_tasks.execute_task")
def execute_task(task_type: str, params: dict[str, Any], handlers: dict[str, TaskHandler] | None = None) -> dict[str, Any]:
    registry = handlers or DEFAULT_HANDLERS
    if task_type not in registry:
        result = run_task(task_type, lambda _: {}, params)
        return {
            **result.to_dict(),
            "status": "failed",
            "summary": {},
            "error": f"ValueError: Unsupported task type: {task_type}",
        }
    result = run_task(task_type, registry[task_type], params)
    return result.to_dict()
