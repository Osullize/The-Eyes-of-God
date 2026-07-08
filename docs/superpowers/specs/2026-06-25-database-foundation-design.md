# Database Foundation Design

## Status

Approved for first implementation by the user on 2026-06-25.

## Background

The project currently persists search and crawl output as CSV files and per-company profile JSON files. This is enough for a local tool, but it is not enough for a server-side platform with background jobs, API queries, deduplication, country attribution, and AI profile scoring.

The first database step should preserve the existing crawler/search behavior and add a durable persistence layer beside it. `run_search.py` and `run_crawl.py` should continue to work as command-line tools. The database layer should import their outputs and later become the shared storage target for backend tasks.

## Goals

- Store each domain once globally, regardless of how many country/keyword searches found it.
- Preserve search evidence: keyword, engine, source URL, country, country term, industry, and matched metadata.
- Preserve crawl evidence: crawl status, extracted company name, contacts, description, crawled pages, page categories, and output file.
- Preserve profile-analysis input package metadata and the path to each JSON evidence package.
- Record country signals separately instead of assuming a search country is the company's true country.
- Provide import functions and a CLI for loading existing CSV/JSON outputs into the database.
- Use a stack that can run locally with SQLite for tests and later run on PostgreSQL in production.

## Non-Goals

- Do not change scraping engine logic.
- Do not call AI or implement profile scoring in this step.
- Do not build the backend API, task queue, or desktop console in this step.
- Do not migrate generated CSV/JSON files away; they remain useful evidence and backup outputs.

## Technology

- SQLAlchemy 2.x ORM for models and database access.
- Alembic for schema migrations.
- PostgreSQL as the production target.
- SQLite as the default local/test database target.
- Standard-library `csv` and `json` for importing existing outputs.

## Data Model

### `domains`

Global dedupe table. One row per normalized domain.

Important fields:

- `id`
- `domain` unique
- `website`
- `display_name`
- `description`
- `latest_status`
- `created_at`
- `updated_at`

### `search_results`

One row per imported search CSV row or future search result event.

Important fields:

- `id`
- `domain_id`
- `keyword`
- `title`
- `website`
- `source_url`
- `engine`
- `country`
- `country_term`
- `industry`
- `industry_term`
- `matched_keywords`
- `matched_countries`
- `matched_industries`
- `matched_industry_terms`
- `source_file`
- `created_at`

### `crawl_results`

One row per imported crawl CSV row or future crawl run output.

Important fields:

- `id`
- `domain_id`
- `company_name`
- `website`
- `status`
- `error`
- `emails`
- `phones`
- `possible_address`
- `description`
- `crawled_pages`
- `social_links`
- `contacts`
- `page_categories`
- `country`
- `industry`
- `matched_keywords`
- `matched_countries`
- `matched_industries`
- `matched_industry_terms`
- `source_file`
- `created_at`

### `contacts`

Normalized contact facts derived from crawl CSV and profile JSON.

Important fields:

- `id`
- `domain_id`
- `kind`: `email`, `phone`, `social`, or `person`
- `value`
- `label`
- `source`
- `created_at`

### `profile_packages`

Pointer to one per-company profile JSON evidence package.

Important fields:

- `id`
- `domain_id`
- `path`
- `schema_version`
- `crawl_status`
- `page_count`
- `crawl_time`
- `source_dir`
- `created_at`
- `updated_at`

### `country_signals`

Country evidence from search metadata, domain TLD inference, crawl row country, profile package metadata, and later AI analysis.

Important fields:

- `id`
- `domain_id`
- `country`
- `signal_type`
- `confidence`
- `evidence`
- `source`
- `created_at`

Country attribution should be treated as a scored inference, not a single hard-coded value. For example, a French keyword hit creates a `search_country` signal, but the final company country can later be decided by address, phone prefix, language, TLD, and AI evidence.

## Import Flow

1. `import_search_csv(path)`: read rows from `company_websites*.csv`, upsert domains, insert search result rows, and create country signals.
2. `import_crawl_csv(path)`: read rows from `company_info*.csv`, upsert domains, insert crawl result rows, update latest domain summary, and extract contacts.
3. `import_profile_dir(path)`: scan `*.json`, upsert domains, insert/update profile package rows, and extract profile contact/country signals.
4. `scripts/import_existing_data.py`: CLI wrapper that can import one or many CSV/profile directories into a database URL.

## CLI Contract

Default local import:

```bash
python scripts/import_existing_data.py --database-url sqlite:///leadgen.db
```

Selective import:

```bash
python scripts/import_existing_data.py \
  --database-url sqlite:///leadgen.db \
  --search-csv company_websites_france.csv \
  --crawl-csv company_info_france.csv \
  --profile-dir profile_inputs/france
```

Production shape:

```bash
python scripts/import_existing_data.py \
  --database-url postgresql+psycopg://user:password@host:5432/leadgen
```

## Compatibility

The database layer is additive. Existing CSV/JSON generation remains the source of truth during this step. Later background workers can call the same shared functions and write to both CSV/JSON and database, or eventually write directly to database after the compatibility path is proven.
