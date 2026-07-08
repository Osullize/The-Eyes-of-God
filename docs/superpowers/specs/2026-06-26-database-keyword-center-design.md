# Database Keyword Center Design

## Goal

Move the console's keyword configuration from YAML files into the database.

The existing YAML files remain as CLI compatibility and as one-time import sources, but the console workflow should use database keyword groups.

## Keyword Group Table

Create a `keyword_groups` table.

Fields:

- `id`
- `name`
- `country`
- `country_terms`
- `keyword_terms`
- `notes`
- `is_active`
- `created_at`
- `updated_at`

`country_terms` and `keyword_terms` are newline-separated text fields in the first version. This keeps the UI simple and avoids over-building term-level versioning before it is needed.

## Keyword Generation

For each active keyword group:

```text
keyword term + country term
```

Each generated keyword becomes a `KeywordSpec` with:

- `country`: keyword group country
- `country_term`: one country term line
- `industry`: keyword group name
- `industry_term`: one keyword term line
- `keyword`: combined string

This preserves compatibility with the existing search pipeline and search result schema.

## API

Add CRUD endpoints:

- `GET /keyword-groups`
- `POST /keyword-groups`
- `PUT /keyword-groups/{group_id}`
- `DELETE /keyword-groups/{group_id}`

Deleting a keyword group does not delete historical search/crawl/company records.

## Search Task Integration

`POST /tasks/search` accepts `keyword_group_id`.

If `keyword_group_id` is present, the handler loads terms from the database and passes generated `KeywordSpec` values into `run_search()`.

If `keyword_group_id` is absent, YAML `config_path` remains supported for CLI and compatibility behavior.

## Frontend

Add a `关键词配置中心` module.

First version features:

- list keyword groups
- select a keyword group
- create a keyword group
- edit and save group fields
- add notes
- delete a group
- choose a keyword group in the `找官网` task form

## Initial Import

Provide a script to import existing YAML files into `keyword_groups`.

Initial files:

- `config/keywords_france.yaml`
- `config/keywords_france_complement.yaml`
- `config/keywords_uk.yaml`
- `config/keywords_uk_complement.yaml`

The importer should upsert by group name so it can be run more than once.

## Verification

Backend:

- database model and migration tests
- keyword group CRUD query tests
- keyword group API tests
- search handler test proving `keyword_group_id` drives generated search terms

Frontend:

- TypeScript build passes
- console shows keyword center and search task can select a group
