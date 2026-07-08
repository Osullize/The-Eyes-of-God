# Database-Native Company Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the console workflow database-native and add A/B/C enterprise library views.

**Architecture:** Keep CLI CSV compatibility, but remove CSV as the console handoff path. Search tasks write Stage A tables directly; crawl tasks can select candidates from Stage A tables and write Stage B tables directly; Stage C tables exist for later AI/confirmation but remain empty until that workflow is implemented.

**Tech Stack:** Python, SQLAlchemy, Alembic, FastAPI, unittest, Vue 3, TypeScript.

---

### Task 1: Stage C Database Tables

**Files:**
- Modify: `database/models.py`
- Add: `alembic/versions/20260626_0002_stage_c_company_library.py`
- Modify: `tests/test_database_models.py`

- [x] Add failing tests that create metadata and assert `qualified_leads`, `company_profiles`, and `lead_scores` exist.
- [x] Add SQLAlchemy models for `QualifiedLead`, `CompanyProfile`, and `LeadScore`.
- [x] Add an Alembic migration creating those tables with foreign keys to `domains`.
- [x] Run `python -B -m unittest tests/test_database_models.py` and verify it passes.

### Task 2: Stage Library Queries

**Files:**
- Modify: `database/queries.py`
- Modify: `tests/test_database_queries.py`

- [x] Add failing tests for `list_stage_a_companies()`, `list_stage_b_companies()`, `list_stage_c_companies()`, and `get_company_library_stats()`.
- [x] Implement Stage A query from `domains + search_results + country_signals`.
- [x] Implement Stage B query from `domains + crawl_results + contacts + profile_packages + country_signals`.
- [x] Implement Stage C query from `qualified_leads + company_profiles + lead_scores`.
- [x] Run `python -B -m unittest tests/test_database_queries.py` and verify it passes.

### Task 3: Database-Native Crawl Candidate Selection

**Files:**
- Modify: `tasks/handlers.py`
- Modify: `api/schemas.py`
- Modify: `tests/test_task_handlers.py`

- [x] Add failing tests proving `run_crawl_task()` can run without `input_file` by selecting Stage A domains from the database.
- [x] Add crawl request fields: `candidate_country`, `candidate_query`, `candidate_limit`, and `recrawl_existing`.
- [x] Implement a temporary in-memory company input list from Stage A candidates and pass it into `run_crawl()` without requiring a CSV file.
- [x] Keep direct CLI CSV behavior unchanged.
- [x] Run `python -B -m unittest tests/test_task_handlers.py` and verify it passes.

### Task 4: Company Library API Endpoints

**Files:**
- Modify: `api/app.py`
- Modify: `tests/test_api_read_endpoints.py`

- [x] Add failing API tests for `GET /company-library/stats`, `/stage-a`, `/stage-b`, and `/stage-c`.
- [x] Implement the endpoints using the stage library query functions.
- [x] Preserve existing `/domains` endpoints for backward compatibility.
- [x] Run `python -B -m unittest tests/test_api_read_endpoints.py` and verify it passes.

### Task 5: Frontend Enterprise Library

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

- [x] Add TypeScript types and API client functions for Stage A/B/C library responses.
- [x] Add an `企业库` section with tabs for `官网候选库 A`, `抓取画像库 B`, and `优先客户库 C`.
- [x] Remove CSV input/output fields from the main search/crawl forms.
- [x] Add database-native crawl filters: country, keyword/query text, candidate limit, and recrawl toggle.
- [x] Run `npm run build` under `frontend/` and verify it passes.

### Task 6: Documentation And Worklog

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_FILE_GUIDE.md`
- Modify: `AI_WORKLOG.md`
- Modify: `docs/superpowers/plans/2026-06-26-database-native-company-library.md`

- [x] Document that console search/crawl no longer require CSV files.
- [x] Document that profile JSON is retained as AI-analysis material.
- [x] Update worklog with changed files and verification.
- [x] Run `python -B -m unittest discover -s tests`.
- [x] Run `npm run build` under `frontend/`.
