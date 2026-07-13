import type {
  CandidateGroupListResponse,
  CandidateGroupRecord,
  AIProfileTaskRequest,
  CrawlTaskRequest,
  CompanyLibraryStats,
  DatabaseStats,
  DomainDetail,
  DomainListResponse,
  KeywordGroup,
  KeywordGroupPayload,
  ProfileSourceGroupListResponse,
  RawAIProfileResultRow,
  RawCrawlResultRow,
  RawDomainRow,
  RawSearchResultRow,
  RawTableListResponse,
  RuntimeInfo,
  SearchTaskRequest,
  StageACompany,
  StageBCompany,
  StageCCompany,
  StageCompanyListResponse,
  TaskStartResponse,
  TaskStatusResponse,
  TaskRunListResponse,
  TaskRunRecord,
} from "./types";

const defaultApiBaseUrl = "http://127.0.0.1:8000";

export const apiBaseUrl = String(import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl).replace(/\/$/, "");

export interface DomainQuery {
  q: string;
  country: string;
  status: string;
  limit: number;
  offset: number;
}

export interface CompanyLibraryQuery {
  q: string;
  country: string;
  status?: string;
  limit: number;
  offset: number;
}

export interface RawTableQuery {
  q: string;
  country?: string;
  status?: string;
  engine?: string;
  keyword?: string;
  priority?: string;
  model_name?: string;
  prompt_version?: string;
  limit: number;
  offset: number;
}

export async function fetchStats(): Promise<DatabaseStats> {
  return requestJson<DatabaseStats>("/database/stats");
}

export async function fetchRuntime(): Promise<RuntimeInfo> {
  return requestJson<RuntimeInfo>("/runtime");
}

export async function fetchTaskRuns(query: { limit: number; offset: number; task_type?: string; status?: string }): Promise<TaskRunListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  if (query.task_type?.trim()) params.set("task_type", query.task_type.trim());
  if (query.status?.trim()) params.set("status", query.status.trim());
  return requestJson<TaskRunListResponse>(`/task-runs?${params.toString()}`);
}

export async function fetchTaskRunDetail(id: number): Promise<TaskRunRecord> {
  return requestJson<TaskRunRecord>(`/task-runs/${id}`);
}

export async function exportTaskRunResultsXlsx(id: number): Promise<{ blob: Blob; filename: string }> {
  const response = await fetch(`${apiBaseUrl}/task-runs/${id}/results/export.xlsx`);
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return {
    blob: await response.blob(),
    filename: filenameFromContentDisposition(response.headers.get("content-disposition")) || `crawl-task-${id}-results.xlsx`,
  };
}

export async function exportSelectedRawCrawlResultsXlsx(ids: number[]): Promise<{ blob: Blob; filename: string }> {
  const params = new URLSearchParams();
  params.set("ids", ids.join(","));
  const response = await fetch(`${apiBaseUrl}/raw-tables/crawl-results/export.xlsx?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return {
    blob: await response.blob(),
    filename: filenameFromContentDisposition(response.headers.get("content-disposition")) || "crawl-results-selected.xlsx",
  };
}

export async function cancelTaskRun(id: number): Promise<TaskRunRecord> {
  return requestJson<TaskRunRecord>(`/task-runs/${id}/cancel`, {
    method: "POST",
  });
}

export async function fetchCandidateGroups(query: { limit: number; offset: number; status?: string }): Promise<CandidateGroupListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  if (query.status?.trim()) params.set("status", query.status.trim());
  return requestJson<CandidateGroupListResponse>(`/candidate-groups?${params.toString()}`);
}

export async function fetchCandidateGroupDetail(id: number): Promise<CandidateGroupRecord> {
  return requestJson<CandidateGroupRecord>(`/candidate-groups/${id}`);
}

export async function fetchProfileSourceGroups(query: { limit: number; offset: number; q?: string }): Promise<ProfileSourceGroupListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  if (query.q?.trim()) params.set("q", query.q.trim());
  return requestJson<ProfileSourceGroupListResponse>(`/profile-source-groups?${params.toString()}`);
}

export async function fetchKeywordGroups(): Promise<KeywordGroup[]> {
  return requestJson<KeywordGroup[]>("/keyword-groups");
}

export async function createKeywordGroup(payload: KeywordGroupPayload): Promise<KeywordGroup> {
  return requestJson<KeywordGroup>("/keyword-groups", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateKeywordGroup(id: number, payload: Partial<KeywordGroupPayload>): Promise<KeywordGroup> {
  return requestJson<KeywordGroup>(`/keyword-groups/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteKeywordGroup(id: number): Promise<{ deleted: boolean }> {
  return requestJson<{ deleted: boolean }>(`/keyword-groups/${id}`, {
    method: "DELETE",
  });
}

export async function fetchCompanyLibraryStats(): Promise<CompanyLibraryStats> {
  return requestJson<CompanyLibraryStats>("/company-library/stats");
}

export async function fetchStageACompanies(query: CompanyLibraryQuery): Promise<StageCompanyListResponse<StageACompany>> {
  return requestJson<StageCompanyListResponse<StageACompany>>(`/company-library/stage-a?${companyLibraryParams(query).toString()}`);
}

export async function fetchStageBCompanies(query: CompanyLibraryQuery): Promise<StageCompanyListResponse<StageBCompany>> {
  return requestJson<StageCompanyListResponse<StageBCompany>>(`/company-library/stage-b?${companyLibraryParams(query).toString()}`);
}

export async function fetchStageCCompanies(query: CompanyLibraryQuery): Promise<StageCompanyListResponse<StageCCompany>> {
  return requestJson<StageCompanyListResponse<StageCCompany>>(`/company-library/stage-c?${companyLibraryParams(query).toString()}`);
}

export async function fetchDomains(query: DomainQuery): Promise<DomainListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  if (query.q.trim()) params.set("q", query.q.trim());
  if (query.country.trim()) params.set("country", query.country.trim());
  if (query.status.trim()) params.set("status", query.status.trim());
  return requestJson<DomainListResponse>(`/domains?${params.toString()}`);
}

export async function fetchDomainDetail(domain: string): Promise<DomainDetail> {
  return requestJson<DomainDetail>(`/domains/${encodeURIComponent(domain)}`);
}

export async function fetchRawDomains(query: RawTableQuery): Promise<RawTableListResponse<RawDomainRow>> {
  return requestJson<RawTableListResponse<RawDomainRow>>(`/raw-tables/domains?${rawTableParams(query).toString()}`);
}

export async function fetchRawSearchResults(query: RawTableQuery): Promise<RawTableListResponse<RawSearchResultRow>> {
  return requestJson<RawTableListResponse<RawSearchResultRow>>(`/raw-tables/search-results?${rawTableParams(query).toString()}`);
}

export async function fetchRawCrawlResults(query: RawTableQuery): Promise<RawTableListResponse<RawCrawlResultRow>> {
  return requestJson<RawTableListResponse<RawCrawlResultRow>>(`/raw-tables/crawl-results?${rawTableParams(query).toString()}`);
}

export async function fetchRawAIProfileResults(query: RawTableQuery): Promise<RawTableListResponse<RawAIProfileResultRow>> {
  return requestJson<RawTableListResponse<RawAIProfileResultRow>>(`/raw-tables/ai-profile-results?${rawTableParams(query).toString()}`);
}

export async function startSearchTask(payload: SearchTaskRequest): Promise<TaskStartResponse> {
  return requestJson<TaskStartResponse>("/tasks/search", {
    method: "POST",
    body: JSON.stringify(cleanPayload(payload)),
  });
}

export async function startCrawlTask(payload: CrawlTaskRequest): Promise<TaskStartResponse> {
  return requestJson<TaskStartResponse>("/tasks/crawl", {
    method: "POST",
    body: JSON.stringify(cleanPayload(payload)),
  });
}

export async function startAIProfileTask(payload: AIProfileTaskRequest): Promise<TaskStartResponse> {
  return requestJson<TaskStartResponse>("/tasks/ai-profile", {
    method: "POST",
    body: JSON.stringify(cleanPayload(payload)),
  });
}

export async function fetchTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  return requestJson<TaskStatusResponse>(`/tasks/${encodeURIComponent(taskId)}`);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return (await response.json()) as T;
}

function filenameFromContentDisposition(value: string | null): string {
  const match = value?.match(/filename="?([^";]+)"?/i);
  return match?.[1] || "";
}

function cleanPayload(payload: object): Record<string, unknown> {
  const cleaned: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(payload)) {
    if (value === "" || value === undefined || value === null) {
      continue;
    }
    if (Array.isArray(value) && value.length === 0) {
      continue;
    }
    cleaned[key] = value;
  }
  return cleaned;
}

function companyLibraryParams(query: CompanyLibraryQuery): URLSearchParams {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  if (query.q.trim()) params.set("q", query.q.trim());
  if (query.country.trim()) params.set("country", query.country.trim());
  if (query.status?.trim()) params.set("status", query.status.trim());
  return params;
}

function rawTableParams(query: RawTableQuery): URLSearchParams {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  if (query.q.trim()) params.set("q", query.q.trim());
  if (query.country?.trim()) params.set("country", query.country.trim());
  if (query.status?.trim()) params.set("status", query.status.trim());
  if (query.engine?.trim()) params.set("engine", query.engine.trim());
  if (query.keyword?.trim()) params.set("keyword", query.keyword.trim());
  if (query.priority?.trim()) params.set("priority", query.priority.trim());
  if (query.model_name?.trim()) params.set("model_name", query.model_name.trim());
  if (query.prompt_version?.trim()) params.set("prompt_version", query.prompt_version.trim());
  return params;
}
