from __future__ import annotations

from pydantic import BaseModel, Field

from ai.model_api_client import (
    DEFAULT_API_BASE_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_PROVIDER,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SECONDS,
)
from database.session import DEFAULT_DATABASE_URL


class SearchTaskRequest(BaseModel):
    keyword_group_id: int | None = None
    config_path: str | None = None
    output_file: str | None = None
    state_dir: str | None = None
    engines: str | None = None
    backend: str | None = None
    max_pages: int | None = None
    limit_keywords: int | None = None
    keyword_delay_seconds: float | None = None
    engine_request_delay_seconds: float | None = None
    retry_failed: bool = False
    persist_to_database: bool | None = None


class CrawlTaskRequest(BaseModel):
    candidate_group_id: int | None = None
    input_file: str | None = None
    output_file: str | None = None
    state_dir: str | None = None
    backend: str | None = None
    workers: int | None = None
    max_depth: int | None = None
    max_pages_per_site: int | None = None
    profile_input_dir: str | None = None
    profile_page_char_limit: int | None = None
    max_retries: int | None = None
    backoff_base: float | None = None
    backoff_max: float | None = None
    global_delay: float | None = None
    domain_delay: float | None = None
    proxy: str | None = None
    use_system_proxy: bool | None = None
    headless: bool | None = None
    browser_max_pages: int | None = None
    browser_timeout_ms: int | None = None
    browser_wait_ms: int | None = None
    respect_robots: bool | None = None
    retry_failed: bool = False
    persist_to_database: bool | None = None
    candidate_country: str | None = None
    candidate_query: str | None = None
    candidate_limit: int | None = None
    recrawl_existing: bool | None = None


class ImportExistingDataRequest(BaseModel):
    database_url: str = DEFAULT_DATABASE_URL
    search_csvs: list[str] | None = Field(default=None)
    crawl_csvs: list[str] | None = Field(default=None)
    profile_dirs: list[str] | None = Field(default=None)
    create_tables: bool = True


class AIProfileTaskRequest(BaseModel):
    profile_package_ids: list[int] | str | None = None
    profile_source_group_id: int | None = None
    model_provider: str = DEFAULT_MODEL_PROVIDER
    api_base_url: str = DEFAULT_API_BASE_URL
    api_key: str = ""
    model_name: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_TEMPERATURE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    persist_to_database: bool | None = None


class KeywordGroupCreateRequest(BaseModel):
    name: str
    country: str
    country_terms: str
    keyword_terms: str = ""
    product_terms: str = ""
    role_terms: str = ""
    search_templates: str = ""
    notes: str = ""
    is_active: bool = True


class KeywordGroupUpdateRequest(BaseModel):
    name: str | None = None
    country: str | None = None
    country_terms: str | None = None
    keyword_terms: str | None = None
    product_terms: str | None = None
    role_terms: str | None = None
    search_templates: str | None = None
    notes: str | None = None
    is_active: bool | None = None
