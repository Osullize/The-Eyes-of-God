# Database-Native Company Library Design

## User Decision

AI inference is postponed. The immediate goal is to remove CSV files from the console's primary workflow and make the database the source of record for every acquisition stage.

Profile JSON files are retained for now as AI-analysis source material. They are not the primary stage handoff mechanism.

## Target Flow

```text
Keyword config
  -> Search official websites
  -> Stage A tables: domains + search_results + country_signals
  -> Crawl domains selected from Stage A
  -> Stage B tables: crawl_results + contacts + profile_packages + country_signals
  -> Later confirmation / AI scoring
  -> Stage C tables: qualified_leads + company_profiles + lead_scores
```

CSV files should not appear in the console as required task inputs or outputs. Existing CLI CSV behavior can remain as compatibility and export tooling, but it is not the product workflow.

## Stage A: Official Website Candidate Library

Stage A represents companies discovered by search before any site crawl.

Tables:

- `domains`
- `search_results`
- `country_signals`

Console behavior:

- The search task accepts search configuration and runtime controls.
- The search task writes directly to Stage A tables.
- The UI should not ask for "website output CSV".

## Stage B: Crawled Company Library

Stage B represents companies whose websites were crawled and whose public profile/contact information was extracted.

Tables:

- `domains`
- `crawl_results`
- `contacts`
- `profile_packages`
- `country_signals`

Console behavior:

- The crawl task selects domains from Stage A tables.
- The crawl task accepts filters such as country, keyword text, status exclusion, and max domain count.
- The crawl task writes directly to Stage B tables.
- The UI should not ask for "website input CSV" or "company info output CSV".
- Profile JSON output remains configurable as an analysis-material directory.

## Stage C: Priority Customer Library

Stage C represents confirmed or scored opportunities after later AI/human review.

Tables:

- `qualified_leads`
- `company_profiles`
- `lead_scores`

First implementation behavior:

- Create the tables and read endpoints.
- The table can be empty.
- Do not implement AI inference or automatic promotion from Stage B to Stage C yet.

## Backend API

Add stage-specific read endpoints:

- `GET /company-library/stage-a`
- `GET /company-library/stage-b`
- `GET /company-library/stage-c`
- `GET /company-library/stats`

Add database-native crawl task behavior:

- `POST /tasks/crawl` can run without CSV input/output fields.
- When no input CSV is provided, the handler selects crawl candidates from Stage A.
- Candidate selection should skip domains that already have a `crawl_results` row unless retry/recrawl behavior is explicitly requested later.

## Frontend

Add a new "企业库" module with three tabs:

- `官网候选库 A`
- `抓取画像库 B`
- `优先客户库 C`

Keep the existing task panel, but simplify it:

- Search task removes CSV output and state-dir clutter from the primary controls.
- Crawl task removes CSV input/output from the primary controls.
- Import from old files should be treated as legacy import, not the main pipeline.

## Compatibility

Existing CLI scripts can keep CSV parameters for compatibility and manual export workflows.

The console's primary workflow should not require CSV files.

## Verification

Backend:

- Unit tests for selecting Stage A crawl candidates.
- Unit tests for stage library query functions.
- API tests for new stage library endpoints.
- Existing task and importer tests should continue passing.

Frontend:

- Type-check and production build must pass.
- The UI should present A/B/C enterprise library tabs and no longer require CSV fields for console search/crawl tasks.
