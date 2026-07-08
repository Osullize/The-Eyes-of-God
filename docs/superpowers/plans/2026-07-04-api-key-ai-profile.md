# API Key AI Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Claude Code AI inference with a frontend-supplied API Key flow and add a dedicated page-style AI profile result viewer.

**Architecture:** The backend will call an OpenAI-compatible chat completions API using request-scoped credentials that are never persisted. The heat-pump lead prompt remains backend-owned and forces Chinese natural-language output while preserving stable JSON field names. The frontend keeps AI task execution in the task console and moves AI result reading to a dedicated module.

**Tech Stack:** FastAPI, SQLAlchemy, Python stdlib HTTP client, Vue 3, TypeScript, unittest.

---

### Task 1: Backend AI API Client

**Files:**
- Create: `ai/model_api_client.py`
- Modify: `ai/lead_profile_prompt.py`
- Delete: `ai/claude_code_client.py`
- Test: `tests/test_model_api_client.py`

- [ ] Write tests for OpenAI-compatible request shape, JSON extraction, and missing API Key validation.
- [ ] Implement the API client with `urllib.request` so no new dependency is needed.
- [ ] Update the prompt to require Chinese output and internal prompt version `heat_pump_lead_cn_v1`.
- [ ] Delete Claude Code client code and tests.

### Task 2: Backend Task Flow

**Files:**
- Modify: `tasks/handlers.py`
- Modify: `api/schemas.py`
- Test: `tests/test_task_handlers.py`
- Test: `tests/test_api_app.py`

- [ ] Write tests proving API Key is passed to the runtime client but redacted from task params.
- [ ] Remove frontend-facing `prompt_version` from the request schema.
- [ ] Use fixed internal prompt version for storage and dedupe.
- [ ] Preserve `ai_profile_results` writes and existing task batch behavior.

### Task 3: Frontend AI Task Form

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/types.ts`
- Test: `tests/test_frontend_ai_profile_task.py`

- [ ] Replace Claude Code form fields with model service, API Base URL, API Key, model name, temperature, timeout, and profile package IDs.
- [ ] Remove prompt version input from the UI.
- [ ] Ensure API Key is sent only in task request payload.

### Task 4: Dedicated AI Profile Reader

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `tests/test_frontend_raw_tables_module.py`
- Create or modify: frontend-focused tests as needed.

- [ ] Remove `ai_profile_results` from the raw database table tabs.
- [ ] Add a left-nav module named `AI画像分析`.
- [ ] Render one AI profile result per page with previous/next controls, filters, and raw JSON disclosure.
- [ ] Reuse the existing `GET /raw-tables/ai-profile-results` endpoint.

### Task 5: Verification

- [ ] Run focused backend tests.
- [ ] Run frontend source tests.
- [ ] Run `python -m unittest discover -s tests`.
- [ ] Run `npm run build` in `frontend/`.
- [ ] Restart FastAPI on `127.0.0.1:8000`.
