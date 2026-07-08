# Database Keyword Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store keyword groups in the database and let the console manage/search with database keyword groups instead of YAML files.

**Architecture:** Add a `keyword_groups` table and backend CRUD helpers. Search tasks accept `keyword_group_id`; the handler converts database terms into existing `KeywordSpec` values and reuses the current search pipeline. YAML files remain as CLI compatibility and can be imported into the database once.

**Tech Stack:** Python, SQLAlchemy, Alembic, FastAPI, unittest, Vue 3, TypeScript.

---

### Task 1: Keyword Group Model And Migration

**Files:**
- Modify: `database/models.py`
- Add: `alembic/versions/20260626_0003_keyword_groups.py`
- Modify: `tests/test_database_models.py`

- [x] Add failing model test that asserts `keyword_groups` is created.
- [x] Add `KeywordGroup` model with name/country/terms/notes/is_active timestamps.
- [x] Add Alembic migration for `keyword_groups`.
- [x] Run `python -B -m unittest tests/test_database_models.py`.

### Task 2: Keyword Group Service

**Files:**
- Add: `database/keyword_groups.py`
- Add: `tests/test_keyword_groups.py`

- [x] Add failing tests for create/list/update/delete keyword groups.
- [x] Add failing test for generating `KeywordSpec` values from a group.
- [x] Add failing test for importing YAML into keyword groups.
- [x] Implement CRUD helpers, spec generation, and YAML import helpers.
- [x] Run `python -B -m unittest tests/test_keyword_groups.py`.

### Task 3: Search Task Integration

**Files:**
- Modify: `run_search.py`
- Modify: `tasks/handlers.py`
- Modify: `api/schemas.py`
- Modify: `tests/test_run_search.py`
- Modify: `tests/test_task_handlers.py`

- [x] Add failing test proving `run_search()` can accept direct `keyword_specs`.
- [x] Add failing test proving `run_search_task(keyword_group_id=...)` loads database terms.
- [x] Add `keyword_group_id` to search task request schema.
- [x] Implement direct `keyword_specs` support in `run_search()`.
- [x] Implement database keyword group loading in `run_search_task()`.
- [x] Run search and handler tests.

### Task 4: Keyword Group API

**Files:**
- Modify: `api/schemas.py`
- Modify: `api/app.py`
- Modify: `tests/test_api_read_endpoints.py`

- [x] Add failing API tests for list/create/update/delete keyword groups.
- [x] Implement FastAPI endpoints.
- [x] Run `python -B -m unittest tests/test_api_read_endpoints.py`.

### Task 5: Import Existing YAML Keyword Files

**Files:**
- Add: `scripts/import_keyword_groups.py`
- Add: `tests/test_import_keyword_groups_script.py`

- [x] Add failing test for importing selected YAML files into an empty database.
- [x] Implement script with `--database-url` and optional file args.
- [x] Run the script against local PostgreSQL after migration.

### Task 6: Frontend Keyword Center

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

- [x] Add keyword group types and API client functions.
- [x] Add `关键词配置中心` module with list, edit form, save, create, and delete controls.
- [x] Change search task form from YAML path to keyword group selector.
- [x] Run `npm run build` under `frontend/`.

### Task 7: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_FILE_GUIDE.md`
- Modify: `AI_WORKLOG.md`
- Modify: `docs/superpowers/plans/2026-06-26-database-keyword-center.md`

- [x] Document that console keyword configuration lives in database.
- [x] Document YAML compatibility/import behavior.
- [x] Update worklog.
- [x] Run `python -B -m unittest discover -s tests`.
- [x] Run `npm run build` under `frontend/`.
- [x] Apply migration, import existing YAML groups, restart FastAPI, and verify keyword group endpoints.
