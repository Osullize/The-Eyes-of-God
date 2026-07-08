# Database-First Stage Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist search and crawl stage outputs into the database automatically after each task finishes.

**Architecture:** Treat CSV/JSON outputs as compatibility artifacts. Add row-based database import functions that reuse the existing CSV importer rules, then call the same stage-persistence helpers from direct scripts and task handlers whenever a database URL is configured through params, CLI flags, or `DATABASE_URL`.

**Tech Stack:** Python, SQLAlchemy, unittest, FastAPI task handlers.

---

### Task 1: Row-Based Importers

**Files:**
- Modify: `database/importers.py`
- Modify: `tests/test_database_importers.py`

- [x] Add failing tests for `import_search_rows()` and `import_crawl_rows()`.
- [x] Refactor CSV importers to call row-based helpers.
- [x] Preserve current dedupe semantics and source tracking with a supplied `source_name`.
- [x] Run `python -B -m unittest tests/test_database_importers.py`.

### Task 2: Task Handler Persistence

**Files:**
- Modify: `tasks/handlers.py`
- Modify: `tests/test_task_handlers.py`
- Modify: `scripts/run_task.py`
- Modify: `api/schemas.py`
- Modify: `run_search.py`
- Modify: `run_crawl.py`
- Add: `database/stage_persistence.py`

- [x] Add failing tests proving `run_search_task()` and `run_crawl_task()` write returned rows to a SQLite database when `database_url` is provided.
- [x] Add `database_url` and `persist_to_database` handling to search/crawl task params.
- [x] After search, call `import_search_rows()`.
- [x] After crawl, call `import_crawl_rows()` and import generated profile directory metadata.
- [x] Return database import counts in task summaries.
- [x] Add direct-script `--database-url` / `--no-persist-to-database` controls for search and crawl.
- [x] Run task handler tests.

### Task 3: Documentation And UI Defaults

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_FILE_GUIDE.md`
- Modify: `AI_WORKLOG.md`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.vue`

- [x] Document that CSV files are now compatibility artifacts and database is the stage-of-record when configured.
- [x] Remove frontend database URL from import controls or make clear only import uses it.
- [x] Update worklog with this design choice and verification.
- [x] Run `python -B -m unittest discover -s tests`.
- [x] Run `npm run build` under `frontend/`.
