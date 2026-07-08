# Task Cancellation Design

## Goal
Add a user-facing cancel action for running search and crawl tasks so the console can stop long or blocked runs without killing the FastAPI backend process.

## Scope
- Add cancellation for database-backed `task_runs` in `pending`, `running`, or `cancelling` state.
- Support search and crawl loops in the current inline execution mode.
- Preserve already completed search/crawl outputs.
- Mark not-yet-started task items as `cancelled`.
- Do not add Celery, a new queue backend, or a new database table in this version.

## Behavior
- The frontend sends `POST /task-runs/{task_run_id}/cancel`.
- The backend changes the task run status to `cancelling` and marks `pending` task items as `cancelled`.
- Search checks for cancellation before starting each keyword and after each keyword finishes.
- Crawl checks for cancellation before starting each domain and after each domain finishes.
- If cancellation is requested, the task run finishes as `cancelled`.
- A currently active HTTP/browser request is not forcibly interrupted; it stops after the current keyword/domain completes or times out.

## UI
- The realtime progress panel shows a cancel button while the task is `pending`, `running`, or `cancelling`.
- The task center detail view also shows a cancel button for active task runs.
- Status text includes `取消中` for `cancelling` and `已取消` for `cancelled`.

## Error Handling
- Cancelling a missing task returns 404.
- Cancelling an already terminal task is idempotent and returns the task detail unchanged.
- If a task item was already marked `cancelled`, later progress callbacks must not overwrite it as success or failed.

## Tests
- Unit tests cover database cancellation state transitions.
- Handler tests verify search/crawl runners receive a cancellation checker and final task status becomes `cancelled`.
- API tests cover the cancel endpoint.
- Frontend source tests verify the cancel API and buttons are wired.
