# Console Task Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add search/crawl/import task submission and Celery task polling controls to the Vue3 console.

**Architecture:** Keep task execution in the existing FastAPI endpoints and add a small `/runtime` endpoint so the console can display whether the backend runs tasks inline or through Celery. The Vue console will post task payloads, show inline task results immediately, and poll `/tasks/{task_id}` when the backend returns a queued Celery task.

**Tech Stack:** FastAPI, unittest, Vue3, Vite, TypeScript.

---

### Task 1: Backend Runtime Mode Endpoint

**Files:**
- Modify: `api/app.py`
- Modify: `tests/test_api_app.py`

- [x] Add a failing test for `GET /runtime` returning `{"task_execution_mode": "celery"}` when `create_app(execution_mode="celery")` is used.
- [x] Run `python -B -m unittest tests/test_api_app.py` and confirm the failure is a missing endpoint.
- [x] Implement `GET /runtime` in `api/app.py`.
- [x] Re-run `python -B -m unittest tests/test_api_app.py`.

### Task 2: Frontend Task API Client

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`

- [x] Add task request, task response, task status, and runtime TypeScript interfaces.
- [x] Add `fetchRuntime()`, `startSearchTask()`, `startCrawlTask()`, `startImportTask()`, and `fetchTaskStatus()`.

### Task 3: Vue Task Controls

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

- [x] Add a compact task control panel above the customer workspace.
- [x] Add safe default form values for France search, France crawl, and existing data import.
- [x] Submit the selected task and display either inline result or queued task id.
- [x] Poll Celery task status when the response includes `task_id`.

### Task 4: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_FILE_GUIDE.md`
- Modify: `AI_WORKLOG.md`

- [x] Document task controls and Celery mode expectations.
- [x] Run `python -B -m unittest discover -s tests`.
- [x] Run `npm run build` in `frontend/`.
- [x] Smoke test `GET /runtime` against the running API.
