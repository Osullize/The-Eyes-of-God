export interface DatabaseStats {
  domains: number;
  search_results: number;
  crawl_results: number;
  contacts: number;
  profile_packages: number;
  country_signals: number;
}

export interface KeywordGroup {
  id: number;
  name: string;
  country: string;
  country_terms: string;
  keyword_terms: string;
  product_terms: string;
  role_terms: string;
  search_templates: string;
  notes: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  keyword_count: number;
}

export interface KeywordGroupPayload {
  name: string;
  country: string;
  country_terms: string;
  keyword_terms?: string;
  product_terms?: string;
  role_terms?: string;
  search_templates?: string;
  notes?: string;
  is_active?: boolean;
}

export interface CompanyLibraryStats {
  stage_a_companies: number;
  stage_b_companies: number;
  stage_c_companies: number;
  search_results: number;
  crawl_results: number;
  qualified_leads: number;
}

export interface DomainSummary {
  id: number;
  domain: string;
  website: string;
  display_name: string;
  description: string;
  latest_status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface DomainListResponse {
  items: DomainSummary[];
  count: number;
  total: number;
  limit: number;
  offset: number;
}

export type RawDomainRow = DomainSummary;

export interface RawSearchResultRow {
  id: number;
  domain_id: number;
  domain: string;
  keyword: string;
  title: string;
  website: string;
  source_url: string;
  engine: string;
  country: string;
  country_term: string;
  industry: string;
  industry_term: string;
  matched_keywords: string;
  matched_countries: string;
  matched_industries: string;
  matched_industry_terms: string;
  source_file: string;
  created_at: string | null;
}

export interface RawCrawlResultRow {
  id: number;
  domain_id: number;
  domain: string;
  keyword: string;
  company_name: string;
  website: string;
  emails: string;
  phones: string;
  possible_address: string;
  description: string;
  crawled_pages: string;
  status: string;
  error: string;
  social_links: string;
  contacts: string;
  page_categories: string;
  country: string;
  industry: string;
  matched_keywords: string;
  matched_countries: string;
  matched_industries: string;
  matched_industry_terms: string;
  source_file: string;
  created_at: string | null;
}

export interface AIProfileRecommendedContact {
  type: string;
  value: string;
  label: string;
  reason: string;
}

export interface AIProfileContactAnalysis {
  contact_quality?: string;
  available_channels?: string[];
  preferred_channel?: string;
  recommended_contacts?: AIProfileRecommendedContact[];
  outreach_strategy?: string;
}

export interface RawAIProfileResultRow {
  id: number;
  domain_id: number;
  domain: string;
  company_name: string;
  country: string;
  contacts: Contact[];
  contact_analysis: AIProfileContactAnalysis;
  profile_package_id: number;
  task_run_id: number | null;
  task_item_id: number | null;
  model_provider: string;
  model_name: string;
  prompt_version: string;
  input_hash: string;
  profile_summary: string;
  business_type: string;
  market_role: string;
  product_fit: string;
  customer_priority: string;
  score_total: number;
  score_breakdown_json: Record<string, unknown>;
  evidence_json: unknown[];
  risk_flags_json: unknown[];
  recommended_action: string;
  status: string;
  error: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface RawTableListResponse<T> {
  items: T[];
  count: number;
  total: number;
  limit: number;
  offset: number;
}

export interface Contact {
  id: number;
  kind: string;
  value: string;
  label: string;
  source: string;
  created_at: string | null;
}

export interface ProfilePackage {
  id: number;
  schema_version: string;
  crawl_status: string;
  page_count: number;
  crawl_time: string | null;
  candidate_group_id?: number | null;
  crawl_task_run_id?: number | null;
  crawl_result_id?: number | null;
  content_hash?: string;
  payload_stored?: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface CountrySignal {
  id: number;
  country: string;
  signal_type: string;
  confidence: number;
  evidence: string;
  source: string;
  created_at: string | null;
}

export interface SearchResultSummary {
  id: number;
  keyword: string;
  title: string;
  website: string;
  source_url: string;
  engine: string;
  country: string;
  industry: string;
  source_file: string;
  created_at: string | null;
}

export interface CrawlResultSummary {
  id: number;
  company_name: string;
  website: string;
  status: string;
  description: string;
  possible_address: string;
  country: string;
  industry: string;
  source_file: string;
  created_at: string | null;
}

export interface QualifiedLeadSummary {
  id: number;
  priority: string;
  status: string;
  segment: string;
  source: string;
  notes: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface CompanyProfileSummary {
  id: number;
  business_type: string;
  product_fit: string;
  market_role: string;
  summary: string;
  evidence: string;
  source: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface LeadScoreSummary {
  id: number;
  score_name: string;
  score_value: number;
  reason: string;
  source: string;
  created_at: string | null;
}

export interface StageACompany {
  domain: DomainSummary;
  search_result_count: number;
  latest_search: SearchResultSummary | null;
  countries: string[];
}

export interface StageBCompany {
  domain: DomainSummary;
  latest_crawl: CrawlResultSummary | null;
  contact_count: number;
  profile_package_count: number;
  countries: string[];
}

export interface StageCCompany {
  domain: DomainSummary;
  qualified_lead: QualifiedLeadSummary | null;
  company_profile: CompanyProfileSummary | null;
  scores: LeadScoreSummary[];
}

export interface StageCompanyListResponse<T> {
  items: T[];
  count: number;
  total: number;
  limit: number;
  offset: number;
}

export interface DomainDetail {
  domain: DomainSummary;
  contacts: Contact[];
  profile_packages: ProfilePackage[];
  country_signals: CountrySignal[];
}

export interface RuntimeInfo {
  task_execution_mode: "inline" | "celery";
}

export interface TaskItemRecord {
  id: number;
  task_run_id: number;
  item_type: string;
  item_key: string;
  domain_id?: number | null;
  status: string;
  attempt_count: number;
  error: string;
  result_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface TaskRunRecord {
  id: number;
  task_type: string;
  name: string;
  status: string;
  params_json: Record<string, unknown>;
  summary_json: Record<string, unknown>;
  created_by: string;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  item_counts: Record<string, number>;
  items?: TaskItemRecord[];
}

export interface TaskRunListResponse {
  items: TaskRunRecord[];
  count: number;
  total: number;
  limit: number;
  offset: number;
}

export interface CandidateGroupItemRecord {
  id: number;
  group_id: number;
  domain: DomainSummary;
  search_result: Partial<SearchResultSummary>;
  status: string;
  rank: number;
  has_crawl_result: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface CandidateGroupRecord {
  id: number;
  name: string;
  group_type: string;
  source_task_run_id?: number | null;
  keyword_group_id?: number | null;
  country: string;
  status: string;
  params_json: Record<string, unknown>;
  item_count: number;
  crawled_count: number;
  uncrawled_count: number;
  created_at: string | null;
  updated_at: string | null;
  items?: CandidateGroupItemRecord[];
}

export interface CandidateGroupListResponse {
  items: CandidateGroupRecord[];
  count: number;
  total: number;
  limit: number;
  offset: number;
}

export interface ProfileSourceGroup {
  id: number;
  task_run_id: number;
  name: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  candidate_group_id: number | null;
  candidate_group_name: string;
  country: string;
  profile_package_count: number;
  ai_profile_count: number;
  pending_profile_count: number;
  domain_count: number;
  profile_package_ids: number[];
}

export interface ProfileSourceGroupListResponse {
  items: ProfileSourceGroup[];
  count: number;
  total: number;
  limit: number;
  offset: number;
}

export interface SearchTaskRequest {
  keyword_group_id?: number;
  config_path?: string;
  output_file?: string;
  state_dir?: string;
  engines?: string;
  backend?: string;
  max_pages?: number;
  limit_keywords?: number;
  keyword_delay_seconds?: number;
  engine_request_delay_seconds?: number;
  retry_failed?: boolean;
  persist_to_database?: boolean;
}

export interface CrawlTaskRequest {
  candidate_group_id?: number;
  input_file?: string;
  output_file?: string;
  state_dir?: string;
  backend?: string;
  workers?: number;
  max_depth?: number;
  max_pages_per_site?: number;
  profile_input_dir?: string;
  profile_page_char_limit?: number;
  max_retries?: number;
  backoff_base?: number;
  backoff_max?: number;
  global_delay?: number;
  domain_delay?: number;
  proxy?: string;
  use_system_proxy?: boolean;
  headless?: boolean;
  browser_max_pages?: number;
  browser_timeout_ms?: number;
  browser_wait_ms?: number;
  retry_failed?: boolean;
  persist_to_database?: boolean;
  candidate_country?: string;
  candidate_query?: string;
  candidate_limit?: number;
  recrawl_existing?: boolean;
}

export interface AIProfileTaskRequest {
  profile_package_ids?: string | number[];
  profile_source_group_id?: number;
  model_provider?: string;
  api_base_url?: string;
  api_key?: string;
  model_name?: string;
  temperature?: number;
  timeout_seconds?: number;
  persist_to_database?: boolean;
}

export interface InlineTaskResponse {
  task_type: string;
  status: "success" | "failed";
  params: Record<string, unknown>;
  summary: Record<string, unknown>;
  started_at: string;
  finished_at: string;
  duration_seconds: number;
  error: string;
}

export interface QueuedTaskResponse {
  task_id: string;
  task_type: string;
  status: "queued";
}

export type TaskStartResponse = InlineTaskResponse | QueuedTaskResponse;

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  result: InlineTaskResponse | null;
}
