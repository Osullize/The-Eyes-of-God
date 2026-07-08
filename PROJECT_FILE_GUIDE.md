# 项目文件说明

最后更新：2026-06-26

这份文档用来说明项目里的文件分别是干什么的，以及哪些文件属于源码、配置、运行状态、搜索输出、爬取输出或 AI 分析输出。

## 主流程

```text
数据库关键词组 keyword_groups
        |
        v
控制台找官网 / scripts/run_task.py search --database-url "$DATABASE_URL"
        |
        v
数据库表 A: domains + search_results + country_signals
候选组表: candidate_groups + candidate_group_items（长期保存搜索输出域名组）
数据库任务表: task_runs + task_items（记录搜索任务批次和关键词执行项）
        |
        +----> company_websites_*.csv（仅 CLI 兼容备份 / 审计文件）
        |
        v
控制台 / 任务封装从候选组或阶段 A 数据库选择待抓取企业
        |
        v
数据库表 B: crawl_results + contacts + profile_packages + country_signals
数据库任务表: task_runs + task_items（记录抓取任务批次和域名执行项）
        |
        +----> profile_inputs/<country>/<domain>.json（保留为 AI 输入素材）
        +----> company_info_*.csv（仅 CLI 兼容备份）
        |
        v
画像分析 Codex / skill 或后续 AI 服务（待实现为后台节点）
        |
        v
数据库表 C: qualified_leads + company_profiles + lead_scores（待实现）
```

## 源码文件

这些文件是项目逻辑，不要删除。

| 路径 | 用途 |
| --- | --- |
| `run_search.py` | 搜索主入口。可读取数据库关键词组或兼容 YAML，调用 DuckDuckGo/Bing，配置数据库连接后写入 `domains` / `search_results`；CLI 仍可输出 `company_websites*.csv`。 |
| `run_crawl.py` | 爬取主入口。可读取数据库候选企业或兼容 CSV 输入，抓取公司网站后写入 `crawl_results` / `contacts` / `profile_packages`，并保留画像 JSON 输入包。 |
| `find_url.py` | 搜索兼容入口。 |
| `find_messsage.py` | 爬取兼容入口。 |
| `config/keywords.py` | 加载关键词 YAML，并生成搜索关键词组合。 |
| `config/search.py` | 加载搜索运行配置。 |
| `search/` | 搜索引擎、聚合逻辑、URL 过滤逻辑。 |
| `crawl/` | requests/browser 抓取器、站内链接探索、内容提取逻辑。 |
| `pipeline/` | CSV 写入和 CLI 兼容状态记录工具；控制台主流程改用数据库任务批次。 |
| `profile_analysis/` | 为画像分析构建每家公司一个 JSON 输入包。 |
| `database/` | SQLAlchemy 数据库模型、session 工具、关键词组服务、候选组服务、任务批次服务、阶段落库工具、CSV/JSON 导入器和后端读查询。 |
| `api/` | FastAPI 后端入口；当前提供健康检查、数据库读接口、候选组接口和任务执行接口。 |
| `frontend/` | Vue3 控制台，用来管理关键词组、候选组、任务中心、数据库统计、企业库 A/B/C、客户列表和客户详情。 |
| `tasks/` | 任务封装层；把 search/crawl/import 包成可复用 handler，搜索和抓取完成后会调用数据库阶段落库工具，并提供 Celery worker 入口。 |
| `scripts/import_existing_data.py` | 把现有搜索 CSV、爬取 CSV、profile JSON 导入 SQLite/PostgreSQL。 |
| `scripts/run_task.py` | 当前的统一任务入口；搜索和抓取任务在配置数据库后会写入 `task_runs` / `task_items`，同时返回本次执行结果。 |
| `alembic/` / `alembic.ini` | 数据库迁移配置和初始表结构。 |
| `tests/` | 单元测试。 |

## 关键词配置文件

控制台主流程使用数据库表 `keyword_groups` 决定搜索什么。下面这些 YAML 文件保留为 CLI 兼容配置和导入来源。

| 路径 | 用途 |
| --- | --- |
| `config/keywords.yaml` | 最早的多国家实验配置：Turkey、Germany、UAE。 |
| `config/keywords_france.yaml` | France 主关键词集：泳池热泵、泳池加热、泳池加热分销。 |
| `config/keywords_france_complement.yaml` | France 互补关键词集：通用热泵 / HVAC / contractor / distributor 词。 |
| `config/keywords_uk.yaml` | UK 主关键词集：最初那套通用热泵 / HVAC / contractor / distributor 词。 |
| `config/keywords_uk_complement.yaml` | UK 互补关键词集：泳池热泵 / 泳池加热相关词。 |
| `config/search.yaml` | 默认搜索运行参数；命令行参数可以覆盖它。 |

推荐模式：一个国家或一个业务主题一个数据库关键词组；控制台主流程直接写数据库，不再需要搜索输出 CSV，也不再需要手写 YAML。

## 搜索输出

这些文件保存搜索阶段发现的公司官网或候选网站 URL，由 `run_search.py` 的 CLI 兼容模式生成。控制台主流程配置 `DATABASE_URL` 后会直接写入数据库的 `domains`、`search_results`、`country_signals`，不再需要这些 CSV 文件作为阶段输入。

| 文件 | 当前状态 |
| --- | --- |
| `company_websites.csv` | 原始混合国家搜索输出。525 行，524 个唯一域名。 |
| `company_websites_france.csv` | France 搜索输出。315 行，315 个唯一域名。已包含互补搜索结果。 |
| `company_websites_uk.csv` | UK 搜索输出。484 行，484 个唯一域名。已包含互补搜索结果。 |
| `company_websites_success_missing_json.csv` | 临时回填输入表，用于补跑那些曾经 success 但缺少 JSON 的旧域名。只有想保留审计记录时才需要继续保留。 |

## 爬取输出

这些文件保存从官网提取出的公司信息，由 `run_crawl.py` 的 CLI 兼容模式生成。控制台主流程会从阶段 A 数据库表选择候选企业，抓取后直接写入 `crawl_results`、`contacts`、`profile_packages`、`country_signals`；画像 JSON 继续保留为 AI 输入素材。

| 文件 | 当前状态 |
| --- | --- |
| `company_info.csv` | 原始混合国家爬取输出。525 行：483 个 `success`，42 个 `empty`。 |
| `company_info_france.csv` | France 爬取输出。149 行：132 个 `success`，17 个 `empty`。注意：它还没追上当前 France 搜索结果里的 315 个域名。 |
| `company_info_uk.csv` | UK 爬取输出。320 行：294 个 `success`，26 个 `empty`。注意：它还没追上当前 UK 搜索结果里的 484 个域名。 |
| `company_info_success_missing_json_backfill.csv` | 针对旧 success 但缺 JSON 域名的回填爬取输出。159 行：157 个 `success`，2 个 `empty`。 |

## 运行状态目录

这些目录现在只用于 CLI 兼容模式的断点续跑。控制台主流程已经用数据库 `task_runs` / `task_items` 记录任务批次、执行项、失败项和统计，不再要求用户手动选择这些目录。

| 目录 | 用途 |
| --- | --- |
| `.search_state/` | 原始混合国家搜索状态。 |
| `.search_state_france/` | France 主搜索状态。 |
| `.search_state_france_complement/` | France 互补搜索状态。 |
| `.search_state_uk/` | UK 主搜索状态。 |
| `.search_state_uk_complement/` | UK 互补搜索状态。 |
| `.crawl_state/` | 原始混合国家爬取状态。 |
| `.crawl_state_france/` | France 爬取状态。 |
| `.crawl_state_uk/` | UK 爬取状态。 |
| `.crawl_state_success_missing_json_backfill/` | 针对 success 但缺 JSON 域名的回填爬取状态。 |

除非你在手动运行 CLI 并明确想复用旧进度，否则不要把同一个状态目录混用于不同国家或不同输入文件。

## 画像 JSON 输入包

这些 JSON 文件是给画像分析 Codex / skill 使用的输入材料。

| 路径 | 用途 |
| --- | --- |
| `profile_inputs/*.json` | 原始混合国家画像输入包。当前根目录下有 481 个 JSON 文件。 |
| `profile_inputs/france/*.json` | France 画像输入包。当前有 132 个 JSON 文件。 |
| `profile_inputs/uk/*.json` | UK 画像输入包。当前有 294 个 JSON 文件。 |
| `profile_inputs/.codex/skills/analyze-heat-pump-lead-profile/` | 项目级 Codex skill，用来分析这些 JSON 文件。 |
| `profile_inputs/scripts/` | 画像分析过程中创建的分析 / 报告辅助脚本。 |

正常情况下，每个成功爬取的域名对应一个 JSON 文件：

```text
profile_inputs/<country>/<domain>.json
```

## AI 分析输出

这些文件是在画像 JSON 分析之后生成的，不是爬虫本身直接生成的。

| 路径 | 用途 |
| --- | --- |
| `profile_inputs/heat_pump_lead_analysis_outputs/batch_2026-06-22_new_only/` | 早期针对原始 / 混合数据的批量画像分析输出。 |
| `profile_inputs/heat_pump_lead_analysis_outputs/france_2026-06-23/` | France 画像分析输出。 |
| `profile_inputs/heat_pump_lead_analysis_outputs/uk_2026-06-24/` | UK 画像分析输出。 |
| `profile_inputs/heat_pump_lead_analysis_outputs/*.md` / `*.html` / `*.csv` / `*.json` | 人可读报告、排序表、摘要和机器可读分析结果。 |

## 数据库文件

这些文件是把项目从本地 CSV 工具升级为后端平台的第一步。

| 路径 | 用途 |
| --- | --- |
| `requirements.txt` | 项目依赖清单，包含爬虫依赖和数据库依赖。 |
| `database/models.py` | 表结构模型：`domains`、`search_results`、`crawl_results`、`contacts`、`profile_packages`、`country_signals`、`task_runs`、`task_items`、`candidate_groups`、`candidate_group_items`。 |
| `database/importers.py` | 从搜索/抓取返回行或现有 `company_websites*.csv`、`company_info*.csv`、`profile_inputs/**/*.json` 导入数据库。 |
| `database/keyword_groups.py` | 关键词组 CRUD、数据库关键词生成、旧 YAML 关键词导入。 |
| `database/candidate_groups.py` | 候选组创建、列表、详情、统计和按组选择抓取候选域名。 |
| `database/task_batches.py` | 数据库任务批次和执行项的创建、状态更新、统计和序列化。 |
| `database/stage_persistence.py` | 搜索阶段和抓取阶段共用的落库工具；`run_search.py`、`run_crawl.py`、`tasks/handlers.py` 都复用它。 |
| `database/queries.py` | 为 FastAPI 提供统计、域名列表、域名详情、联系人、profile 包和国家信号查询。 |
| `database/session.py` | 创建数据库 engine/session，以及本地建表工具。 |
| `api/app.py` | FastAPI 应用入口，包含 `/health`、`/runtime`、`/database/stats`、`/domains`、`/domains/{domain}`、`/candidate-groups`、`/task-runs` 和 `/tasks/*` 接口。 |
| `api/schemas.py` | FastAPI 请求模型。 |
| `frontend/package.json` | Vue3 控制台依赖和脚本：`npm run dev`、`npm run build`。 |
| `frontend/src/App.vue` | 控制台主界面：统计、任务面板、候选组、任务中心、企业库 A/B/C、筛选列表、分页、客户详情。 |
| `frontend/src/api.ts` | 前端调用 FastAPI 的 API client，包括读接口、任务提交和任务状态查询。 |
| `frontend/src/style.css` | 控制台布局和样式。 |
| `tasks/handlers.py` | `search`、`crawl`、`import_existing_data` 三类任务的业务封装；搜索 handler 生成候选组，抓取 handler 可按候选组读取域名并写入数据库。 |
| `tasks/runner.py` | 进程内任务 runner，负责返回 `success` / `failed`、耗时、摘要和错误。 |
| `tasks/celery_app.py` | Celery 应用配置，默认 Redis broker/backend。 |
| `tasks/celery_tasks.py` | Celery worker 任务入口，内部复用 `tasks/handlers.py`。 |
| `scripts/import_existing_data.py` | 导入脚本；默认可导入当前项目已存在的 CSV 和 JSON。 |
| `scripts/import_keyword_groups.py` | 把旧 `config/keywords_*.yaml` 导入数据库关键词组。 |
| `scripts/run_task.py` | 统一任务 CLI；未来 Celery worker 可以直接复用 `tasks/handlers.py`。 |
| `alembic/versions/20260625_0001_database_foundation.py` | 第一版数据库迁移。 |

本地 SQLite 导入示例：

```bash
python scripts/import_existing_data.py --database-url sqlite:///leadgen.db
```

服务器 PostgreSQL 导入示例：

```bash
python scripts/import_existing_data.py \
  --database-url postgresql+psycopg://user:password@host:5432/leadgen
```

## 文档和工作记录

| 路径 | 用途 |
| --- | --- |
| `README.md` | 主要使用说明。 |
| `AI_WORKLOG.md` | 持续记录关键对话和工作会话。 |
| `docs/profile-analysis-agent-prompt.md` | 给单独画像分析 Codex 使用的提示词。 |
| `docs/superpowers/` | 开发过程中创建的设计文档和实现计划。 |
| `PROJECT_FILE_GUIDE.md` | 当前这份文件说明文档。 |

## 生成文件或本地工具文件

这些是本地生成文件，不是核心业务数据。

| 路径 | 说明 |
| --- | --- |
| `__pycache__/`, `*/__pycache__/` | Python 字节码缓存。可以重新生成。 |
| `.DS_Store`, `profile_inputs/.DS_Store` | macOS Finder 元数据。可以重新生成。 |
| `.idea/` | 本地 IDE 项目文件。如果你使用该 IDE 可以保留，否则不是核心项目逻辑。 |
| `.understand-anything/` | 代码知识图谱插件数据。如果你使用知识图谱视图可以保留。 |
| `.worktrees/` | 本地 git worktree 存放目录。通常应该为空或被忽略。 |

## 当前需要记住的缺口

France 和 UK 的搜索输出已经通过互补搜索扩展过，但爬取输出还没有完全追上：

```text
France search domains: 315
France crawled domains: 149

UK search domains: 484
UK crawled domains: 320
```

如果要继续爬取新发现的 France 域名，继续使用同一套 France 输出 / 状态 / 画像目录：

```bash
python run_crawl.py \
  --database-url "$DATABASE_URL" \
  --input company_websites_france.csv \
  --output company_info_france.csv \
  --state-dir .crawl_state_france \
  --backend requests \
  --workers 3 \
  --max-depth 2 \
  --max-pages-per-site 12 \
  --global-delay 1 \
  --domain-delay 3 \
  --max-retries 2 \
  --profile-input-dir profile_inputs/france
```

如果要继续爬取新发现的 UK 域名：

```bash
python run_crawl.py \
  --input company_websites_uk.csv \
  --output company_info_uk.csv \
  --state-dir .crawl_state_uk \
  --backend requests \
  --workers 3 \
  --max-depth 2 \
  --max-pages-per-site 12 \
  --global-delay 1 \
  --domain-delay 3 \
  --max-retries 2 \
  --profile-input-dir profile_inputs/uk
```

因为复用了相同的状态目录、输出文件和画像目录，所以已经完成的域名会被跳过，新域名会被继续追加并按域名去重。
