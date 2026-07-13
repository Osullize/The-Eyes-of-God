# AI Worklog

This file records key user/assistant context that should survive across chat sessions.
At the end of each work session, append a new entry with the problem, decisions, changed files, verification, and next steps.

## How to Update

Use this structure for each new entry:

```md
## YYYY-MM-DD - Short Title

### User Context
- Key user requests or constraints.

### Work Summary
- What was inspected, changed, or decided.

### Files Touched
- `path/to/file`

### Verification
- Commands run and results.

### Next Steps
- Pending items or suggested continuation.
```

## 2026-06-17 - Preserve Cross-Session Context

### User Context
- The user asked why the assistant could not see the previous conversation even though this is the same project folder.
- The explanation given: project files and chat history are separate. The assistant can inspect local files, Git state, and logs, but cannot automatically read previous chat sessions unless the relevant context was saved into the project.
- The user asked how to solve this class of problem.
- The agreed solution is to persist important working context in a Markdown file inside the project.
- The user then asked to create a Markdown file that records key conversation content from each work session.

### Work Summary
- Created this `AI_WORKLOG.md` file as the persistent cross-session work log.
- Future sessions should read this file before continuing prior work and append a new entry when meaningful progress, decisions, or blockers occur.

### Files Touched
- `AI_WORKLOG.md`

### Verification
- Not run; documentation-only change.

### Next Steps
- For future work, append concise entries here whenever important user requirements, decisions, fixes, verification results, or unresolved issues arise.

## 2026-06-18 - Read Current Code Knowledge Graph

### User Context
- The user asked the assistant to become familiar with the current code knowledge graph.

### Work Summary
- Read `.understand-anything/knowledge-graph.json` through the understand-chat workflow.
- Established the project baseline: a Python/YAML/Markdown sales lead generation system for overseas markets.
- Identified the main pipeline: keyword/search configuration -> search engine aggregation -> company website CSV output -> website crawl/link exploration -> contact/company profile extraction -> CSV/state persistence.
- Noted that the graph metadata points at git commit `53a90918201c9f8da99d36de9bca94856b501dfd`, which is also current `HEAD`.
- Noted that the working tree has later modifications in `README.md`, `config/keywords.yaml`, `config/search.py`, `config/search.yaml`, `run_crawl.py`, `run_search.py`, `tests/test_search_config.py`, generated caches, state files, and `company_websites.csv`, so graph-level architecture is reliable but changed file details should be checked directly.

### Files Touched
- `AI_WORKLOG.md`

### Verification
- Inspected graph metadata, node type counts, architectural layers, tour nodes, file summaries, edge relationships, current `HEAD`, and Git diff summary.
- Did not run tests; no code behavior was changed.

### Next Steps
- For future coding tasks, use the knowledge graph as an architecture map but inspect currently modified source files before making detailed assumptions.

## 2026-06-18 - Start Opportunity Analysis System Brainstorm

### User Context
- The user wants to add a new "商机分析系统" and asked for the assistant's thinking.

### Work Summary
- Reviewed current project context from `README.md`, file layout, recent git log, and the knowledge graph layers.
- Current project already covers lead collection: keyword configuration, website search, website crawling, contact/company profile extraction, CSV output, and status persistence.
- Initial product direction: place the opportunity analysis system after `company_info.csv`, turning collected company/contact data into scored, explainable, prioritized sales opportunities.
- No implementation has started; this is still in brainstorming/design mode.

### Files Touched
- `AI_WORKLOG.md`

### Verification
- Inspected project files, README, recent git log, and knowledge graph layer summaries.
- Did not run tests; no behavior changed.

### Next Steps
- Clarify whether the first version should focus on lead scoring, market segmentation, sales action recommendations, or an end-to-end but smaller MVP.

## 2026-06-18 - Lead Profile Analysis Protocol Design

### User Context
- The user reframed the project into three stages: define the information template needed for opportunity analysis, crawl target websites according to that template, then build customer profiles and score them.
- The user clarified that the search keywords should stay broad and cover all configured keyword targets. The goal is to collect enough company websites first, then deeply analyze each official website to build a customer profile.
- The user's company manufactures heat pumps. The target workflow is B2B overseas lead analysis for heat pump sales and marketing.
- The first-version marketing goal is automated marketing segmentation, not a single exact target type.
- The user chose AI-led analysis, direct website text input to AI, CSV plus JSON outputs, a separate profile-analysis Codex, and a reusable prompt/scoring standard as the first deliverable.

### Work Summary
- Designed a stable handoff protocol between the current crawler project and a separate profile-analysis Codex.
- Fixed first-version campaign segments: `distributor_dealer`, `installer_contractor`, `project_supply_candidate`, `brand_oem_candidate`, `manufacturer_competitor_or_partner`, and `low_fit_or_unknown`.
- Defined an input data package containing company metadata, search-source metadata, extracted contacts, page URLs/categories/text, and crawl metadata.
- Defined an output JSON schema containing customer profile facts, campaign segment, multi-dimensional scores, evidence, message angle, and next action.
- Defined a scoring model with these dimensions: `product_relevance`, `business_type_fit`, `cooperation_potential`, `company_scale_signal`, `contactability`, and `evidence_confidence`.
- Wrote the approved design document at `docs/superpowers/specs/2026-06-18-lead-profile-analysis-protocol-design.md`.

### Files Touched
- `AI_WORKLOG.md`
- `docs/superpowers/specs/2026-06-18-lead-profile-analysis-protocol-design.md`

### Verification
- Self-reviewed the design document for placeholders, contradictions, ambiguity, and scope drift.
- Did not run code tests because this was a documentation/design-only change.

### Next Steps
- The user should review the written design spec.
- After approval, create an implementation plan for generating profile-analysis input packages and later integrating profile-analysis outputs.

## 2026-06-18 - Lead Profile Input Package Implementation Plan

### User Context
- The user asked to enter the implementation planning stage after reviewing the purpose of the design document.

### Work Summary
- Created an implementation plan for the first handoff-layer version of the lead profile analysis protocol.
- Scoped the first implementation to generating per-company JSON input packages and a reusable profile-analysis Codex prompt.
- Kept AI calls, scoring execution, CRM integration, and email generation outside this first implementation scope.
- Planned a pure `profile_analysis/input_package.py` builder, optional `run_crawl.py --profile-input-dir` export, tests, README documentation, and verification steps.

### Files Touched
- `AI_WORKLOG.md`
- `docs/superpowers/plans/2026-06-18-lead-profile-input-packages.md`

### Verification
- Self-reviewed the plan for spec coverage, placeholder terms, type consistency, and task-level testability.
- Did not run code tests because no production code was changed in this planning step.

### Next Steps
- The user should choose an execution mode: subagent-driven execution or inline execution.

## 2026-06-18 - Profile Input Package Export Implementation

### User Context
- The user approved entering the implementation plan for the lead profile analysis protocol.
- First implementation scope is the handoff layer: generate JSON input packages and a reusable prompt for a separate profile-analysis Codex.
- The user explicitly noted that the crawling engine should continue using the existing scraping framework.

### Work Summary
- Added `profile_analysis/input_package.py` to build per-company JSON input packages from crawled pages and extracted contacts.
- Added optional `run_crawl.py --profile-input-dir` and `--profile-page-char-limit` support without replacing the existing `requests` or browser/Scrapling crawling flow.
- Added `docs/profile-analysis-agent-prompt.md` for the separate profile-analysis Codex.
- Updated README usage instructions.

### Files Touched
- `profile_analysis/__init__.py`
- `profile_analysis/input_package.py`
- `tests/test_profile_input_package.py`
- `run_crawl.py`
- `tests/test_run_crawl.py`
- `docs/profile-analysis-agent-prompt.md`
- `README.md`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests/test_profile_input_package.py tests/test_run_crawl.py`
- `python -m unittest discover -s tests`
- Deterministic sample export check using `run_crawl.py --profile-input-dir ...` against a temporary local HTTP page and temporary input CSV. The CLI used the existing requests crawl path, produced `127.0.0.1.json`, and the JSON contained `schema_version`, `company`, `contacts`, `pages`, and `crawl_metadata`.
- An earlier full CSV sample export was inconclusive, so final sample verification used the deterministic local HTTP page and temporary input CSV.

### Next Steps
- Open a separate Codex session with `docs/profile-analysis-agent-prompt.md`.
- Feed it sample `profile_inputs/<domain>.json` files and calibrate profile judgments.

## 2026-06-18 - CLI Parameter Comment Notes

### User Context
- The user asked to add comments around the customizable parameter sections in `run_crawl.py` and `run_search.py`.

### Work Summary
- Expanded Chinese comments in both scripts' `build_parser()` sections.
- Grouped the comments around input/output, search/crawl coverage, retry/rate-limit behavior, network/proxy settings, and browser-mode options.
- Kept this as a documentation-only code change; no command behavior or defaults were changed.

### Files Touched
- `run_crawl.py`
- `run_search.py`
- `AI_WORKLOG.md`

### Verification
- `python run_crawl.py --help`
- `python run_search.py --help`

## 2026-06-18 - Project-Level Lead Profile Analysis Skill

### User Context
- The user asked for a skill that a newly opened Codex can use to analyze customer profiles from `profile_inputs`.
- The user clarified that a project-level skill is enough because the new Codex will be opened from the `profile_inputs` directory.

### Work Summary
- Created a project-local Codex skill at `profile_inputs/.codex/skills/analyze-heat-pump-lead-profile/`.
- The skill instructs the new Codex to analyze only supplied `profile_inputs/*.json` files, not to browse or recrawl websites by default.
- The skill defines heat-pump B2B lead segments, scoring dimensions, priority levels, evidence requirements, output JSON schema, and batch-ranking behavior.

### Files Touched
- `profile_inputs/.codex/skills/analyze-heat-pump-lead-profile/SKILL.md`
- `profile_inputs/.codex/skills/analyze-heat-pump-lead-profile/agents/openai.yaml`
- `AI_WORKLOG.md`

### Verification
- Confirmed the skill files exist.
- Confirmed `SKILL.md` frontmatter includes `name` and `description`.
- Confirmed `agents/openai.yaml` includes display name, short description, default prompt, and implicit invocation policy.
- The official `quick_validate.py` script could not run in the current Python environment because `pyyaml` is not installed.

## 2026-06-22 - Default Profile Input Export Directory

### User Context
- The user asked to make `--profile-input-dir profile_inputs` the default for `run_crawl.py`.

### Work Summary
- Changed the `run_crawl.py` CLI default so direct `python run_crawl.py` runs now export profile-analysis JSON packages to `profile_inputs`.
- Updated the `--profile-input-dir` help text to describe it as the export directory.
- Updated README usage notes to state that profile input packages are exported by default and that the parameter is now mainly for overriding the directory.
- Added a regression test for the CLI default value.

### Files Touched
- `run_crawl.py`
- `tests/test_run_crawl.py`
- `README.md`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests.test_run_crawl.RunCrawlTests.test_cli_defaults_profile_input_dir_to_profile_inputs`
- `python -B -m unittest tests/test_run_crawl.py`
- `python run_crawl.py --help`

## 2026-06-22 - Success Missing Profile JSON Backfill Input

### User Context
- The user had already completed a first crawl round and found that some successful domains did not have profile JSON files because earlier runs happened before profile export was defaulted.
- The user asked to compare only `status=success` domains, generate a dedicated input table for those missing JSON files, and provide a command to run just that subset.

### Work Summary
- Compared `company_info.csv` success domains against existing `profile_inputs/<domain>.json` files.
- Found 159 successful domains without matching profile JSON files.
- Generated `company_websites_success_missing_json.csv` containing only those missing-success domains from `company_websites.csv`.
- Generated `success_missing_profile_json_domains.txt` as a plain domain list for review.

### Files Touched
- `company_websites_success_missing_json.csv`
- `success_missing_profile_json_domains.txt`
- `AI_WORKLOG.md`

### Verification
- Confirmed the generated CSV has 159 rows and 159 unique domains.
- Confirmed all generated rows map to `status=success` in `company_info.csv`.
- Confirmed none of the generated domains currently has a matching `profile_inputs/<domain>.json`.
- Confirmed there are no duplicate domains in the generated input CSV.

## 2026-06-23 - France Pool Heating Keyword File

### User Context
- The user decided to use one keyword YAML file per country.
- The user asked for a France-specific keyword file covering French and English terms for pool heat pumps, pool heating, and pool heating distribution.

### Work Summary
- Created `config/keywords_france.yaml`.
- Included only `France` as the country term to avoid mixing France keywords with other countries.
- Added bilingual English/French keyword groups for pool heat pumps, pool heating, and pool-heating distribution.

### Files Touched
- `config/keywords_france.yaml`
- `AI_WORKLOG.md`

### Verification
- Ran `build_keywords_from_config("config/keywords_france.yaml")`.
- Confirmed the file generates 23 keyword combinations.

## 2026-06-23 - France Keyword French Terms Correction

### User Context
- The user pointed out that the French terms were not sufficiently included in the France keyword file.

### Work Summary
- Updated `config/keywords_france.yaml` to preserve the user's original French phrases:
  - `Pompes à chaleur pour piscines`
  - `Chauffage de piscine`
  - `Distribution du chauffage de piscine`
- Added additional French variants for pool heat pumps, pool heating, and distribution/supplier searches.
- Added `en France` as an additional France country term so generated French search queries include natural French location wording.

### Files Touched
- `config/keywords_france.yaml`
- `AI_WORKLOG.md`

### Verification
- Ran `build_keywords_from_config("config/keywords_france.yaml")`.
- Confirmed the file now generates 60 keyword combinations and includes French query samples ending in both `France` and `en France`.

## 2026-06-23 - France Country Term Clarification

### User Context
- The user clarified that the missing French term referred to the country/location wording for France, not the industry keywords.

### Work Summary
- Added `France métropolitaine` to the France country terms in `config/keywords_france.yaml`.
- Kept `France` and `en France` as country/location terms.

### Files Touched
- `config/keywords_france.yaml`
- `AI_WORKLOG.md`

### Verification
- Ran `build_keywords_from_config("config/keywords_france.yaml")`.
- Confirmed the France keyword file now generates 90 keyword combinations and includes `France métropolitaine` in generated search queries.

## 2026-06-23 - United Kingdom Keyword File

### User Context
- The user asked for a UK-specific keyword YAML file using the same industry keywords as the original `config/keywords.yaml`.
- The user also asked for recommended commands for running search and crawl against that UK-specific input.

### Work Summary
- Created `config/keywords_uk.yaml`.
- Kept the original industry keyword groups: `heat_pump`, `hvac`, `mechanical_contractor`, and `distributor`.
- Scoped the country terms to `United Kingdom`, `UK`, `Great Britain`, and `England`.

### Files Touched
- `config/keywords_uk.yaml`
- `AI_WORKLOG.md`

### Verification
- Ran `build_keywords_from_config("config/keywords_uk.yaml")`.
- Confirmed the file generates 80 keyword combinations.

## 2026-06-24 - France UK Complement Keyword Files

### User Context
- The user wanted to swap France and UK keyword sets for complementary searches while keeping output locations unchanged to preserve domain uniqueness.

### Work Summary
- Created `config/keywords_france_complement.yaml` with France country terms and the UK/general HVAC keyword set.
- Created `config/keywords_uk_complement.yaml` with UK country terms and the France pool-heating keyword set.
- The intended search outputs remain `company_websites_france.csv` and `company_websites_uk.csv`, so `run_search.py` can continue deduping by domain in each country file.

### Files Touched
- `config/keywords_france_complement.yaml`
- `config/keywords_uk_complement.yaml`
- `AI_WORKLOG.md`

### Verification
- Ran `build_keywords_from_config("config/keywords_france_complement.yaml")`; it generates 60 keyword combinations.
- Ran `build_keywords_from_config("config/keywords_uk_complement.yaml")`; it generates 120 keyword combinations.

## 2026-06-23 - France Crawl Output Directory Setup

### User Context
- The user finished running France search and wanted to crawl companies from `company_websites_france.csv`.
- The user wanted France profile JSON files stored separately under `profile_inputs`.

### Work Summary
- Checked `company_websites_france.csv`; it contains 149 rows and 149 unique domains.
- Created `profile_inputs/france` for France crawl JSON output.

### Files Touched
- `profile_inputs/france/`
- `AI_WORKLOG.md`

### Verification
- Confirmed `company_websites_france.csv` exists and counted 149 unique domains.

## 2026-06-24 - Project File Guide

### User Context
- The user said the project files had become hard to remember and asked to organize/explain what the files are for.

### Work Summary
- Created `PROJECT_FILE_GUIDE.md` as a project file map.
- Categorized files into source code, keyword configs, search outputs, crawl outputs, runtime state directories, profile JSON inputs, AI analysis outputs, docs/work records, and generated/local tool files.
- Documented current France/UK mismatch after complement searches: search outputs have more domains than crawl outputs.
- Included recommended `run_crawl.py` commands for catching up France and UK crawl outputs while reusing existing state/output/profile directories.

### Files Touched
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Counted current `company_websites*.csv` and `company_info*.csv` rows, unique domains, and crawl statuses.
- Counted current JSON files in `profile_inputs/`, `profile_inputs/france/`, and `profile_inputs/uk/`.
- Reviewed the generated guide content after writing it.

## 2026-06-25 - Project File Guide Chinese Translation

### User Context
- The user asked to translate `PROJECT_FILE_GUIDE.md` into Chinese.

### Work Summary
- Translated `PROJECT_FILE_GUIDE.md` from English to Chinese.
- Preserved file paths, commands, current counts, and section structure.
- Kept the original filename `PROJECT_FILE_GUIDE.md`.

### Files Touched
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Reviewed the beginning and ending sections of `PROJECT_FILE_GUIDE.md` after translation.
- Confirmed the translated file has 202 lines.

## 2026-06-25 - Database Foundation

### User Context
- The user wants to evolve the current scraper from a small local tool into a larger deployed project.
- The agreed first implementation area is the database layer.
- Existing `run_search.py` and `run_crawl.py` scraping behavior should remain unchanged; the database should be additive.

### Work Summary
- Created a database foundation design and implementation plan.
- Added SQLAlchemy models for global domain dedupe, search results, crawl results, contacts, profile JSON package metadata, and country signals.
- Added SQLite/PostgreSQL-compatible session helpers and Alembic migration files.
- Added importers for existing `company_websites*.csv`, `company_info*.csv`, and `profile_inputs/**/*.json` data.
- Added `scripts/import_existing_data.py` so existing project outputs can be loaded into `sqlite:///leadgen.db` locally or PostgreSQL on a server.
- Added `requirements.txt` and updated README usage documentation.

### Files Touched
- `database/__init__.py`
- `database/models.py`
- `database/session.py`
- `database/importers.py`
- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/20260625_0001_database_foundation.py`
- `.gitignore`
- `scripts/import_existing_data.py`
- `requirements.txt`
- `tests/test_database_importers.py`
- `docs/superpowers/specs/2026-06-25-database-foundation-design.md`
- `docs/superpowers/plans/2026-06-25-database-foundation.md`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Installed new dependencies from `requirements.txt`.
- Ran `python -B -m unittest discover -s tests -p 'test_database_importers.py'`: 3 tests passed.
- Ran `DATABASE_URL=sqlite:////private/tmp/leadgen_alembic_test.db alembic upgrade head`: migration succeeded.
- Ran a France import smoke test into `/private/tmp/leadgen_import_smoke_20260625.db`: imported 315 domains, 315 search results, 315 crawl results, 3656 contacts, 194 profile packages, and 824 country signals.
- Re-ran the same France import against the same database: no duplicate search/crawl/contact/profile/country signal rows were inserted.
- Ran related tests for search, crawl, profile input packages, and database importers: all passed.
- Ran `python -B -m unittest discover -s tests`: 50 tests passed.

### Next Steps
- Decide whether to merge the database foundation branch into the main workspace.
- Next backend step should wrap search/crawl/import operations as background jobs while continuing to call the existing scraping functions.

## 2026-06-25 - PostgreSQL Full Data Import

### User Context
- The user chose to run PostgreSQL locally in Docker for now instead of deploying to a Windows server.
- The user asked to speed up and import all existing data into the database.

### Work Summary
- Ran the default full import into the local Docker PostgreSQL database.
- Detected that `profile_inputs/heat_pump_lead_analysis_outputs/heat_pump_lead_analysis.json` was being treated as a profile input package even though it is an analysis output file.
- Fixed `import_profile_dir` so profile JSON import requires a valid `company.domain` or `company.website`; it no longer falls back to the JSON filename.
- Deleted the one incorrectly imported empty-domain row from PostgreSQL.
- Re-ran the full import and confirmed the analysis output directory no longer imports anything.

### Files Touched
- `database/importers.py`
- `tests/test_database_importers.py`
- `AI_WORKLOG.md`

### Verification
- Ran full import into `postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen`.
- Final PostgreSQL counts:
  - `domains`: 1234
  - `search_results`: 2281
  - `crawl_results`: 2282
  - `contacts`: 18647
  - `profile_packages`: 1737
  - `country_signals`: 6379
- Re-ran full import after the fix; no duplicate search/crawl/contact/country/profile rows were added.
- Ran `python -B -m unittest discover -s tests`: 51 tests passed.

### Next Steps
- Merge the database foundation branch into the main workspace when ready.
- Start the background-task backend layer so search/crawl/import jobs can run from a service rather than manual CLI commands.

## 2026-06-25 - Process-Local Task Wrapper

### User Context
- The user asked to start wrapping the current CLI operations into backend tasks.
- The user rejected storing task status in the database for now.
- The agreed direction is to create reusable task handlers first, then add Celery later without rewriting the business logic.

### Work Summary
- Added a process-local task layer under `tasks/`.
- Added reusable handlers for `search`, `crawl`, and `import_existing_data`.
- Added a generic `run_task` wrapper that returns `success` / `failed`, params, summary, timestamps, duration, and error text without writing job state to the database.
- Added `scripts/run_task.py` as the unified CLI entry point.
- Refactored `scripts/import_existing_data.py` to reuse the shared import source discovery/import functions.
- Preserved existing `run_search.py`, `run_crawl.py`, and scraper behavior.

### Files Touched
- `tasks/__init__.py`
- `tasks/models.py`
- `tasks/runner.py`
- `tasks/importing.py`
- `tasks/handlers.py`
- `scripts/run_task.py`
- `scripts/import_existing_data.py`
- `tests/test_task_runner.py`
- `tests/test_task_handlers.py`
- `tests/test_run_task.py`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Watched new task tests fail before implementation because `tasks` / `scripts.run_task` did not exist.
- Ran task tests after implementation:
  - `python -B -m unittest discover -s tests -p 'test_task_runner.py'`
  - `python -B -m unittest discover -s tests -p 'test_task_handlers.py'`
  - `python -B -m unittest discover -s tests -p 'test_run_task.py'`
- Ran a `scripts/run_task.py import-existing-data` smoke test into `/private/tmp/leadgen_task_smoke_20260625.db`; it imported 159 domains and 159 search rows from `company_websites_success_missing_json.csv`.
- Ran `python -B -m unittest discover -s tests`: 59 tests passed.

### Next Steps
- Add Celery as the scheduling/execution layer later; Celery tasks should call the same `tasks/handlers.py` functions.
- Add FastAPI endpoints after task handlers are stable.

## 2026-06-25 - FastAPI Task API

### User Context
- The user asked the assistant to verify the task wrapper and continue with FastAPI if there were no issues.
- The task layer should still avoid database-backed job state; Celery will be added later.

### Work Summary
- Verified the existing task wrapper and PostgreSQL import state.
- Added a FastAPI app with:
  - `GET /health`
  - `POST /tasks/search`
  - `POST /tasks/crawl`
  - `POST /tasks/import-existing-data`
- The API executes handlers synchronously and returns the same process-local task result shape as `scripts/run_task.py`.
- Added request schemas for search, crawl, and import tasks.
- Documented API startup and example curl calls.

### Files Touched
- `api/__init__.py`
- `api/app.py`
- `api/schemas.py`
- `tests/test_api_app.py`
- `requirements.txt`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Ran `python -B -m unittest discover -s tests`: 59 tests passed before FastAPI work.
- Ran `python -B scripts/run_task.py import-existing-data --database-url sqlite:////private/tmp/leadgen_task_verify_20260625.db --search-csv company_websites_success_missing_json.csv`: task CLI succeeded.
- Queried local Docker PostgreSQL counts: 1234 domains, 2281 search results, 2282 crawl results, 18647 contacts, 1737 profile packages, 6379 country signals.
- Watched `tests/test_api_app.py` fail first because the `api` package did not exist, then implemented the API and made the tests pass.
- Ran `python -B -m unittest discover -s tests`: 63 tests passed.
- Started FastAPI with `python -B -m uvicorn api.app:app --host 127.0.0.1 --port 8010`.
- Verified `GET /health` returned `{"status":"ok"}`.
- Verified `POST /tasks/import-existing-data` imported `company_websites_success_missing_json.csv` into `/private/tmp/leadgen_api_smoke_20260625.db` and returned a `success` task result.

### Next Steps
- Run the FastAPI server locally with `uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload`.
- Add Celery worker integration next so API requests can enqueue tasks instead of blocking until completion.

## 2026-06-25 - Celery Task Queue

### User Context
- The user approved adding Celery and asked to proceed, with assistance requested only if needed.
- The task state should still not be stored in the business database.

### Work Summary
- Added Celery configuration using Redis broker/result backend.
- Added `lead_tasks.execute_task`, which calls the same `tasks/handlers.py` registry used by CLI and inline FastAPI.
- Added FastAPI `execution_mode="celery"` support.
- Added `TASK_EXECUTION_MODE=celery` environment variable support for `api.app:app`.
- Added `GET /tasks/{task_id}` to read Celery task status/result from Redis.
- Documented Redis, Celery worker, Celery-mode FastAPI, enqueue, and task-status commands.

### Files Touched
- `tasks/celery_app.py`
- `tasks/celery_tasks.py`
- `api/app.py`
- `requirements.txt`
- `tests/test_celery_integration.py`
- `tests/test_api_app.py`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Watched `tests/test_celery_integration.py` fail first because `tasks.celery_tasks` did not exist.
- Installed `celery` and `redis`.
- Ran `python -B -m unittest discover -s tests`: 67 tests passed.
- Started Redis with Docker: `leadgen-redis`.
- Started Celery worker with `python -B -m celery -A tasks.celery_app.celery_app worker --loglevel=INFO --pool=solo`.
- Started FastAPI in Celery mode on `127.0.0.1:8011`.
- Submitted `POST /tasks/import-existing-data`; API returned HTTP 202 and a Celery `task_id`.
- Queried `GET /tasks/{task_id}`; API returned `SUCCESS` and a task result importing 159 domains and 159 search rows into `/private/tmp/leadgen_celery_e2e_20260625.db`.

### Next Steps
- Keep Redis running when using Celery mode; stop/start with Docker as needed.
- Next backend step can add read-only API endpoints for browsing domains, contacts, profile packages, and country signals from PostgreSQL.

## 2026-06-25 - FastAPI Read Endpoints

### User Context
- The user asked to continue backend development after Celery.
- The next useful step is to make imported PostgreSQL data readable through the backend before building a Vue console UI.

### Work Summary
- Added a database query layer for read-only backend access.
- Added FastAPI endpoints:
  - `GET /database/stats`
  - `GET /domains`
  - `GET /domains/{domain}`
- `GET /domains` supports `q`, `country`, `status`, `limit`, and `offset`.
- `GET /domains/{domain}` returns the domain record plus contacts, profile packages, and country signals.
- Added API tests using an in-memory SQLite database with injected session factory.
- Updated README and project file guide with the new read endpoints.

### Files Touched
- `database/queries.py`
- `api/app.py`
- `tests/test_api_read_endpoints.py`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Watched `tests/test_api_read_endpoints.py` fail first because `create_app()` did not support `session_factory` and no read endpoints existed.
- Implemented `database/queries.py` and FastAPI read routes.
- Ran `python -B -m unittest tests/test_api_read_endpoints.py`: 4 tests passed.
- Ran `python -B -m unittest discover -s tests`: 71 tests passed.
- Ran a read-only FastAPI smoke test against local Docker PostgreSQL:
  - `GET /database/stats` returned 1234 domains, 2281 search results, 2282 crawl results, 18647 contacts, 1737 profile packages, and 6379 country signals.
  - `GET /domains?country=France&status=success&limit=3` returned 3 domain rows from the live database.
- Started Uvicorn on `http://127.0.0.1:8000` with the local PostgreSQL `DATABASE_URL`.
- Verified real HTTP `curl http://127.0.0.1:8000/database/stats` returned the same live database counts.

### Next Steps
- Add more read endpoints only when the Vue console needs them, such as search history, crawl history, profile package download, or pagination totals.

## 2026-06-25 - Vue Console First Version

### User Context
- The user approved moving from backend-only work to the first Vue3 console.
- The agreed first screen is an operational console, not a landing page: database summary, customer list, filters, pagination, and customer detail.

### Work Summary
- Added backend pagination metadata: `GET /domains` now returns `total` before `limit` / `offset`.
- Added FastAPI CORS support for local Vue dev origins:
  - `http://127.0.0.1:5173`
  - `http://localhost:5173`
- Created the Vue3/Vite/TypeScript console under `frontend/`.
- Added a typed API client for:
  - `GET /database/stats`
  - `GET /domains`
  - `GET /domains/{domain}`
- Built the first console UI:
  - database metrics
  - searchable/filterable lead table
  - pagination
  - selected lead detail with website, contacts, profile packages, and country signals
- Updated README and project file guide with frontend usage and file roles.

### Files Touched
- `.gitignore`
- `api/app.py`
- `database/queries.py`
- `tests/test_api_app.py`
- `tests/test_api_read_endpoints.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/index.html`
- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/style.css`
- `frontend/src/env.d.ts`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`

### Verification
- Watched `tests/test_api_read_endpoints.py` fail first because `/domains` did not return `total`.
- Implemented `total` in `database/queries.py`; `python -B -m unittest tests/test_api_read_endpoints.py` passed with 5 tests.
- Watched `tests/test_api_app.py` fail first because CORS headers were missing.
- Added FastAPI CORS middleware; `python -B -m unittest tests/test_api_app.py` passed with 6 tests.
- Ran `npm install` in `frontend/`; replaced deprecated `lucide-vue-next` with `@lucide/vue`.
- Ran `npm run build`; fixed Vite env typing and Vue plugin configuration; final build passed.
- Ran `python -B -m unittest discover -s tests`: 73 tests passed.
- Re-ran `npm run build`: Vue type-check and Vite production build passed.
- Restarted FastAPI on `http://127.0.0.1:8000` using local PostgreSQL.
- Verified `GET /domains?country=France&status=success&limit=2` returned `total: 217`.
- Verified CORS with `Origin: http://127.0.0.1:5173` returned HTTP 200 and `access-control-allow-origin`.
- Started Vite dev server on `http://127.0.0.1:5173/` and confirmed the page returns HTML.

### Next Steps
- Next product step can add task submission forms for search/crawl/import and Celery task polling into the console.

## 2026-06-25 - Console Task Controls

### User Context
- The user approved continuing after the first Vue3 console.
- The next product step is to operate search/crawl/import tasks from the console instead of only browsing existing data.

### Work Summary
- Added `GET /runtime` to report the current task execution mode: `inline` or `celery`.
- Added frontend task API types and client functions for:
  - `POST /tasks/search`
  - `POST /tasks/crawl`
  - `POST /tasks/import-existing-data`
  - `GET /tasks/{task_id}`
- Added a compact task panel to the Vue console.
- The task panel includes safe default France-oriented parameters for search, crawl, and import.
- Inline task responses display their summary immediately.
- Celery queued task responses display task id and poll task status automatically.
- Updated README and project file guide with task control behavior.

### Files Touched
- `api/app.py`
- `tests/test_api_app.py`
- `frontend/src/types.ts`
- `frontend/src/api.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `AI_WORKLOG.md`
- `docs/superpowers/plans/2026-06-25-console-task-controls.md`

### Verification
- Watched `tests/test_api_app.py` fail first because `/runtime` returned 404.
- Implemented `/runtime`; `python -B -m unittest tests/test_api_app.py` passed with 7 tests.
- Ran `npm run build`; fixed TypeScript payload typing; final Vue type-check and Vite production build passed.
- Ran `python -B -m unittest discover -s tests`: 74 tests passed.
- Re-ran `npm run build`: Vue type-check and Vite production build passed.
- Restarted FastAPI on `http://127.0.0.1:8000` using local PostgreSQL.
- Verified real HTTP `GET /runtime` returned `{"task_execution_mode":"inline"}`.
- Verified CORS for `Origin: http://127.0.0.1:5173` on `/runtime`.
- Verified the running Vite console at `http://127.0.0.1:5173/` returns HTML.

### Next Steps
- Use Celery mode for long search/crawl/import tasks from the console; inline mode is acceptable for short smoke tests only.

## 2026-06-25 - Chinese Heat Pump Console Copy

### User Context
- The user asked to change the frontend into Chinese and make it more personalized.
- The desired direction is no longer a generic English "Lead Console"; it should feel like an internal heat-pump lead generation console.

### Work Summary
- Renamed the console experience to `热泵商机雷达`.
- Changed the document language and browser title to Chinese.
- Localized visible frontend text across the dashboard, task controls, customer table, pagination, empty states, and detail panel.
- Reframed generic CRM labels into heat-pump lead workflow language:
  - `客户域名`
  - `画像素材包`
  - `国家信号`
  - `获客流水线`
  - `找官网`
  - `抓官网`
  - `入库`
- Kept backend API names and task payload field names unchanged.

### Files Touched
- `frontend/index.html`
- `frontend/src/App.vue`
- `AI_WORKLOG.md`

### Verification
- Ran `npm run build`: Vue type-check and Vite production build passed.
- Verified the running Vite page returns `lang="zh-CN"` and `<title>热泵商机雷达</title>`.
- Scanned for old visible English strings like `Lead Console`, `Task execution`, and `Loading leads`; no matches remained in `frontend/src` or `frontend/index.html`.

## 2026-06-25 - Project Services Shutdown

### User Context
- The user asked to stop all currently running project-related services and restart them tomorrow on request.

### Work Summary
- Stopped the FastAPI backend running on `127.0.0.1:8000`.
- Stopped the Vue/Vite console running on `127.0.0.1:5173`.
- Stopped Docker containers:
  - `leadgen-redis`
  - `leadgen-postgres`
- Data is preserved because the Docker containers were stopped, not removed.

### Verification
- Confirmed no listeners remained on ports `8000`, `5173`, `5432`, or `6379`.
- Confirmed `docker ps` showed no running project containers.

### Restart Notes
- Tomorrow, restart Docker containers first:
  - `docker start leadgen-postgres leadgen-redis`
- Then start FastAPI from `/Users/zhize/The Eyes of God/.worktrees/database-foundation`.
- Then start Vue/Vite from `/Users/zhize/The Eyes of God/.worktrees/database-foundation/frontend`.

## 2026-06-26 - Database-First Stage Persistence

### User Context
- The user decided to postpone AI inference and first implement the earlier database-first workflow.
- Target flow: search official websites -> store stage A in database; crawl official websites -> store stage B in database; later confirmation / AI scoring -> store final high-value table C.
- CSV/JSON outputs should remain useful, but they should no longer be the only place where stage data exists.

### Work Summary
- Added row-based database importers so search/crawl task output can be inserted directly without rereading CSV files.
- Added `database/stage_persistence.py` as the shared persistence layer for search and crawl stages.
- Connected database persistence to:
  - direct `run_search.py` / `run_crawl.py` commands through `--database-url`, `DATABASE_URL`, and `--no-persist-to-database`;
  - `tasks/handlers.py`, used by `scripts/run_task.py`, FastAPI task endpoints, and future Celery workers.
- Search stage now persists to `domains`, `search_results`, and `country_signals` when a database URL is configured.
- Crawl stage now persists to `domains`, `crawl_results`, `contacts`, `profile_packages`, and `country_signals` when a database URL is configured.
- Kept final confirmation / AI scoring tables (`qualified_leads`, `company_profiles`, `lead_scores`) out of this implementation because the user wants AI inference later.
- Updated README and project file guide to describe database as the configured stage-of-record, with CSV/JSON retained as compatibility backup and AI input material.

### Files Touched
- `database/importers.py`
- `database/stage_persistence.py`
- `tasks/handlers.py`
- `scripts/run_task.py`
- `api/schemas.py`
- `run_search.py`
- `run_crawl.py`
- `tests/test_database_importers.py`
- `tests/test_task_handlers.py`
- `tests/test_run_search.py`
- `tests/test_run_crawl.py`
- `frontend/src/types.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `docs/superpowers/plans/2026-06-26-database-first-stage-persistence.md`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests/test_database_importers.py`: 6 tests passed.
- `python -B -m unittest tests/test_task_handlers.py`: 6 tests passed.
- `python -B -m unittest tests/test_run_search.py`: 5 tests passed.
- `python -B -m unittest tests/test_run_crawl.py`: 10 tests passed.
- `python -B -m unittest discover -s tests`: 78 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- Project services were not restarted during this work session.

### Next Steps
- Start the database, FastAPI, and Vue services only when the user asks to resume running the project.
- Next implementation milestone should be table C design: confirmed leads, normalized company profiles, scoring records, and the future AI inference/confirmation node.

## 2026-06-26 - Database-Native Console And Company Library

### User Context
- The user can now connect directly to the database and asked why CSV files are still needed.
- The user asked to cancel CSV files from the main workflow, store all search results directly into database tables, and add a frontend enterprise library module split into three libraries:
  - Stage A tables from search.
  - Stage B tables from crawl.
  - Stage C tables from later confirmation / AI scoring.
- The user confirmed profile JSON should be retained.

### Work Summary
- Kept CLI CSV compatibility but removed CSV as the console's primary search/crawl handoff path.
- Added Stage C SQLAlchemy models and migration:
  - `qualified_leads`
  - `company_profiles`
  - `lead_scores`
- Added company library query functions for Stage A/B/C and stage-level stats.
- Added FastAPI endpoints:
  - `GET /company-library/stats`
  - `GET /company-library/stage-a`
  - `GET /company-library/stage-b`
  - `GET /company-library/stage-c`
- Changed crawl task handling so the console can omit CSV input/output; the backend selects candidates from Stage A database rows.
- Changed search task handling so the console can omit CSV output; search rows persist directly to Stage A tables.
- Updated `run_search.py` / `run_crawl.py` internals to support `output_file=None` while keeping direct CLI defaults unchanged.
- Updated Vue console:
  - Added `企业库` module with `官网候选库 A`、`抓取画像库 B`、`优先客户库 C`.
  - Removed CSV input/output fields from primary search/crawl controls.
  - Added database-native crawl filters: candidate country, candidate query, candidate limit, and recrawl toggle.
- Updated README, project file guide, design spec, and implementation plan.

### Files Touched
- `database/models.py`
- `database/queries.py`
- `alembic/versions/20260626_0002_stage_c_company_library.py`
- `tasks/handlers.py`
- `api/app.py`
- `api/schemas.py`
- `run_search.py`
- `run_crawl.py`
- `frontend/src/types.ts`
- `frontend/src/api.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_database_models.py`
- `tests/test_database_queries.py`
- `tests/test_api_read_endpoints.py`
- `tests/test_task_handlers.py`
- `tests/test_run_search.py`
- `tests/test_run_crawl.py`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `docs/superpowers/specs/2026-06-26-database-native-company-library-design.md`
- `docs/superpowers/plans/2026-06-26-database-native-company-library.md`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests/test_database_models.py`: 1 test passed.
- `python -B -m unittest tests/test_database_queries.py`: 4 tests passed.
- `python -B -m unittest tests/test_task_handlers.py`: 8 tests passed.
- `python -B -m unittest tests/test_api_read_endpoints.py`: 9 tests passed.
- `python -B -m unittest tests/test_run_search.py`: 6 tests passed.
- `python -B -m unittest tests/test_run_crawl.py`: 11 tests passed.
- `python -B -m unittest discover -s tests`: 91 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `DATABASE_URL='postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen' alembic upgrade head`: applied migration `20260626_0002`.
- Restarted FastAPI with the new code.
- Verified `GET /company-library/stats` against local PostgreSQL returned Stage A/B counts and Stage C count 0.
- Verified `GET /company-library/stage-a`, `/stage-b`, and `/stage-c` return valid JSON against local PostgreSQL.

### Next Steps
- Later work: implement the confirmation / AI scoring node that writes actual Stage C records.

## 2026-06-26 - Database Keyword Center

### User Context
- The user decided keyword configuration should no longer be edited through YAML files in the normal console workflow.
- The user asked for a frontend keyword configuration center backed by the database, with basic create, save, notes, and delete operations.
- The user approved importing the existing YAML keyword files as initial database keyword groups.

### Work Summary
- Added `keyword_groups` database storage for reusable keyword groups, including country terms, keyword terms, notes, active status, and timestamps.
- Added CRUD helpers and YAML import helpers in `database/keyword_groups.py`.
- Added FastAPI endpoints:
  - `GET /keyword-groups`
  - `POST /keyword-groups`
  - `PUT /keyword-groups/{group_id}`
  - `DELETE /keyword-groups/{group_id}`
- Changed search task requests to accept `keyword_group_id`.
- Changed search task execution so the backend loads keyword terms from the database and converts them into the existing `KeywordSpec` flow.
- Kept YAML support only as CLI/backfill compatibility, not as the console's primary workflow.
- Added `scripts/import_keyword_groups.py` and imported four existing groups into local PostgreSQL:
  - `keywords_france`
  - `keywords_france_complement`
  - `keywords_uk`
  - `keywords_uk_complement`
- Updated the Vue console with a new `关键词配置中心` module and changed `找官网` to select a database keyword group instead of entering a YAML path.
- Updated README, project file guide, design spec, and implementation plan.

### Files Touched
- `database/models.py`
- `database/keyword_groups.py`
- `alembic/versions/20260626_0003_keyword_groups.py`
- `tasks/handlers.py`
- `api/app.py`
- `api/schemas.py`
- `run_search.py`
- `frontend/src/types.ts`
- `frontend/src/api.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `scripts/import_keyword_groups.py`
- `tests/test_database_models.py`
- `tests/test_keyword_groups.py`
- `tests/test_import_keyword_groups_script.py`
- `tests/test_run_search.py`
- `tests/test_task_handlers.py`
- `tests/test_api_read_endpoints.py`
- `tests/test_api_app.py`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `docs/superpowers/specs/2026-06-26-database-keyword-center-design.md`
- `docs/superpowers/plans/2026-06-26-database-keyword-center.md`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest discover -s tests`: 99 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `DATABASE_URL='postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen' alembic upgrade head`: applied migration `20260626_0003`.
- `python scripts/import_keyword_groups.py --database-url 'postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen'`: imported four keyword groups.
- Verified `GET /health` returned `{"status":"ok"}`.
- Verified `GET /runtime` returned inline task execution mode.
- Verified `GET /keyword-groups` returned the four imported keyword groups.
- Verified the Vue dev server returned HTTP 200 at `http://127.0.0.1:5173/`.

### Next Steps
- Use the console keyword center as the normal place to maintain search keyword groups.
- Later work: add the Stage C confirmation / AI scoring node and connect AI inference there.

## 2026-06-26 - Console Sidebar Navigation

### User Context
- The user felt the console should not put every feature into one long frontend form.
- The user asked for a left navigation bar where modules such as enterprise library and keyword configuration center are links that switch to their own control pages.

### Work Summary
- Changed the Vue console from a vertically stacked single page into an application shell with a left sidebar.
- Added top-level modules:
  - `任务控制台`
  - `企业库`
  - `关键词配置中心`
  - `客户池`
- Kept the existing backend APIs and data loading logic unchanged.
- Kept enterprise library A/B/C as internal tabs inside the enterprise library module.
- Changed enterprise library row clicks to open the selected company in the `客户池` detail page.
- Added responsive behavior so the sidebar becomes a compact top navigation on narrower screens.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `AI_WORKLOG.md`

### Verification
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `curl -I http://127.0.0.1:5173/`: local Vite service returned HTTP 200.
- Browser automation was attempted, but local Playwright browser binaries were unavailable and launching system Chrome in headless mode failed in the current sandbox. No production code depends on that check.

## 2026-06-26 - Console Advanced Task Parameters

### User Context
- The user asked to expose additional runtime parameters in the frontend instead of leaving them only available through backend schemas or CLI.

### Work Summary
- Added search task controls for:
  - Keyword delay seconds.
  - Search engine request delay seconds.
- Added crawl task controls for:
  - Max retries.
  - Retry failed only.
  - Backoff base and max delay.
  - Global request delay.
  - Proxy URL.
  - System proxy usage.
  - Browser headless mode.
  - Browser timeout, wait time, and max pages.
- Grouped advanced crawl settings into `重试退避` and `代理与浏览器` sections so the task form remains scannable.
- Extended frontend `CrawlTaskRequest` TypeScript type to include the backend-supported advanced fields.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `frontend/src/types.ts`
- `AI_WORKLOG.md`

### Verification
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `curl -I http://127.0.0.1:5173/`: local Vite service returned HTTP 200.

## 2026-06-26 - System Logic Refactor Design

### User Context
- The user clarified that the current confusion is not frontend layout, but system logic.
- The core issue is that database stages, local state directories, CSV compatibility, JSON files, and A/B/C library views are not yet governed by one clear source-of-truth model.
- The user approved designing the system according to the assistant's recommended direction.

### Work Summary
- Wrote a system-level design document for restructuring the project around one database-first acquisition pipeline:
  - Keyword groups.
  - Search tasks.
  - Stage A official website candidate library.
  - Crawl tasks.
  - Stage B crawled profile material library.
  - AI / human confirmation tasks.
  - Stage C priority customer library.
- Defined that task progress should move from `.search_state` / `.crawl_state` directories into database tables.
- Proposed new `task_runs` and `task_items` tables to track task batches, task items, item status, errors, attempts, and summaries.
- Clarified that CSV should become a legacy import/export tool, not a primary workflow dependency.
- Clarified that profile JSON should be treated as registered attachments through `profile_packages`, not as the source of truth for stage membership.
- Defined B library semantics more strictly: default B should represent successful crawl material; empty, failed, and error states should be sub-statuses.
- Outlined a phased migration strategy that preserves the existing scraping engines while moving orchestration and progress tracking into the database.

### Files Touched
- `docs/superpowers/specs/2026-06-26-system-logic-refactor-design.md`
- `AI_WORKLOG.md`

### Verification
- Reviewed current `database/models.py`, `tasks/handlers.py`, `database/queries.py`, and the previous company library design before writing the spec.
- Scanned the new design document for placeholder markers such as `TBD`, `TODO`, and unresolved ambiguity; none were found.

## 2026-06-26 - Database Task Batches Phase 1

### User Context
- The user approved implementing the system logic refactor.
- The agreed first implementation phase is moving search/crawl task progress away from user-facing local state directories and into database task batches.

### Work Summary
- Added task batch database models:
  - `task_runs`
  - `task_items`
- Added Alembic migration `20260626_0004_task_batches`.
- Added `database/task_batches.py` for creating task runs, creating task items, updating item status, finishing runs, listing runs, and reading run detail.
- Updated `run_search.py`:
  - Supports `state_dir=None` for database-native no-state execution.
  - Supports `on_keyword_done` callback for per-keyword progress.
  - Keeps legacy state directory behavior when a state directory is provided.
- Updated `run_crawl.py`:
  - Supports `state_dir=None` for database-native no-state execution.
  - Supports `on_domain_done` callback for per-domain progress.
  - Keeps legacy state directory behavior when a state directory is provided.
- Updated `tasks/handlers.py`:
  - Database-backed search/crawl tasks now create `task_runs`.
  - Search tasks create keyword `task_items` when using database keyword groups.
  - Crawl tasks create domain `task_items` when selecting candidates from Stage A.
  - Search/crawl callbacks update task item status.
  - Task runs finish with `success`, `partial_failed`, or `failed` based on item statuses.
- Added FastAPI task center endpoints:
  - `GET /task-runs`
  - `GET /task-runs/{id}`
- Updated Vue console:
  - Added `任务中心` module.
  - Added task run list and task item detail view.
  - Removed visible search/crawl state directory inputs from primary task forms.
- Updated README, project file guide, and implementation plan.

### Files Touched
- `database/models.py`
- `database/task_batches.py`
- `alembic/versions/20260626_0004_task_batches.py`
- `run_search.py`
- `run_crawl.py`
- `tasks/handlers.py`
- `api/app.py`
- `frontend/src/types.ts`
- `frontend/src/api.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_database_models.py`
- `tests/test_task_batches.py`
- `tests/test_run_search.py`
- `tests/test_run_crawl.py`
- `tests/test_task_handlers.py`
- `tests/test_api_read_endpoints.py`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `docs/superpowers/plans/2026-06-26-database-task-batches.md`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests/test_database_models.py`: 3 tests passed.
- `python -B -m unittest tests/test_task_batches.py`: 3 tests passed.
- `python -B -m unittest tests/test_run_search.py`: 8 tests passed.
- `python -B -m unittest tests/test_run_crawl.py`: 12 tests passed.
- `python -B -m unittest tests/test_task_handlers.py`: 11 tests passed.
- `python -B -m unittest tests/test_api_read_endpoints.py`: 12 tests passed.
- `python -B -m unittest discover -s tests`: 109 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- Applied PostgreSQL migration `20260626_0004`.
- Restarted FastAPI from the current worktree.
- Verified `GET /health` returned `{"status":"ok"}`.
- Verified `GET /task-runs?limit=3` returned a valid empty task-run list on local PostgreSQL.
- Verified local Vue dev server returned HTTP 200.

### Next Steps
- Next phase should make B library default to successful crawl material and show empty/failed/error as explicit sub-statuses.
- Later phase should add confirm/AI task that promotes B material into C priority customer records.

## 2026-06-27 - Empty State Directory Response Cleanup

### User Context
- The user ran a console search task and saw a successful database-backed result, but the response still included `"state_dir": ""`.
- The expected system logic is that console/database tasks should not surface local state directory concepts.

### Work Summary
- Interpreted the run result: 7 search rows persisted, no CSV output, task batch id 1, no crawl/contact/profile changes because it was a search task.
- Updated task handlers so blank `state_dir` values are treated the same as an omitted value.
- Database-backed search/crawl summaries no longer include `state_dir` when the frontend/API sends an empty string.

### Files Touched
- `tasks/handlers.py`
- `tests/test_task_handlers.py`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests/test_task_handlers.py`: 11 tests passed.
- `git diff --check`: passed.

## 2026-06-29 - Candidate Groups Between Search And Crawl

### User Context
- The user wanted search task output to be stored as persistent groups that can be selected later by crawl tasks.
- The user specifically rejected a one-time "crawl domains from this task now" button because search output may be crawled days later.

### Work Summary
- Added a candidate group layer between Stage A search output and Stage B crawl input.
- Search tasks now create `candidate_groups` and `candidate_group_items` after persisting search rows.
- Candidate group items store `domain_id` and `search_result_id` so crawl tasks use stable domain indexes while preserving search evidence.
- Crawl tasks now accept `candidate_group_id` and read domains from that group.
- Added FastAPI endpoints:
  - `GET /candidate-groups`
  - `GET /candidate-groups/{id}`
- Updated Vue console:
  - Added `候选组` navigation module.
  - Added candidate group list/detail view.
  - Added candidate group selector to the crawl form.
- Added design and implementation plan documents for the candidate group mechanism.

### Files Touched
- `database/models.py`
- `database/candidate_groups.py`
- `alembic/versions/20260629_0005_candidate_groups.py`
- `tasks/handlers.py`
- `api/app.py`
- `api/schemas.py`
- `scripts/run_task.py`
- `frontend/src/types.ts`
- `frontend/src/api.ts`
- `frontend/src/App.vue`
- `tests/test_database_models.py`
- `tests/test_candidate_groups.py`
- `tests/test_task_handlers.py`
- `tests/test_api_read_endpoints.py`
- `README.md`
- `PROJECT_FILE_GUIDE.md`
- `docs/superpowers/specs/2026-06-29-candidate-groups-design.md`
- `docs/superpowers/plans/2026-06-29-candidate-groups.md`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests/test_database_models.py`: 4 tests passed.
- `python -B -m unittest tests/test_candidate_groups.py`: 3 tests passed.
- `python -B -m unittest tests/test_task_handlers.py`: 13 tests passed.
- `python -B -m unittest tests/test_api_read_endpoints.py`: 14 tests passed.
- `python -B -m unittest discover -s tests`: 117 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `git diff --check`: passed.
- Applied PostgreSQL migration `20260629_0005`.
- Started FastAPI and Vue dev server.
- Verified `GET /health` returned `{"status":"ok"}`.
- Verified `GET /candidate-groups?limit=3` returned a valid empty list.
- Verified local Vue dev server returned HTTP 200.

### Next Steps
- Run a new search task from the console; it should create a candidate group.
- Then run a crawl task by selecting that candidate group.
- Later add Celery worker execution so each crawl domain can be processed as an independent queue item.

## 2026-06-29 - Search Console Keyword Count Display

### User Context
- The user clarified that the search console should normally run every keyword combination in the selected keyword group.
- The previous editable "关键词数" field was misleading because it implied users should manually limit combinations during normal use.

### Work Summary
- Changed the Vue search task form from editable "关键词数" to read-only "关键词组合数".
- The displayed value now follows the selected keyword group's actual `keyword_count`.
- The console no longer sends `limit_keywords` when starting a search task, so the backend runs all keyword combinations by default.
- Kept backend/API compatibility for `limit_keywords` so old scripts and direct API calls can still use it for testing.

### Files Touched
- `frontend/src/App.vue`
- `README.md`
- `AI_WORKLOG.md`

### Verification
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-06-29 - Crawl Form Context-Aware Disabled Fields

### User Context
- The user wanted crawl parameters that do not apply in the current context to be greyed out and non-editable.
- Specifically, candidate country/query should be inactive when a candidate group is selected, and backend-specific settings should only be editable for the backend where they apply.

### Work Summary
- Added computed form state for candidate-group selection, requests mode, and browser mode.
- Disabled and greyed out candidate country/query when a candidate group is selected.
- Disabled and greyed out browser-only settings in requests mode:
  - browser timeout
  - browser wait
  - browser max pages
  - browser headless
- Disabled and greyed out the requests-only system proxy option in browser mode.
- Updated crawl task payload construction so inactive context fields are not submitted.
- Added a small regression test for the frontend crawl form disabled-state bindings.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_crawl_form_state.py`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests/test_frontend_crawl_form_state.py`: 3 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-06-29 - Console Realtime Task Progress

### User Context
- The user observed that search and crawl tasks had no visible runtime feedback in the frontend.
- The command line felt better because it printed progress while tasks were running.

### Work Summary
- Added a realtime progress panel to the task console for search and crawl tasks.
- When a task starts, the frontend now polls the latest running `task_runs` record for that task type.
- The panel shows:
  - task status
  - completed / total item count
  - per-status counts
  - recent keyword/domain execution items
- Inline task completion still loads the final task run detail from the returned `task_run_id`.
- Added a regression test to ensure the console keeps the task progress polling and progress panel bindings.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_task_progress_panel.py`
- `AI_WORKLOG.md`

### Verification
- `python -B -m unittest tests/test_frontend_task_progress_panel.py`: 3 tests passed.
- `python -B -m unittest tests/test_frontend_crawl_form_state.py`: 3 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-06-29 - Search Task 5 Failure Diagnosis

### User Context
- The user ran a search task and received `rows: 0`, `candidate_group_id: null`, and zero database imports.
- The user reported that the whole round failed.

### Diagnosis
- Database task run `5` was a `search` task for keyword group `6` (`意大利泳池机`).
- The keyword group generated 60 keyword combinations: 15 business terms times 4 Italy country terms.
- All 60 task items ran and all 60 failed.
- The dominant errors were:
  - 49 keywords timed out against `html.duckduckgo.com`.
  - 11 keywords received DuckDuckGo HTTP 202 challenge/throttle pages.
- Therefore this was not a deduplication issue and not a database write issue. The search source was throttled or unreachable, so no domains could be persisted and no candidate group was created.

### Next Action
- Retry with Bing first, or use both engines after reducing pressure.
- For a smoke test, run fewer pages and keep larger keyword/request intervals.
- Improve the console/API so search failures expose task status and top error summaries directly instead of only showing `rows: 0`.

## 2026-06-29 - Search Task 6 Emergency Stop

### User Context
- The user switched the search engine to Bing, but the run was still failing.
- The user wanted to pause the task from the console, but the current UI had no pause/cancel button.

### Diagnosis
- Database task run `6` was a `search` task for keyword group `6` (`意大利泳池机`).
- Parameters were `engines=bing`, `backend=requests`, `max_pages=1`, `keyword_delay_seconds=10`, and `engine_request_delay_seconds=5`.
- Bing returned captcha/challenge pages for the first keywords, so the run was blocked by the search source.

### Emergency Action
- Stopped the running FastAPI `uvicorn` process that was executing the inline search task.
- Marked task run `6` as `cancelled` in the database.
- Final item summary: 5 failed keywords and 55 cancelled keywords.
- Restarted the FastAPI backend on `http://127.0.0.1:8000`.

### Product Gap
- Inline task mode has no user-facing cancellation control.
- The next implementation should add a cancel button and a backend cancellation endpoint so search/crawl loops can stop cleanly without killing the whole backend process.

## 2026-06-29 - Task Cancellation Button

### User Context
- The user wanted a frontend cancel button after search tasks were blocked by DuckDuckGo and Bing challenge/captcha pages.
- The previous workaround required killing the FastAPI backend process, which stopped the task but also interrupted the whole console backend.

### Work Summary
- Added cooperative task cancellation using existing database task tables.
- Added `POST /task-runs/{task_run_id}/cancel`.
- Added database helpers to mark a task run as `cancelling`, mark pending items as `cancelled`, and prevent late callbacks from overwriting cancelled items.
- Added cancellation checks to `run_search` and `run_crawl`.
  - Search stops between keywords.
  - Crawl stops between domains.
  - A currently active HTTP/browser request is allowed to finish or time out before the loop stops.
- Updated task finalization so cancelling tasks finish as `cancelled`.
- Updated the outer task result so inline API responses can report `cancelled` instead of always reporting `success`.
- Added cancel buttons in:
  - realtime task progress panel
  - task center detail panel
- Added `取消中` status display and task center filter option.

### Files Touched
- `database/task_batches.py`
- `tasks/handlers.py`
- `tasks/models.py`
- `tasks/runner.py`
- `api/app.py`
- `run_search.py`
- `run_crawl.py`
- `frontend/src/api.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_task_batches.py`
- `tests/test_task_handlers.py`
- `tests/test_task_runner.py`
- `tests/test_run_search.py`
- `tests/test_run_crawl.py`
- `tests/test_api_app.py`
- `tests/test_frontend_task_progress_panel.py`
- `docs/superpowers/specs/2026-06-29-task-cancellation-design.md`
- `docs/superpowers/plans/2026-06-29-task-cancellation.md`

### Verification
- `python -B -m unittest tests/test_task_runner.py tests/test_task_batches.py tests/test_run_search.py tests/test_run_crawl.py tests/test_task_handlers.py tests/test_api_app.py tests/test_frontend_task_progress_panel.py`: 60 tests passed.
- `python -B -m unittest discover -s tests`: 135 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-06-30 - Italy Pool Search Duplicate Domain Diagnosis

### User Context
- The user ran a new Italy pool heat pump search and saw the candidate group show 11 already-crawled domains before starting a new crawl.
- The user asked whether those repeated domains were written again to the search result database table.

### Diagnosis
- Search task `7` created candidate group `2` (`意大利泳池机 search #7`).
- Correct distinct candidate count is 92 domains.
- 11 of those 92 domains already had historical `crawl_results`.
- Those 11 domains also had prior search evidence from older CSV imports or previous search sources.
- The `domains` table is upserted by normalized domain, so the domain entity itself was not duplicated.
- The `search_results` table does record a new row for the new task source `task:search:7` when the same domain appears in this new search task.
- For the 11 historically crawled domains, each had one new `task:search:7` search result row.

### Clarification
- The candidate group count should be interpreted as:
  - 92 candidates total.
  - 11 historically crawled.
  - 81 not yet crawled.
- A previous diagnostic query overcounted candidate items because joining `crawl_results` multiplied rows for domains with multiple historical crawl records. The corrected query uses `count(distinct ...)`.

## 2026-06-30 - AI Project Handoff Document

### User Context
- The user wanted to transfer the current project to another AI and asked for important changes plus the whole project situation to be recorded.

### Work Summary
- Created a full handoff document for the next AI:
  - current worktree path
  - project goal
  - architecture
  - database connection and service commands
  - current database counts
  - keyword groups
  - candidate groups
  - recent search/crawl task status
  - important code changes
  - known issues
  - recommended next steps
  - testing commands
- Added a root-level entry document that points to the active worktree handoff file.

### Files Touched
- `/Users/zhize/The Eyes of God/.worktrees/database-foundation/AI_PROJECT_HANDOFF.md`
- `/Users/zhize/The Eyes of God/AI_PROJECT_HANDOFF.md`
- `AI_WORKLOG.md`

## 2026-07-02 - Raw Database Table Viewer

### User Context
- The user asked whether `domains`, `search_results`, and `crawl_results` map directly to the frontend A/B/C company library.
- After clarifying that A/B/C are business-stage views, the user requested a separate frontend module to inspect those three physical tables directly.

### Work Summary
- Added read-only backend endpoints:
  - `GET /raw-tables/domains`
  - `GET /raw-tables/search-results`
  - `GET /raw-tables/crawl-results`
- Added full-row serializers and filters for the three tables.
- Added a Vue sidebar module named `原始数据表`.
- The module has tabs for:
  - `域名主表 domains`
  - `找官网结果 search_results`
  - `抓官网结果 crawl_results`
- Each tab renders every field with Chinese column labels, plus basic search, filters, and pagination.
- `search_results` and `crawl_results` include an extra `关联域名` display column for readability while still exposing `domain_id`.

### Files Touched
- `database/queries.py`
- `api/app.py`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_database_queries.py`
- `tests/test_api_read_endpoints.py`
- `tests/test_frontend_raw_tables_module.py`

### Verification
- `python -m unittest tests.test_database_queries tests.test_api_read_endpoints tests.test_frontend_raw_tables_module`: 23 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- FastAPI and Vue dev server were started on `127.0.0.1:8000` and `127.0.0.1:5173`.
- Runtime note: PostgreSQL was not running because Docker daemon was closed, so database-backed API calls return connection errors until the local database is started.

## 2026-07-03 - Structured Search Keywords

### User Context
- The user observed that domain discovery yield was low and that output depended too heavily on increasing simple keyword combination counts.
- The agreed next step was to implement:
  - product / role oriented keyword structure
  - template-based search query generation

### Work Summary
- Extended `keyword_groups` with:
  - `product_terms`
  - `role_terms`
  - `search_templates`
- Preserved backward compatibility:
  - existing `keyword_terms × country_terms` keyword groups still generate exactly as before.
  - new structured groups can generate `product × role × country × template` search queries.
- Added keyword generation deduplication so templates that do not include `{country}` do not create duplicate queries across country terms.
- Added default structured templates:
  - `{product} {role} {country}`
  - `{product} {role} in {country}`
- Updated the Vue keyword configuration center to edit product terms, role terms, and templates.
- Added Alembic migration `20260703_0006_structured_keyword_groups.py`.

### Files Touched
- `database/models.py`
- `database/keyword_groups.py`
- `api/schemas.py`
- `frontend/src/types.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `alembic/versions/20260703_0006_structured_keyword_groups.py`
- `tests/test_keyword_groups.py`
- `tests/test_database_models.py`
- `tests/test_frontend_structured_keywords.py`

### Verification
- `python -m unittest tests.test_keyword_groups tests.test_database_models tests.test_frontend_structured_keywords`: 12 tests passed.
- `python -m unittest tests.test_task_handlers tests.test_api_read_endpoints tests.test_keyword_groups tests.test_database_models tests.test_frontend_structured_keywords`: 42 tests passed.
- `python -m unittest discover -s tests`: 145 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

### Runtime Note
- Existing PostgreSQL databases must run `alembic upgrade head` before saving structured keyword fields from the frontend.

## 2026-07-03 - Profile JSON Payload Persistence

### User Context
- The user wanted all crawl-generated JSON profile files stored in the database while still being able to resolve grouped JSON sets through candidate-group/domain indexes.
- The user also requested existing profile JSON files to be transferred into the database.

### Work Summary
- Extended `profile_packages` into the JSON storage table by adding:
  - `payload_json`
  - `content_hash`
  - `source_mtime`
  - `candidate_group_id`
  - `crawl_task_run_id`
  - `crawl_result_id`
- Updated profile JSON import so every valid JSON package writes the full JSON payload and SHA-256 content hash.
- Updated crawl-stage persistence so future control-console crawl tasks attach `candidate_group_id` and `crawl_task_run_id` when the crawl came from a candidate group.
- Extended profile package serialization with `payload_stored`, hash, source mtime, and group/task IDs.
- Added Alembic migration `20260703_0007_profile_json_payloads.py`.
- Imported existing profile JSON files from:
  - `profile_inputs`
  - `profile_inputs/france`
  - `profile_inputs/uk`

### Import Result
- Existing crawl JSON files scanned/imported: 1109
  - `profile_inputs`: 481
  - `profile_inputs/france`: 194
  - `profile_inputs/uk`: 434
- Database state after import:
  - `profile_packages` total rows: 2336
  - rows with `payload_json` stored: 1109
  - rows with `content_hash` stored: 1109

### Files Touched
- `database/models.py`
- `database/importers.py`
- `database/stage_persistence.py`
- `database/queries.py`
- `tasks/handlers.py`
- `frontend/src/types.ts`
- `alembic/versions/20260703_0007_profile_json_payloads.py`
- `tests/test_database_importers.py`
- `tests/test_database_models.py`

### Verification
- `python -m unittest tests.test_database_importers tests.test_database_models tests.test_database_queries tests.test_api_read_endpoints tests.test_task_handlers`: 47 tests passed.
- `python -m unittest discover -s tests`: 147 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `alembic upgrade head` ran successfully through revision `20260703_0007`.
- `GET /domains/123pools.co.uk` returned a profile package with `payload_stored: true` and a populated `content_hash`.

## 2026-07-03 - Profile Packages Database-First Cleanup

### User Context
- The user decided file paths should not be part of the profile JSON business model.
- Future crawl-generated profile JSON should be stored directly in PostgreSQL instead of relying on `profile_inputs` files.
- Existing missing/empty `payload_json` rows needed to be recovered from local JSON files.

### Work Summary
- Removed `path`, `source_dir`, and `source_mtime` from `profile_packages`.
- Replaced path-based uniqueness with a partial unique index on non-empty `content_hash`.
- Changed profile JSON import to dedupe by canonical JSON content hash, so the same JSON content is not duplicated when loaded from different directories or absolute/relative paths.
- Added direct crawl payload persistence:
  - `run_crawl()` now emits an internal `_profile_package` payload for successful crawls.
  - CSV output still excludes the internal JSON field.
  - `import_crawl_rows()` writes `_profile_package` directly to `profile_packages` and links it to `crawl_result_id`.
- Changed CLI/control-console defaults so `profile_input_dir` is empty by default; local JSON file export is now legacy/optional.
- Updated API serialization and Vue detail display to show profile package IDs/hash instead of paths.
- Added Alembic migration `20260703_0008_profile_packages_database_first.py`.

### Data Migration Result
- Ran `alembic upgrade head` successfully through `20260703_0008`.
- Migration backfilled empty payloads from legacy paths, recomputed canonical content hashes, deleted unrecoverable empty rows, deduped identical JSON content, and dropped path columns.
- Scanned existing profile JSON directories under both the worktree and project root.
- Final `profile_packages` state:
  - total rows: 1211
  - empty payload rows: 0
  - distinct non-empty content hashes: 1211

### Files Touched
- `run_crawl.py`
- `database/models.py`
- `database/importers.py`
- `database/stage_persistence.py`
- `database/queries.py`
- `tasks/handlers.py`
- `frontend/src/App.vue`
- `frontend/src/types.ts`
- `alembic/versions/20260703_0008_profile_packages_database_first.py`
- `tests/test_database_importers.py`
- `tests/test_database_models.py`
- `tests/test_run_crawl.py`
- `tests/test_database_queries.py`
- `tests/test_api_read_endpoints.py`

### Verification
- `python -m unittest discover -s tests`: 149 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `GET /company-library/stats`: HTTP 200 after FastAPI restart.
- `GET /domains/123pools.co.uk`: returned `payload_stored: true`, `has_path: false`.

### Runtime Note
- FastAPI restarted on `http://127.0.0.1:8000`.
- Vue control console restarted on `http://127.0.0.1:5173/`.

## 2026-07-04 - DeepSeek AI Profile Task Prototype

### User Context
- The user wants a first API-connected AI inference attempt.
- The selected provider is DeepSeek API.
- AI inference should consume selected `profile_packages` rows and write structured lead-profile analysis back into the database.

### Work Summary
- Added a DeepSeek-compatible AI client using the OpenAI-style chat completion endpoint.
- Added `ai_profile_results` as the first customer profile inference result table.
- Added the `ai_profile` task flow:
  - accepts selected `profile_package_ids`;
  - creates a `task_runs` row and per-package `task_items`;
  - sends each profile JSON package to DeepSeek one by one;
  - stores normalized structured analysis in `ai_profile_results`.
- Added FastAPI endpoint `POST /tasks/ai-profile`.
- Registered the task handler for the existing task runner/Celery-compatible handler map.
- Added an `AI画像` control page in the Vue console for running the first DeepSeek test from the frontend.

### DeepSeek Runtime Configuration
- Required environment variable: `DEEPSEEK_API_KEY`.
- Optional environment variables:
  - `DEEPSEEK_MODEL`, default `deepseek-v4-flash`;
  - `DEEPSEEK_BASE_URL`, default `https://api.deepseek.com`.
- Current local backend service was restarted without `DEEPSEEK_API_KEY`, so real inference calls will fail until the key is configured and the backend is restarted.

### Files Touched
- `ai/deepseek_client.py`
- `database/ai_profiles.py`
- `database/models.py`
- `tasks/handlers.py`
- `tasks/celery_tasks.py`
- `api/app.py`
- `api/schemas.py`
- `frontend/src/App.vue`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `alembic/versions/20260704_0009_ai_profile_results.py`
- `tests/test_deepseek_client.py`
- `tests/test_database_models.py`
- `tests/test_task_handlers.py`
- `tests/test_api_app.py`
- `tests/test_frontend_ai_profile_task.py`

### Verification
- `alembic upgrade head` ran successfully through revision `20260704_0009`.
- `python -m unittest tests.test_deepseek_client tests.test_database_models tests.test_task_handlers tests.test_api_app`: 33 tests passed.
- `python -m unittest tests.test_frontend_ai_profile_task`: 1 test passed.
- `python -m unittest discover -s tests`: 154 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

### Runtime Note
- FastAPI is listening on `http://127.0.0.1:8000`.
- Vue control console is listening on `http://127.0.0.1:5173/`.
- To run a real DeepSeek test, export `DEEPSEEK_API_KEY` before starting the backend.

## 2026-07-04 - Heat Pump Lead Business Knowledge Prompt

### User Context
- The user pointed out that DeepSeek must know the company's product and target lead type before it can score customer profiles.
- The named skill `analyze-heat-pump-lead-profile` currently exists as a placeholder template, so the usable business rules were added directly to the project AI prompt.

### Work Summary
- Upgraded the default AI prompt version from `heat_pump_lead_v1` to `heat_pump_lead_v2`.
- Added explicit business context to the DeepSeek system prompt:
  - the company is a heat pump manufacturer;
  - the core product is the heat pump itself;
  - product scope includes pool heat pumps, heating heat pumps, air-source heat pumps, HVAC heating equipment, and hot-water heat pumps;
  - priority targets are importers, distributors, wholesalers, dealers, resellers, installers, engineering contractors, HVAC contractors, pool system integrators, pool equipment companies, and B2B channel sellers;
  - low-priority/risky targets include directories, pure content sites, unrelated industries, weak-evidence sites, end consumers, and direct competitors without clear OEM/import/distribution potential.
- Added a fixed scoring rubric:
  - `product_relevance`: 0-30
  - `customer_type_fit`: 0-20
  - `distribution_potential`: 0-15
  - `market_country_fit`: 0-10
  - `contactability`: 0-10
  - `evidence_quality`: 0-10
  - `risk_penalty`: 0 to -15
- Added priority thresholds:
  - A: 80-100
  - B: 65-79
  - C: 45-64
  - D: 0-44
- Synchronized defaults in backend task handling, FastAPI schema, and Vue console.

### Files Touched
- `ai/deepseek_client.py`
- `tasks/handlers.py`
- `api/schemas.py`
- `frontend/src/App.vue`
- `tests/test_deepseek_client.py`
- `tests/test_api_app.py`
- `tests/test_frontend_ai_profile_task.py`

### Verification
- Added failing tests first for missing prompt business knowledge and prompt version.
- `python -m unittest tests.test_deepseek_client`: 2 tests passed after implementation.
- `python -m unittest tests.test_api_app tests.test_task_handlers tests.test_frontend_ai_profile_task`: 28 tests passed.
- `python -m unittest discover -s tests`: 156 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

### Runtime Note
- FastAPI restarted on `http://127.0.0.1:8000` with the new `heat_pump_lead_v2` prompt code.
- Vue control console remains available on `http://127.0.0.1:5173/`.
- `DEEPSEEK_API_KEY` still needs to be configured before a real API inference task can succeed.

## 2026-07-04 - Backend Dotenv Configuration

### User Context
- The user wanted `.env` auto-loading so DeepSeek API keys and database settings do not need to be exported manually every time.

### Work Summary
- Added `config.env.load_project_env()` to load project-root `.env` with `override=False`.
- Wired `.env` loading into:
  - FastAPI backend startup;
  - Celery app startup;
  - Alembic migrations;
  - reusable task CLI;
  - legacy data import scripts.
- Added `.env.example` as the safe template.
- Updated `.gitignore` so real `.env` files are not committed.
- Added `python-dotenv>=1.0` to `requirements.txt`.

### Files Touched
- `config/env.py`
- `api/app.py`
- `tasks/celery_app.py`
- `alembic/env.py`
- `scripts/run_task.py`
- `scripts/import_existing_data.py`
- `scripts/import_keyword_groups.py`
- `.env.example`
- `.gitignore`
- `requirements.txt`
- `tests/test_env_config.py`

### Verification
- `python -m unittest tests.test_env_config tests.test_deepseek_client tests.test_api_app tests.test_task_handlers`: 31 tests passed.
- `python -m compileall config api tasks scripts alembic ai`: compile check passed.
- `python -m unittest discover -s tests`: 158 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- FastAPI restarted on `http://127.0.0.1:8000`; `/health` returned `{"status":"ok"}`.

## 2026-07-04 - DeepSeek Model Selection Fix

### User Context
- The user configured `.env` with `DEEPSEEK_MODEL=deepseek-v4-pro`.
- The task result metadata and the actual DeepSeek API client must use the same model name.

### Work Summary
- Fixed `run_ai_profile_task()` so the requested `model_name` is passed into `DeepSeekClient`.
- If no task-level model is supplied, the backend now falls back to `.env` `DEEPSEEK_MODEL`, then to the code default.
- Added regression coverage to ensure `deepseek-v4-pro` is actually used by the DeepSeek client, not only recorded in task metadata.

### Verification
- `python -m unittest tests.test_task_handlers.TaskHandlerTests.test_run_ai_profile_task_initializes_deepseek_client_with_requested_model`: passed.
- `python -m unittest tests.test_task_handlers tests.test_deepseek_client tests.test_env_config`: 22 tests passed.
- `python -m unittest discover -s tests`: 160 tests passed.
- FastAPI restarted from plain `uvicorn api.app:app --host 127.0.0.1 --port 8000`.
- `.env` check showed `has_deepseek_key=True`, `DEEPSEEK_MODEL=deepseek-v4-pro`, and `DATABASE_URL` present.
- `/health` returned `{"status":"ok"}` and `/database/stats` returned live PostgreSQL counts.

## 2026-07-04 - AI Profile Results Table Viewer

### User Context
- The user asked where AI inference output can be viewed from the frontend.

### Work Summary
- Added a backend raw-table endpoint for `ai_profile_results`:
  - `GET /raw-tables/ai-profile-results`
  - supports pagination plus filters for search text, status, priority, model name, and prompt version.
- Added `AI画像结果 ai_profile_results` as a fourth tab in the frontend `原始数据表` module.
- Added Chinese table columns for AI result fields including profile package ID, model, prompt version, profile summary, customer priority, total score, score breakdown, evidence, risks, and recommended action.
- Improved raw table cell rendering so JSON fields display as JSON text instead of `[object Object]`.

### Verification
- `python -m unittest tests.test_database_queries tests.test_api_read_endpoints tests.test_frontend_raw_tables_module`: 25 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 162 tests passed.
- FastAPI restarted on `http://127.0.0.1:8000`.
- `GET /raw-tables/ai-profile-results?limit=5&offset=0` returned HTTP 200 with `total: 0`, confirming the endpoint works and the current table is empty before any real AI run.

## 2026-07-04 - Claude Code AI Profile Pipeline

### User Context
- The user decided the direct DeepSeek API approach was too cumbersome.
- The requested direction is to remove the real `.env` file and stop calling a model API directly from backend code.
- AI inference should now use the local Claude Code CLI.

### Work Summary
- Deleted the real project `.env` file.
- Removed the DeepSeek client and DeepSeek-specific tests.
- Added `ai/lead_profile_prompt.py` for the heat-pump business knowledge, scoring rubric, prompt version, and structured JSON schema.
- Added `ai/claude_code_client.py`, which calls local `claude --print` with:
  - `--output-format json`
  - `--system-prompt`
  - `--json-schema`
  - no session persistence
- Updated the AI task defaults to:
  - `model_provider`: `claude_code`
  - `model_name`: `sonnet`
  - `prompt_version`: `heat_pump_lead_v2`
- Updated the Vue AI profile form so the only model service option is `claude_code`.
- Kept `ai_profile_results` as the database result table; it is model-provider-neutral and can store Claude Code outputs.
- Changed the default database URL to local PostgreSQL, so the backend can start without relying on `.env`.
- Fixed a real write failure found during endpoint verification:
  - `ai_profile_results.product_fit` was too short as `varchar(50)`;
  - upgraded it to `text` with Alembic revision `20260704_0010`;
  - added rollback handling when one AI item fails during database flush.
- Cleaned two old non-terminal AI task records created during the transition:
  - task `9`: old DeepSeek attempt, now `cancelled`;
  - task `10`: failed pre-migration Claude Code verification, now `cancelled`.

### Files Touched
- `ai/lead_profile_prompt.py`
- `ai/claude_code_client.py`
- `tasks/handlers.py`
- `api/schemas.py`
- `database/models.py`
- `database/session.py`
- `alembic.ini`
- `alembic/versions/20260704_0010_ai_profile_product_fit_text.py`
- `.env.example`
- `requirements.txt`
- `frontend/src/App.vue`
- `tests/test_claude_code_client.py`
- `tests/test_task_handlers.py`
- `tests/test_api_app.py`
- `tests/test_database_models.py`
- `tests/test_database_queries.py`
- `tests/test_api_read_endpoints.py`
- `tests/test_env_config.py`
- `tests/test_frontend_ai_profile_task.py`

### Verification
- `claude --print` smoke test succeeded locally with structured JSON output.
- `alembic upgrade head` upgraded PostgreSQL from `20260704_0009` to `20260704_0010`.
- FastAPI restarted on `http://127.0.0.1:8000`.
- Real endpoint test succeeded:
  - `POST /tasks/ai-profile`
  - profile package ID: `769`
  - model provider: `claude_code`
  - model name: `sonnet`
  - prompt version: `heat_pump_lead_v2`
  - result: task `11`, `success`, `results_created: 1`.
- `GET /raw-tables/ai-profile-results?limit=5&offset=0&model_name=sonnet` returned the new row for `ekolis.de` from `ai_profile_results`.
- `python -m unittest tests.test_database_models tests.test_task_handlers tests.test_claude_code_client`: 28 tests passed.
- `python -m unittest discover -s tests`: 164 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

### Runtime Note
- No DeepSeek API key is needed for the current AI profile path.
- The backend now depends on the local `claude` CLI being installed and authenticated in the same user environment that starts FastAPI.
- The frontend AI form should use `sonnet` as the model name unless another Claude Code model alias is intentionally selected.

## 2026-07-04 - API Key AI Profile Pipeline And Reader Module

### User Context
- The user rejected the Claude Code subprocess approach after testing because task execution was opaque and harder to control.
- The requested direction is to remove Claude Code code entirely and return to a model API Key flow.
- The API Key should be entered from the frontend for each AI run, but should not be saved.
- The user also requested Chinese AI output and a dedicated AI profile reader instead of showing AI results inside the raw database table module.

### Work Summary
- Removed the Claude Code client and tests:
  - deleted `ai/claude_code_client.py`;
  - deleted `tests/test_claude_code_client.py`.
- Added `ai/model_api_client.py`, a generic OpenAI-compatible chat completions client using Python stdlib HTTP calls.
- Set AI task defaults to:
  - `model_provider`: `deepseek`;
  - `api_base_url`: `https://api.deepseek.com`;
  - `model_name`: `deepseek-chat`;
  - `temperature`: `0.2`;
  - `timeout_seconds`: `180`.
- Updated the AI prompt version internally to `heat_pump_lead_cn_v1`.
- Updated the heat-pump lead prompt so all natural-language fields must be written in Chinese while JSON field names remain stable in English.
- Removed `prompt_version` from the frontend task form and FastAPI AI task request schema.
- Added request-scoped API Key handling:
  - frontend sends `api_key` only with the task request;
  - backend uses it only to call the model API;
  - task params store only `api_key_configured: true/false`;
  - API Key is not written into task params, AI result rows, or raw response JSON.
- Moved AI result viewing out of `原始数据表`.
- Added a new sidebar module `AI画像分析`:
  - one AI result per page;
  - domain, profile package ID, task ID, model, priority, score, and time at the top;
  - separate sections for summary, business type, market role, product fit, score breakdown, evidence, risk flags, and recommended action;
  - filters for search text, priority, model, and status;
  - previous/next controls;
  - collapsible raw JSON.
- Kept `ai_profile_results.prompt_version` in the database as an internal dedupe/audit field.

### Files Touched
- `ai/model_api_client.py`
- `ai/lead_profile_prompt.py`
- `tasks/handlers.py`
- `api/schemas.py`
- `frontend/src/App.vue`
- `frontend/src/types.ts`
- `frontend/src/style.css`
- `tests/test_model_api_client.py`
- `tests/test_task_handlers.py`
- `tests/test_api_app.py`
- `tests/test_database_queries.py`
- `tests/test_api_read_endpoints.py`
- `tests/test_frontend_ai_profile_task.py`
- `tests/test_frontend_raw_tables_module.py`
- `docs/superpowers/plans/2026-07-04-api-key-ai-profile.md`

### Verification
- `python -m unittest tests.test_model_api_client tests.test_task_handlers tests.test_api_app`: 34 tests passed.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 5 tests passed.
- `python -m unittest discover -s tests`: 166 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- FastAPI restarted on `http://127.0.0.1:8000` with the API Key AI path loaded.

### Runtime Note
- To run AI analysis now, use the frontend `AI画像` task form and fill:
  - profile package IDs;
  - model service `deepseek`;
  - API Base URL `https://api.deepseek.com`;
  - API Key;
  - model name such as `deepseek-chat`.
- After the task finishes, view the output in the new `AI画像分析` sidebar module.

## 2026-07-04 - Frontend Task Progress Restore After Refresh

### User Context
- The user refreshed the browser while a task was running.
- After refresh, the console returned to the initial state and no longer showed the running task.

### Root Cause
- The backend task state was already stored in the database.
- The frontend `onMounted()` flow only reloaded lists and summary data.
- It did not restore `activeTaskProgress` from the latest running task record, so the realtime progress panel stayed hidden after refresh.

### Work Summary
- Added `initializeDashboard()` to run startup loading and then restore active task progress.
- Added `restoreActiveTaskProgressAfterRefresh()`:
  - queries the latest `running` task from `/task-runs`;
  - restores it only if it is `search`, `crawl`, or `ai_profile`;
  - loads full task detail;
  - switches the UI back to `任务控制台`;
  - restarts task progress polling.
- Added `progressTaskTypeFromTaskRun()` to safely map database task types back to frontend progress task types.

### Files Touched
- `frontend/src/App.vue`
- `tests/test_frontend_task_progress_panel.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_task_progress_panel`: 5 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 167 tests passed.

## 2026-07-04 - Console Visual Redesign

### User Context
- The user invoked `$taste-skill:gpt-taste` and said the frontend looked too rough.
- The approved direction was to keep this as an operational lead-generation console, not a marketing landing page.

### Work Summary
- Added a short design spec for the visual redesign.
- Reworked the Vue console visual layer:
  - deep command-rail sidebar;
  - lighter data workspace;
  - stronger module header;
  - denser bento-style metric cards;
  - refined task panels, buttons, forms, tables, progress panel, and AI profile reader;
  - switched the primary font stack away from Inter toward Geist / Cabinet Grotesk style fonts.
- Kept backend APIs, database schema, task logic, crawling logic, and AI inference logic unchanged.

### Files Touched
- `docs/superpowers/specs/2026-07-04-console-visual-redesign-design.md`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_visual_redesign.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_visual_redesign`: 4 tests passed.
- `python -m unittest tests.test_frontend_visual_redesign tests.test_frontend_task_progress_panel tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module tests.test_frontend_crawl_form_state tests.test_frontend_structured_keywords`: 20 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 171 tests passed.
- Browser screenshot smoke test could not complete in this environment because the Playwright browser cache was missing and local Chrome headless exited immediately.

## 2026-07-04 - Impeccable Product And Design Context

### User Context
- The user invoked `$impeccable`.
- The project had no `PRODUCT.md`, so the impeccable setup flow required project-level product context before other design commands.
- The user confirmed the surface should be treated as a task-oriented backend console with technical feeling, for the founder/operator and company senior leadership.

### Work Summary
- Added `PRODUCT.md` with:
  - register `product`;
  - users, product purpose, brand personality, anti-references, design principles, and accessibility expectations.
- Added `.impeccable/live/config.json` for the Vite/Vue app entry.
- Ran the equivalent of `$impeccable document frontend`:
  - added `DESIGN.md` with frontmatter design tokens and the six required DESIGN.md sections;
  - added `.impeccable/design.json` sidecar for color metadata, typography metadata, shadows, motion, breakpoints, and representative components.

### Files Touched
- `PRODUCT.md`
- `DESIGN.md`
- `.impeccable/live/config.json`
- `.impeccable/design.json`
- `AI_WORKLOG.md`

### Verification
- `DESIGN.md` structure check passed.
- `python -m json.tool .impeccable/design.json`: JSON is valid.
- `python -m unittest tests.test_frontend_visual_redesign`: 4 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-07-04 - Task Console Distill

### User Context
- The user approved the `$impeccable` critique direction and chose:
  - task form noise reduction;
  - experience-first defaults;
  - raw data tables as audit/debug entry points.

### Work Summary
- Repositioned the raw database table module from a daily workflow module to `审计排错`.
- Reduced the daily search task form to keyword group, engine, page count, and computed keyword count.
- Moved search backend, keyword delay, engine delay, and retry-only controls into collapsed `搜索高级设置`.
- Added crawl presets (`标准`, `保守`, `深挖`) and an `applyCrawlPreset()` helper.
- Reduced the daily crawl task form to candidate source, mode, candidate quantity, depth, and page count.
- Moved crawl concurrency, delay, retry backoff, proxy, and browser-only/request-only controls into collapsed `抓取高级设置`.
- Added a candidate source summary to make group-based crawling clearer.
- Removed the progress bar `width` transition that triggered the design detector layout-transition warning.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_task_console_distill.py`
- `tests/test_frontend_raw_tables_module.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_task_console_distill tests.test_frontend_crawl_form_state tests.test_frontend_raw_tables_module tests.test_frontend_visual_redesign`: 15 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: 37 remaining findings, all `advisory:design-system-color`; no layout-transition warning remains.

## 2026-07-04 - Console Layout Compaction

### User Context
- The user wanted less explanatory text and a more task-focused main surface.
- The top current-module area plus the four global metrics should occupy only a small top region.
- The `审计排错` module should not show database table names.
- The left navigation should support a hidden/collapsed state where only icons remain visible.

### Work Summary
- Added `sidebarCollapsed` UI state and a left-navigation collapse/expand button.
- Collapsed sidebar mode now uses a 76px command rail and shows only module icons with accessible labels/titles.
- Removed visible navigation descriptions and module header explanatory copy across the main modules.
- Replaced `审计排错` tab labels from database table names to business-facing labels:
  - `域名主档`
  - `搜索证据`
  - `抓取结果`
- Reworked the top area into a compact `module-overview` strip:
  - current module and backend sync controls on the left;
  - `客户域名`, `联系方式`, `画像素材包`, `国家信号` as compact status blocks on the right.
- Reduced metric card height, type scale, padding, and decorative treatment so the module's main content becomes the primary viewport area.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_visual_redesign.py`
- `tests/test_frontend_task_console_distill.py`
- `tests/test_frontend_raw_tables_module.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_visual_redesign tests.test_frontend_task_console_distill tests.test_frontend_raw_tables_module tests.test_frontend_crawl_form_state`: 15 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 175 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: 38 remaining findings, all `advisory:design-system-color`; no layout-transition warning.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned the Vue console HTML.

## 2026-07-06 - Profile Source Groups For AI Profile Tasks

### User Context
- The user introduced a new concept: "画像源数据组".
- One crawl task should produce a group of JSON/profile packages.
- AI profiling should support selecting that group instead of manually typing individual profile package IDs.
- Manual profile package ID input should remain available.
- The user decided the mutual exclusion can be enforced in the frontend only: selecting a group disables manual ID input, and manual ID mode disables the group selector.

### Work Summary
- Added database query support to list and read profile source groups, using `crawl_task_run_id` as the source group ID.
- Added FastAPI read endpoints:
  - `GET /profile-source-groups`
  - `GET /profile-source-groups/{crawl_task_run_id}`
- Extended AI profile task parameters to accept either `profile_source_group_id` or `profile_package_ids`.
- Updated AI profile task execution so group mode resolves all profile packages whose `ProfilePackage.crawl_task_run_id` matches the selected source group.
- Added frontend API/types for profile source groups.
- Updated the AI profile task form:
  - default input mode is group mode;
  - group selector shows crawl-task groups and pending profile counts;
  - manual profile package IDs are still supported;
  - group and manual ID inputs are mutually disabled based on selected mode.
- Added tests for backend group querying, API endpoints, task submission, task execution, and frontend controls.

### Files Touched
- `database/queries.py`
- `api/app.py`
- `api/schemas.py`
- `tasks/handlers.py`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/App.vue`
- `tests/test_database_queries.py`
- `tests/test_api_read_endpoints.py`
- `tests/test_api_app.py`
- `tests/test_task_handlers.py`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_ai_profile_task`: 1 test passed after first confirming the test failed before implementation.
- `python -m unittest tests.test_database_queries tests.test_api_read_endpoints tests.test_api_app tests.test_task_handlers tests.test_frontend_ai_profile_task`: 59 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 182 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: returned existing `design-system-color` advisory findings only; no blocking issue introduced by this change.

### Next Steps
- FastAPI has been restarted and `GET /profile-source-groups` is available.
- Current local database has 1211 existing profile packages, but none has `crawl_task_run_id`, `candidate_group_id`, or `crawl_result_id`, so existing historical packages cannot be reliably reconstructed into crawl-task source groups.
- New crawl tasks should create groupable profile packages. Historical packages can still be profiled by manual profile package IDs, or a later explicit backfill tool can create a manual "historical default group" if the user wants that behavior.

## 2026-07-06 - AI Profile Input Mutual Locking

### User Context
- The user rejected the extra "画像输入方式" mode selector.
- Desired behavior: keep only the profile source group select and the profile package ID textarea.
- If a profile source group is selected, the profile package ID textarea should be greyed out and disabled.
- If the profile package ID textarea contains data, the profile source group select should be greyed out and disabled.

### Work Summary
- Removed the `aiProfileTask.input_mode` state and the visible "画像输入方式" dropdown.
- Added frontend computed state:
  - `hasAIProfileSourceGroup`
  - `hasAIProfilePackageIdsText`
  - `isAIProfileSourceGroupDisabled`
  - `isAIProfilePackageIdsDisabled`
- Updated AI profile task submission:
  - selected source group sends `profile_source_group_id`;
  - otherwise typed IDs send `profile_package_ids`;
  - if both are empty, frontend raises a validation error.
- Stopped auto-selecting the first source group when loading groups, so manual profile package ID mode remains reachable.
- Updated the frontend regression test to forbid the removed mode selector and verify the mutual locking bindings.

### Files Touched
- `frontend/src/App.vue`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_ai_profile_task`: first failed against the old UI, then passed after implementation.
- `python -m unittest tests.test_api_app tests.test_task_handlers tests.test_frontend_ai_profile_task`: 34 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 182 tests passed.

## 2026-07-06 - Backfill Italy And Australia Pool Profile Source Groups

### User Context
- The user asked to find the JSON/profile packages crawled from the candidate groups:
  - `意大利泳池机`
  - `澳大利亚泳池机`
- The user wanted these JSON packages grouped so AI profiling can use profile source groups.

### Work Summary
- Located the candidate groups:
  - Candidate group `#2`: `意大利泳池机 search #7`, country `Italy`, 92 candidate domains.
  - Candidate group `#1`: `澳大利亚泳池机 search #2`, country `Australia`, 52 candidate domains.
- Located related crawl task runs:
  - Crawl task `#8`: candidate group `#2`, summary `success: 59`, `empty: 22`.
  - Crawl task `#4`: candidate group `#1`, summary `success: 27`, `empty: 5`.
  - Crawl task `#3`: candidate group `#1`, summary `success: 16`, `empty: 4`; those JSON files were imported together in the later task `#4` profile import window.
- Avoided grouping by domain alone because Italy/Australia candidate domains overlapped with older historical profile packages.
- Grouped only profile packages matching both candidate group domains and crawl-task time windows:
  - Australia: profile package IDs `1755-1797`, 43 packages, assigned `candidate_group_id=1`, `crawl_task_run_id=4`.
  - Italy: profile package IDs `1798-1856`, 59 packages, assigned `candidate_group_id=2`, `crawl_task_run_id=8`.
- Renamed the task runs for readable frontend display:
  - `澳大利亚泳池机 crawl #4`
  - `意大利泳池机 crawl #8`

### Verification
- Queried `list_profile_source_groups(..., q="泳池机")`; it returned exactly 2 groups.
- Verified `GET /profile-source-groups?limit=10&offset=0&q=泳池机` returned:
  - `意大利泳池机 crawl #8`: 59 profile packages, 59 pending AI profiles.
  - `澳大利亚泳池机 crawl #4`: 43 profile packages, 43 pending AI profiles.

## 2026-07-06 - Auto Promote A-Level AI Profiles To Stage C

### User Context
- The user asked for AI profile outputs scored as A-level customers to automatically enter the priority customer library.

### Work Summary
- Added AI-result-to-Stage-C synchronization after each successful AI profile analysis.
- When `customer_priority` normalizes to `A`, the system now writes or updates:
  - `qualified_leads`
  - `company_profiles`
  - `lead_scores`
- Non-A AI results do not create priority customer records.
- Automatic Stage C records use an AI-specific source key based on prompt version, model provider, and model name, so manual `qualified_leads` records are not overwritten.
- Task item result JSON now includes `promoted_to_qualified_lead` for easier audit/debugging.

### Files Touched
- `database/ai_profiles.py`
- `tasks/handlers.py`
- `tests/test_task_handlers.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_task_handlers.TaskHandlerTests.test_run_ai_profile_task_analyzes_selected_profile_packages`: 1 test passed after first confirming the new test failed because no `qualified_leads` row existed.
- `python -m unittest tests.test_task_handlers`: 20 tests passed.
- `python -m unittest tests.test_task_handlers tests.test_database_queries tests.test_api_read_endpoints`: 42 tests passed.
- `python -m unittest tests.test_model_api_client tests.test_api_app`: 14 tests passed.
- `python -m unittest discover -s tests`: 177 tests passed.

## 2026-07-06 - Backfill Existing A-Level AI Profile To Stage C

### User Context
- The user asked to manually write existing A-level AI profile results into the priority customer library.

### Work Summary
- Ran a one-time database backfill against the default local PostgreSQL database.
- Scanned existing successful `ai_profile_results`.
- Found 1 existing A-level AI profile result.
- Promoted 1 unique domain into Stage C:
  - `acrepairindubai.com`
- Wrote the corresponding rows into:
  - `qualified_leads`
  - `company_profiles`
  - `lead_scores`

### Verification
- Backfill output:
  - `a_level_ai_profile_results=1`
  - `promoted_records=1`
  - `promoted_unique_domains=1`
  - `qualified_leads_total_before=0`
  - `qualified_leads_total_after=1`
- Follow-up verification output:
  - `auto_qualified_leads=1`
  - `auto_company_profiles=1`
  - `auto_lead_scores=8`
  - source: `ai_profile:heat_pump_lead_cn_v1:deepseek:deepseek-v4-pro`

## 2026-07-06 - Remove Legacy Import From Console

### User Context
- The user asked to remove the confusing `入库` module because it is unrelated to the normal database-first workflow.
- The user also asked what `企业库`里的`优先客户库 C` is for.

### Work Summary
- Removed the `入库` task tab from the frontend task console.
- Removed the old file-import form and its default CSV/profile directory fields from the daily task surface.
- Removed unused frontend import task plumbing:
  - `startImportTask`
  - `ImportTaskRequest`
  - `UploadCloud`
  - `importTask`
  - `import-form` styling
- Changed the task console heading from `搜索、抓取、入库` to `搜索、抓取、画像`.
- Kept backend import scripts/endpoints untouched as maintenance-only tools for historical CSV/JSON migration.
- Kept old `import_existing_data` task-run display readable as `旧文件导入`.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/style.css`
- `tests/test_frontend_task_console_distill.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_task_console_distill tests.test_frontend_visual_redesign`: 10 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 177 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: returned existing `design-system-color` advisory findings only; no blocking issue introduced by this change.

## 2026-07-06 - Search Engine Select

### User Context
- The user asked to make the search engine configurable as options, with `duckduckgo` as the default.

### Work Summary
- Added a frontend search engine option list for the official-site discovery task:
  - DuckDuckGo
  - Bing
  - DuckDuckGo + Bing
- Changed the default search engine from `duckduckgo,bing` to `duckduckgo`.
- Replaced the free-text search engine field with a dropdown bound to the existing `searchTask.engines` request field.
- Added a frontend regression test so this control remains a select and keeps the DuckDuckGo default.

### Files Touched
- `frontend/src/App.vue`
- `tests/test_frontend_task_console_distill.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_task_console_distill tests.test_frontend_visual_redesign`: 9 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 176 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: returned existing `design-system-color` advisory findings only; no blocking issue introduced by this change.

## 2026-07-06 - Default AI Model Name

### User Context
- The user requested the default AI model name to be `deepseek-v4-pro`.

### Work Summary
- Changed backend model API default from `deepseek-chat` to `deepseek-v4-pro`.
- Changed the frontend AI profile task form default model name to `deepseek-v4-pro`.
- Updated API schema and frontend/model-client tests so the default is locked at `deepseek-v4-pro`.
- Preserved explicit model override behavior; tasks can still use another model if the user types one in the frontend form.

### Files Touched
- `ai/model_api_client.py`
- `frontend/src/App.vue`
- `tests/test_model_api_client.py`
- `tests/test_api_app.py`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_model_api_client tests.test_api_app tests.test_task_handlers tests.test_frontend_ai_profile_task`: 35 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 175 tests passed.
- FastAPI restarted on `http://127.0.0.1:8000` so the new backend default is active.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned the Vue console HTML.

## 2026-07-04 - Top Overview Micro Compaction

### User Context
- The user said the top overview area still occupied too much space and asked to continue shrinking it.

### Work Summary
- Removed the visible `当前模块` label from the top overview.
- Reduced the top app padding from `30px` to `22px 24px 24px`.
- Reduced the topbar height from `78px` to `52px`.
- Reduced topbar padding, h1 size, backend pill padding, and topbar shadow weight.
- Converted the four global metric blocks into one-line compact status items:
  - 52px height;
  - 16px icons;
  - smaller value text;
  - tighter gaps and lower shadow.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_visual_redesign.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_visual_redesign tests.test_frontend_task_console_distill tests.test_frontend_raw_tables_module`: 12 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 175 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: 38 remaining findings, all `advisory:design-system-color`; no layout-transition warning.

## 2026-07-04 - Fixed Top Overview Strip

### User Context
- The user said the top area still changed size when switching modules.
- The user also said the backend URL is developer-facing information and should not appear in the frontend.

### Work Summary
- Removed the visible backend URL from the top overview.
- Kept only the `同步` action in the top-right control area.
- Fixed the desktop top overview strip at `44px` height.
- Fixed topbar and metric item heights at `44px` so module switching does not move the main content start position.
- Forced the module name to a single-line ellipsis so long names do not wrap and resize the top area.
- Reduced app top padding to lift module content further upward.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_visual_redesign.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_visual_redesign tests.test_frontend_task_console_distill tests.test_frontend_raw_tables_module`: 12 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 175 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: 38 remaining findings, all `advisory:design-system-color`; no layout-transition warning.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned the Vue console HTML.

## 2026-07-06 - AI Profile Company Name And Directory Review

### User Context
- The user asked that future AI inference should fill the inferred company name.
- Existing inferred rows should use the current title-derived value as a temporary company name.
- The AI profile review module should become a left directory plus right detail layout, with the directory showing company name, region, score, and rating level.

### Work Summary
- Added `company_name` to `ai_profile_results`.
- Added Alembic migration `20260706_0011_ai_profile_company_name.py`.
- Backfilled existing AI profile rows from `result_json.company_name`, profile package `company.company_name`, domain display name, or domain.
- Updated the AI prompt/schema so future model responses must include `company_name`, with guidance not to use generic page titles like `Home`, `Products`, or `Contact`.
- Updated AI result persistence to store model-provided `company_name`, with fallback to profile package title/domain if missing.
- Updated AI profile list API to return `company_name` and a `country` summary from country signals.
- Expanded AI profile search to include company name, domain display name, and country signal.
- Rebuilt the frontend AI profile module as:
  - left-side profile directory;
  - right-side selected profile detail;
  - basic filters for search, priority, model, and status;
  - 20 results per page instead of one result per page.

### Files Touched
- `ai/lead_profile_prompt.py`
- `database/models.py`
- `database/ai_profiles.py`
- `database/queries.py`
- `alembic/versions/20260706_0011_ai_profile_company_name.py`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `frontend/src/types.ts`
- `tests/test_database_models.py`
- `tests/test_database_queries.py`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_database_models.DatabaseModelTests.test_ai_profile_result_table_is_registered_and_created tests.test_database_queries.DatabaseQueryTests.test_list_raw_ai_profile_results_returns_full_rows_with_filters tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_review_uses_directory_layout`: 3 tests passed.
- `python -m unittest tests.test_database_models tests.test_database_queries tests.test_api_read_endpoints tests.test_task_handlers tests.test_model_api_client tests.test_frontend_ai_profile_task`: 57 tests passed.
- `python -m unittest discover -s tests`: 183 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings were `advisory:design-system-color`.
- `DATABASE_URL='postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen' alembic upgrade head`: applied migration `20260706_0011`.
- Live database check after migration:
  - `ai_profile_results` total rows: 64.
  - rows with empty `company_name`: 0.
  - rows with `result_json.company_name`: 64.
- FastAPI restarted on `http://127.0.0.1:8000`.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned the Vue console HTML.
  - `GET /raw-tables/ai-profile-results?limit=3&offset=0` returned rows with `company_name` and `country`.

## 2026-07-06 - AI Profile Directory Pagination

### User Context
- The user asked to correct the AI profile record whose title-derived company name was `Home` to `EnerPlus Italia srl`.
- The user asked to remove the previous profile-by-profile pagination behavior and use directory pagination instead.
- Directory pages should default to 100 items and allow 100, 300, or 500 as selectable page sizes at the bottom.
- The right-side profile detail should only switch when the user clicks a directory item.

### Work Summary
- Updated the live PostgreSQL AI profile row for `enerplusitalia.com`:
  - `ai_profile_results.company_name`;
  - `ai_profile_results.result_json.company_name`;
  - linked `profile_packages.payload_json.company.company_name`.
- Changed the AI profile directory default page size from 20 to 100.
- Added `100 / 300 / 500` directory page-size selector in the AI profile module footer.
- Changed AI profile pagination labels from profile-item wording to directory-page wording.
- Kept right-side profile switching driven by directory item clicks.
- Raised only the AI profile raw-list backend limit cap to 500 while leaving the default raw-table cap unchanged.

### Files Touched
- `database/queries.py`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_database_queries.py`
- `tests/test_frontend_ai_profile_task.py`
- `tests/test_frontend_raw_tables_module.py`
- `AI_WORKLOG.md`

### Verification
- Watched the new tests fail first:
  - AI profile list limit was capped at 200 instead of 500.
  - Frontend lacked directory page-size options and still used profile-item pagination wording.
- `python -m unittest tests.test_database_queries.DatabaseQueryTests.test_list_raw_ai_profile_results_allows_large_directory_pages tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_review_uses_directory_layout`: 2 tests passed.
- `python -m unittest tests.test_database_queries tests.test_api_read_endpoints tests.test_frontend_ai_profile_task`: 28 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 184 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings were `advisory:design-system-color`.
- FastAPI restarted on `http://127.0.0.1:8000`.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned the Vue console HTML.
  - `GET /raw-tables/ai-profile-results?limit=500&offset=0&q=EnerPlus` returned `company_name: "EnerPlus Italia srl"` and `limit: 500`.

## 2026-07-06 - AI Profile Directory Export

### User Context
- The user asked to make the AI profile directory as tall as the right-side profile detail area.
- The user asked for an export function that can export selected profile packages from the directory.
- Export selection must support selecting the current page, selecting all filtered results, and selecting only specific rows.

### Work Summary
- Changed the AI profile review layout so the left directory stretches to match the right profile detail panel.
- Moved directory scrolling into the directory list area instead of the whole directory panel.
- Added checkbox selection for AI profile directory rows.
- Added current-page select all / cancel select all.
- Added filtered-result select all mode.
- Added clear selection.
- Added `导出画像包` action that downloads selected AI profile rows as a JSON package.
- The export payload includes export time, count, selection mode, active filters, and the selected profile rows.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the new frontend tests fail first:
  - directory layout did not yet stretch with the profile detail area;
  - selection and export functions did not yet exist.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_review_uses_directory_layout tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_directory_supports_selection_and_export`: 2 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 185 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings were `advisory:design-system-color`.

## 2026-07-06 - AI Profile Directory Selection Correction

### User Context
- The user clarified that the directory should only be lengthened within the original profile information page structure.
- The directory should not be stretched to display every item at once.
- The user also clarified that `筛选后全选` should not be a separate button.
- The intended behavior is: after applying filters, clicking `全选` selects the current filtered result set.

### Work Summary
- Removed the separate `筛选后全选` button from the AI profile directory.
- Changed the `全选` action to select the current filtered AI profile result set.
- Kept partial export through per-row checkboxes.
- Kept export behavior for filtered-all mode by fetching all matching filtered rows before download.
- Set a fixed responsive AI profile work-area height so the left directory and right profile detail are equal height without letting the directory grow to show all rows.
- Kept scrolling inside the directory list and profile detail panel.
- Added a mobile exception so small screens use natural vertical scrolling instead of fixed dual scroll areas.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the revised tests fail first because the fixed profile work-area height and the new `全选` behavior were not present, and the old `筛选后全选` button still existed.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_review_uses_directory_layout tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_directory_supports_selection_and_export`: 2 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 185 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings were `advisory:design-system-color`.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned HTTP 200.

## 2026-07-06 - AI Profile Preview Adaptive Cards

### User Context
- The user reported that the AI profile preview modal had too much blank space.
- The likely cause was the previous fixed-size small content card design.
- The requested change is to cancel fixed small card sizing and return the profile preview content to adaptive sizing.

### Work Summary
- Removed the fixed `grid-auto-rows: minmax(180px, auto)` behavior from the AI profile section grid.
- Removed fixed minimum heights from AI profile content cards.
- Removed per-card internal scrolling for score breakdown, evidence, and risk flags.
- Kept the modal page itself scrollable, so long profile content naturally extends the preview page.
- Added AI-profile-specific overrides so the raw JSON detail block also expands naturally inside the preview page.
- Updated frontend tests to reject the old fixed-card and internal-card-scroll selectors.

### Files Touched
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the adaptive-layout test fail first against the old fixed-card rules.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 8 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings are advisory design-system color items already present across `style.css`.

## 2026-07-06 - AI Profile Preview Report Layout Correction

### User Context
- The user reported that the adaptive card version became more chaotic than before.
- The problem was the multi-column adaptive card grid: uneven content heights made the modal read as a scattered layout.
- The corrected direction is a stable report-style preview instead of cards.

### Work Summary
- Replaced `ai-profile-sections-grid` with `ai-profile-report`.
- Removed the multi-column `auto-fit` profile section grid.
- Converted profile sections into one vertical report:
  - left column: section label;
  - right column: content;
  - each section separated by a simple divider.
- Kept score breakdown as a compact inner data grid inside the report content area.
- Kept the whole profile page scrollable instead of adding per-card scroll zones.
- Updated frontend tests to reject the old multi-column card/grid selectors.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the report-layout test fail first because `ai-profile-report` did not exist and the old grid was still present.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 8 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings are advisory design-system color items already present across `style.css`.

## 2026-07-06 - AI Profile Directory With Modal Preview

### User Context
- The user rejected the fixed right-side profile information page because the layout was still awkward and hard to tune.
- New desired behavior:
  - remove the permanent profile information page from the main AI profile module;
  - keep only the profile directory/list on the page;
  - clicking a directory entry opens a preview modal;
  - all profile details live inside that modal.

### Work Summary
- Replaced the old `currentAIProfileResult` fixed detail pane with a modal preview state:
  - `openAIProfilePreview`;
  - `closeAIProfilePreview`;
  - `previewAIProfileResult`;
  - `previewAIProfileRawJson`.
- Changed the AI profile module body to a single `ai-profile-directory-board`.
- Kept the directory selection/export workflow unchanged:
  - checkbox selection;
  - filtered-page select all;
  - clear selection;
  - export selected profile package.
- Moved the full profile detail content into `ai-profile-preview-modal`.
- Added a fixed full-screen `ai-profile-preview-backdrop` with click-outside close behavior.
- Updated the raw-table reader test to reference the new preview modal instead of the removed permanent profile page state.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `tests/test_frontend_raw_tables_module.py`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 8 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings are advisory design-system color items already present across `style.css`.
- Attempted in-app browser verification, but no in-app browser instance was available in this Codex session.

## 2026-07-06 - AI Profile Readable Scroll Layout

### User Context
- The user clarified that forcing every profile information block into one screen made the cards too small and hard to use.
- The intended behavior is not "see every profile detail at a glance".
- The page can be larger and the user can scroll down to inspect the profile.
- Short sections should not become tiny scroll boxes; only genuinely long sections should scroll internally.

### Work Summary
- Changed the right-side AI profile page back to a readable scroll page.
- Kept the left profile directory equal-height with the profile detail area.
- Replaced the compressed fixed 2-column / 4-row card grid with a larger responsive content grid.
- Increased profile card padding and minimum height.
- Let normal text sections display naturally without internal scrolling:
  - summary;
  - product fit;
  - business type;
  - market role;
  - recommended action.
- Limited internal scrolling to long/detail-heavy blocks only:
  - score breakdown;
  - evidence;
  - risk flags;
  - raw JSON.
- Updated the console-redesign override so it no longer forces the profile page to `overflow: hidden`.

### Files Touched
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the revised readable-scroll-layout test fail first against the compressed fixed-card layout.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_page_uses_readable_scroll_layout`: 1 test passed.
- `python -m unittest tests.test_frontend_ai_profile_task`: 4 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 186 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings were `advisory:design-system-color`.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned HTTP 200.

## 2026-07-06 - AI Profile Fixed Dossier Cards

### User Context
- The user reported that the AI profile information page was no longer fully visible after the previous equal-height layout change.
- The desired behavior is:
  - each profile information page has a fixed visible area;
  - all small information blocks on the page are visible at once;
  - each small information block has its own fixed size;
  - if a small block has too much content, that block scrolls internally.

### Work Summary
- Changed the right-side AI profile page from whole-page scrolling to a fixed dossier layout.
- Added an `ai-profile-sections-grid` for the profile content blocks.
- Split the profile content into fixed cards:
  - profile summary;
  - product fit;
  - business type;
  - market role;
  - score breakdown;
  - recommended action;
  - evidence;
  - risk flags.
- Added `ai-profile-section-body` containers so long content scrolls inside each card.
- Kept the raw JSON section as a bounded collapsible area instead of allowing it to expand the whole page.
- Preserved the mobile exception so small screens can still use vertical natural flow.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the new fixed-card layout test fail first because the fixed grid and internal card body scroll containers did not exist.
- `python -m unittest tests.test_frontend_ai_profile_task`: 4 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `python -m unittest discover -s tests`: 186 tests passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: remaining findings were `advisory:design-system-color`.
- Live service checks passed:
  - `GET http://127.0.0.1:8000/health` returned `{"status":"ok"}`.
  - `GET http://127.0.0.1:5173/` returned HTTP 200.

## 2026-07-06 - AI Profile Preview Modal Scroll Fix

### User Context
- The user reported that the AI profile preview could not show complete information and could not be scrolled.
- The issue appeared after changing the AI profile module to a directory-only list with profile details shown in a preview modal.
- The expected behavior is simple: clicking a directory item opens a readable preview window, and if the profile content is longer than the window, the preview body scrolls normally.

### Work Summary
- Identified the root cause in the modal CSS:
  - the modal only had `max-height`, not a real height, so its inner grid row did not reliably form a scrollable area;
  - `.ai-profile-preview-body` used `overflow: hidden`, which clipped long profile content;
  - `.ai-profile-page` inside the modal was forced to `height: 100%`, which fought against natural report-height content.
- Changed the modal to a fixed viewport-bounded grid:
  - header stays at the top;
  - body uses `overflow: auto`;
  - profile page inside the modal uses natural height and visible overflow;
  - mobile viewport height is also bounded consistently.
- Strengthened the frontend test so this scroll behavior is protected from future regressions.

### Files Touched
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the focused preview-layout test fail before the CSS fix.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_preview_uses_report_layout`: passed.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 8 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend`: only existing `advisory:design-system-color` findings remained.

### Next Steps
- If the user still sees clipping in the browser, verify the running frontend service is using the current worktree build/dev server and not an older process.

## 2026-07-06 - AI Profile Export Package Standardization

### User Context
- The user accepted the corrected AI profile preview modal behavior.
- The user asked for the exported AI profile package to follow the same standard: complete, readable, structured, and traceable instead of a raw database-row dump.

### Work Summary
- Changed `导出画像包` so it no longer exports `profiles: rows` directly.
- Added `buildAIProfileExportPackage` to produce a stable export wrapper with:
  - `schema_version`;
  - export name and timestamp;
  - selected count;
  - selection mode and filters;
  - total available records under the active filters.
- Added `toAIProfileExportProfile` so each exported profile follows the same report order as the preview modal:
  - customer summary;
  - product fit;
  - business type;
  - market role;
  - score breakdown;
  - recommended action;
  - evidence;
  - risk flags.
- Preserved machine-readable fields for downstream processing:
  - company identifiers;
  - score object;
  - model metadata;
  - audit/status fields;
  - original raw record under `raw_record`.

### Files Touched
- `frontend/src/App.vue`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched `test_ai_profile_export_uses_preview_report_standard` fail before implementing the export wrapper.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_export_uses_preview_report_standard`: passed.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 9 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-07-07 - Remove AI Profile Raw JSON Viewer

### User Context
- The user asked twice to remove the raw JSON package viewing function from the AI profile module.
- The intended cleanup is UI-facing: the AI profile preview should show the readable profile report only, without a `查看原始 JSON` collapsible block.
- The export package still keeps `raw_record` for machine-readable downstream processing and debugging.

### Work Summary
- Removed `previewAIProfileRawJson` from the Vue component.
- Removed the `查看原始 JSON` details block from the AI profile preview modal.
- Removed unused `.raw-json-detail` CSS.
- Updated frontend tests so the raw JSON viewer is explicitly forbidden in the AI profile module.

### Files Touched
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_frontend_ai_profile_task.py`
- `tests/test_frontend_raw_tables_module.py`
- `AI_WORKLOG.md`

### Verification
- Watched the focused tests fail first because the old raw JSON viewer was still present.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_preview_uses_report_layout tests.test_frontend_raw_tables_module.FrontendRawTablesModuleTests.test_ai_profile_results_have_dedicated_reader_module`: passed.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 9 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-07-07 - AI Profile Export As Offline HTML Report

### User Context
- The user clarified that `导出画像包` should not export a JSON file.
- The intended output is a single offline HTML report file that can be sent to other people and opened without the backend or frontend service.
- The HTML report should visually follow the current AI profile preview layout and focus on business-readable content.

### Work Summary
- Replaced the JSON export path with an HTML export path.
- `导出HTML报告` now downloads `ai-profile-report-YYYY-MM-DD.html`.
- Added `buildAIProfileExportHtml` to generate a complete standalone HTML document with inline CSS.
- Added a report directory, export header, and repeated profile report pages.
- Each profile page contains:
  - company name, domain, country, profile package id, task id;
  - priority level and total score;
  - model/status metadata;
  - customer summary, product fit, business type, market role;
  - score breakdown, recommended action, evidence, and risk flags.
- Removed the previous `raw_record` JSON-oriented export content from the user-facing report.
- Added HTML escaping for all dynamic values so exported company/profile text cannot break the report markup.
- Kept the selection behavior unchanged:
  - manual row selection;
  - current-filter full selection;
  - clear selection.

### Files Touched
- `frontend/src/App.vue`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the export tests fail first against the old JSON export behavior.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_directory_supports_selection_and_export tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_export_builds_offline_html_report`: passed.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 9 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend/src/App.vue`: no findings.

## 2026-07-07 - Custom Filename For AI Profile HTML Export

### User Context
- The user asked to choose the filename when exporting the AI profile HTML report.

### Work Summary
- Added a filename prompt before export.
- The prompt defaults to `ai-profile-report-YYYY-MM-DD.html`.
- If the user cancels the prompt, export is aborted.
- If the user enters a filename without `.html`, the frontend appends `.html`.
- Illegal filename characters such as `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, and `|` are replaced with `-`.

### Files Touched
- `frontend/src/App.vue`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the focused export tests fail before the custom filename implementation.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_directory_supports_selection_and_export tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_export_builds_offline_html_report`: passed.
- `python -m unittest tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 9 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend/src/App.vue`: no findings.

## 2026-07-07 - AI Profile Contacts In Preview And HTML Export

### User Context
- The user asked to append the corresponding contact information to the AI profile preview modal and to the exported offline HTML report.

### Work Summary
- Added `contacts` to the `/raw-tables/ai-profile-results` response by resolving `AIProfileResult.domain_id` to rows in the `contacts` table.
- Added `contacts: Contact[]` to the frontend AI profile result type.
- Added a `对应联系方式` section to the AI profile preview modal.
- Added the same `对应联系方式` section to offline HTML exports.
- Exported contact rows include contact type and value; email, phone, and URL-like social links remain clickable.

### Files Touched
- `database/queries.py`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `frontend/src/types.ts`
- `tests/test_api_read_endpoints.py`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Watched the focused API and frontend tests fail first because `contacts` and the `对应联系方式` sections were missing.
- `python -m unittest tests.test_api_read_endpoints.FastApiReadEndpointTests.test_raw_ai_profile_results_endpoint_returns_ai_outputs`: passed.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_export_builds_offline_html_report tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_preview_uses_report_layout`: passed.
- `python -m unittest tests.test_api_read_endpoints tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 27 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-07-07 - Fix Missing Profile Source Group After Crawl

### User Context
- The user had just completed a crawl task for Italy heating leads, but the AI profile module could not find the corresponding profile source group.
- The user correctly pointed out that the crawl had already been run, so the issue should not be treated as missing execution.

### Investigation
- Crawl task `#22` finished successfully with 96 selected domains: 59 `success` and 37 `empty`.
- The crawl generated 59 `profile_packages` through in-memory `_profile_package` payloads.
- Those 59 packages were linked to `crawl_results`, but their `crawl_task_run_id` and `candidate_group_id` fields were `NULL`.
- The profile source group list groups packages by `ProfilePackage.crawl_task_run_id`, so these packages existed in the database but were invisible as a selectable source group.

### Work Summary
- Updated `import_crawl_rows()` and `import_crawl_row()` so generated profile packages can receive `candidate_group_id` and `crawl_task_run_id`.
- Updated `persist_crawl_rows_to_database()` to pass the crawl task and candidate group IDs into `import_crawl_rows()`.
- Backfilled the already-generated task `#22` packages to `crawl_task_run_id = 22` and `candidate_group_id = 3`.
- Restarted the FastAPI backend so future crawl tasks use the fixed code.

### Files Touched
- `database/importers.py`
- `database/stage_persistence.py`
- `tests/test_database_importers.py`
- `AI_WORKLOG.md`

### Verification
- Watched `tests.test_database_importers.DatabaseImporterTests.test_import_crawl_rows_attaches_generated_profile_to_source_group` fail first because `import_crawl_rows()` did not accept `candidate_group_id`.
- `python -m unittest tests.test_database_importers.DatabaseImporterTests.test_import_crawl_rows_attaches_generated_profile_to_source_group`: passed after the fix.
- `python -m unittest tests.test_database_importers tests.test_task_handlers tests.test_database_queries`: 38 tests passed.
- `python -m unittest tests.test_api_read_endpoints tests.test_run_crawl`: 32 tests passed.
- Database backfill result: task `#22` had 59 generated profile packages, 59 were missing source-group fields before backfill, and 59 were updated.
- Backend restarted and reported Uvicorn running on `http://127.0.0.1:8000`.

### Next Steps
- In the AI profile module, choose the newly visible source group for crawl task `#22` instead of manually entering individual profile package IDs.

## 2026-07-07 - Recover Interrupted Inline Search Task

### User Context
- The user closed project services while a task was running and asked how to recover.

### Investigation
- PostgreSQL and Redis were still running.
- FastAPI backend on `127.0.0.1:8000` and Vite frontend on `127.0.0.1:5173` were not listening.
- Latest task run `#18` was a `search` task stuck in `running`.
- Task `#18` had 124 keyword items: 21 `success`, 4 `failed`, and 99 still `pending`.
- Because the current search task persists search rows and creates the candidate group only after the search runner returns, task `#18` had not produced persisted search results or a candidate group before the service was killed.

### Work Summary
- Used the project task-batch functions to cancel unfinished task items for task `#18`.
- Marked task `#18` as `cancelled` with summary `{"success": 21, "failed": 4, "cancelled": 99}`.
- Restarted FastAPI backend on `http://127.0.0.1:8000`.
- Restarted Vite frontend on `http://127.0.0.1:5173`.

### Verification
- `GET /health`: returned `{"status":"ok"}`.
- `GET /task-runs?limit=1&offset=0&status=running`: returned zero running tasks.
- `GET /task-runs/18`: returned status `cancelled` and the expected summary.
- `node /Users/zhize/.agents/skills/impeccable/scripts/detect.mjs --json frontend/src/App.vue frontend/src/style.css`: reported existing `style.css` design-system color advisories; no new deterministic issue was introduced by the small contact-list CSS change.

## 2026-07-07 - Hide Contact Source Labels From User-Facing UI

### User Context
- The user clarified that contact source labels such as `crawl_csv` are developer/internal provenance and must not appear in customer-facing preview windows or exported reports.

### Standing Rule
- User-facing business surfaces must not display implementation provenance: CSV filenames, crawl/import source labels, internal pipeline fields, or database-oriented labels.
- Contact rows should show business-useful information only: contact type, value, and optional business label.
- Internal provenance can remain in the database/API for audit purposes, but it belongs only in explicit audit/debug views.

### Work Summary
- Removed `contact.source` and `未知来源` from AI profile preview contact rows.
- Removed `contact.source` and `未知来源` from offline HTML export contact rows.
- Removed `contact.source` from customer detail contact rows.
- Added `contactDisplayMeta` so contact rows show type plus optional business label only.
- Added the rule to `DESIGN.md` as the Operator-Facing Data Rule.
- Added a frontend regression test that fails if `contact.source` or `未知来源` reappears in `App.vue`.

### Files Touched
- `frontend/src/App.vue`
- `tests/test_frontend_ai_profile_task.py`
- `DESIGN.md`
- `AI_WORKLOG.md`

### Verification
- Watched the focused frontend test fail first because `contact.source` was still present.
- `python -m unittest tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_export_builds_offline_html_report tests.test_frontend_ai_profile_task.FrontendAIProfileTaskTests.test_ai_profile_preview_uses_report_layout`: passed.
- `rg -n "contact\\.source|未知来源" frontend/src/App.vue`: no matches.
- `python -m unittest tests.test_api_read_endpoints tests.test_frontend_ai_profile_task tests.test_frontend_raw_tables_module`: 27 tests passed.
- `npm run build` in `frontend/`: Vue type-check and Vite production build passed.

## 2026-07-07 - Backfill Interrupted Crawl Profile Packages

### User Context
- The user pointed out that the latest crawl source group should not only include the 59 packages from task `#22`, because earlier interrupted crawl attempts had also run.

### Investigation
- Task `#20` was a cancelled crawl task with `candidate_limit = 20`, but it only persisted 3 successful crawl results and 3 profile packages.
- Task `#21` was a cancelled crawl task with `candidate_limit = 20`, but it only persisted 3 crawl results: 1 successful profile package and 2 empty crawl results.
- Therefore the previous interrupted attempts did not produce 20 + 20 usable profile packages. They produced 4 usable profile packages total.

### Work Summary
- Backfilled task `#20`'s 3 generated profile packages to `crawl_task_run_id = 20` and `candidate_group_id = 3`.
- Backfilled task `#21`'s 1 generated profile package to `crawl_task_run_id = 21` and `candidate_group_id = 3`.
- Current usable profile source group packages for this candidate group are now:
  - task `#20`: 3 packages
  - task `#21`: 1 package
  - task `#22`: 59 packages
  - total: 63 packages

### Files Touched
- `AI_WORKLOG.md`

### Verification
- Database verification query returned groups: `#20 = 3`, `#21 = 1`, `#22 = 59`, all under candidate group `#3`.

## 2026-07-08 - Expand Git Ignore Rules Before Git Transfer

### User Context
- The user decided not to use the temporary migration folder transfer flow and instead plans to upload/transfer the project through Git.
- The user asked to add local useless artifacts to `.gitignore`.

### Work Summary
- Expanded `.gitignore` in the active `database-foundation` worktree.
- Synchronized the root project `.gitignore` as well, so running Git from either location ignores local tool state.
- Added ignore rules for local worktrees, transfer packages, `.env` files except `.env.example`, Python caches, virtualenvs, local databases/dumps, frontend dependencies/builds, service logs, search/crawl state directories, generated CSV/JSON crawl artifacts, local agent/tool directories, and OS/editor files.

### Files Touched
- `.gitignore`
- `AI_WORKLOG.md`

### Verification
- `git check-ignore -v` confirmed ignore matches for local agent directories, `server_migration_package/`, `frontend/node_modules/`, `frontend/dist/`, and generated `profile_inputs/**/*.json`.
- `git status --short` confirmed new local artifact directories are now ignored; previously tracked cache files still appear because `.gitignore` does not untrack files already in Git history.

## 2026-07-08 - Promote Server Migration Package To Clean Development Root

### User Context
- The user decided the existing project directory is too messy and wants to abandon it for future work.
- Future development should happen inside `server_migration_package`.

### Work Summary
- Re-synced the latest backend, frontend, crawler/search modules, database migrations, scripts, docs, and tests into `server_migration_package`.
- Added a standalone `.gitignore` inside `server_migration_package` suitable for making it an independent Git repository.
- Added the `tests/` directory so the package is suitable for continued development, not just deployment transfer.

### Files Touched
- `server_migration_package/.gitignore`
- `server_migration_package/AI_WORKLOG.md`
- `server_migration_package/tests/`

### Verification
- Confirmed `server_migration_package/tests` contains 36 test files.
- Confirmed no `node_modules`, `dist`, `__pycache__`, or `.service_logs` directories exist inside the package.
- `python -m unittest tests.test_database_models` from inside `server_migration_package`: passed.

### Next Steps
- Open future Codex sessions from `server_migration_package`.
- If using Git from this clean directory, run `git init` or connect it to the target remote from inside `server_migration_package`.

## 2026-07-10 - Current Conversation and Saved Context Snapshot

### Repository and Environment Rules
- `/Users/zhize/Eyes` is the current formal repository. It has been synchronized with Git/GitHub, and the server production environment runs the formal version from this line of development.
- All future implementation changes must first be made and verified in the test worktree:

```text
/Users/zhize/The Eyes of God/.worktrees/database-foundation
```

- Do not synchronize test-worktree code back into `/Users/zhize/Eyes` until the user has reviewed the result and explicitly approved the synchronization.
- The two previously discovered local listeners are the intended test environment, not accidental duplicate services. At the last verification they were:
  - FastAPI backend: `http://127.0.0.1:8000`
  - Vite frontend: `http://127.0.0.1:5173`
- This worklog entry is a direct user-requested documentation update in the formal directory. It does not mean the feature code described below has been synchronized into the formal repository.

### Task and Result Data Model
- Crawl-website output that was previously handled as CSV is now persisted primarily in the `crawl_results` database table.
- Executable project tasks are represented by `task_runs.id`; per-target/per-keyword execution units are represented by `task_items` associated with the task run.
- Crawl results can be tied to a crawl task through source identifiers such as `task:crawl:<task_run_id>`.
- Candidate-group status `已抓` means that the domain has a historical crawl result. It does not by itself mean that the currently viewed/later crawl task executed that domain.

### Agreed Crawl-Result UX
- Do not add a new standalone task-result module. The existing result-viewing location remains `审计排错 -> 抓取结果` (`rawTables / crawl_results`).
- Task Center contains only a `查看结果` action for crawl tasks; it must not contain the export action.
- `查看结果` jumps to the existing crawl-result page, filters with `task:crawl:<task_run_id>`, clears unrelated filters, loads the first page, and selects all rows on that page.
- The crawl-result page contains:
  - one checkbox before each result row,
  - one checkbox before the table column headers for selecting/deselecting the current page,
  - a fixed `导出XLSX` button that is disabled until at least one row is selected,
  - `最大显示条数` options of `100`, `300`, and `500`, with `100` as the default.
- XLSX export is based on selected `crawl_results.id` values, not all rows belonging to a task. The test-worktree endpoint is:

```text
GET /raw-tables/crawl-results/export.xlsx?ids=1,2,3
```

- The endpoint rejects an empty/invalid ID list and caps one export at 1000 selected IDs.

### Duplicate Crawl Semantics
- The examples discussed were candidate/search flows `意大利泳池机 search #7` and `意大利采暖机 search #19`, which contain overlapping domains.
- Duplicate domains may remain in both search results and candidate groups as evidence of each search task.
- With the default `recrawl_existing=false`, a domain that already has a crawl result is excluded from a later crawl execution list.
- A skipped historical duplicate must not be copied into the later task's `task:crawl:<later_task_id>` result set. It only belongs to the later task if that task actually re-crawls it with `recrawl_existing=true`.
- A temporary change that copied historical rows into task `#22` was identified as incorrect and fully removed from the test-worktree code.
- The temporary data was cleaned up by deleting 26 wrongly copied `crawl_results` rows and 27 related `country_signals`. Final verification showed task `#22` had 96 `task_items` and `task:crawl:22` had 96 crawl-result rows.
- Residual audit note: the mistaken temporary run reported 20 domain records as updated through the normal upsert path. No before-value snapshot existed for those domain main fields, so only the inserted crawl-result and country-signal rows could be precisely reverted. No further domain-field restoration was requested.

### Test-Worktree Implementation Status
- Relevant implementation files in the test worktree include:
  - `api/app.py`
  - `database/task_results.py`
  - `frontend/src/App.vue`
  - `frontend/src/api.ts`
  - `frontend/src/style.css`
  - `frontend/src/types.ts`
  - `tests/test_api_read_endpoints.py`
  - `tests/test_frontend_task_results_module.py`
- Focused result-view/export tests passed: 24 tests.
- The broader related backend/frontend suite passed: 63 tests.
- The frontend production build passed.
- A live selected-row XLSX request was verified with HTTP 200 and the XLSX MIME type.

### Standing Instructions
- Continue all code changes in `/Users/zhize/The Eyes of God/.worktrees/database-foundation` first.
- Preserve the existing crawl-result viewing module and selected-row export design.
- Do not reintroduce copying historical crawl results into later task IDs.
- Obtain explicit user approval before synchronizing any test-worktree implementation into `/Users/zhize/Eyes`.

## 2026-07-10 - Crawl Result Viewing, Selected XLSX Export, and Duplicate Crawl Clarification

### User Context
- The user wanted task results to be easy to find after a task finishes, especially crawl task results.
- The user clarified not to add a new task-result module because the frontend already has an existing place to view crawl results: `审计排错 -> 抓取结果`.
- The requested UX is:
  - Task Center only shows `查看结果` as a jump button.
  - Export belongs inside the crawl-result viewing area.
  - Crawl-result rows can be selected individually or by selecting the current page.
  - XLSX export should export selected crawl-result rows.
  - The page should support larger page sizes so filtered results can be selected in bulk.

### Final Behavior
- `任务中心 -> 查看结果` now jumps to `审计排错 -> 抓取结果`, sets `rawTableFilters.q = task:crawl:<task_run_id>`, clears other raw-table filters, loads the first page, and selects the current page.
- The separate `任务结果` navigation/module that had been temporarily added was removed.
- The crawl-result page has:
  - a checkbox before every row,
  - a header checkbox before the column labels,
  - header checkbox behavior for selecting/deselecting the current page,
  - a fixed `导出XLSX` button that is disabled until at least one crawl result is selected.
- Export now uses selected `crawl_results.id` values and calls:

```text
GET /raw-tables/crawl-results/export.xlsx?ids=1,2,3
```

- The old task-level crawl XLSX endpoint still exists for backend compatibility, but the frontend export action uses the selected-row endpoint.
- The crawl-result page now has `最大显示条数` options:

```text
100 / 300 / 500
```

- Default raw-table page size was changed from `20` to `100`.

### Backend Work
- Added selected-row XLSX export support in `database/task_results.py`:
  - `build_selected_crawl_results_xlsx(session, crawl_result_ids)`
  - Preserves selected ID order.
  - Uses the same XLSX generator and crawl-result columns as task-level export.
- Added FastAPI endpoint in `api/app.py`:

```text
/raw-tables/crawl-results/export.xlsx?ids=...
```

- Added ID parsing and validation:
  - empty selection returns `400`,
  - invalid IDs return `400`,
  - export is capped at 1000 IDs.

### Frontend Work
- Updated `frontend/src/App.vue`:
  - Removed the added `taskResults` module and navigation item.
  - Added selected crawl-result row state.
  - Added current-page selection state.
  - Added `selectCurrentPageRawCrawlResults()`, `toggleCurrentPageRawCrawlResults()`, `toggleRawCrawlResultSelection()`.
  - `导出XLSX` now calls selected-row export and is disabled when no rows are selected.
  - Added `最大显示条数` selector in the raw table pager for `抓取结果`.
- Updated `frontend/src/api.ts`:
  - Added `exportSelectedRawCrawlResultsXlsx(ids)`.
- Updated `frontend/src/style.css`:
  - Added fixed-width selection-cell styling.
  - Reused existing page-size control styling.

### Tests Added / Updated
- `tests/test_api_read_endpoints.py`
  - Verifies selected crawl-result XLSX export only contains selected rows.
- `tests/test_frontend_task_results_module.py`
  - Verifies Task Center has `查看结果` but no export button.
  - Verifies there is no separate `taskResults` module.
  - Verifies `查看结果` jumps to `rawTables/crawl_results` and auto-selects the current page.
  - Verifies crawl-result view has row selection, page selection, selected-row export, and page-size options.

### Duplicate Crawl Clarification
- The user asked about two search/candidate flows with overlapping domains:
  - `意大利泳池机 search #7`
  - `意大利采暖机 search #19`
- Confirmed the correct behavior:
  - Duplicate domains can exist in both search results and both candidate groups.
  - When a later crawl task uses a candidate group, already-crawled domains are skipped by default because `recrawl_existing=false`.
  - Those skipped duplicate domains should not be written into the later crawl task's `task:crawl:<later_task_id>` result set.
  - Candidate group `已抓` means "historically has a crawl result", not "was crawled by this later task".
- A temporary implementation was started to copy already-crawled duplicate rows into the later task result ID, but the user clarified that this was wrong.
- That code was fully reverted.
- The temporary database backfill was also reverted:
  - deleted 26 mistakenly backfilled `crawl_results` from `task:crawl:22`,
  - deleted 27 corresponding `country_signals`,
  - verified `task:crawl:22` returned to 96 crawl results and task `#22` has 96 task items.

### Verification
- Focused tests after selected-row export and page-size changes:

```text
python -m unittest tests.test_frontend_task_results_module tests.test_api_read_endpoints
```

passed with 24 tests.

- Full relevant suite after reverting the duplicate-copy mistake:

```text
python -m unittest tests.test_database_queries tests.test_api_read_endpoints tests.test_task_handlers tests.test_frontend_task_results_module tests.test_frontend_task_progress_panel tests.test_frontend_task_console_distill
```

passed with 63 tests.

- Frontend build:

```text
npm run build
```

passed after allowing Vite to write `frontend/node_modules/.vite-temp`.

- Test services were kept running from the test worktree:
  - FastAPI backend: `127.0.0.1:8000`
  - Vite frontend: `127.0.0.1:5173`

### Important Standing Note
- Do not reintroduce automatic copying of historical crawl results into a later crawl task ID.
- The intended model is:
  - search/candidate groups can preserve duplicate evidence,
  - crawl execution skips historically crawled domains by default,
  - skipped historical domains do not appear in the later crawl task's result set unless the task actually re-crawls them with `recrawl_existing=true`.

## 2026-07-11 - Include Contacts In AI Profile Analysis

### User Context
- The user asked to include extracted contact information in AI profile analysis.
- Work remains in the test worktree and has not been synchronized to `/Users/zhize/Eyes`.

### Work Summary
- Upgraded the internal AI prompt version from `heat_pump_lead_cn_v1` to `heat_pump_lead_cn_v2`.
- AI task input now merges the profile package contacts with all current normalized `contacts` rows for the same domain.
- Normalized contact records are deduplicated by contact kind and value, and internal provenance/source labels are not sent to the model.
- The actual AI input hash now includes the merged contact payload.
- Added required `contact_analysis` output with:
  - contact quality;
  - available channels;
  - preferred channel;
  - up to three recommended contacts;
  - Chinese outreach strategy.
- Prompt rules prohibit inventing or rewriting contact values and require contactability scores to agree with the contact analysis.
- Added contact analysis to the AI profile preview and offline HTML report while retaining the raw extracted contact list beside it.
- Existing `cn_v1` results remain readable and return an empty contact analysis until re-analyzed.

### Files Touched
- `ai/lead_profile_prompt.py`
- `tasks/handlers.py`
- `database/ai_profiles.py`
- `database/queries.py`
- `frontend/src/types.ts`
- `frontend/src/App.vue`
- `frontend/src/style.css`
- `tests/test_task_handlers.py`
- `tests/test_model_api_client.py`
- `tests/test_database_queries.py`
- `tests/test_api_read_endpoints.py`
- `tests/test_frontend_ai_profile_task.py`
- `AI_WORKLOG.md`

### Verification
- Focused backend/frontend regression suite: 56 tests passed.
- Full Python suite: 194 tests passed.
- `npm run build`: Vue type-check and Vite production build passed.
- Docker Desktop, `leadgen-postgres`, and `leadgen-redis` were restarted.
- FastAPI health and database stats returned HTTP 200.
- AI profile list API returns `contact_analysis`; historical `cn_v1` rows return `{}`.
- Vite frontend returned HTTP 200 at `http://127.0.0.1:5173/`.

### Next Steps
- Re-run AI profiling for selected profile packages or source groups to generate `heat_pump_lead_cn_v2` contact analysis.
- Review sample outputs before bulk re-analysis, especially recommended contact selection and contactability scoring.

## 2026-07-13 - Promote Tested Changes To Formal Environment

### User Context
- The user explicitly approved migrating the completed test-environment changes into `/Users/zhize/Eyes`.

### Work Summary
- Synchronized the reviewed implementation files from the test directory into the formal Git working tree.
- Promoted the crawl-result workflow:
  - Task Center `查看结果` jumps to `审计排错 -> 抓取结果` with the task source filter.
  - Crawl-result rows support individual/current-page selection.
  - Selected rows can be exported through `/raw-tables/crawl-results/export.xlsx?ids=...`.
  - Crawl-result page sizes support 100, 300, and 500 rows.
- Promoted `heat_pump_lead_cn_v2` contact-aware AI analysis and its preview/offline-report UI.
- Added the missing backward-compatible `find_url.py` and `find_messsage.py` entry points.
- Preserved the formal `.gitignore`, local `frontend/.env.local`, database data, generated artifacts, logs, caches, `node_modules`, and `dist` exclusions.
- Merged test and formal worklog history so the prior 7/8 and 7/10 formal context was not overwritten.

### Verification
- Formal-directory Python suite: 194 tests passed.
- Installed formal frontend dependencies with `npm ci`.
- Formal-directory `npm run build`: Vue type-check and Vite production build passed.
- Started `leadgen-postgres` and `leadgen-redis`.
- Started FastAPI and Vite from `/Users/zhize/Eyes`.
- `/health`, `/database/stats`, AI profile list, and frontend homepage returned HTTP 200.
- Selected-row XLSX export returned the correct MIME type and passed ZIP integrity validation.
- Existing `heat_pump_lead_cn_v1` AI rows remain readable with empty `contact_analysis` until re-analyzed.

### Git State
- Changes are present in the formal working tree but were not committed or pushed during this migration.
