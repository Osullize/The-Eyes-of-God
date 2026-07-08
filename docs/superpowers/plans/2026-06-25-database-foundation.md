# Database Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for production code changes. Keep existing crawler/search logic unchanged.

**Goal:** Add the first database foundation so existing search CSVs, crawl CSVs, and profile JSON packages can be imported into a durable relational store with global domain dedupe.

**Architecture:** Create an additive `database` package using SQLAlchemy models, Alembic migrations, and importer functions. Add a CLI under `scripts/` for loading existing files. Keep `run_search.py` and `run_crawl.py` behavior unchanged in this first step.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.x, Alembic, PostgreSQL production URL, SQLite for local tests, `unittest`.

---

## Scope

- Add database models and session helpers.
- Add an initial Alembic migration.
- Add importers for search CSV, crawl CSV, and profile JSON directories.
- Add a script to import the existing project outputs.
- Add tests covering dedupe, imports, contacts, country signals, and profile package metadata.
- Add dependency and usage documentation.

## Files

- Create `database/__init__.py`
- Create `database/models.py`
- Create `database/session.py`
- Create `database/importers.py`
- Create `alembic.ini`
- Create `alembic/env.py`
- Create `alembic/versions/20260625_0001_database_foundation.py`
- Create `scripts/import_existing_data.py`
- Create `requirements.txt`
- Create `tests/test_database_importers.py`
- Modify `README.md`
- Modify `AI_WORKLOG.md`

## Task 1: Write Failing Importer Tests

- [ ] Create `tests/test_database_importers.py`.
- [ ] Test that importing duplicate domains from multiple search rows creates one `Domain` and multiple `SearchResult` rows.
- [ ] Test that crawl CSV import updates domain summary and creates email/phone/social contact rows.
- [ ] Test that profile JSON import creates a `ProfilePackage`, preserves schema/page metadata, and adds profile country/contact signals.
- [ ] Run `python -m unittest tests/test_database_importers.py` and confirm it fails because `database` does not exist yet.

## Task 2: Add Dependencies

- [ ] Create `requirements.txt` with existing runtime dependencies plus `SQLAlchemy`, `alembic`, and `psycopg[binary]`.
- [ ] Update README installation section to use the dependency file.

## Task 3: Implement Models and Session Helpers

- [ ] Create SQLAlchemy `Base` and ORM models for `Domain`, `SearchResult`, `CrawlResult`, `Contact`, `ProfilePackage`, and `CountrySignal`.
- [ ] Add indexes/uniqueness constraints for `domains.domain` and `profile_packages.path`.
- [ ] Add `database/session.py` with `create_engine_from_url`, `create_session_factory`, and `create_all`.
- [ ] Keep timestamp defaults database-agnostic.

## Task 4: Implement Importers

- [ ] Add `import_search_csv(session, path)`.
- [ ] Add `import_crawl_csv(session, path)`.
- [ ] Add `import_profile_dir(session, path)`.
- [ ] Add `ImportSummary` return values with inserted/updated counts.
- [ ] Normalize domains with existing `search.url_utils.normalize_domain` where possible.
- [ ] Split semicolon contact fields conservatively and dedupe per domain/kind/value.

## Task 5: Add Migration Files

- [ ] Add `alembic.ini`.
- [ ] Add `alembic/env.py` that reads `DATABASE_URL` and imports model metadata.
- [ ] Add initial migration with all database foundation tables and indexes.

## Task 6: Add Import CLI

- [ ] Create `scripts/import_existing_data.py`.
- [ ] Default to `sqlite:///leadgen.db`.
- [ ] Accept repeated `--search-csv`, `--crawl-csv`, and `--profile-dir` arguments.
- [ ] If no files are passed, import the known project defaults that exist.
- [ ] Print concise per-source import summaries.

## Task 7: Documentation and Worklog

- [ ] Document local SQLite import and production PostgreSQL URL shape in README.
- [ ] Append `AI_WORKLOG.md` with the database design/implementation summary.

## Task 8: Verification

- [ ] Install new dependencies if needed.
- [ ] Run `python -m unittest tests/test_database_importers.py`.
- [ ] Run existing relevant tests: `python -m unittest tests/test_run_search.py tests/test_run_crawl.py tests/test_profile_input_package.py`.
- [ ] Run a small import smoke test against a temporary SQLite database.
- [ ] Run `git status --short` and report changed files.
