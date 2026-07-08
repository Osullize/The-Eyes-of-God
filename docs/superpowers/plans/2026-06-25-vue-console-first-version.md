# Vue Console First Version Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable Vue3 backend console for browsing imported lead data and prepare the backend list API for pagination.

**Architecture:** Keep the Python backend as the source of truth and add a lightweight Vue3 SPA under `frontend/`. The backend exposes read-only JSON endpoints; the frontend calls those endpoints directly and renders a dashboard, filterable customer table, and customer detail panel.

**Tech Stack:** FastAPI, SQLAlchemy, unittest, Vue3, Vite, TypeScript.

---

### Task 1: Backend Domain Pagination Total

**Files:**
- Modify: `database/queries.py`
- Modify: `tests/test_api_read_endpoints.py`

- [x] Add a failing API test asserting `GET /domains?limit=1` returns `total: 2`, `count: 1`, and one row.
- [x] Run `python -B -m unittest tests/test_api_read_endpoints.py` and confirm the failure is missing `total`.
- [x] Update `list_domains()` to compute total before applying `offset` and `limit`.
- [x] Re-run `python -B -m unittest tests/test_api_read_endpoints.py` and confirm it passes.

### Task 2: Vue3 Console Scaffold

**Files:**
- Modify: `api/app.py`
- Modify: `tests/test_api_app.py`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/style.css`

- [x] Add a failing FastAPI test requiring CORS for `http://127.0.0.1:5173`.
- [x] Configure FastAPI CORS for local Vue dev origins.
- [x] Create a Vite Vue3 TypeScript app skeleton under `frontend/`.
- [x] Implement an API client for `/database/stats`, `/domains`, and `/domains/{domain}`.
- [x] Implement a dashboard summary, filters, paginated customer table, and customer detail view.
- [x] Keep the UI dense and operational: no landing page, no marketing copy, no decorative hero.

### Task 3: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_FILE_GUIDE.md`
- Modify: `AI_WORKLOG.md`

- [x] Document frontend install/start commands and the API dependency.
- [x] Update the file guide with the new `frontend/` directory.
- [x] Append the key work summary to `AI_WORKLOG.md`.
- [x] Run backend tests with `python -B -m unittest discover -s tests`.
- [x] If Node dependencies are unavailable locally, document that `npm install` is required before `npm run build`.
