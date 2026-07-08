# Database Task Batches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move console search/crawl progress tracking into database task batches so the product no longer depends on user-facing `.search_state` / `.crawl_state` directories.

**Architecture:** Add `task_runs` and `task_items` models plus CRUD/query helpers. Task handlers create task runs, create per-keyword/per-domain task items, and update status while still reusing the existing scraping engines. FastAPI exposes read endpoints for task center data, and Vue removes state directory inputs from the primary task form.

**Tech Stack:** Python, SQLAlchemy, Alembic, FastAPI, unittest, Vue 3, TypeScript.

---

### Task 1: Task Batch Models And Migration

**Files:**
- Modify: `database/models.py`
- Add: `alembic/versions/20260626_0004_task_batches.py`
- Modify: `tests/test_database_models.py`

- [x] Add failing model test asserting `task_runs` and `task_items` are created.
- [x] Add `TaskRun` and `TaskItem` SQLAlchemy models with relationships to each other and optional domain relationship.
- [x] Add Alembic migration for both tables and indexes.
- [x] Run `python -B -m unittest tests/test_database_models.py`.

### Task 2: Task Batch Service

**Files:**
- Add: `database/task_batches.py`
- Add: `tests/test_task_batches.py`

- [x] Add failing tests for creating a task run, creating items, updating item status, finishing a run, listing runs, and reading run detail.
- [x] Implement task batch helpers and serializers.
- [x] Run `python -B -m unittest tests/test_task_batches.py`.

### Task 3: Search/Crawl Engine Callbacks

**Files:**
- Modify: `run_search.py`
- Modify: `run_crawl.py`
- Modify: `tests/test_run_search.py`
- Modify: `tests/test_run_crawl.py`

- [x] Add failing tests proving `run_search()` can run with `state_dir=None` and call an `on_keyword_done` callback.
- [x] Add failing tests proving `run_crawl()` can run with `state_dir=None` and call an `on_domain_done` callback.
- [x] Implement no-state execution for search/crawl without removing legacy state directory behavior.
- [x] Implement callbacks after each keyword/domain is processed.
- [x] Run `python -B -m unittest tests/test_run_search.py tests/test_run_crawl.py`.

### Task 4: Task Handler Integration

**Files:**
- Modify: `tasks/handlers.py`
- Modify: `tests/test_task_handlers.py`

- [x] Add failing tests proving database-backed search creates `task_runs` and keyword `task_items`.
- [x] Add failing tests proving database-backed crawl creates `task_runs` and domain `task_items`.
- [x] Update search/crawl handlers to default to database task batches when `database_url` is present.
- [x] Preserve legacy `state_dir` behavior when explicitly passed for CLI compatibility.
- [x] Run `python -B -m unittest tests/test_task_handlers.py`.

### Task 5: Task Center API

**Files:**
- Modify: `database/queries.py` or use `database/task_batches.py`
- Modify: `api/app.py`
- Modify: `tests/test_api_read_endpoints.py`

- [x] Add failing API tests for `GET /task-runs` and `GET /task-runs/{id}`.
- [x] Implement task run list and detail endpoints.
- [x] Run `python -B -m unittest tests/test_api_read_endpoints.py`.

### Task 6: Frontend Task Center And State Directory Removal

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

- [x] Add task run/item types and API client functions.
- [x] Remove visible search/crawl state directory inputs from primary task forms.
- [x] Add a `任务中心` navigation module showing task runs and task detail.
- [x] Run `npm run build` under `frontend/`.

### Task 7: Documentation And Verification

**Files:**
- Modify: `AI_WORKLOG.md`
- Modify: `README.md`
- Modify: `PROJECT_FILE_GUIDE.md`
- Modify: this plan file.

- [x] Document that console task progress now lives in database task batches.
- [x] Document that state directories remain CLI compatibility only.
- [x] Update worklog.
- [x] Run `python -B -m unittest discover -s tests`.
- [x] Run `npm run build` under `frontend/`.
- [x] Apply migration to local PostgreSQL and verify `/task-runs`.
