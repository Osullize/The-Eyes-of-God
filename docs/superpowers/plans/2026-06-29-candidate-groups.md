# Candidate Groups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent candidate groups so search task outputs can be selected later as crawl task inputs.

**Architecture:** Add `candidate_groups` and `candidate_group_items` tables plus a focused service module. Search handlers create a candidate group after persisting search rows; crawl handlers can select companies from a candidate group. FastAPI exposes candidate group read endpoints and Vue adds a candidate group module plus crawl form selection.

**Tech Stack:** Python, SQLAlchemy, Alembic, FastAPI, unittest, Vue 3, TypeScript.

---

### Task 1: Database Models And Migration

**Files:**
- Modify: `database/models.py`
- Add: `alembic/versions/20260629_0005_candidate_groups.py`
- Modify: `tests/test_database_models.py`

- [x] Add failing model test asserting `candidate_groups` and `candidate_group_items` tables are created.
- [x] Add `CandidateGroup` and `CandidateGroupItem` SQLAlchemy models with relationships to task runs, keyword groups, domains, search results, and task items.
- [x] Add Alembic migration for both tables, indexes, and uniqueness constraints.
- [x] Run `python -B -m unittest tests/test_database_models.py`.

### Task 2: Candidate Group Service

**Files:**
- Add: `database/candidate_groups.py`
- Add: `tests/test_candidate_groups.py`

- [x] Add tests for creating a group from search rows, deduping domains, listing groups with counts, reading group detail, and selecting crawl candidates.
- [x] Implement helper functions for group creation, serialization, and candidate selection.
- [x] Run `python -B -m unittest tests/test_candidate_groups.py`.

### Task 3: Task Handler Integration

**Files:**
- Modify: `tasks/handlers.py`
- Modify: `tests/test_task_handlers.py`

- [x] Add failing test proving `run_search_task` creates a candidate group after search rows are persisted.
- [x] Add failing test proving `run_crawl_task` can select domains by `candidate_group_id`.
- [x] Implement handler integration and return `candidate_group_id` in search summaries.
- [x] Run `python -B -m unittest tests/test_task_handlers.py`.

### Task 4: API Endpoints

**Files:**
- Modify: `api/app.py`
- Modify: `tests/test_api_read_endpoints.py`

- [x] Add tests for `GET /candidate-groups` and `GET /candidate-groups/{id}`.
- [x] Implement endpoints using `database/candidate_groups.py`.
- [x] Run `python -B -m unittest tests/test_api_read_endpoints.py`.

### Task 5: Frontend Candidate Groups

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

- [x] Add candidate group types and API client functions.
- [x] Add `候选组` navigation module with list and detail.
- [x] Add candidate group selector to crawl form.
- [x] Run `npm run build` in `frontend/`.

### Task 6: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_FILE_GUIDE.md`
- Modify: `AI_WORKLOG.md`
- Modify: this plan file.

- [x] Document candidate groups as the link between Stage A search output and Stage B crawl input.
- [x] Run `python -B -m unittest discover -s tests`.
- [x] Run `npm run build` in `frontend/`.
- [x] Run `git diff --check`.
