# Task Cancellation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cooperative cancellation for running search and crawl tasks from the Vue console.

**Architecture:** Use the existing `task_runs` and `task_items` tables as the cancellation control plane. The API marks a run as `cancelling`; search and crawl loops check a callback between units of work and finish the run as `cancelled`.

**Tech Stack:** FastAPI, SQLAlchemy, Python `unittest`, Vue 3, TypeScript.

---

### Task 1: Database Cancellation Helpers

**Files:**
- Modify: `database/task_batches.py`
- Test: `tests/test_task_batches.py`

- [ ] Add tests for requesting cancellation, preserving terminal tasks, and preventing cancelled items from being overwritten.
- [ ] Implement `request_task_run_cancel`, `is_task_run_cancel_requested`, and cancelled-item guards.
- [ ] Run `python -B -m unittest tests/test_task_batches.py`.

### Task 2: Handler And Loop Cancellation

**Files:**
- Modify: `tasks/handlers.py`
- Modify: `run_search.py`
- Modify: `run_crawl.py`
- Test: `tests/test_task_handlers.py`
- Test: `tests/test_run_search.py`
- Test: `tests/test_run_crawl.py`

- [ ] Add tests showing handlers pass `should_cancel` into runners.
- [ ] Add tests showing search and crawl stop before subsequent units of work when `should_cancel` returns true.
- [ ] Update task finalization so a cancelling run finishes as `cancelled`.
- [ ] Run targeted Python tests.

### Task 3: API Endpoint

**Files:**
- Modify: `api/app.py`
- Test: `tests/test_api_app.py`

- [ ] Add `POST /task-runs/{task_run_id}/cancel`.
- [ ] Return current task detail after cancellation.
- [ ] Return 404 for missing tasks.
- [ ] Run `python -B -m unittest tests/test_api_app.py`.

### Task 4: Frontend Cancel Controls

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/types.ts` if needed
- Test: `tests/test_frontend_task_progress_panel.py`

- [ ] Add `cancelTaskRun`.
- [ ] Add cancel buttons in realtime progress and task center detail.
- [ ] Keep progress polling active for `cancelling`.
- [ ] Run frontend source tests and `npm run build`.

### Task 5: Worklog And Verification

**Files:**
- Modify: `AI_WORKLOG.md`

- [ ] Record behavior and operational caveat.
- [ ] Run the targeted tests.
- [ ] Run `git diff --check`.
