<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Database,
  Download,
  ExternalLink,
  FileJson,
  Flag,
  Globe2,
  Loader2,
  Mail,
  PanelLeftClose,
  PanelLeftOpen,
  Phone,
  Plus,
  PlayCircle,
  RefreshCw,
  Save,
  Search,
  ListChecks,
  Trash2,
  Users,
  XCircle,
} from "@lucide/vue";
import {
  cancelTaskRun,
  createKeywordGroup,
  deleteKeywordGroup,
  fetchCandidateGroupDetail,
  fetchCandidateGroups,
  fetchCompanyLibraryStats,
  fetchDomainDetail,
  fetchDomains,
  fetchKeywordGroups,
  fetchProfileSourceGroups,
  fetchRawAIProfileResults,
  fetchRawCrawlResults,
  fetchRawDomains,
  fetchRawSearchResults,
  fetchRuntime,
  fetchStageACompanies,
  fetchStageBCompanies,
  fetchStageCCompanies,
  fetchStats,
  fetchTaskRunDetail,
  fetchTaskRuns,
  fetchTaskStatus,
  startAIProfileTask,
  startCrawlTask,
  startSearchTask,
  updateKeywordGroup,
  exportSelectedRawCrawlResultsXlsx,
} from "./api";
import type {
  CandidateGroupRecord,
  AIProfileTaskRequest,
  CompanyLibraryStats,
  Contact,
  CrawlTaskRequest,
  DatabaseStats,
  DomainDetail,
  DomainSummary,
  KeywordGroup,
  KeywordGroupPayload,
  ProfileSourceGroup,
  RawAIProfileResultRow,
  RawCrawlResultRow,
  RawDomainRow,
  RawSearchResultRow,
  RuntimeInfo,
  SearchTaskRequest,
  StageACompany,
  StageBCompany,
  StageCCompany,
  TaskStartResponse,
  TaskStatusResponse,
  TaskItemRecord,
  TaskRunRecord,
} from "./types";

type ProgressTaskType = "search" | "crawl" | "ai_profile";
type RawTableKey = "domains" | "search_results" | "crawl_results";
type RawTableRow = RawDomainRow | RawSearchResultRow | RawCrawlResultRow;

interface RawTableColumn {
  key: string;
  label: string;
}

type AIProfileSelectionMode = "filtered" | "manual";

interface AIProfileReportSection {
  key: string;
  label: string;
  content: unknown;
}

const runtime = ref<RuntimeInfo | null>(null);
const stats = ref<DatabaseStats | null>(null);
const libraryStats = ref<CompanyLibraryStats | null>(null);
const keywordGroups = ref<KeywordGroup[]>([]);
const selectedKeywordGroupId = ref<number | null>(null);
const taskRuns = ref<TaskRunRecord[]>([]);
const selectedTaskRun = ref<TaskRunRecord | null>(null);
const candidateGroups = ref<CandidateGroupRecord[]>([]);
const selectedCandidateGroup = ref<CandidateGroupRecord | null>(null);
const profileSourceGroups = ref<ProfileSourceGroup[]>([]);
const domains = ref<DomainSummary[]>([]);
const stageACompanies = ref<StageACompany[]>([]);
const stageBCompanies = ref<StageBCompany[]>([]);
const stageCCompanies = ref<StageCCompany[]>([]);
const rawDomainRows = ref<RawDomainRow[]>([]);
const rawSearchResultRows = ref<RawSearchResultRow[]>([]);
const rawCrawlResultRows = ref<RawCrawlResultRow[]>([]);
const selectedRawCrawlResultIds = ref<number[]>([]);
const rawAIProfileResultRows = ref<RawAIProfileResultRow[]>([]);
const selectedAIProfileResultId = ref<number | null>(null);
const aiProfilePreviewOpen = ref(false);
const selectedAIProfileRows = ref<Record<number, RawAIProfileResultRow>>({});
const aiProfileFilteredSelectionActive = ref(false);
const exportingAIProfiles = ref(false);
const selectedDetail = ref<DomainDetail | null>(null);
const selectedDomain = ref("");
const total = ref(0);
const libraryTotal = ref(0);
const rawTableTotal = ref(0);
const aiProfileTotal = ref(0);
const loadingRuntime = ref(false);
const loadingStats = ref(false);
const loadingLibrary = ref(false);
const loadingRawTable = ref(false);
const loadingAIProfiles = ref(false);
const loadingKeywordGroups = ref(false);
const loadingTaskRuns = ref(false);
const loadingTaskRunDetail = ref(false);
const loadingCandidateGroups = ref(false);
const loadingCandidateGroupDetail = ref(false);
const loadingProfileSourceGroups = ref(false);
const savingKeywordGroup = ref(false);
const loadingDomains = ref(false);
const loadingDetail = ref(false);
const taskSubmitting = ref(false);
const cancellingTaskRunId = ref<number | null>(null);
const exportingTaskRunResults = ref(false);
const errorMessage = ref("");
const taskMessage = ref("");
const selectedTask = ref<ProgressTaskType>("crawl");
const selectedLibraryStage = ref<"stageA" | "stageB" | "stageC">("stageA");
const selectedRawTable = ref<RawTableKey>("domains");
const activeModule = ref<"tasks" | "library" | "rawTables" | "aiProfiles" | "keywords" | "candidateGroups" | "taskCenter" | "customers">("tasks");
const sidebarCollapsed = ref(false);
const latestTaskResponse = ref<TaskStartResponse | null>(null);
const latestTaskStatus = ref<TaskStatusResponse | null>(null);
let taskPollHandle: number | undefined;
const activeTaskProgress = ref<TaskRunRecord | null>(null);
const progressPollingTaskType = ref<ProgressTaskType | null>(null);
let taskRunProgressPollHandle: number | undefined;

const filters = reactive({
  q: "",
  country: "",
  status: "",
  limit: 20,
  offset: 0,
});

const libraryFilters = reactive({
  q: "",
  country: "",
  status: "",
  limit: 20,
  offset: 0,
});

const rawTableFilters = reactive({
  q: "",
  country: "",
  status: "",
  engine: "",
  keyword: "",
  limit: 100,
  offset: 0,
});

const aiProfileFilters = reactive({
  q: "",
  status: "",
  priority: "",
  model_name: "",
  limit: 100,
  offset: 0,
});
const aiProfileDirectoryPageSizeOptions = [100, 300, 500];
const rawTablePageSizeOptions = [100, 300, 500];

const taskRunFilters = reactive({
  task_type: "",
  status: "",
  limit: 20,
  offset: 0,
});

const candidateGroupFilters = reactive({
  status: "active",
  limit: 20,
  offset: 0,
});

const defaultSearchTemplates = "{product} {role} {country}\n{product} {role} in {country}";

const statusOptions = [
  { label: "全部状态", value: "" },
  { label: "已抓取", value: "success" },
  { label: "空结果", value: "empty" },
  { label: "失败", value: "failed" },
  { label: "异常", value: "error" },
];

const taskTabs = [
  { label: "找官网", value: "search", icon: Search },
  { label: "抓官网", value: "crawl", icon: Globe2 },
  { label: "AI画像", value: "ai_profile", icon: FileJson },
] as const;

const libraryTabs = [
  { label: "官网候选库 A", value: "stageA", description: "搜索发现但未必抓取的官网候选" },
  { label: "抓取画像库 B", value: "stageB", description: "已抓官网并沉淀联系方式和画像素材" },
  { label: "优先客户库 C", value: "stageC", description: "后续 AI / 人工确认后的高价值客户" },
] as const;

const rawTableTabs = [
  { label: "域名主档", value: "domains" },
  { label: "搜索证据", value: "search_results" },
  { label: "抓取结果", value: "crawl_results" },
] as const;

const rawTableColumns: Record<RawTableKey, RawTableColumn[]> = {
  domains: [
    { key: "id", label: "ID" },
    { key: "domain", label: "域名" },
    { key: "website", label: "官网地址" },
    { key: "display_name", label: "显示名称" },
    { key: "description", label: "描述" },
    { key: "latest_status", label: "最新状态" },
    { key: "created_at", label: "创建时间" },
    { key: "updated_at", label: "更新时间" },
  ],
  search_results: [
    { key: "id", label: "ID" },
    { key: "domain_id", label: "域名ID" },
    { key: "domain", label: "关联域名" },
    { key: "keyword", label: "搜索关键词" },
    { key: "title", label: "结果标题" },
    { key: "website", label: "结果官网" },
    { key: "source_url", label: "来源URL" },
    { key: "engine", label: "搜索引擎" },
    { key: "country", label: "目标国家" },
    { key: "country_term", label: "国家词" },
    { key: "industry", label: "行业" },
    { key: "industry_term", label: "行业词" },
    { key: "matched_keywords", label: "匹配关键词" },
    { key: "matched_countries", label: "匹配国家" },
    { key: "matched_industries", label: "匹配行业" },
    { key: "matched_industry_terms", label: "匹配行业词" },
    { key: "source_file", label: "来源标记" },
    { key: "created_at", label: "创建时间" },
  ],
  crawl_results: [
    { key: "id", label: "ID" },
    { key: "domain_id", label: "域名ID" },
    { key: "domain", label: "关联域名" },
    { key: "keyword", label: "搜索关键词" },
    { key: "company_name", label: "公司名称" },
    { key: "website", label: "官网地址" },
    { key: "emails", label: "邮箱" },
    { key: "phones", label: "电话" },
    { key: "possible_address", label: "可能地址" },
    { key: "description", label: "描述" },
    { key: "crawled_pages", label: "已抓页面" },
    { key: "status", label: "抓取状态" },
    { key: "error", label: "错误信息" },
    { key: "social_links", label: "社交链接" },
    { key: "contacts", label: "联系方式文本" },
    { key: "page_categories", label: "页面分类" },
    { key: "country", label: "国家" },
    { key: "industry", label: "行业" },
    { key: "matched_keywords", label: "匹配关键词" },
    { key: "matched_countries", label: "匹配国家" },
    { key: "matched_industries", label: "匹配行业" },
    { key: "matched_industry_terms", label: "匹配行业词" },
    { key: "source_file", label: "来源标记" },
    { key: "created_at", label: "创建时间" },
  ],
};

const navigationItems = [
  { label: "任务控制台", value: "tasks", icon: Activity },
  { label: "企业库", value: "library", icon: Database },
  { label: "AI画像分析", value: "aiProfiles", icon: FileJson },
  { label: "审计排错", value: "rawTables", icon: Database },
  { label: "候选组", value: "candidateGroups", icon: ListChecks },
  { label: "关键词配置中心", value: "keywords", icon: Search },
  { label: "任务中心", value: "taskCenter", icon: ListChecks },
  { label: "客户池", value: "customers", icon: Users },
] as const;

const searchEngineOptions = [
  { label: "DuckDuckGo", value: "duckduckgo" },
  { label: "Bing", value: "bing" },
  { label: "DuckDuckGo + Bing", value: "duckduckgo,bing" },
] as const;

const searchTask = reactive<SearchTaskRequest>({
  keyword_group_id: undefined,
  engines: "duckduckgo",
  backend: "requests",
  max_pages: 1,
  keyword_delay_seconds: 10,
  engine_request_delay_seconds: 5,
  retry_failed: false,
});

const keywordForm = reactive<KeywordGroupPayload>({
  name: "",
  country: "",
  country_terms: "",
  keyword_terms: "",
  product_terms: "",
  role_terms: "",
  search_templates: defaultSearchTemplates,
  notes: "",
  is_active: true,
});

const crawlTask = reactive<CrawlTaskRequest>({
  candidate_group_id: undefined,
  backend: "requests",
  workers: 3,
  max_depth: 2,
  max_pages_per_site: 12,
  profile_page_char_limit: 8000,
  max_retries: 2,
  backoff_base: 1,
  backoff_max: 30,
  global_delay: 1,
  domain_delay: 3,
  proxy: "",
  use_system_proxy: true,
  headless: true,
  browser_timeout_ms: 30000,
  browser_wait_ms: 0,
  browser_max_pages: 1,
  retry_failed: false,
  candidate_country: "France",
  candidate_query: "",
  candidate_limit: 20,
  recrawl_existing: false,
});

const crawlPresetOptions = [
  {
    label: "标准",
    description: "3并发 · 深度2 · 12页",
    workers: 3,
    max_depth: 2,
    max_pages_per_site: 12,
    candidate_limit: 20,
    global_delay: 1,
    domain_delay: 3,
    max_retries: 2,
    backoff_base: 1,
    backoff_max: 30,
  },
  {
    label: "保守",
    description: "2并发 · 深度1 · 8页",
    workers: 2,
    max_depth: 1,
    max_pages_per_site: 8,
    candidate_limit: 20,
    global_delay: 2,
    domain_delay: 5,
    max_retries: 2,
    backoff_base: 2,
    backoff_max: 45,
  },
  {
    label: "深挖",
    description: "2并发 · 深度3 · 18页",
    workers: 2,
    max_depth: 3,
    max_pages_per_site: 18,
    candidate_limit: 10,
    global_delay: 1.5,
    domain_delay: 4,
    max_retries: 3,
    backoff_base: 1,
    backoff_max: 45,
  },
] as const;

const aiProfileTask = reactive({
  profile_source_group_id: undefined as number | undefined,
  profile_package_ids_text: "",
  model_provider: "deepseek",
  api_base_url: "https://api.deepseek.com",
  api_key: "",
  model_name: "deepseek-v4-pro",
  temperature: 0.2,
  timeout_seconds: 180,
});

const metricCards = computed(() => {
  const value = stats.value;
  return [
    { label: "客户域名", value: value?.domains ?? 0, icon: Database },
    { label: "联系方式", value: value?.contacts ?? 0, icon: Users },
    { label: "画像素材包", value: value?.profile_packages ?? 0, icon: FileJson },
    { label: "国家信号", value: value?.country_signals ?? 0, icon: Flag },
  ];
});

const currentPage = computed(() => Math.floor(filters.offset / filters.limit) + 1);
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / filters.limit)));
const libraryCurrentPage = computed(() => Math.floor(libraryFilters.offset / libraryFilters.limit) + 1);
const libraryTotalPages = computed(() => Math.max(1, Math.ceil(libraryTotal.value / libraryFilters.limit)));
const rawTableCurrentPage = computed(() => Math.floor(rawTableFilters.offset / rawTableFilters.limit) + 1);
const rawTableTotalPages = computed(() => Math.max(1, Math.ceil(rawTableTotal.value / rawTableFilters.limit)));
const aiProfileCurrentPage = computed(() => Math.floor(aiProfileFilters.offset / aiProfileFilters.limit) + 1);
const aiProfileTotalPages = computed(() => Math.max(1, Math.ceil(aiProfileTotal.value / aiProfileFilters.limit)));
const taskRunCurrentPage = computed(() => Math.floor(taskRunFilters.offset / taskRunFilters.limit) + 1);
const taskRunTotalPages = computed(() => Math.max(1, Math.ceil(taskRunTotal.value / taskRunFilters.limit)));
const candidateGroupCurrentPage = computed(() => Math.floor(candidateGroupFilters.offset / candidateGroupFilters.limit) + 1);
const candidateGroupTotalPages = computed(() => Math.max(1, Math.ceil(candidateGroupTotal.value / candidateGroupFilters.limit)));
const canGoPrevious = computed(() => filters.offset > 0);
const canGoNext = computed(() => currentPage.value < totalPages.value);
const canLibraryGoPrevious = computed(() => libraryFilters.offset > 0);
const canLibraryGoNext = computed(() => libraryCurrentPage.value < libraryTotalPages.value);
const canRawTableGoPrevious = computed(() => rawTableFilters.offset > 0);
const canRawTableGoNext = computed(() => rawTableCurrentPage.value < rawTableTotalPages.value);
const canAIProfileGoPrevious = computed(() => aiProfileFilters.offset > 0);
const canAIProfileGoNext = computed(() => aiProfileCurrentPage.value < aiProfileTotalPages.value);
const canTaskRunGoPrevious = computed(() => taskRunFilters.offset > 0);
const canTaskRunGoNext = computed(() => taskRunCurrentPage.value < taskRunTotalPages.value);
const canCandidateGroupGoPrevious = computed(() => candidateGroupFilters.offset > 0);
const canCandidateGroupGoNext = computed(() => candidateGroupCurrentPage.value < candidateGroupTotalPages.value);
const runtimeText = computed(() => {
  if (runtime.value?.task_execution_mode === "celery") return "队列模式";
  if (runtime.value?.task_execution_mode === "inline") return "本机直跑";
  return "未连接";
});
const activeNavigationItem = computed(
  () => navigationItems.find((item) => item.value === activeModule.value) ?? navigationItems[0],
);
const selectedSearchKeywordGroup = computed(
  () => keywordGroups.value.find((group) => group.id === searchTask.keyword_group_id) ?? null,
);
const selectedSearchKeywordCountText = computed(() => {
  if (!selectedSearchKeywordGroup.value) return "请选择关键词组";
  return `${selectedSearchKeywordGroup.value.keyword_count} 个组合`;
});
const isCandidateFilterDisabled = computed(() => {
  const selectedGroupId = crawlTask.candidate_group_id;
  return typeof selectedGroupId === "number" && Number.isFinite(selectedGroupId);
});
const selectedCrawlCandidateGroup = computed(
  () => candidateGroups.value.find((group) => group.id === crawlTask.candidate_group_id) ?? null,
);
const selectedProfileSourceGroup = computed(
  () => profileSourceGroups.value.find((group) => group.id === aiProfileTask.profile_source_group_id) ?? null,
);
const hasAIProfileSourceGroup = computed(() => {
  const selectedGroupId = aiProfileTask.profile_source_group_id;
  return typeof selectedGroupId === "number" && Number.isFinite(selectedGroupId);
});
const hasAIProfilePackageIdsText = computed(() => Boolean(aiProfileTask.profile_package_ids_text.trim()));
const isAIProfileSourceGroupDisabled = computed(() => hasAIProfilePackageIdsText.value);
const isAIProfilePackageIdsDisabled = computed(() => hasAIProfileSourceGroup.value);
const crawlCandidateSourceText = computed(() => {
  if (selectedCrawlCandidateGroup.value) {
    const group = selectedCrawlCandidateGroup.value;
    return `${group.name || `候选组 #${group.id}`} · ${group.uncrawled_count}/${group.item_count} 未抓`;
  }
  const country = crawlTask.candidate_country || "未限定国家";
  const keyword = crawlTask.candidate_query ? ` · ${crawlTask.candidate_query}` : "";
  return `${country}${keyword}`;
});
const isBrowserMode = computed(() => crawlTask.backend === "browser");
const isRequestsMode = computed(() => crawlTask.backend === "requests");
const activeRawTableColumns = computed(() => rawTableColumns[selectedRawTable.value]);
const activeRawTableRows = computed<RawTableRow[]>(() => {
  if (selectedRawTable.value === "domains") return rawDomainRows.value;
  if (selectedRawTable.value === "search_results") return rawSearchResultRows.value;
  return rawCrawlResultRows.value;
});
const rawTableColumnSpan = computed(() => activeRawTableColumns.value.length + (selectedRawTable.value === "crawl_results" ? 1 : 0));
const selectedRawCrawlResultIdSet = computed(() => new Set(selectedRawCrawlResultIds.value));
const currentPageRawCrawlResultIds = computed(() => rawCrawlResultRows.value.map((row) => row.id));
const selectedRawCrawlResultCount = computed(() => selectedRawCrawlResultIds.value.length);
const allCurrentPageRawCrawlResultsSelected = computed(() => {
  const ids = currentPageRawCrawlResultIds.value;
  return ids.length > 0 && ids.every((id) => selectedRawCrawlResultIdSet.value.has(id));
});
const someCurrentPageRawCrawlResultsSelected = computed(() => {
  const ids = currentPageRawCrawlResultIds.value;
  return ids.some((id) => selectedRawCrawlResultIdSet.value.has(id));
});
const showRawCountryFilter = computed(() => selectedRawTable.value === "search_results" || selectedRawTable.value === "crawl_results");
const showRawStatusFilter = computed(() => selectedRawTable.value !== "search_results" && selectedRawTable.value !== "domains");
const showRawEngineFilter = computed(() => selectedRawTable.value === "search_results");
const showRawKeywordFilter = computed(() => selectedRawTable.value === "search_results" || selectedRawTable.value === "crawl_results");
const previewAIProfileResult = computed(() => {
  if (!aiProfilePreviewOpen.value || selectedAIProfileResultId.value === null) return null;
  return rawAIProfileResultRows.value.find((result) => result.id === selectedAIProfileResultId.value) ?? null;
});
const selectedAIProfileCount = computed(() =>
  aiProfileFilteredSelectionActive.value ? aiProfileTotal.value : Object.keys(selectedAIProfileRows.value).length,
);
const latestTaskResult = computed(() => latestTaskStatus.value?.result ?? (isInlineTaskResponse(latestTaskResponse.value) ? latestTaskResponse.value : null));
const taskStatusLabel = computed(() => latestTaskStatus.value?.status ?? latestTaskResponse.value?.status ?? "idle");
const taskStatusText = computed(() => statusText(taskStatusLabel.value));
const activeProgressItems = computed(() => activeTaskProgress.value?.items?.slice(-20).reverse() ?? []);
const progressCounts = computed(() => activeTaskProgress.value?.item_counts ?? {});
const progressTotal = computed(() => Object.values(progressCounts.value).reduce((total, count) => total + Number(count || 0), 0));
const progressCompleted = computed(() => {
  const pending = Number(progressCounts.value.pending || 0);
  const running = Number(progressCounts.value.running || 0);
  return Math.max(progressTotal.value - pending - running, 0);
});
const progressPercent = computed(() => {
  if (!progressTotal.value) return 0;
  return Math.round((progressCompleted.value / progressTotal.value) * 100);
});
const activeTaskCanCancel = computed(() => Boolean(activeTaskProgress.value && canCancelTaskRun(activeTaskProgress.value)));
const selectedTaskRunCanCancel = computed(() => Boolean(selectedTaskRun.value && canCancelTaskRun(selectedTaskRun.value)));

async function loadRuntime() {
  loadingRuntime.value = true;
  try {
    runtime.value = await fetchRuntime();
  } catch (error) {
    setError(error);
  } finally {
    loadingRuntime.value = false;
  }
}

async function loadStats() {
  loadingStats.value = true;
  try {
    stats.value = await fetchStats();
  } catch (error) {
    setError(error);
  } finally {
    loadingStats.value = false;
  }
}

async function loadCompanyLibraryStats() {
  try {
    libraryStats.value = await fetchCompanyLibraryStats();
  } catch (error) {
    setError(error);
  }
}

async function loadKeywordGroups() {
  loadingKeywordGroups.value = true;
  try {
    keywordGroups.value = await fetchKeywordGroups();
    if (keywordGroups.value.length > 0) {
      const activeSelection = keywordGroups.value.find((group) => group.id === selectedKeywordGroupId.value);
      selectKeywordGroup(activeSelection ?? keywordGroups.value[0]);
    } else {
      selectedKeywordGroupId.value = null;
      clearKeywordForm();
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingKeywordGroups.value = false;
  }
}

const taskRunTotal = ref(0);
const candidateGroupTotal = ref(0);

async function loadTaskRuns(resetPage = false) {
  if (resetPage) {
    taskRunFilters.offset = 0;
  }
  loadingTaskRuns.value = true;
  try {
    const response = await fetchTaskRuns({ ...taskRunFilters });
    taskRuns.value = response.items;
    taskRunTotal.value = response.total;
    if (response.items.length > 0) {
      const selectedStillVisible = response.items.some((run) => run.id === selectedTaskRun.value?.id);
      if (!selectedTaskRun.value || !selectedStillVisible) {
        await loadTaskRunDetail(response.items[0].id);
      }
    } else {
      selectedTaskRun.value = null;
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingTaskRuns.value = false;
  }
}

async function loadCandidateGroups(resetPage = false) {
  if (resetPage) {
    candidateGroupFilters.offset = 0;
  }
  loadingCandidateGroups.value = true;
  try {
    const response = await fetchCandidateGroups({ ...candidateGroupFilters });
    candidateGroups.value = response.items;
    candidateGroupTotal.value = response.total;
    if (response.items.length > 0) {
      const selectedStillVisible = response.items.some((group) => group.id === selectedCandidateGroup.value?.id);
      if (!selectedCandidateGroup.value || !selectedStillVisible) {
        await loadCandidateGroupDetail(response.items[0].id);
      }
      if (!crawlTask.candidate_group_id) {
        crawlTask.candidate_group_id = response.items[0].id;
      }
    } else {
      selectedCandidateGroup.value = null;
      crawlTask.candidate_group_id = undefined;
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingCandidateGroups.value = false;
  }
}

async function loadCandidateGroupDetail(id: number) {
  loadingCandidateGroupDetail.value = true;
  try {
    selectedCandidateGroup.value = await fetchCandidateGroupDetail(id);
    crawlTask.candidate_group_id = id;
  } catch (error) {
    setError(error);
  } finally {
    loadingCandidateGroupDetail.value = false;
  }
}

async function loadProfileSourceGroups() {
  loadingProfileSourceGroups.value = true;
  try {
    const response = await fetchProfileSourceGroups({ limit: 50, offset: 0 });
    profileSourceGroups.value = response.items;
    const selectedStillVisible = response.items.some((group) => group.id === aiProfileTask.profile_source_group_id);
    if (!selectedStillVisible) {
      aiProfileTask.profile_source_group_id = undefined;
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingProfileSourceGroups.value = false;
  }
}

async function loadTaskRunDetail(id: number) {
  loadingTaskRunDetail.value = true;
  try {
    selectedTaskRun.value = await fetchTaskRunDetail(id);
  } catch (error) {
    setError(error);
  } finally {
    loadingTaskRunDetail.value = false;
  }
}

async function openTaskRunResults(taskRun: TaskRunRecord) {
  if (!canViewTaskRunResults(taskRun)) return;
  errorMessage.value = "";
  clearRawCrawlResultSelection();
  selectedRawTable.value = "crawl_results";
  rawTableFilters.q = `task:crawl:${taskRun.id}`;
  rawTableFilters.country = "";
  rawTableFilters.status = "";
  rawTableFilters.engine = "";
  rawTableFilters.keyword = "";
  rawTableFilters.offset = 0;
  activeModule.value = "rawTables";
  await loadRawTable(true);
  selectCurrentPageRawCrawlResults();
}

async function loadCompanyLibrary(resetPage = false) {
  if (resetPage) {
    libraryFilters.offset = 0;
  }
  loadingLibrary.value = true;
  try {
    const query = { ...libraryFilters };
    if (selectedLibraryStage.value === "stageA") {
      const response = await fetchStageACompanies(query);
      stageACompanies.value = response.items;
      libraryTotal.value = response.total;
    } else if (selectedLibraryStage.value === "stageB") {
      const response = await fetchStageBCompanies(query);
      stageBCompanies.value = response.items;
      libraryTotal.value = response.total;
    } else {
      const response = await fetchStageCCompanies(query);
      stageCCompanies.value = response.items;
      libraryTotal.value = response.total;
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingLibrary.value = false;
  }
}

async function loadRawTable(resetPage = false) {
  if (resetPage) {
    rawTableFilters.offset = 0;
  }
  loadingRawTable.value = true;
  try {
    const query = { ...rawTableFilters };
    if (selectedRawTable.value === "domains") {
      const response = await fetchRawDomains(query);
      rawDomainRows.value = response.items;
      rawTableTotal.value = response.total;
    } else if (selectedRawTable.value === "search_results") {
      const response = await fetchRawSearchResults(query);
      rawSearchResultRows.value = response.items;
      rawTableTotal.value = response.total;
    } else if (selectedRawTable.value === "crawl_results") {
      const response = await fetchRawCrawlResults(query);
      rawCrawlResultRows.value = response.items;
      rawTableTotal.value = response.total;
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingRawTable.value = false;
  }
}

async function loadAIProfileResults(resetPage = false) {
  if (resetPage) {
    aiProfileFilters.offset = 0;
  }
  loadingAIProfiles.value = true;
  try {
    const response = await fetchRawAIProfileResults({ ...aiProfileFilters });
    rawAIProfileResultRows.value = response.items;
    aiProfileTotal.value = response.total;
    if (!response.items.some((item) => item.id === selectedAIProfileResultId.value)) {
      selectedAIProfileResultId.value = response.items[0]?.id ?? null;
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingAIProfiles.value = false;
  }
}

async function loadDomains(resetPage = false) {
  if (resetPage) {
    filters.offset = 0;
    selectedDomain.value = "";
    selectedDetail.value = null;
  }
  loadingDomains.value = true;
  try {
    const response = await fetchDomains(filters);
    domains.value = response.items;
    total.value = response.total;
    const selectionStillVisible = response.items.some((domain) => domain.domain === selectedDomain.value);
    if ((!selectedDomain.value || !selectionStillVisible) && response.items.length > 0) {
      await loadDomainDetail(response.items[0].domain);
    } else if (response.items.length === 0) {
      selectedDomain.value = "";
      selectedDetail.value = null;
    }
  } catch (error) {
    setError(error);
  } finally {
    loadingDomains.value = false;
  }
}

async function loadDomainDetail(domain: string) {
  selectedDomain.value = domain;
  loadingDetail.value = true;
  try {
    selectedDetail.value = await fetchDomainDetail(domain);
  } catch (error) {
    setError(error);
  } finally {
    loadingDetail.value = false;
  }
}

function openDomainDetail(domain: string) {
  activeModule.value = "customers";
  void loadDomainDetail(domain);
}

function applyCrawlPreset(preset: (typeof crawlPresetOptions)[number]) {
  crawlTask.workers = preset.workers;
  crawlTask.max_depth = preset.max_depth;
  crawlTask.max_pages_per_site = preset.max_pages_per_site;
  crawlTask.candidate_limit = preset.candidate_limit;
  crawlTask.global_delay = preset.global_delay;
  crawlTask.domain_delay = preset.domain_delay;
  crawlTask.max_retries = preset.max_retries;
  crawlTask.backoff_base = preset.backoff_base;
  crawlTask.backoff_max = preset.backoff_max;
}

async function refreshAll() {
  errorMessage.value = "";
  await Promise.all([
    loadRuntime(),
    loadStats(),
    loadKeywordGroups(),
    loadTaskRuns(),
    loadCandidateGroups(),
    loadProfileSourceGroups(),
    loadCompanyLibraryStats(),
    loadCompanyLibrary(),
    loadRawTable(),
    loadAIProfileResults(),
    loadDomains(),
  ]);
}

async function initializeDashboard() {
  await refreshAll();
  await restoreActiveTaskProgressAfterRefresh();
}

async function restoreActiveTaskProgressAfterRefresh() {
  try {
    const response = await fetchTaskRuns({ limit: 1, offset: 0, status: "running" });
    const restoredTaskRun = response.items[0];
    const restoredTaskType = progressTaskTypeFromTaskRun(restoredTaskRun);
    if (!restoredTaskRun || !restoredTaskType) return;

    const detail = await fetchTaskRunDetail(restoredTaskRun.id);
    activeTaskProgress.value = detail;
    selectedTaskRun.value = detail;
    selectedTask.value = restoredTaskType;
    activeModule.value = "tasks";
    taskMessage.value = `已恢复正在执行的${taskTypeText(restoredTaskType)}任务 #${detail.id}`;
    startTaskRunProgressPolling(restoredTaskType);
    activeTaskProgress.value = detail;
  } catch (error) {
    setError(error);
  }
}

async function submitSelectedTask() {
  errorMessage.value = "";
  taskMessage.value = "";
  latestTaskResponse.value = null;
  latestTaskStatus.value = null;
  clearTaskPolling();
  const progressTaskType = progressTaskTypeForSelectedTask();
  if (progressTaskType) {
    startTaskRunProgressPolling(progressTaskType);
  } else {
    clearTaskRunProgressPolling();
    activeTaskProgress.value = null;
  }
  taskSubmitting.value = true;
  try {
    const response = await startSelectedTask();
    latestTaskResponse.value = response;
    if (isQueuedTaskResponse(response)) {
      taskMessage.value = `${taskTypeText(response.task_type)} 已进入队列：${response.task_id}`;
      startTaskPolling(response.task_id);
    } else {
      taskMessage.value = `${taskTypeText(response.task_type)}已结束：${statusText(response.status)}`;
      await loadTaskRunProgressFromTaskResponse(response);
      await refreshAll();
    }
  } catch (error) {
    clearTaskRunProgressPolling();
    setError(error);
  } finally {
    taskSubmitting.value = false;
  }
}

async function startSelectedTask(): Promise<TaskStartResponse> {
  if (selectedTask.value === "search") {
    if (!searchTask.keyword_group_id) {
      throw new Error("请先在关键词配置中心选择或保存一个关键词组");
    }
    return startSearchTask({
      keyword_group_id: searchTask.keyword_group_id,
      engines: searchTask.engines,
      backend: searchTask.backend,
      max_pages: searchTask.max_pages,
      keyword_delay_seconds: searchTask.keyword_delay_seconds,
      engine_request_delay_seconds: searchTask.engine_request_delay_seconds,
      retry_failed: searchTask.retry_failed,
    });
  }
  if (selectedTask.value === "crawl") {
    const payload: CrawlTaskRequest = {
      candidate_group_id: crawlTask.candidate_group_id,
      backend: crawlTask.backend,
      workers: crawlTask.workers,
      max_depth: crawlTask.max_depth,
      max_pages_per_site: crawlTask.max_pages_per_site,
      profile_page_char_limit: crawlTask.profile_page_char_limit,
      max_retries: crawlTask.max_retries,
      backoff_base: crawlTask.backoff_base,
      backoff_max: crawlTask.backoff_max,
      global_delay: crawlTask.global_delay,
      domain_delay: crawlTask.domain_delay,
      proxy: crawlTask.proxy,
      retry_failed: crawlTask.retry_failed,
      candidate_limit: crawlTask.candidate_limit,
      recrawl_existing: crawlTask.recrawl_existing,
    };
    if (isRequestsMode.value) {
      payload.use_system_proxy = crawlTask.use_system_proxy;
    }
    if (!isCandidateFilterDisabled.value) {
      payload.candidate_country = crawlTask.candidate_country;
      payload.candidate_query = crawlTask.candidate_query;
    }
    if (isBrowserMode.value) {
      payload.headless = crawlTask.headless;
      payload.browser_timeout_ms = crawlTask.browser_timeout_ms;
      payload.browser_wait_ms = crawlTask.browser_wait_ms;
      payload.browser_max_pages = crawlTask.browser_max_pages;
    }
    return startCrawlTask(payload);
  }
  if (selectedTask.value === "ai_profile") {
    const payload: AIProfileTaskRequest = {
      model_provider: aiProfileTask.model_provider,
      api_base_url: aiProfileTask.api_base_url,
      api_key: aiProfileTask.api_key,
      model_name: aiProfileTask.model_name,
      temperature: aiProfileTask.temperature,
      timeout_seconds: aiProfileTask.timeout_seconds,
    };
    if (hasAIProfileSourceGroup.value) {
      payload.profile_source_group_id = aiProfileTask.profile_source_group_id;
    } else if (hasAIProfilePackageIdsText.value) {
      payload.profile_package_ids = aiProfileTask.profile_package_ids_text;
    } else {
      throw new Error("请选择画像源数据组或填写画像包 ID");
    }
    return startAIProfileTask(payload);
  }
  throw new Error(`不支持的任务类型：${selectedTask.value}`);
}

function startTaskPolling(taskId: string) {
  void pollTaskStatus(taskId);
  taskPollHandle = window.setInterval(() => {
    void pollTaskStatus(taskId);
  }, 2500);
}

async function pollTaskStatus(taskId: string) {
  try {
    const status = await fetchTaskStatus(taskId);
    latestTaskStatus.value = status;
    if (["SUCCESS", "FAILURE", "REVOKED"].includes(status.status)) {
      clearTaskPolling();
      if (status.result) {
        taskMessage.value = `${taskTypeText(status.result.task_type)}已结束：${statusText(status.result.status)}`;
        await refreshAll();
      }
    }
  } catch (error) {
    clearTaskPolling();
    setError(error);
  }
}

function clearTaskPolling() {
  if (taskPollHandle !== undefined) {
    window.clearInterval(taskPollHandle);
    taskPollHandle = undefined;
  }
}

function progressTaskTypeForSelectedTask(): ProgressTaskType | null {
  return selectedTask.value;
}

function progressTaskTypeFromTaskRun(taskRun: TaskRunRecord | undefined): ProgressTaskType | null {
  if (!taskRun) return null;
  if (taskRun.task_type === "search" || taskRun.task_type === "crawl" || taskRun.task_type === "ai_profile") {
    return taskRun.task_type;
  }
  return null;
}

function startTaskRunProgressPolling(taskType: ProgressTaskType) {
  clearTaskRunProgressPolling();
  activeTaskProgress.value = null;
  progressPollingTaskType.value = taskType;
  void pollLatestTaskRunProgress(taskType);
  taskRunProgressPollHandle = window.setInterval(() => {
    void pollLatestTaskRunProgress(taskType);
  }, 2000);
}

async function pollLatestTaskRunProgress(taskType: ProgressTaskType) {
  try {
    let taskRunId = activeTaskProgress.value?.id;
    if (!taskRunId || !isTaskRunActive(activeTaskProgress.value?.status || "")) {
      const response = await fetchTaskRuns({ limit: 1, offset: 0, task_type: taskType, status: "running" });
      taskRunId = response.items[0]?.id;
    }
    if (!taskRunId) return;
    const detail = await fetchTaskRunDetail(taskRunId);
    activeTaskProgress.value = detail;
    if (!isTaskRunActive(detail.status)) {
      clearTaskRunProgressPolling();
    }
  } catch (error) {
    clearTaskRunProgressPolling();
    setError(error);
  }
}

async function loadTaskRunProgressFromTaskResponse(response: TaskStartResponse) {
  const taskRunId = taskRunIdFromResponse(response);
  if (taskRunId === null) return;
  try {
    activeTaskProgress.value = await fetchTaskRunDetail(taskRunId);
  } catch (error) {
    setError(error);
  } finally {
    clearTaskRunProgressPolling();
  }
}

function taskRunIdFromResponse(response: TaskStartResponse): number | null {
  if (!isInlineTaskResponse(response)) return null;
  const taskRunId = response.summary?.task_run_id;
  return typeof taskRunId === "number" ? taskRunId : null;
}

function clearTaskRunProgressPolling() {
  if (taskRunProgressPollHandle !== undefined) {
    window.clearInterval(taskRunProgressPollHandle);
    taskRunProgressPollHandle = undefined;
  }
  progressPollingTaskType.value = null;
}

function isTaskRunActive(status: string) {
  return status === "running" || status === "pending" || status === "cancelling";
}

function canCancelTaskRun(taskRun: TaskRunRecord) {
  return taskRun.status === "running" || taskRun.status === "pending";
}

function canViewTaskRunResults(taskRun: TaskRunRecord) {
  return taskRun.task_type === "crawl";
}

async function cancelActiveTaskRun() {
  if (!activeTaskProgress.value || !canCancelTaskRun(activeTaskProgress.value)) return;
  await cancelTaskRunById(activeTaskProgress.value.id);
}

async function cancelSelectedTaskRun() {
  if (!selectedTaskRun.value || !canCancelTaskRun(selectedTaskRun.value)) return;
  await cancelTaskRunById(selectedTaskRun.value.id);
}

async function cancelTaskRunById(taskRunId: number) {
  errorMessage.value = "";
  cancellingTaskRunId.value = taskRunId;
  try {
    const detail = await cancelTaskRun(taskRunId);
    if (activeTaskProgress.value?.id === taskRunId) {
      activeTaskProgress.value = detail;
    }
    if (selectedTaskRun.value?.id === taskRunId) {
      selectedTaskRun.value = detail;
    }
    taskMessage.value = `任务 #${taskRunId} 已请求取消`;
    await loadTaskRuns();
  } catch (error) {
    setError(error);
  } finally {
    cancellingTaskRunId.value = null;
  }
}

async function exportCurrentCrawlTaskResultsXlsx() {
  const selectedIds = selectedRawCrawlResultIds.value;
  if (selectedIds.length === 0) return;
  exportingTaskRunResults.value = true;
  errorMessage.value = "";
  try {
    const { blob, filename } = await exportSelectedRawCrawlResultsXlsx(selectedIds);
    downloadBlobFile(filename, blob);
  } catch (error) {
    setError(error);
  } finally {
    exportingTaskRunResults.value = false;
  }
}

function applyFilters() {
  errorMessage.value = "";
  void loadDomains(true);
}

function applyLibraryFilters() {
  errorMessage.value = "";
  void loadCompanyLibrary(true);
}

function applyRawTableFilters() {
  errorMessage.value = "";
  clearRawCrawlResultSelection();
  void loadRawTable(true);
}

function applyAIProfileFilters() {
  errorMessage.value = "";
  clearAIProfileSelection();
  void loadAIProfileResults(true);
}

function applyTaskRunFilters() {
  errorMessage.value = "";
  void loadTaskRuns(true);
}

function applyCandidateGroupFilters() {
  errorMessage.value = "";
  void loadCandidateGroups(true);
}

function setLibraryStage(stage: "stageA" | "stageB" | "stageC") {
  selectedLibraryStage.value = stage;
  void loadCompanyLibrary(true);
}

function setRawTable(table: RawTableKey) {
  selectedRawTable.value = table;
  clearRawCrawlResultSelection();
  void loadRawTable(true);
}

function setRawTablePageSize(event: Event) {
  const value = Number((event.target as HTMLSelectElement).value);
  if (!rawTablePageSizeOptions.includes(value)) return;
  rawTableFilters.limit = value;
  clearRawCrawlResultSelection();
  void loadRawTable(true);
}

function clearRawCrawlResultSelection() {
  selectedRawCrawlResultIds.value = [];
}

function selectCurrentPageRawCrawlResults() {
  if (selectedRawTable.value !== "crawl_results") return;
  const selectedIds = new Set(selectedRawCrawlResultIds.value);
  for (const id of currentPageRawCrawlResultIds.value) {
    selectedIds.add(id);
  }
  selectedRawCrawlResultIds.value = Array.from(selectedIds);
}

function toggleCurrentPageRawCrawlResults() {
  if (selectedRawTable.value !== "crawl_results") return;
  const pageIds = new Set(currentPageRawCrawlResultIds.value);
  if (allCurrentPageRawCrawlResultsSelected.value) {
    selectedRawCrawlResultIds.value = selectedRawCrawlResultIds.value.filter((id) => !pageIds.has(id));
    return;
  }
  selectCurrentPageRawCrawlResults();
}

function isRawCrawlResultSelected(row: RawTableRow) {
  const id = rawRowNumericId(row);
  return id !== null && selectedRawCrawlResultIdSet.value.has(id);
}

function toggleRawCrawlResultSelection(row: RawTableRow) {
  if (selectedRawTable.value !== "crawl_results") return;
  const id = rawRowNumericId(row);
  if (id === null) return;
  if (selectedRawCrawlResultIdSet.value.has(id)) {
    selectedRawCrawlResultIds.value = selectedRawCrawlResultIds.value.filter((selectedId) => selectedId !== id);
    return;
  }
  selectedRawCrawlResultIds.value = [...selectedRawCrawlResultIds.value, id];
}

function openAIProfilePreview(result: RawAIProfileResultRow) {
  selectedAIProfileResultId.value = result.id;
  aiProfilePreviewOpen.value = true;
}

function closeAIProfilePreview() {
  aiProfilePreviewOpen.value = false;
}

function isAIProfileSelected(result: RawAIProfileResultRow) {
  return aiProfileFilteredSelectionActive.value || Boolean(selectedAIProfileRows.value[result.id]);
}

function toggleAIProfileSelection(result: RawAIProfileResultRow) {
  if (aiProfileFilteredSelectionActive.value) {
    selectedAIProfileRows.value = Object.fromEntries(rawAIProfileResultRows.value.map((row) => [row.id, row]));
    aiProfileFilteredSelectionActive.value = false;
  }
  const nextRows = { ...selectedAIProfileRows.value };
  if (nextRows[result.id]) {
    delete nextRows[result.id];
  } else {
    nextRows[result.id] = result;
  }
  selectedAIProfileRows.value = nextRows;
}

function selectAllFilteredAIProfiles() {
  if (aiProfileFilteredSelectionActive.value) {
    clearAIProfileSelection();
    return;
  }
  selectedAIProfileRows.value = {};
  aiProfileFilteredSelectionActive.value = true;
}

function clearAIProfileSelection() {
  selectedAIProfileRows.value = {};
  aiProfileFilteredSelectionActive.value = false;
}

function selectKeywordGroup(group: KeywordGroup) {
  selectedKeywordGroupId.value = group.id;
  searchTask.keyword_group_id = group.id;
  keywordForm.name = group.name;
  keywordForm.country = group.country;
  keywordForm.country_terms = group.country_terms;
  keywordForm.keyword_terms = group.keyword_terms;
  keywordForm.product_terms = group.product_terms;
  keywordForm.role_terms = group.role_terms;
  keywordForm.search_templates = group.search_templates;
  keywordForm.notes = group.notes;
  keywordForm.is_active = group.is_active;
}

function newKeywordGroup() {
  selectedKeywordGroupId.value = null;
  searchTask.keyword_group_id = undefined;
  keywordForm.name = "";
  keywordForm.country = "";
  keywordForm.country_terms = "";
  keywordForm.keyword_terms = "";
  keywordForm.product_terms = "";
  keywordForm.role_terms = "";
  keywordForm.search_templates = defaultSearchTemplates;
  keywordForm.notes = "";
  keywordForm.is_active = true;
}

async function saveKeywordGroup() {
  errorMessage.value = "";
  savingKeywordGroup.value = true;
  try {
    const payload: KeywordGroupPayload = {
      name: keywordForm.name,
      country: keywordForm.country,
      country_terms: keywordForm.country_terms,
      keyword_terms: keywordForm.keyword_terms,
      product_terms: keywordForm.product_terms,
      role_terms: keywordForm.role_terms,
      search_templates: keywordForm.search_templates,
      notes: keywordForm.notes,
      is_active: Boolean(keywordForm.is_active),
    };
    const saved = selectedKeywordGroupId.value
      ? await updateKeywordGroup(selectedKeywordGroupId.value, payload)
      : await createKeywordGroup(payload);
    await loadKeywordGroups();
    const refreshed = keywordGroups.value.find((group) => group.id === saved.id);
    if (refreshed) selectKeywordGroup(refreshed);
    taskMessage.value = `关键词组已保存：${saved.name}`;
  } catch (error) {
    setError(error);
  } finally {
    savingKeywordGroup.value = false;
  }
}

async function deleteCurrentKeywordGroup() {
  if (!selectedKeywordGroupId.value) return;
  errorMessage.value = "";
  savingKeywordGroup.value = true;
  try {
    await deleteKeywordGroup(selectedKeywordGroupId.value);
    await loadKeywordGroups();
    taskMessage.value = "关键词组已删除";
  } catch (error) {
    setError(error);
  } finally {
    savingKeywordGroup.value = false;
  }
}

function clearKeywordForm() {
  keywordForm.name = "";
  keywordForm.country = "";
  keywordForm.country_terms = "";
  keywordForm.keyword_terms = "";
  keywordForm.product_terms = "";
  keywordForm.role_terms = "";
  keywordForm.search_templates = defaultSearchTemplates;
  keywordForm.notes = "";
  keywordForm.is_active = true;
}

function previousPage() {
  if (!canGoPrevious.value) return;
  filters.offset = Math.max(0, filters.offset - filters.limit);
  void loadDomains();
}

function nextPage() {
  if (!canGoNext.value) return;
  filters.offset += filters.limit;
  void loadDomains();
}

function previousLibraryPage() {
  if (!canLibraryGoPrevious.value) return;
  libraryFilters.offset = Math.max(0, libraryFilters.offset - libraryFilters.limit);
  void loadCompanyLibrary();
}

function nextLibraryPage() {
  if (!canLibraryGoNext.value) return;
  libraryFilters.offset += libraryFilters.limit;
  void loadCompanyLibrary();
}

function previousRawTablePage() {
  if (!canRawTableGoPrevious.value) return;
  rawTableFilters.offset = Math.max(0, rawTableFilters.offset - rawTableFilters.limit);
  void loadRawTable();
}

function nextRawTablePage() {
  if (!canRawTableGoNext.value) return;
  rawTableFilters.offset += rawTableFilters.limit;
  void loadRawTable();
}

function previousAIProfilePage() {
  if (!canAIProfileGoPrevious.value) return;
  aiProfileFilters.offset = Math.max(0, aiProfileFilters.offset - aiProfileFilters.limit);
  void loadAIProfileResults();
}

function nextAIProfilePage() {
  if (!canAIProfileGoNext.value) return;
  aiProfileFilters.offset += aiProfileFilters.limit;
  void loadAIProfileResults();
}

function setAIProfileDirectoryPageSize() {
  aiProfileFilters.offset = 0;
  selectedAIProfileResultId.value = null;
  void loadAIProfileResults();
}

async function exportSelectedAIProfiles() {
  if (!selectedAIProfileCount.value || exportingAIProfiles.value) return;
  const exportedAt = new Date().toISOString();
  const filename = promptForAIProfileExportFilename(exportedAt);
  if (!filename) return;
  exportingAIProfiles.value = true;
  try {
    const rows = aiProfileFilteredSelectionActive.value ? await fetchAllFilteredAIProfiles() : Object.values(selectedAIProfileRows.value);
    const selectionMode = aiProfileFilteredSelectionActive.value ? "filtered" : "manual";
    downloadHtmlFile(
      filename,
      buildAIProfileExportHtml(rows, selectionMode, exportedAt),
    );
  } catch (error) {
    setError(error);
  } finally {
    exportingAIProfiles.value = false;
  }
}

function defaultAIProfileExportFilename(exportedAt: string) {
  return `ai-profile-report-${exportedAt.slice(0, 10)}.html`;
}

function promptForAIProfileExportFilename(exportedAt: string) {
  const defaultFilename = defaultAIProfileExportFilename(exportedAt);
  const requestedFilename = window.prompt("请输入导出文件名", defaultFilename);
  if (requestedFilename === null) return "";
  return normalizeHtmlFilename(requestedFilename, defaultFilename);
}

function normalizeHtmlFilename(value: string, fallback: string) {
  const filename = value.trim().replace(/[\\/:*?"<>|\u0000-\u001f]+/g, "-") || fallback;
  return filename.endsWith(".html") ? filename : `${filename}.html`;
}

function buildAIProfileExportHtml(rows: RawAIProfileResultRow[], selectionMode: AIProfileSelectionMode, exportedAt: string) {
  const profiles = rows.map(toAIProfileExportProfile);
  const mode_label = selectionMode === "filtered" ? "当前筛选结果" : "手动选择";
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI画像离线报告</title>
  <style>
    :root {
      color: #07111f;
      background: #eef2ec;
      font-family: "Cabinet Grotesk", "Avenir Next", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #eef2ec;
      color: #07111f;
      line-height: 1.55;
    }
    a { color: inherit; text-decoration: none; }
    h1, h2, h3, .score-card strong {
      font-family: "Avenir Next", "Cabinet Grotesk", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .report-shell {
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: 100vh;
    }
    .report-directory {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 22px 18px;
      background: #07111f;
      color: #f7f8f5;
    }
    .directory-title {
      margin-bottom: 22px;
      border-bottom: 1px solid rgba(203, 213, 225, 0.22);
      padding-bottom: 18px;
    }
    .directory-title p,
    .profile-meta,
    .muted {
      color: #64748b;
    }
    .report-directory .muted,
    .directory-title p {
      color: #cbd5e1;
    }
    .directory-title h1 {
      margin: 0 0 8px;
      font-size: 22px;
      line-height: 1.2;
    }
    .directory-item {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      margin-bottom: 8px;
      padding: 12px;
      border: 1px solid rgba(203, 213, 225, 0.2);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.06);
    }
    .directory-item strong,
    .directory-item small {
      display: block;
    }
    .directory-item small {
      margin-top: 4px;
      color: #cbd5e1;
    }
    .directory-score {
      min-width: 54px;
      text-align: right;
    }
    .directory-score b,
    .directory-score i {
      display: block;
    }
    .directory-score i {
      color: #8bd8cf;
      font-style: normal;
      font-weight: 800;
    }
    .report-content {
      padding: 26px;
    }
    .export-header {
      max-width: 1180px;
      margin: 0 auto 20px;
      padding: 22px 24px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      background: #ffffff;
      box-shadow: 0 18px 50px rgba(7, 17, 31, 0.08);
    }
    .export-header h2 {
      margin: 0 0 8px;
      font-size: 24px;
      line-height: 1.2;
    }
    .export-header p {
      margin: 0;
      color: #304155;
    }
    .profile-report {
      max-width: 1180px;
      margin: 0 auto 18px;
      overflow: hidden;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      background: #ffffff;
      box-shadow: 0 18px 50px rgba(7, 17, 31, 0.08);
      break-inside: avoid;
    }
    .profile-report-header {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 116px;
      gap: 18px;
      align-items: center;
      padding: 20px 22px;
      border-bottom: 1px solid #e2e8f0;
      background: linear-gradient(135deg, rgba(223, 247, 242, 0.92), #ffffff);
    }
    .profile-report-header h2 {
      margin: 0 0 8px;
      font-size: 21px;
      line-height: 1.2;
    }
    .score-card {
      border: 1px solid rgba(15, 118, 110, 0.24);
      border-radius: 8px;
      padding: 12px;
      background: #ffffff;
      text-align: center;
    }
    .score-card span,
    .score-card small {
      display: block;
      color: #0f766e;
      font-weight: 800;
    }
    .score-card strong {
      display: block;
      margin: 4px 0;
      font-size: 30px;
      line-height: 1;
    }
    .profile-meta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 12px 22px;
      border-bottom: 1px solid #e2e8f0;
      color: #304155;
      font-size: 12px;
      font-weight: 700;
    }
    .profile-meta-row span {
      border: 1px solid #e2e8f0;
      border-radius: 999px;
      padding: 5px 9px;
      background: #f8fafc;
    }
    .profile-report-sections {
      display: grid;
      grid-template-columns: minmax(128px, 180px) minmax(0, 1fr);
    }
    .report-section {
      display: contents;
    }
    .report-section h3,
    .report-section-body {
      margin: 0;
      padding: 16px 18px;
      border-bottom: 1px solid #e2e8f0;
    }
    .report-section h3 {
      background: #f8fafc;
      color: #304155;
      font-size: 13px;
    }
    .report-section-body p,
    .report-section-body ul {
      margin: 0;
    }
    .report-section-body li + li {
      margin-top: 7px;
    }
    .score-breakdown {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 8px;
    }
    .score-breakdown div {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 8px 10px;
      background: #f8fafc;
    }
    .score-breakdown span {
      color: #64748b;
    }
    .contact-list {
      display: grid;
      gap: 8px;
    }
    .contact-row {
      display: grid;
      grid-template-columns: 70px minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 9px 10px;
      background: #f8fafc;
    }
    .contact-row strong,
    .contact-row small {
      overflow-wrap: anywhere;
    }
    .contact-kind {
      color: #0f766e;
      font-size: 12px;
      font-weight: 800;
    }
    .contact-row small {
      color: #64748b;
      font-size: 12px;
    }
    .recommendation {
      color: #0f766e;
      font-weight: 800;
    }
    @media (max-width: 900px) {
      .report-shell { display: block; }
      .report-directory { position: static; height: auto; }
      .report-content { padding: 14px; }
      .profile-report-header,
      .profile-report-sections { grid-template-columns: 1fr; }
      .report-section h3 { border-bottom: 0; }
    }
    @media print {
      body { background: #ffffff; }
      .report-shell { display: block; }
      .report-directory { display: none; }
      .report-content { padding: 0; }
      .export-header,
      .profile-report { box-shadow: none; }
    }
  </style>
</head>
<body>
  <main class="report-shell">
    <aside class="report-directory">
      <div class="directory-title">
        <h1>AI画像离线报告</h1>
        <p>${escapeHtml(mode_label)} · ${profiles.length} 份画像 · ${escapeHtml(exportedAt)}</p>
      </div>
      ${renderAIProfileExportDirectory(profiles)}
    </aside>
    <section class="report-content">
      <header class="export-header">
        <h2>AI画像离线报告</h2>
        <p>导出时间：${escapeHtml(exportedAt)} · 导出范围：${escapeHtml(mode_label)} · 画像数量：${profiles.length}</p>
      </header>
      ${profiles.map(renderAIProfileReportPage).join("")}
    </section>
  </main>
</body>
</html>`;
}

function toAIProfileExportProfile(result: RawAIProfileResultRow) {
  const report_sections: AIProfileReportSection[] = [
    { key: "profile_summary", label: "客户画像摘要", content: result.profile_summary || "未记录" },
    { key: "product_fit", label: "产品匹配度", content: result.product_fit || "未记录" },
    { key: "business_type", label: "业务类型", content: result.business_type || "未记录" },
    { key: "market_role", label: "市场角色", content: result.market_role || "未记录" },
    { key: "score_breakdown", label: "评分明细", content: result.score_breakdown_json || {} },
    { key: "recommended_action", label: "推荐动作", content: result.recommended_action || "未记录" },
    { key: "contact_analysis", label: "联系方式分析", content: result.contact_analysis || {} },
    { key: "contacts", label: "对应联系方式", content: result.contacts || [] },
    { key: "evidence", label: "证据", content: result.evidence_json || [] },
    { key: "risk_flags", label: "风险点", content: result.risk_flags_json || [] },
  ];
  return {
    profile_id: result.id,
    title: `${companyNameForAIProfile(result)} · ${regionForAIProfile(result)} · ${result.customer_priority || "未定级"}`,
    company: {
      name: companyNameForAIProfile(result),
      domain: result.domain,
      country: regionForAIProfile(result),
      profile_package_id: result.profile_package_id,
      task_run_id: result.task_run_id,
      task_item_id: result.task_item_id,
    },
    score: {
      priority: result.customer_priority || "未定级",
      total: result.score_total,
      breakdown: result.score_breakdown_json || {},
    },
    model: {
      provider: result.model_provider,
      name: result.model_name,
      prompt_version: result.prompt_version,
      input_hash: result.input_hash,
    },
    report_sections,
    audit: {
      status: result.status,
      status_label: statusText(result.status),
      created_at: result.created_at,
      updated_at: result.updated_at,
      error: result.error,
    },
  };
}

type AIProfileExportProfile = ReturnType<typeof toAIProfileExportProfile>;

function renderAIProfileExportDirectory(profiles: AIProfileExportProfile[]) {
  return profiles
    .map(
      (profile) => `<a class="directory-item" href="#profile-${profile.profile_id}">
        <span>
          <strong>${escapeHtml(profile.company.name)}</strong>
          <small>${escapeHtml(profile.company.country)} · ${escapeHtml(profile.company.domain)}</small>
        </span>
        <span class="directory-score">
          <b>${escapeHtml(profile.score.total)}</b>
          <i>${escapeHtml(profile.score.priority)}</i>
        </span>
      </a>`,
    )
    .join("");
}

function renderAIProfileReportPage(profile: AIProfileExportProfile) {
  return `<article class="profile-report" id="profile-${profile.profile_id}">
    <header class="profile-report-header">
      <div>
        <p class="profile-meta">画像 #${escapeHtml(profile.profile_id)}</p>
        <h2>${escapeHtml(profile.company.name)}</h2>
        <p>${escapeHtml(profile.company.domain)} · ${escapeHtml(profile.company.country)}</p>
        <p class="profile-meta">画像包 #${escapeHtml(profile.company.profile_package_id)} · 任务 #${escapeHtml(profile.company.task_run_id || "未记录")}</p>
      </div>
      <div class="score-card">
        <span>${escapeHtml(profile.score.priority)}</span>
        <strong>${escapeHtml(profile.score.total)}</strong>
        <small>总分</small>
      </div>
    </header>
    <div class="profile-meta-row">
      <span>${escapeHtml(profile.model.provider)} / ${escapeHtml(profile.model.name)}</span>
      <span>${escapeHtml(profile.audit.status_label)}</span>
      <span>${escapeHtml(profile.audit.created_at || "未记录时间")}</span>
    </div>
    <div class="profile-report-sections">
      ${profile.report_sections.map(renderAIProfileReportSection).join("")}
    </div>
  </article>`;
}

function renderAIProfileReportSection(section: AIProfileReportSection) {
  const recommendationClass = section.key === "recommended_action" ? " recommendation" : "";
  let content = renderExportContent(section.content);
  if (section.key === "contacts") content = renderAIProfileContactList(section.content);
  if (section.key === "contact_analysis") content = renderAIProfileContactAnalysis(section.content);
  return `<section class="report-section">
    <h3>${escapeHtml(section.label)}</h3>
    <div class="report-section-body${recommendationClass}">
      ${content}
    </div>
  </section>`;
}

function renderAIProfileContactAnalysis(content: unknown): string {
  const analysis = content && typeof content === "object"
    ? (content as RawAIProfileResultRow["contact_analysis"])
    : {};
  if (!Object.keys(analysis).length) return `<p class="muted">旧画像暂无联系方式分析，请重新运行画像任务。</p>`;

  const channels = (analysis.available_channels || []).map(formatAIContactChannel).join("、") || "无";
  const recommendations = analysis.recommended_contacts || [];
  const recommendedHtml = recommendations.length
    ? `<div class="contact-list">${recommendations
        .map(
          (contact) => `<div class="contact-row">
            <span class="contact-kind">${escapeHtml(formatAIContactChannel(contact.type))}</span>
            <strong>${escapeHtml(contact.value || "未记录")}</strong>
            <small>${escapeHtml([contact.label, contact.reason].filter(Boolean).join(" · ") || "未记录")}</small>
          </div>`,
        )
        .join("")}</div>`
    : `<p class="muted">没有推荐的直接联系方式。</p>`;

  return `<div class="contact-analysis-summary">
    <div class="score-breakdown">
      <div><span>联系质量</span><strong>${escapeHtml(formatAIContactQuality(analysis.contact_quality))}</strong></div>
      <div><span>可用渠道</span><strong>${escapeHtml(channels)}</strong></div>
      <div><span>首选渠道</span><strong>${escapeHtml(formatAIContactChannel(analysis.preferred_channel || "none"))}</strong></div>
    </div>
    ${recommendedHtml}
    <p>${escapeHtml(analysis.outreach_strategy || "未记录联系策略")}</p>
  </div>`;
}

function renderAIProfileContactList(content: unknown): string {
  const contacts = Array.isArray(content) ? (content as Contact[]) : [];
  if (!contacts.length) return `<p class="muted">未记录</p>`;
  return `<div class="contact-list">${contacts
    .map((contact) => {
      const href = contactHref(contact);
      const tag = href ? "a" : "div";
      const hrefAttribute = href ? ` href="${escapeHtml(href)}"` : "";
      return `<${tag} class="contact-row"${hrefAttribute}>
        <span class="contact-kind">${escapeHtml(formatAIProfileContactKind(contact.kind))}</span>
        <strong>${escapeHtml(contact.value)}</strong>
        ${contact.label ? `<small>${escapeHtml(contact.label)}</small>` : ""}
      </${tag}>`;
    })
    .join("")}</div>`;
}

function renderExportContent(content: unknown): string {
  if (Array.isArray(content)) {
    if (!content.length) return `<p class="muted">未记录</p>`;
    return `<ul>${content.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }
  if (content && typeof content === "object") {
    const entries = Object.entries(content as Record<string, unknown>);
    if (!entries.length) return `<p class="muted">未记录</p>`;
    return `<div class="score-breakdown">${entries
      .map(([name, value]) => `<div><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("")}</div>`;
  }
  return `<p>${escapeHtml(content || "未记录")}</p>`;
}

async function fetchAllFilteredAIProfiles() {
  const rows: RawAIProfileResultRow[] = [];
  let offset = 0;
  const limit = 500;
  while (offset < Math.max(aiProfileTotal.value, 1)) {
    const response = await fetchRawAIProfileResults({ ...aiProfileFilters, limit, offset });
    rows.push(...response.items);
    if (rows.length >= response.total || response.items.length === 0) break;
    offset += limit;
  }
  return rows;
}

function escapeHtml(value: unknown) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function downloadHtmlFile(filename: string, html: string) {
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  downloadBlobFile(filename, blob);
}

function downloadBlobFile(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function previousTaskRunPage() {
  if (!canTaskRunGoPrevious.value) return;
  taskRunFilters.offset = Math.max(0, taskRunFilters.offset - taskRunFilters.limit);
  void loadTaskRuns();
}

function nextTaskRunPage() {
  if (!canTaskRunGoNext.value) return;
  taskRunFilters.offset += taskRunFilters.limit;
  void loadTaskRuns();
}

function previousCandidateGroupPage() {
  if (!canCandidateGroupGoPrevious.value) return;
  candidateGroupFilters.offset = Math.max(0, candidateGroupFilters.offset - candidateGroupFilters.limit);
  void loadCandidateGroups();
}

function nextCandidateGroupPage() {
  if (!canCandidateGroupGoNext.value) return;
  candidateGroupFilters.offset += candidateGroupFilters.limit;
  void loadCandidateGroups();
}

function statusClass(status: string) {
  return `status status-${status || "unknown"}`;
}

function statusText(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "success") return "已完成";
  if (normalized === "partial_failed") return "部分失败";
  if (normalized === "failed" || normalized === "failure") return "失败";
  if (normalized === "cancelling") return "取消中";
  if (normalized === "cancelled") return "已取消";
  if (normalized === "queued") return "排队中";
  if (normalized === "pending") return "等待中";
  if (normalized === "running") return "运行中";
  if (normalized === "started") return "运行中";
  if (normalized === "empty") return "空结果";
  if (normalized === "error") return "异常";
  if (normalized === "idle") return "待执行";
  if (normalized === "unknown" || !normalized) return "未知";
  return status;
}

function taskTypeText(taskType: string) {
  if (taskType === "search") return "官网搜索";
  if (taskType === "crawl") return "官网抓取";
  if (taskType === "ai_profile") return "AI画像";
  if (taskType === "import_existing_data") return "旧文件导入";
  if (taskType === "legacy_import") return "历史导入";
  if (taskType === "confirm") return "客户确认";
  return taskType;
}

function displayName(domain: DomainSummary) {
  return domain.display_name || domain.domain;
}

function companyNameForAIProfile(result: RawAIProfileResultRow) {
  return result.company_name || result.domain;
}

function regionForAIProfile(result: RawAIProfileResultRow) {
  return result.country || "地区未识别";
}

function formatAIProfileContactKind(kind: string) {
  if (kind === "email") return "邮箱";
  if (kind === "phone") return "电话";
  if (kind === "social") return "社媒";
  if (kind === "person") return "联系人";
  return kind || "联系方式";
}

function formatAIContactChannel(channel?: string) {
  if (channel === "contact_form") return "联系表单";
  if (channel === "none") return "无";
  return formatAIProfileContactKind(channel || "");
}

function formatAIContactQuality(quality?: string) {
  if (quality === "high") return "高";
  if (quality === "medium") return "中";
  if (quality === "low") return "低";
  return "无";
}

function contactDisplayMeta(contact: Contact) {
  const kindLabel = formatAIProfileContactKind(contact.kind);
  return contact.label ? `${kindLabel} · ${contact.label}` : kindLabel;
}

function rawCellValue(row: RawTableRow, key: string) {
  const value = (row as unknown as Record<string, unknown>)[key];
  if (value === null || value === undefined || value === "") return "未记录";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function rawRowNumericId(row: RawTableRow) {
  const value = (row as unknown as Record<string, unknown>).id;
  const id = typeof value === "number" ? value : Number(value);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function contactHref(contact: Contact) {
  if (contact.kind === "email") return `mailto:${contact.value}`;
  if (contact.kind === "phone") return `tel:${contact.value.replace(/[^+\d]/g, "")}`;
  if (contact.value.startsWith("http://") || contact.value.startsWith("https://")) return contact.value;
  return "";
}

function taskItemDetailText(item: TaskItemRecord) {
  const companyName = item.result_json.company_name;
  if (item.error) return item.error;
  if (typeof companyName === "string" && companyName) return companyName;
  return item.finished_at || item.started_at || "等待执行";
}

function setError(error: unknown) {
  errorMessage.value = error instanceof Error ? error.message : "接口请求异常";
}

function isQueuedTaskResponse(response: TaskStartResponse | null): response is Extract<TaskStartResponse, { task_id: string }> {
  return Boolean(response && "task_id" in response);
}

function isInlineTaskResponse(response: TaskStartResponse | null): response is Exclude<TaskStartResponse, { task_id: string }> {
  return Boolean(response && "summary" in response);
}

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

onMounted(() => {
  void initializeDashboard();
});

onBeforeUnmount(() => {
  clearTaskPolling();
  clearTaskRunProgressPolling();
});
</script>

<template>
  <main class="app-shell console-redesign" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }" aria-label="控制台导航">
      <div class="sidebar-brand">
        <div class="sidebar-title">
          <p class="eyebrow">海外热泵渠道</p>
          <strong>热泵商机雷达</strong>
        </div>
        <button
          class="sidebar-toggle"
          type="button"
          :aria-label="sidebarCollapsed ? '展开导航' : '收起导航'"
          :title="sidebarCollapsed ? '展开导航' : '收起导航'"
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          <PanelLeftOpen v-if="sidebarCollapsed" :size="18" />
          <PanelLeftClose v-else :size="18" />
        </button>
      </div>
      <nav class="sidebar-nav">
        <button
          v-for="item in navigationItems"
          :key="item.value"
          type="button"
          :aria-label="item.label"
          :class="{ active: activeModule === item.value }"
          :title="item.label"
          @click="activeModule = item.value"
        >
          <component :is="item.icon" :size="17" />
          <span>
            <strong>{{ item.label }}</strong>
          </span>
        </button>
      </nav>
    </aside>

    <section class="app-main">
      <section class="module-overview" aria-label="模块概览">
        <header class="topbar">
          <div>
            <h1>{{ activeNavigationItem.label }}</h1>
          </div>
          <div class="topbar-actions">
            <button class="icon-button" type="button" :disabled="loadingStats || loadingDomains" @click="refreshAll">
              <RefreshCw :size="16" />
              同步
            </button>
          </div>
        </header>

        <section class="metrics" aria-label="数据库概览">
          <div v-for="metric in metricCards" :key="metric.label" class="metric-card">
            <component :is="metric.icon" :size="16" />
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value.toLocaleString() }}</strong>
          </div>
        </section>
      </section>

      <div v-if="errorMessage" class="error-banner">
        {{ errorMessage }}
      </div>

    <section v-if="activeModule === 'keywords'" class="keyword-panel" aria-label="关键词配置中心">
      <div class="keyword-panel-header">
        <div>
          <p class="eyebrow">关键词配置中心</p>
          <h2>关键词组</h2>
        </div>
        <button class="icon-button" type="button" @click="newKeywordGroup">
          <Plus :size="16" />
          新增关键词组
        </button>
      </div>

      <div class="keyword-grid">
        <div class="keyword-list" aria-label="关键词组列表">
          <button
            v-for="group in keywordGroups"
            :key="group.id"
            type="button"
            :class="{ active: selectedKeywordGroupId === group.id }"
            @click="selectKeywordGroup(group)"
          >
            <strong>{{ group.name }}</strong>
            <span>{{ group.country }} · {{ group.keyword_count }} 个组合</span>
          </button>
          <div v-if="loadingKeywordGroups" class="keyword-empty">
            <Loader2 :size="16" class="spin" />
            正在加载关键词组
          </div>
          <div v-else-if="keywordGroups.length === 0" class="keyword-empty">暂无关键词组，先新建一个。</div>
        </div>

        <div class="keyword-form">
          <label>
            关键词组名称
            <input v-model="keywordForm.name" type="text" placeholder="France - Pool Heating" />
          </label>
          <label>
            目标国家
            <input v-model="keywordForm.country" type="text" placeholder="France" />
          </label>
          <label>
            国家词
            <textarea v-model="keywordForm.country_terms" rows="5" placeholder="France&#10;en France" />
          </label>
          <label>
            直接关键词
            <textarea v-model="keywordForm.keyword_terms" rows="5" placeholder="pool heat pump&#10;pompe à chaleur piscine" />
          </label>
          <label>
            产品词
            <textarea v-model="keywordForm.product_terms" rows="5" placeholder="pool heat pump&#10;pompa di calore piscina" />
          </label>
          <label>
            角色词
            <textarea v-model="keywordForm.role_terms" rows="5" placeholder="distributor&#10;installer&#10;rivenditore&#10;installatore" />
          </label>
          <label class="keyword-template-field">
            搜索模板
            <textarea v-model="keywordForm.search_templates" rows="5" placeholder="{product} {role} {country}&#10;{product} {role} in {country}" />
          </label>
          <label class="keyword-notes">
            备注
            <textarea v-model="keywordForm.notes" rows="5" placeholder="用于法国泳池热泵渠道搜索" />
          </label>
          <label class="check-row keyword-active">
            <input v-model="keywordForm.is_active" type="checkbox" />
            启用
          </label>
          <div class="keyword-actions">
            <button class="icon-button primary" type="button" :disabled="savingKeywordGroup" @click="saveKeywordGroup">
              <Loader2 v-if="savingKeywordGroup" :size="16" class="spin" />
              <Save v-else :size="16" />
              保存关键词组
            </button>
            <button class="icon-button danger" type="button" :disabled="!selectedKeywordGroupId || savingKeywordGroup" @click="deleteCurrentKeywordGroup">
              <Trash2 :size="16" />
              删除
            </button>
          </div>
        </div>
      </div>
    </section>

    <section v-if="activeModule === 'tasks'" class="task-panel" aria-label="任务控制台">
      <div class="task-panel-header">
        <div>
          <p class="eyebrow">获客流水线</p>
          <h2>搜索、抓取、画像</h2>
        </div>
        <div class="runtime-pill">
          <Activity :size="15" />
          <span>{{ loadingRuntime ? "检测中" : runtimeText }}</span>
        </div>
      </div>

      <div class="task-tabs" role="tablist" aria-label="任务类型">
        <button
          v-for="tab in taskTabs"
          :key="tab.value"
          type="button"
          :class="{ active: selectedTask === tab.value }"
          @click="selectedTask = tab.value"
        >
          <component :is="tab.icon" :size="16" />
          {{ tab.label }}
        </button>
      </div>

      <div v-if="selectedTask === 'search'" class="task-form daily-task-form search-daily-form">
        <label>
          关键词组
          <select v-model.number="searchTask.keyword_group_id">
            <option disabled :value="undefined">请选择关键词组</option>
            <option v-for="group in keywordGroups" :key="group.id" :value="group.id">
              {{ group.name }}
            </option>
          </select>
        </label>
        <label>
          搜索引擎
          <select v-model="searchTask.engines">
            <option v-for="engine in searchEngineOptions" :key="engine.value" :value="engine.value">
              {{ engine.label }}
            </option>
          </select>
        </label>
        <label>
          每词页数
          <input v-model.number="searchTask.max_pages" min="1" type="number" />
        </label>
        <label>
          关键词组合数
          <input :value="selectedSearchKeywordCountText" readonly type="text" />
        </label>

        <details class="task-fieldset task-advanced-details search-advanced-settings">
          <summary>
            <span>搜索高级设置</span>
          </summary>
          <div class="task-fieldset-grid">
            <label>
              请求模式
              <select v-model="searchTask.backend">
                <option value="requests">requests</option>
                <option value="browser">browser</option>
              </select>
            </label>
            <label>
              关键词间隔（秒）
              <input v-model.number="searchTask.keyword_delay_seconds" min="0" step="0.5" type="number" />
            </label>
            <label>
              引擎请求间隔（秒）
              <input v-model.number="searchTask.engine_request_delay_seconds" min="0" step="0.5" type="number" />
            </label>
            <label class="check-row compact-check">
              <input v-model="searchTask.retry_failed" type="checkbox" />
              只补失败
            </label>
          </div>
        </details>
      </div>

      <div v-else-if="selectedTask === 'crawl'" class="task-form daily-task-form crawl-daily-form">
        <div class="task-fieldset task-preset-strip">
          <div>
            <h3>抓取预设</h3>
          </div>
          <div class="task-preset-options">
            <button
              v-for="preset in crawlPresetOptions"
              :key="preset.label"
              class="preset-button"
              type="button"
              @click="applyCrawlPreset(preset)"
            >
              <strong>{{ preset.label }}</strong>
              <span>{{ preset.description }}</span>
            </button>
          </div>
        </div>

        <div class="candidate-source-summary">
          <span>候选来源</span>
          <strong>{{ crawlCandidateSourceText }}</strong>
        </div>

        <label>
          候选组
          <select v-model.number="crawlTask.candidate_group_id">
            <option :value="undefined">不指定候选组</option>
            <option v-for="group in candidateGroups" :key="group.id" :value="group.id">
              {{ group.name }}（{{ group.uncrawled_count }}/{{ group.item_count }}）
            </option>
          </select>
        </label>
        <label :class="{ disabled: isCandidateFilterDisabled }">
          候选国家
          <input v-model="crawlTask.candidate_country" :disabled="isCandidateFilterDisabled" type="text" />
        </label>
        <label :class="{ disabled: isCandidateFilterDisabled }">
          候选关键词
          <input v-model="crawlTask.candidate_query" :disabled="isCandidateFilterDisabled" type="text" placeholder="可留空" />
        </label>
        <label>
          抓取模式
          <select v-model="crawlTask.backend">
            <option value="requests">requests</option>
            <option value="browser">browser</option>
          </select>
        </label>
        <label>
          候选数量
          <input v-model.number="crawlTask.candidate_limit" min="1" type="number" />
        </label>
        <label>
          站内深度
          <input v-model.number="crawlTask.max_depth" min="0" type="number" />
        </label>
        <label>
          每站页数
          <input v-model.number="crawlTask.max_pages_per_site" min="1" type="number" />
        </label>

        <details class="task-fieldset task-advanced-details crawl-advanced-settings">
          <summary>
            <span>抓取高级设置</span>
          </summary>
          <p class="task-advanced-label">重试退避</p>
          <div class="task-fieldset-grid">
            <label>
              域名间隔
              <input v-model.number="crawlTask.domain_delay" min="0" step="0.5" type="number" />
            </label>
            <label>
              全局请求间隔
              <input v-model.number="crawlTask.global_delay" min="0" step="0.5" type="number" />
            </label>
            <label>
              并发数
              <input v-model.number="crawlTask.workers" min="1" type="number" />
            </label>
            <label>
              最大重试次数
              <input v-model.number="crawlTask.max_retries" min="0" type="number" />
            </label>
            <label>
              初始退避（秒）
              <input v-model.number="crawlTask.backoff_base" min="0" step="0.5" type="number" />
            </label>
            <label>
              最大退避（秒）
              <input v-model.number="crawlTask.backoff_max" min="0" step="0.5" type="number" />
            </label>
          </div>
          <p class="task-advanced-label">代理与浏览器</p>
          <div class="task-fieldset-grid">
            <label>
              代理地址
              <input v-model="crawlTask.proxy" type="text" placeholder="http://127.0.0.1:7890" />
            </label>
            <label :class="{ disabled: !isBrowserMode }">
              浏览器超时（ms）
              <input v-model.number="crawlTask.browser_timeout_ms" :disabled="!isBrowserMode" min="1000" step="1000" type="number" />
            </label>
            <label :class="{ disabled: !isBrowserMode }">
              浏览器等待（ms）
              <input v-model.number="crawlTask.browser_wait_ms" :disabled="!isBrowserMode" min="0" step="500" type="number" />
            </label>
            <label :class="{ disabled: !isBrowserMode }">
              浏览器最大页数
              <input v-model.number="crawlTask.browser_max_pages" :disabled="!isBrowserMode" min="1" type="number" />
            </label>
            <label class="check-row compact-check" :class="{ disabled: !isRequestsMode }">
              <input v-model="crawlTask.use_system_proxy" :disabled="!isRequestsMode" type="checkbox" />
              使用系统代理
            </label>
            <label class="check-row compact-check" :class="{ disabled: !isBrowserMode }">
              <input v-model="crawlTask.headless" :disabled="!isBrowserMode" type="checkbox" />
              浏览器 headless
            </label>
            <label class="check-row compact-check">
              <input v-model="crawlTask.retry_failed" type="checkbox" />
              只重试失败
            </label>
            <label class="check-row compact-check">
              <input v-model="crawlTask.recrawl_existing" type="checkbox" />
              允许重抓
            </label>
          </div>
        </details>
      </div>

      <div v-else-if="selectedTask === 'ai_profile'" class="task-form">
        <label :class="{ disabled: isAIProfileSourceGroupDisabled }">
          画像源数据组
          <select v-model="aiProfileTask.profile_source_group_id" :disabled="isAIProfileSourceGroupDisabled">
            <option :value="undefined">
              {{ loadingProfileSourceGroups ? "正在加载画像源数据组" : "请选择画像源数据组" }}
            </option>
            <option v-for="group in profileSourceGroups" :key="group.id" :value="group.id">
              {{ group.name || `抓官网任务 #${group.task_run_id}` }}（{{ group.profile_package_count }} 包 / {{ group.pending_profile_count }} 待画像）
            </option>
          </select>
        </label>
        <div v-if="selectedProfileSourceGroup" class="candidate-source-summary">
          <span>当前画像源</span>
          <strong>
            {{ selectedProfileSourceGroup.domain_count }} 个域名 ·
            {{ selectedProfileSourceGroup.ai_profile_count }} 已画像 ·
            来源候选组 {{ selectedProfileSourceGroup.candidate_group_name || selectedProfileSourceGroup.candidate_group_id || "未记录" }}
          </strong>
        </div>
        <label :class="{ disabled: isAIProfilePackageIdsDisabled }">
          画像包 ID
          <textarea
            v-model="aiProfileTask.profile_package_ids_text"
            :disabled="isAIProfilePackageIdsDisabled"
            rows="4"
            placeholder="例如：1211, 1212, 1213"
          />
        </label>
        <label>
          模型服务
          <select v-model="aiProfileTask.model_provider">
            <option value="deepseek">deepseek</option>
          </select>
        </label>
        <label>
          API Base URL
          <input v-model="aiProfileTask.api_base_url" type="text" placeholder="https://api.deepseek.com" />
        </label>
        <label>
          API Key
          <input v-model="aiProfileTask.api_key" autocomplete="off" type="password" placeholder="仅本次任务使用，不写入数据库" />
        </label>
        <label>
          模型名称
          <input v-model="aiProfileTask.model_name" type="text" />
        </label>
        <label>
          温度
          <input v-model.number="aiProfileTask.temperature" min="0" max="2" step="0.1" type="number" />
        </label>
        <label>
          超时时间（秒）
          <input v-model.number="aiProfileTask.timeout_seconds" min="10" step="10" type="number" />
        </label>
      </div>

      <div class="task-actions">
        <button class="icon-button primary" type="button" :disabled="taskSubmitting" @click="submitSelectedTask">
          <Loader2 v-if="taskSubmitting" :size="16" class="spin" />
          <PlayCircle v-else :size="16" />
          执行{{ taskTabs.find((tab) => tab.value === selectedTask)?.label }}
        </button>
        <span v-if="taskMessage">{{ taskMessage }}</span>
        <span v-else>当前模式：{{ runtimeText }}</span>
      </div>

      <div v-if="latestTaskResponse || latestTaskStatus" class="task-result">
        <div class="task-result-header">
          <strong>
            <CheckCircle2 v-if="taskStatusLabel === 'success' || taskStatusLabel === 'SUCCESS'" :size="16" />
            <XCircle v-else-if="taskStatusLabel === 'failed' || taskStatusLabel === 'FAILURE'" :size="16" />
            <Activity v-else :size="16" />
            {{ taskStatusText }}
          </strong>
          <small v-if="isQueuedTaskResponse(latestTaskResponse)">任务 ID：{{ latestTaskResponse.task_id }}</small>
        </div>
        <pre v-if="latestTaskResult">{{ formatJson(latestTaskResult.summary) }}</pre>
        <pre v-else-if="latestTaskStatus">{{ formatJson(latestTaskStatus) }}</pre>
        <pre v-else>{{ formatJson(latestTaskResponse) }}</pre>
      </div>

      <div v-if="taskSubmitting || activeTaskProgress" class="task-progress-panel">
        <div class="task-progress-header">
          <div>
            <p class="eyebrow">实时进度</p>
            <h3>{{ activeTaskProgress ? taskTypeText(activeTaskProgress.task_type) : "等待任务记录" }}</h3>
          </div>
          <span :class="statusClass(activeTaskProgress?.status || 'running')">
            {{ activeTaskProgress ? statusText(activeTaskProgress.status) : "运行中" }}
          </span>
          <button
            v-if="activeTaskCanCancel"
            class="icon-button danger"
            type="button"
            :disabled="cancellingTaskRunId === activeTaskProgress?.id"
            @click="cancelActiveTaskRun"
          >
            <Loader2 v-if="cancellingTaskRunId === activeTaskProgress?.id" :size="16" class="spin" />
            <XCircle v-else :size="16" />
            取消任务
          </button>
        </div>

        <div class="progress-bar" aria-label="任务进度">
          <span class="progress-bar-fill" :style="{ width: `${progressPercent}%` }" />
        </div>

        <div class="task-progress-summary">
          <span>{{ progressCompleted }} / {{ progressTotal }} 已处理</span>
          <span v-for="(count, status) in progressCounts" :key="status">
            {{ statusText(String(status)) }} {{ count }}
          </span>
          <span v-if="!activeTaskProgress">正在等待后端创建任务批次</span>
        </div>

        <div v-if="activeProgressItems.length" class="task-progress-items">
          <div v-for="item in activeProgressItems" :key="item.id" class="task-progress-item">
            <strong>{{ item.item_key }}</strong>
            <span :class="statusClass(item.status)">{{ statusText(item.status) }}</span>
            <small>{{ taskItemDetailText(item) }}</small>
          </div>
        </div>
      </div>
    </section>

    <section v-if="activeModule === 'candidateGroups'" class="task-center-panel" aria-label="候选组">
      <div class="library-header">
        <div>
          <p class="eyebrow">候选组</p>
          <h2>搜索输出集合</h2>
        </div>
      </div>

      <div class="library-toolbar">
        <select v-model="candidateGroupFilters.status" class="filter-select" @change="applyCandidateGroupFilters">
          <option value="active">可用候选组</option>
          <option value="">全部候选组</option>
          <option value="archived">已归档</option>
        </select>
        <button class="icon-button primary" type="button" @click="applyCandidateGroupFilters">
          <RefreshCw :size="16" />
          刷新
        </button>
      </div>

      <div class="task-center-grid">
        <div class="task-run-list">
          <div v-if="loadingCandidateGroups" class="keyword-empty">
            <Loader2 :size="18" class="spin" />
            正在加载候选组
          </div>
          <button
            v-for="group in candidateGroups"
            :key="group.id"
            type="button"
            :class="{ active: selectedCandidateGroup?.id === group.id }"
            @click="loadCandidateGroupDetail(group.id)"
          >
            <strong>{{ group.name || `候选组 #${group.id}` }}</strong>
            <span>{{ group.country || "未标注国家" }} · {{ group.group_type }}</span>
            <small>{{ group.uncrawled_count }} 未抓 / {{ group.item_count }} 总数</small>
          </button>
          <div v-if="!loadingCandidateGroups && candidateGroups.length === 0" class="keyword-empty">暂无候选组。</div>
        </div>

        <div class="task-run-detail">
          <div v-if="loadingCandidateGroupDetail" class="detail-loading">
            <Loader2 :size="18" class="spin" />
            正在加载候选组详情
          </div>
          <template v-else-if="selectedCandidateGroup">
            <div class="detail-heading">
              <div>
                <p class="eyebrow">候选组 #{{ selectedCandidateGroup.id }}</p>
                <h2>{{ selectedCandidateGroup.name }}</h2>
                <p>{{ selectedCandidateGroup.country || "未标注国家" }} · 来源任务 #{{ selectedCandidateGroup.source_task_run_id || "-" }}</p>
              </div>
              <span :class="statusClass(selectedCandidateGroup.status)">{{ statusText(selectedCandidateGroup.status) }}</span>
            </div>

            <div class="task-counts">
              <span>总域名 {{ selectedCandidateGroup.item_count }}</span>
              <span>已抓 {{ selectedCandidateGroup.crawled_count }}</span>
              <span>未抓 {{ selectedCandidateGroup.uncrawled_count }}</span>
            </div>

            <div v-if="selectedCandidateGroup.items?.length" class="task-item-list">
              <div v-for="item in selectedCandidateGroup.items" :key="item.id" class="task-item-row">
                <strong>{{ item.domain.domain }}</strong>
                <span>{{ item.search_result.title || item.domain.display_name || item.search_result.keyword }}</span>
                <small>{{ item.has_crawl_result ? "已抓取" : "未抓取" }} · {{ item.search_result.engine || "unknown" }}</small>
              </div>
            </div>
            <div v-else class="keyword-empty">这个候选组没有可显示的域名。</div>
          </template>
          <div v-else class="keyword-empty">请选择候选组。</div>
        </div>
      </div>

      <div class="pagination-bar">
        <span>第 {{ candidateGroupCurrentPage }} / {{ candidateGroupTotalPages }} 页，共 {{ candidateGroupTotal }} 组</span>
        <div>
          <button class="square-button" type="button" :disabled="!canCandidateGroupGoPrevious" aria-label="上一页" @click="previousCandidateGroupPage">
            <ChevronLeft :size="16" />
          </button>
          <button class="square-button" type="button" :disabled="!canCandidateGroupGoNext" aria-label="下一页" @click="nextCandidateGroupPage">
            <ChevronRight :size="16" />
          </button>
        </div>
      </div>
    </section>

    <section v-if="activeModule === 'taskCenter'" class="task-center-panel" aria-label="任务中心">
      <div class="library-header">
        <div>
          <p class="eyebrow">任务中心</p>
          <h2>任务批次</h2>
        </div>
      </div>

      <div class="library-toolbar">
        <select v-model="taskRunFilters.task_type" class="filter-select" @change="applyTaskRunFilters">
          <option value="">全部任务类型</option>
          <option value="search">搜索任务</option>
          <option value="crawl">抓取任务</option>
          <option value="confirm">确认任务</option>
          <option value="legacy_import">历史导入</option>
        </select>
        <select v-model="taskRunFilters.status" class="filter-select" @change="applyTaskRunFilters">
          <option value="">全部状态</option>
          <option value="pending">等待中</option>
          <option value="running">运行中</option>
          <option value="cancelling">取消中</option>
          <option value="success">已完成</option>
          <option value="partial_failed">部分失败</option>
          <option value="failed">失败</option>
          <option value="cancelled">已取消</option>
        </select>
        <button class="icon-button primary" type="button" @click="applyTaskRunFilters">
          <Search :size="16" />
          筛选
        </button>
      </div>

      <div class="task-center-grid">
        <section class="task-run-list">
          <div v-if="loadingTaskRuns" class="keyword-empty">
            <Loader2 :size="16" class="spin" />
            正在加载任务批次
          </div>
          <button
            v-for="run in taskRuns"
            v-else
            :key="run.id"
            type="button"
            :class="{ active: selectedTaskRun?.id === run.id }"
            @click="loadTaskRunDetail(run.id)"
          >
            <strong>{{ run.name || taskTypeText(run.task_type) }}</strong>
            <span>{{ taskTypeText(run.task_type) }} · {{ statusText(run.status) }}</span>
            <small>{{ run.created_at }}</small>
          </button>
          <div v-if="!loadingTaskRuns && taskRuns.length === 0" class="keyword-empty">暂无任务批次。</div>
        </section>

        <section class="task-run-detail">
          <div v-if="loadingTaskRunDetail" class="detail-loading">
            <Loader2 :size="18" class="spin" />
            正在加载任务详情
          </div>
          <template v-else-if="selectedTaskRun">
            <div class="detail-header">
              <div>
                <p class="eyebrow">{{ taskTypeText(selectedTaskRun.task_type) }}</p>
                <h2>{{ selectedTaskRun.name || `任务 #${selectedTaskRun.id}` }}</h2>
                <p>{{ statusText(selectedTaskRun.status) }} · {{ selectedTaskRun.created_at }}</p>
              </div>
              <div class="detail-actions">
                <span :class="statusClass(selectedTaskRun.status)">{{ statusText(selectedTaskRun.status) }}</span>
                <button
                  v-if="canViewTaskRunResults(selectedTaskRun)"
                  class="icon-button primary"
                  type="button"
                  @click="openTaskRunResults(selectedTaskRun)"
                >
                  <ExternalLink :size="16" />
                  查看结果
                </button>
                <button
                  v-if="selectedTaskRunCanCancel"
                  class="icon-button danger"
                  type="button"
                  :disabled="cancellingTaskRunId === selectedTaskRun.id"
                  @click="cancelSelectedTaskRun"
                >
                  <Loader2 v-if="cancellingTaskRunId === selectedTaskRun.id" :size="16" class="spin" />
                  <XCircle v-else :size="16" />
                  取消任务
                </button>
              </div>
            </div>

            <section class="detail-section">
              <h3><Activity :size="16" /> 任务统计</h3>
              <div class="task-counts">
                <span v-for="(count, status) in selectedTaskRun.item_counts" :key="status">
                  {{ statusText(String(status)) }} {{ count }}
                </span>
              </div>
            </section>

            <section class="detail-section">
              <h3><ListChecks :size="16" /> 执行项</h3>
              <div v-if="selectedTaskRun.items?.length" class="task-item-list">
                <div v-for="item in selectedTaskRun.items" :key="item.id" class="task-item-row">
                  <strong>{{ item.item_key }}</strong>
                  <span>{{ statusText(item.status) }} · 尝试 {{ item.attempt_count }} 次</span>
                  <small v-if="item.error">{{ item.error }}</small>
                </div>
              </div>
              <p v-else class="muted">这个任务暂未记录执行项。</p>
            </section>
          </template>
          <div v-else class="empty-detail">选择一个任务批次查看执行项。</div>
        </section>
      </div>

      <footer class="pager">
        <span>共 {{ taskRunTotal.toLocaleString() }} 个任务 · 第 {{ taskRunCurrentPage }} / {{ taskRunTotalPages }} 页</span>
        <div>
          <button class="square-button" type="button" :disabled="!canTaskRunGoPrevious" aria-label="上一页" @click="previousTaskRunPage">
            <ChevronLeft :size="18" />
          </button>
          <button class="square-button" type="button" :disabled="!canTaskRunGoNext" aria-label="下一页" @click="nextTaskRunPage">
            <ChevronRight :size="18" />
          </button>
        </div>
      </footer>
    </section>

    <section v-if="activeModule === 'library'" class="library-panel" aria-label="企业库">
      <div class="library-header">
        <div>
          <p class="eyebrow">企业库</p>
          <h2>阶段 A / B / C</h2>
        </div>
        <div class="library-stats">
          <span>A {{ (libraryStats?.stage_a_companies ?? 0).toLocaleString() }}</span>
          <span>B {{ (libraryStats?.stage_b_companies ?? 0).toLocaleString() }}</span>
          <span>C {{ (libraryStats?.stage_c_companies ?? 0).toLocaleString() }}</span>
        </div>
      </div>

      <div class="library-tabs" role="tablist" aria-label="企业库阶段">
        <button
          v-for="tab in libraryTabs"
          :key="tab.value"
          type="button"
          :class="{ active: selectedLibraryStage === tab.value }"
          @click="setLibraryStage(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="library-toolbar">
        <label class="search-field">
          <Search :size="16" />
          <input v-model="libraryFilters.q" type="search" placeholder="搜索域名、公司名、关键词" @keyup.enter="applyLibraryFilters" />
        </label>
        <input v-model="libraryFilters.country" class="filter-input" type="text" placeholder="国家信号" @keyup.enter="applyLibraryFilters" />
        <select v-if="selectedLibraryStage === 'stageB'" v-model="libraryFilters.status" class="filter-select" @change="applyLibraryFilters">
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <button class="icon-button primary" type="button" @click="applyLibraryFilters">
          <Search :size="16" />
          筛选
        </button>
      </div>

      <div class="table-wrap library-table-wrap">
        <table v-if="selectedLibraryStage === 'stageA'">
          <thead>
            <tr>
              <th>候选企业</th>
              <th>搜索关键词</th>
              <th>国家</th>
              <th>来源</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingLibrary">
              <td colspan="4" class="loading-cell">
                <Loader2 :size="16" class="spin" />
                正在加载官网候选库
              </td>
            </tr>
            <template v-else>
              <tr v-for="item in stageACompanies" :key="item.domain.domain" @click="openDomainDetail(item.domain.domain)">
                <td>
                  <strong>{{ item.domain.domain }}</strong>
                  <span>{{ item.latest_search?.title || item.domain.website }}</span>
                </td>
                <td>{{ item.latest_search?.keyword || "未记录" }}</td>
                <td>{{ item.countries.join(", ") || item.latest_search?.country || "未知" }}</td>
                <td>{{ item.latest_search?.engine || "搜索" }} · {{ item.search_result_count }} 条</td>
              </tr>
            </template>
            <tr v-if="!loadingLibrary && stageACompanies.length === 0">
              <td colspan="4" class="empty-cell">当前筛选下没有官网候选。</td>
            </tr>
          </tbody>
        </table>

        <table v-else-if="selectedLibraryStage === 'stageB'">
          <thead>
            <tr>
              <th>已抓企业</th>
              <th>状态</th>
              <th>联系/素材</th>
              <th>摘要</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingLibrary">
              <td colspan="4" class="loading-cell">
                <Loader2 :size="16" class="spin" />
                正在加载抓取画像库
              </td>
            </tr>
            <template v-else>
              <tr v-for="item in stageBCompanies" :key="item.domain.domain" @click="openDomainDetail(item.domain.domain)">
                <td>
                  <strong>{{ item.domain.domain }}</strong>
                  <span>{{ item.latest_crawl?.company_name || item.domain.display_name || item.domain.website }}</span>
                </td>
                <td>
                  <span :class="statusClass(item.latest_crawl?.status || item.domain.latest_status)">{{ statusText(item.latest_crawl?.status || item.domain.latest_status) }}</span>
                </td>
                <td>{{ item.contact_count }} 联系方式 · {{ item.profile_package_count }} JSON</td>
                <td>{{ item.latest_crawl?.description || item.domain.description || item.domain.website }}</td>
              </tr>
            </template>
            <tr v-if="!loadingLibrary && stageBCompanies.length === 0">
              <td colspan="4" class="empty-cell">当前筛选下没有已抓取企业。</td>
            </tr>
          </tbody>
        </table>

        <table v-else>
          <thead>
            <tr>
              <th>优先客户</th>
              <th>优先级</th>
              <th>画像</th>
              <th>评分</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingLibrary">
              <td colspan="4" class="loading-cell">
                <Loader2 :size="16" class="spin" />
                正在加载优先客户库
              </td>
            </tr>
            <template v-else>
              <tr v-for="item in stageCCompanies" :key="item.domain.domain" @click="openDomainDetail(item.domain.domain)">
                <td>
                  <strong>{{ item.domain.domain }}</strong>
                  <span>{{ item.qualified_lead?.segment || item.domain.website }}</span>
                </td>
                <td>{{ item.qualified_lead?.priority || "未定级" }}</td>
                <td>{{ item.company_profile?.summary || item.company_profile?.business_type || "待确认" }}</td>
                <td>{{ item.scores.map((score) => `${score.score_name}:${score.score_value}`).join(" / ") || "待评分" }}</td>
              </tr>
            </template>
            <tr v-if="!loadingLibrary && stageCCompanies.length === 0">
              <td colspan="4" class="empty-cell">优先客户库等待后续 AI / 人工确认写入。</td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="pager">
        <span>共 {{ libraryTotal.toLocaleString() }} 个企业 · 第 {{ libraryCurrentPage }} / {{ libraryTotalPages }} 页</span>
        <div>
          <button class="square-button" type="button" :disabled="!canLibraryGoPrevious" aria-label="上一页" @click="previousLibraryPage">
            <ChevronLeft :size="18" />
          </button>
          <button class="square-button" type="button" :disabled="!canLibraryGoNext" aria-label="下一页" @click="nextLibraryPage">
            <ChevronRight :size="18" />
          </button>
        </div>
      </footer>
    </section>

    <section v-if="activeModule === 'rawTables'" class="library-panel raw-table-panel" aria-label="审计 / 排错">
      <div class="library-header">
        <div>
          <p class="eyebrow">审计 / 排错</p>
          <h2>审计明细</h2>
        </div>
        <div class="library-stats">
          <span>{{ rawTableTotal.toLocaleString() }} 行</span>
          <span>{{ activeRawTableColumns.length }} 个字段</span>
        </div>
      </div>

      <div class="library-tabs" role="tablist" aria-label="审计 / 排错数据表">
        <button
          v-for="tab in rawTableTabs"
          :key="tab.value"
          type="button"
          :class="{ active: selectedRawTable === tab.value }"
          @click="setRawTable(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="library-toolbar raw-table-toolbar">
        <label class="search-field">
          <Search :size="16" />
          <input v-model="rawTableFilters.q" type="search" placeholder="全局搜索当前表" @keyup.enter="applyRawTableFilters" />
        </label>
        <input
          v-if="showRawCountryFilter"
          v-model="rawTableFilters.country"
          class="filter-input"
          type="text"
          placeholder="国家"
          @keyup.enter="applyRawTableFilters"
        />
        <select v-if="showRawStatusFilter" v-model="rawTableFilters.status" class="filter-select" @change="applyRawTableFilters">
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <input
          v-if="showRawEngineFilter"
          v-model="rawTableFilters.engine"
          class="filter-input"
          type="text"
          placeholder="搜索引擎"
          @keyup.enter="applyRawTableFilters"
        />
        <input
          v-if="showRawKeywordFilter"
          v-model="rawTableFilters.keyword"
          class="filter-input"
          type="text"
          placeholder="关键词"
          @keyup.enter="applyRawTableFilters"
        />
        <button class="icon-button primary" type="button" @click="applyRawTableFilters">
          <Search :size="16" />
          筛选
        </button>
        <button
          v-if="selectedRawTable === 'crawl_results'"
          class="icon-button primary"
          type="button"
          :disabled="selectedRawCrawlResultCount === 0 || exportingTaskRunResults || loadingRawTable"
          title="选中抓取结果后可导出"
          @click="exportCurrentCrawlTaskResultsXlsx"
        >
          <Loader2 v-if="exportingTaskRunResults" :size="16" class="spin" />
          <Download v-else :size="16" />
          导出XLSX
        </button>
      </div>

      <div class="table-wrap raw-table-wrap">
        <table>
          <thead>
            <tr>
              <th v-if="selectedRawTable === 'crawl_results'" class="selection-cell">
                <input
                  type="checkbox"
                  :checked="allCurrentPageRawCrawlResultsSelected"
                  :indeterminate.prop="someCurrentPageRawCrawlResultsSelected && !allCurrentPageRawCrawlResultsSelected"
                  aria-label="选择当前页全部抓取结果"
                  @change="toggleCurrentPageRawCrawlResults"
                />
              </th>
              <th v-for="column in activeRawTableColumns" :key="column.key">
                {{ column.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingRawTable">
              <td :colspan="rawTableColumnSpan" class="loading-cell">
                <Loader2 :size="16" class="spin" />
                正在加载审计 / 排错数据
              </td>
            </tr>
            <template v-else>
              <tr v-for="row in activeRawTableRows" :key="`${selectedRawTable}-${rawCellValue(row, 'id')}`" class="raw-row">
                <td v-if="selectedRawTable === 'crawl_results'" class="selection-cell">
                  <input
                    type="checkbox"
                    :checked="isRawCrawlResultSelected(row)"
                    aria-label="选择这条抓取结果"
                    @change="toggleRawCrawlResultSelection(row)"
                    @click.stop
                  />
                </td>
                <td v-for="column in activeRawTableColumns" :key="column.key" class="raw-cell" :title="rawCellValue(row, column.key)">
                  {{ rawCellValue(row, column.key) }}
                </td>
              </tr>
            </template>
            <tr v-if="!loadingRawTable && activeRawTableRows.length === 0">
              <td :colspan="rawTableColumnSpan" class="empty-cell">当前筛选下没有数据。</td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="pager">
        <span>共 {{ rawTableTotal.toLocaleString() }} 行 · 第 {{ rawTableCurrentPage }} / {{ rawTableTotalPages }} 页</span>
        <div>
          <label v-if="selectedRawTable === 'crawl_results'" class="page-size-control">
            最大显示条数
            <select :value="rawTableFilters.limit" @change="setRawTablePageSize">
              <option v-for="option in rawTablePageSizeOptions" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
          </label>
          <button class="square-button" type="button" :disabled="!canRawTableGoPrevious" aria-label="上一页" @click="previousRawTablePage">
            <ChevronLeft :size="18" />
          </button>
          <button class="square-button" type="button" :disabled="!canRawTableGoNext" aria-label="下一页" @click="nextRawTablePage">
            <ChevronRight :size="18" />
          </button>
        </div>
      </footer>
    </section>

    <section v-if="activeModule === 'aiProfiles'" class="library-panel ai-profile-panel" aria-label="AI画像分析">
      <div class="library-header">
        <div>
          <p class="eyebrow">AI画像分析</p>
          <h2>客户画像</h2>
        </div>
        <div class="library-stats">
          <span>{{ aiProfileTotal.toLocaleString() }} 份画像</span>
          <span>目录页 {{ aiProfileCurrentPage }} / {{ aiProfileTotalPages }}</span>
        </div>
      </div>

      <div class="library-toolbar ai-profile-toolbar">
        <label class="search-field">
          <Search :size="16" />
          <input v-model="aiProfileFilters.q" type="search" placeholder="搜索公司、地区、域名、摘要" @keyup.enter="applyAIProfileFilters" />
        </label>
        <input
          v-model="aiProfileFilters.priority"
          class="filter-input"
          type="text"
          placeholder="优先级 A/B/C/D"
          @keyup.enter="applyAIProfileFilters"
        />
        <input
          v-model="aiProfileFilters.model_name"
          class="filter-input"
          type="text"
          placeholder="模型名称"
          @keyup.enter="applyAIProfileFilters"
        />
        <select v-model="aiProfileFilters.status" class="filter-select" @change="applyAIProfileFilters">
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <button class="icon-button primary" type="button" @click="applyAIProfileFilters">
          <Search :size="16" />
          筛选
        </button>
      </div>

      <div v-if="loadingAIProfiles" class="loading-cell ai-profile-loading">
        <Loader2 :size="16" class="spin" />
        正在加载 AI 画像
      </div>

      <div v-else-if="rawAIProfileResultRows.length" class="ai-profile-directory-board">
        <aside class="ai-profile-directory" aria-label="画像目录">
          <header class="ai-directory-header">
            <div>
              <strong>画像目录</strong>
              <span>已选 {{ selectedAIProfileCount.toLocaleString() }} / {{ aiProfileTotal.toLocaleString() }}</span>
            </div>
            <div class="ai-directory-actions">
              <button class="text-button" type="button" title="全选当前筛选结果" @click="selectAllFilteredAIProfiles">
                {{ aiProfileFilteredSelectionActive ? "取消全选" : "全选" }}
              </button>
              <button class="text-button" type="button" :disabled="selectedAIProfileCount === 0" @click="clearAIProfileSelection">清空</button>
              <button
                class="icon-button primary compact"
                type="button"
                :disabled="selectedAIProfileCount === 0 || exportingAIProfiles"
                @click="exportSelectedAIProfiles"
              >
                <Loader2 v-if="exportingAIProfiles" :size="14" class="spin" />
                <FileJson v-else :size="14" />
                导出HTML报告
              </button>
            </div>
          </header>
          <div class="ai-profile-directory-list">
            <div
              v-for="result in rawAIProfileResultRows"
              :key="result.id"
              class="ai-directory-entry"
              :class="{ active: result.id === selectedAIProfileResultId && aiProfilePreviewOpen, selected: isAIProfileSelected(result) }"
            >
              <input
                type="checkbox"
                :checked="isAIProfileSelected(result)"
                :aria-label="`选择 ${companyNameForAIProfile(result)}`"
                @change="toggleAIProfileSelection(result)"
              />
              <button type="button" class="ai-directory-main" @click="openAIProfilePreview(result)">
                <span>
                  <strong>{{ companyNameForAIProfile(result) }}</strong>
                  <small>{{ regionForAIProfile(result) }}</small>
                </span>
                <span class="ai-directory-score">
                  <b>{{ result.score_total }}</b>
                  <i>{{ result.customer_priority || "未定级" }}</i>
                </span>
              </button>
            </div>
          </div>
        </aside>

        <div v-if="previewAIProfileResult" class="ai-profile-preview-backdrop" role="presentation" @click.self="closeAIProfilePreview">
          <div
            class="ai-profile-preview-modal"
            role="dialog"
            aria-modal="true"
            :aria-label="`画像预览 ${companyNameForAIProfile(previewAIProfileResult)}`"
          >
            <header class="ai-profile-preview-header">
              <div>
                <p class="eyebrow">画像预览</p>
                <h2>{{ previewAIProfileResult.company_name || previewAIProfileResult.domain }}</h2>
                <span>{{ previewAIProfileResult.country || "地区未识别" }} · {{ previewAIProfileResult.customer_priority || "未定级" }}</span>
              </div>
              <button class="square-button" type="button" aria-label="关闭画像预览" @click="closeAIProfilePreview">
                <XCircle :size="18" />
              </button>
            </header>

            <div class="ai-profile-preview-body">
              <article class="ai-profile-page">
                <header class="ai-profile-page-header">
                  <div>
                    <p class="eyebrow">画像 #{{ previewAIProfileResult.id }}</p>
                    <h2>{{ previewAIProfileResult.company_name || previewAIProfileResult.domain }}</h2>
                    <p>{{ previewAIProfileResult.domain }} · {{ previewAIProfileResult.country || "地区未识别" }}</p>
                    <p>画像包 #{{ previewAIProfileResult.profile_package_id }} · 任务 #{{ previewAIProfileResult.task_run_id || "未记录" }}</p>
                  </div>
                  <div class="ai-score-strip">
                    <span class="priority-badge">{{ previewAIProfileResult.customer_priority || "未定级" }}</span>
                    <strong>{{ previewAIProfileResult.score_total }}</strong>
                    <small>总分</small>
                  </div>
                </header>

                <div class="ai-meta-row">
                  <span>{{ previewAIProfileResult.model_provider }} / {{ previewAIProfileResult.model_name }}</span>
                  <span>{{ statusText(previewAIProfileResult.status) }}</span>
                  <span>{{ previewAIProfileResult.created_at || "未记录时间" }}</span>
                </div>

                <div class="ai-profile-report">
                  <section class="ai-profile-section profile-summary">
                    <h3>客户画像摘要</h3>
                    <div class="ai-profile-section-body">
                      <p>{{ previewAIProfileResult.profile_summary || "未记录" }}</p>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-product-fit">
                    <h3>产品匹配度</h3>
                    <div class="ai-profile-section-body">
                      <p>{{ previewAIProfileResult.product_fit || "未记录" }}</p>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-business-type">
                    <h3>业务类型</h3>
                    <div class="ai-profile-section-body">
                      <p>{{ previewAIProfileResult.business_type || "未记录" }}</p>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-market-role">
                    <h3>市场角色</h3>
                    <div class="ai-profile-section-body">
                      <p>{{ previewAIProfileResult.market_role || "未记录" }}</p>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-score">
                    <h3>评分明细</h3>
                    <div class="ai-profile-section-body">
                      <div class="score-breakdown">
                        <div v-for="[name, value] in Object.entries(previewAIProfileResult.score_breakdown_json || {})" :key="name">
                          <span>{{ name }}</span>
                          <strong>{{ value }}</strong>
                        </div>
                      </div>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-recommendation recommendation">
                    <h3>推荐动作</h3>
                    <div class="ai-profile-section-body">
                      <p>{{ previewAIProfileResult.recommended_action || "未记录" }}</p>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-contact-analysis">
                    <h3>联系方式分析</h3>
                    <div class="ai-profile-section-body">
                      <div v-if="Object.keys(previewAIProfileResult.contact_analysis || {}).length" class="contact-analysis-summary">
                        <div class="score-breakdown">
                          <div>
                            <span>联系质量</span>
                            <strong>{{ formatAIContactQuality(previewAIProfileResult.contact_analysis.contact_quality) }}</strong>
                          </div>
                          <div>
                            <span>可用渠道</span>
                            <strong>{{ (previewAIProfileResult.contact_analysis.available_channels || []).map(formatAIContactChannel).join("、") || "无" }}</strong>
                          </div>
                          <div>
                            <span>首选渠道</span>
                            <strong>{{ formatAIContactChannel(previewAIProfileResult.contact_analysis.preferred_channel || "none") }}</strong>
                          </div>
                        </div>
                        <div v-if="previewAIProfileResult.contact_analysis.recommended_contacts?.length" class="ai-profile-contact-list contact-analysis-recommendations">
                          <div v-for="(contact, index) in previewAIProfileResult.contact_analysis.recommended_contacts" :key="`ai-contact-${index}`" class="contact-row">
                            <Globe2 :size="15" />
                            <span>{{ contact.value || "未记录" }}</span>
                            <small>
                              {{ formatAIContactChannel(contact.type) }}
                              <template v-if="contact.label"> · {{ contact.label }}</template>
                              <template v-if="contact.reason"> · {{ contact.reason }}</template>
                            </small>
                          </div>
                        </div>
                        <p v-else class="muted">没有推荐的直接联系方式。</p>
                        <p class="contact-analysis-strategy">{{ previewAIProfileResult.contact_analysis.outreach_strategy || "未记录联系策略" }}</p>
                      </div>
                      <p v-else class="muted">旧画像暂无联系方式分析，请重新运行画像任务。</p>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-contacts">
                    <h3>对应联系方式</h3>
                    <div class="ai-profile-section-body">
                      <div v-if="previewAIProfileResult.contacts.length" class="ai-profile-contact-list">
                        <a v-for="contact in previewAIProfileResult.contacts" :key="contact.id" :href="contactHref(contact)" class="contact-row">
                          <Mail v-if="contact.kind === 'email'" :size="15" />
                          <Phone v-else-if="contact.kind === 'phone'" :size="15" />
                          <Globe2 v-else :size="15" />
                          <span>{{ contact.value }}</span>
                          <small>{{ contactDisplayMeta(contact) }}</small>
                        </a>
                      </div>
                      <p v-else class="muted">暂未提取到联系方式。</p>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-evidence">
                    <h3>证据</h3>
                    <div class="ai-profile-section-body">
                      <ul>
                        <li v-for="(item, index) in previewAIProfileResult.evidence_json" :key="`evidence-${index}`">{{ item }}</li>
                      </ul>
                    </div>
                  </section>

                  <section class="ai-profile-section profile-risks">
                    <h3>风险点</h3>
                    <div class="ai-profile-section-body">
                      <ul>
                        <li v-for="(item, index) in previewAIProfileResult.risk_flags_json" :key="`risk-${index}`">{{ item }}</li>
                      </ul>
                    </div>
                  </section>
                </div>

              </article>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-cell">当前筛选下没有 AI 画像结果。</div>

      <footer class="pager">
        <span>共 {{ aiProfileTotal.toLocaleString() }} 份画像 · 目录页 {{ aiProfileCurrentPage }} / {{ aiProfileTotalPages }}</span>
        <div class="pager-controls">
          <label class="page-size-control">
            <span>每页目录</span>
            <select v-model.number="aiProfileFilters.limit" @change="setAIProfileDirectoryPageSize">
              <option v-for="size in aiProfileDirectoryPageSizeOptions" :key="size" :value="size">{{ size }}</option>
            </select>
          </label>
          <button class="square-button" type="button" :disabled="!canAIProfileGoPrevious" aria-label="上一页目录" @click="previousAIProfilePage">
            <ChevronLeft :size="18" />
          </button>
          <button class="square-button" type="button" :disabled="!canAIProfileGoNext" aria-label="下一页目录" @click="nextAIProfilePage">
            <ChevronRight :size="18" />
          </button>
        </div>
      </footer>
    </section>

    <section v-if="activeModule === 'customers'" class="workspace">
      <section class="list-pane" aria-label="客户池">
        <div class="toolbar">
          <label class="search-field">
            <Search :size="16" />
            <input v-model="filters.q" type="search" placeholder="搜索域名、官网、公司名、简介" @keyup.enter="applyFilters" />
          </label>
          <input v-model="filters.country" class="filter-input" type="text" placeholder="国家信号" @keyup.enter="applyFilters" />
          <select v-model="filters.status" class="filter-select" @change="applyFilters">
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <button class="icon-button primary" type="button" @click="applyFilters">
            <Search :size="16" />
            筛选
          </button>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>客户域名</th>
                <th>抓取状态</th>
                <th>官网简介</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingDomains">
                <td colspan="3" class="loading-cell">
                  <Loader2 :size="16" class="spin" />
                  正在加载客户池
                </td>
              </tr>
              <template v-else>
                <tr
                  v-for="domain in domains"
                  :key="domain.domain"
                  :class="{ selected: selectedDomain === domain.domain }"
                  @click="loadDomainDetail(domain.domain)"
                >
                  <td>
                    <strong>{{ domain.domain }}</strong>
                    <span>{{ displayName(domain) }}</span>
                  </td>
                  <td>
                    <span :class="statusClass(domain.latest_status)">{{ statusText(domain.latest_status) }}</span>
                  </td>
                  <td>{{ domain.description || domain.website }}</td>
                </tr>
              </template>
              <tr v-if="!loadingDomains && domains.length === 0">
                <td colspan="3" class="empty-cell">当前筛选下没有客户。</td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="pager">
          <span>共 {{ total.toLocaleString() }} 个客户 · 第 {{ currentPage }} / {{ totalPages }} 页</span>
          <div>
            <button class="square-button" type="button" :disabled="!canGoPrevious" aria-label="上一页" @click="previousPage">
              <ChevronLeft :size="18" />
            </button>
            <button class="square-button" type="button" :disabled="!canGoNext" aria-label="下一页" @click="nextPage">
              <ChevronRight :size="18" />
            </button>
          </div>
        </footer>
      </section>

      <aside class="detail-pane" aria-label="客户详情">
        <div v-if="loadingDetail" class="detail-loading">
          <Loader2 :size="18" class="spin" />
          正在加载画像素材
        </div>
        <template v-else-if="selectedDetail">
          <div class="detail-header">
            <div>
              <p class="eyebrow">当前客户</p>
              <h2>{{ selectedDetail.domain.domain }}</h2>
              <p>{{ selectedDetail.domain.description || selectedDetail.domain.website }}</p>
            </div>
            <a class="square-button" :href="selectedDetail.domain.website" target="_blank" rel="noreferrer" aria-label="打开官网">
              <ExternalLink :size="18" />
            </a>
          </div>

          <section class="detail-section">
            <h3><Globe2 :size="16" /> 官网入口</h3>
            <a :href="selectedDetail.domain.website" target="_blank" rel="noreferrer">{{ selectedDetail.domain.website }}</a>
          </section>

          <section class="detail-section">
            <h3><Users :size="16" /> 联系方式</h3>
            <div v-if="selectedDetail.contacts.length" class="item-list">
              <a v-for="contact in selectedDetail.contacts.slice(0, 12)" :key="contact.id" :href="contactHref(contact)" class="contact-row">
                <Mail v-if="contact.kind === 'email'" :size="15" />
                <Phone v-else-if="contact.kind === 'phone'" :size="15" />
                <Globe2 v-else :size="15" />
                <span>{{ contact.value }}</span>
                <small>{{ contactDisplayMeta(contact) }}</small>
              </a>
            </div>
            <p v-else class="muted">暂未提取到联系方式。</p>
          </section>

          <section class="detail-section">
            <h3><Flag :size="16" /> 国家信号</h3>
            <div v-if="selectedDetail.country_signals.length" class="signal-list">
              <div v-for="signal in selectedDetail.country_signals.slice(0, 8)" :key="signal.id" class="signal-row">
                <strong>{{ signal.country }}</strong>
                <span>{{ signal.signal_type }}</span>
                <small>{{ Math.round(signal.confidence * 100) }}%</small>
              </div>
            </div>
            <p v-else class="muted">暂未记录国家信号。</p>
          </section>

          <section class="detail-section">
            <h3><FileJson :size="16" /> 画像 JSON</h3>
            <div v-if="selectedDetail.profile_packages.length" class="item-list">
              <div v-for="profile in selectedDetail.profile_packages.slice(0, 6)" :key="profile.id" class="profile-row">
                <span>画像包 #{{ profile.id }}</span>
                <small>{{ profile.page_count }} 页 · {{ statusText(profile.crawl_status) }}</small>
                <small v-if="profile.content_hash">hash {{ profile.content_hash.slice(0, 12) }}</small>
              </div>
            </div>
            <p v-else class="muted">暂未生成画像 JSON。</p>
          </section>
        </template>
        <div v-else class="empty-detail">选择一个客户查看画像素材。</div>
      </aside>
    </section>
    </section>
  </main>
</template>
