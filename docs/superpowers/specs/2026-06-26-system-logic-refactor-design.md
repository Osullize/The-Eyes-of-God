# 系统逻辑重构设计

## 背景

当前系统已经从脚本工具扩展出数据库、FastAPI 和 Vue 控制台，但系统逻辑仍然混合了两套时代的概念：

- 旧脚本时代：CSV 文件、`profile_inputs` JSON、本地 `.search_state` / `.crawl_state` 目录负责串联流程。
- 数据库时代：搜索、抓取、画像和企业库已经开始写入 PostgreSQL。

结果是用户在控制台里同时看到业务动作、文件路径、状态目录、历史导入和工程参数。真正的问题不是界面排版，而是系统的“事实来源”没有统一。

本设计目标是把系统收束为一条数据库主流程：

```text
关键词组
  -> 搜索任务
  -> A 官网候选库
  -> 抓取任务
  -> B 抓取素材库
  -> AI / 人工确认任务
  -> C 优先客户库
```

## 设计原则

1. 数据库是业务事实来源。
   业务阶段、任务进度、企业状态、抓取结果和画像素材索引都应以数据库为准。

2. 文件是附件或兼容入口，不是主流程控制点。
   CSV 只用于历史导入或导出；JSON 是画像素材附件，不负责判断企业在哪个阶段。

3. 任务进度不能再依赖本地状态目录。
   搜索和抓取是否完成、失败、跳过，应记录在数据库任务批次表里。

4. A/B/C 是业务阶段，不是简单的“有没有某张结果表”。
   阶段定义必须明确，失败数据不能混进“有效画像库”的业务含义里。

5. 脚本能力保留，产品流程收敛。
   `run_search.py` 和 `run_crawl.py` 可以继续作为底层执行引擎，但控制台不再暴露 CSV 和本地 state 目录。

## 目标业务阶段

### 关键词组

关键词组是搜索输入，不是任务结果。

现有表：

- `keyword_groups`

职责：

- 存储国家、国家词、业务关键词、备注和启用状态。
- 搜索任务只能选择启用的关键词组。
- 修改关键词组不会自动重跑历史任务；新任务会读取最新关键词组配置。

### A：官网候选库

A 阶段表示“搜索发现的潜在官网候选”，还没有经过站内抓取。

核心表：

- `domains`
- `search_results`
- `country_signals`

阶段进入规则：

- 搜索任务拿关键词组生成搜索词。
- 每个搜索结果归一化出 domain。
- domain 写入 `domains`。
- 搜索命中写入 `search_results`。
- 国家来源、关键词国家、搜索词国家写入 `country_signals`。

A 阶段展示规则：

- A 库展示有搜索发现记录的 domain。
- A 库可以显示搜索次数、最新搜索词、来源搜索引擎、国家信号。
- A 库不表示客户质量，只表示“发现过”。

### B：抓取素材库

B 阶段表示“已经尝试抓官网，并形成了抓取结果或画像素材状态”。

核心表：

- `domains`
- `crawl_results`
- `contacts`
- `profile_packages`
- `country_signals`

需要拆清楚的 B 内部状态：

- `crawled_success`：抓取成功，有可用页面和基础画像素材。
- `crawled_empty`：访问过但没有抓到有效页面。
- `crawl_failed`：抓取失败，可重试。
- `crawl_error`：程序异常或不可恢复错误。

阶段进入规则：

- 抓取任务只能从 A 阶段选择候选，除非用户明确选择重抓。
- 每个被选择的 domain 都应产生一个任务项。
- 抓取结束后写入 `crawl_results`。
- 成功抓取时生成画像 JSON 附件，并在 `profile_packages` 中登记路径、页数、状态和来源。
- 从抓取结果和 JSON 中抽取联系方式写入 `contacts`。

B 阶段展示规则：

- B 库应默认展示 `crawled_success`。
- 失败、空结果、异常不应混在默认 B 库里，而应作为 B 阶段的子筛选或“待处理问题”。
- B 库可以显示最新抓取状态、联系方式数量、画像 JSON 数量、国家信号。

### C：优先客户库

C 阶段表示“经过 AI 或人工确认，值得销售优先跟进的客户”。

核心表：

- `qualified_leads`
- `company_profiles`
- `lead_scores`

阶段进入规则：

- C 阶段只能由确认任务写入。
- 确认任务输入来自 B 阶段的成功抓取素材。
- 第一版确认任务可以先人工触发；AI 推理后续接入。

C 阶段展示规则：

- C 库展示优先级、客户画像摘要、评分理由、销售状态。
- C 阶段数据不能仅因为某公司被抓取成功就自动产生。

## 任务批次设计

引入数据库任务表，替代 `.search_state` 和 `.crawl_state`。

### `task_runs`

一条记录表示一次用户发起的任务。

建议字段：

- `id`
- `task_type`：`search` / `crawl` / `confirm` / `legacy_import`
- `name`：用户可读任务名，例如“France pool heat pump search 2026-06-26”
- `status`：`pending` / `running` / `success` / `partial_failed` / `failed` / `cancelled`
- `params_json`：任务参数快照
- `summary_json`：结果统计
- `created_at`
- `started_at`
- `finished_at`
- `created_by`

### `task_items`

一条记录表示任务中的一个最小执行单元。

搜索任务中，一个 item 是一个搜索关键词组合。

抓取任务中，一个 item 是一个 domain。

确认任务中，一个 item 是一个 domain 或一个 profile package。

建议字段：

- `id`
- `task_run_id`
- `item_type`：`keyword` / `domain` / `profile`
- `item_key`：关键词文本或 domain
- `domain_id`
- `status`：`pending` / `running` / `success` / `empty` / `failed` / `skipped`
- `attempt_count`
- `error`
- `result_json`
- `started_at`
- `finished_at`

### 任务状态规则

- 搜索任务是否跳过某关键词，由 `task_items` 和搜索结果决定，不再由 `.search_state` 决定。
- 抓取任务是否跳过某 domain，由 `task_items`、`crawl_results` 和用户选择的重抓策略决定，不再由 `.crawl_state` 决定。
- 用户想补失败时，系统查询上一次任务的失败 item，生成新任务，而不是读取本地 CSV 或 state 文件。

## 文件策略

### CSV

CSV 降级为系统维护能力：

- 历史数据导入。
- 手动导出报表。
- 调试时的临时文件。

CSV 不再是控制台主流程的输入或输出。

### 画像 JSON

画像 JSON 暂时保留为文件附件，但必须由数据库登记。

当前做法：

- JSON 文件保存到 `profile_inputs/...`。
- `profile_packages` 记录路径和元数据。

目标做法：

- 第一阶段继续保留文件路径，系统自动生成目录，用户不需要手填。
- 第二阶段可以在 `profile_packages` 增加 `content_json` 或 `storage_uri`：
  - 本地部署可存数据库 JSONB。
  - 服务器部署可存对象存储路径。

用户不应该通过文件夹来判断企业是否进入 B 阶段；B 阶段以数据库为准。

## 后端流程调整

### 搜索任务

目标接口：

```text
POST /tasks/search
```

输入：

- `keyword_group_id`
- `name`
- `max_keywords`
- `max_pages`
- `engines`
- `runtime_options`

处理流程：

1. 创建 `task_runs`。
2. 从 `keyword_groups` 生成关键词组合。
3. 创建 `task_items`。
4. 逐个 item 执行搜索。
5. 每个 item 更新状态。
6. 搜索结果写入 `domains`、`search_results`、`country_signals`。
7. 更新任务统计。

### 抓取任务

目标接口：

```text
POST /tasks/crawl
```

输入：

- `name`
- `country`
- `query`
- `max_companies`
- `recrawl_policy`
- `runtime_options`

处理流程：

1. 创建 `task_runs`。
2. 从 A 阶段查询候选 domain。
3. 根据重抓策略过滤：
   - `skip_existing_success`
   - `retry_failed_only`
   - `recrawl_all_selected`
4. 创建 `task_items`。
5. 逐个 domain 抓取。
6. 写入 `crawl_results`。
7. 成功时生成并登记 `profile_packages`。
8. 抽取并写入 `contacts`、`country_signals`。
9. 更新任务统计。

### 确认任务

目标接口：

```text
POST /tasks/confirm
```

第一版可以是人工确认或规则确认，AI 后续接入。

处理流程：

1. 从 B 阶段成功抓取素材选择 domain。
2. AI 或人工生成客户画像和评分。
3. 写入 `company_profiles`、`lead_scores`。
4. 对符合标准的客户写入 `qualified_leads`。

## 前端信息架构

左侧模块应围绕业务流程，而不是技术产物：

```text
获客任务
企业库
关键词中心
任务中心
系统维护
```

### 获客任务

只放日常动作：

- 新建搜索任务。
- 新建抓取任务。
- 新建确认任务。

用户看到的是：

- 选择关键词组。
- 选择国家。
- 本次最多处理多少公司。
- 是否重跑已处理公司。
- 高级参数折叠。

用户不再看到：

- 搜索状态目录。
- 抓取状态目录。
- CSV 输入输出。
- 画像 JSON 文件夹路径。

### 企业库

保留 A/B/C，但定义更清楚：

- A：搜索发现的官网候选。
- B：已抓取成功的画像素材库。
- C：确认后的优先客户库。

B 库需要附带子状态：

- 抓取成功。
- 空结果。
- 失败待重试。
- 异常。

### 任务中心

新增模块，展示 `task_runs` 和 `task_items`：

- 任务列表。
- 任务状态。
- 成功/失败/跳过数量。
- 失败项重试。
- 任务详情。

这会替代现在用户理解困难的状态目录。

### 系统维护

放低频和兼容功能：

- 历史 CSV / JSON 导入。
- 数据库连接检查。
- 数据导出。
- 文件附件清理。
- 旧 state 目录迁移。

## 迁移策略

### 第一阶段：建立任务表，不移除旧引擎

- 新增 `task_runs`、`task_items`。
- 保留 `run_search.py` 和 `run_crawl.py` 的核心搜索/抓取逻辑。
- 新任务 handler 负责创建 task run 和 item。
- 底层执行完后同步写任务 item 状态。
- 控制台不再让用户填写 state 目录。

### 第二阶段：重做任务中心和 A/B/C 查询

- 前端新增任务中心。
- A/B/C 企业库按新阶段定义展示。
- B 库默认只显示成功抓取，失败和空结果作为子筛选。
- 企业详情页展示该公司相关搜索记录、抓取记录、画像附件和任务历史。

### 第三阶段：降级历史文件入口

- `历史数据导入` 移入系统维护。
- CSV 入口保留，但不出现在主任务流程。
- 画像 JSON 目录由系统自动生成。
- 旧 `.search_state` / `.crawl_state` 只提供一次性迁移或忽略。

### 第四阶段：接入确认 / AI 节点

- 新增确认任务。
- 从 B 成功素材生成 C 阶段画像、评分、优先级。
- AI 推理失败不会影响 B 阶段数据，只会形成确认任务失败项。

## 兼容策略

- CLI 可以继续支持 CSV 和 state 目录，作为开发和应急工具。
- FastAPI / Vue 控制台应使用数据库任务批次，不再暴露 state 目录。
- 旧 CSV 数据可继续导入现有基础表。
- 已有 `profile_inputs` JSON 继续通过 `profile_packages` 索引。

## 成功标准

实现后，用户应能用业务语言理解系统：

1. 我先配置关键词组。
2. 我创建搜索任务，搜索结果进入 A 库。
3. 我从 A 库创建抓取任务，成功抓取的企业进入 B 库。
4. 我从 B 库创建确认任务，优先客户进入 C 库。
5. 我在任务中心看每次任务的进度、失败项和重试。
6. 我不需要理解 CSV、状态目录或本地文件结构，除非做系统维护。

## 不在本轮设计内

- 不设计 AI 打分提示词和评分标准细节。
- 不移除现有 CLI。
- 不要求马上把完整 JSON 存入数据库。
- 不改变当前 scraping 引擎和抓取算法。
- 不强制引入 Celery；任务表设计兼容 inline 和 Celery 两种执行模式。

