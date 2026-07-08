# AI Project Handoff

最后更新：2026-06-30

这份文档给下一个接手本项目的 AI 使用。请先读本文件，再读 `PROJECT_FILE_GUIDE.md`、`README.md`、`AI_WORKLOG.md`。

## 0. 最重要的路径

当前主要实现不在项目根目录直接开发，而是在这个 worktree：

```text
/Users/zhize/The Eyes of God/.worktrees/database-foundation
```

用户常用项目根目录是：

```text
/Users/zhize/The Eyes of God
```

如果你从根目录接手，先进入：

```bash
cd "/Users/zhize/The Eyes of God/.worktrees/database-foundation"
```

## 1. 项目目标

用户公司是热泵制造商，核心产品是热泵本身。项目目标是搭建一个海外客户线索系统，用搜索和爬虫找到潜在客户官网，抓取公司信息，建立画像素材，后续再接 AI 推理和评分。

业务主线：

```text
关键词组 -> 找官网 -> 阶段 A 候选企业库
候选组 / 阶段 A -> 抓官网 -> 阶段 B 抓取画像库
后续 AI / 人工确认 -> 阶段 C 优先客户库
```

当前阶段重点是前两步：找官网、抓官网、所有阶段数据入数据库，并在前端控制台操作。

## 2. 当前架构

后端：

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- 旧 CLI 仍兼容 CSV/YAML

前端：

- Vue 3
- TypeScript
- Vite
- lucide-vue-next

爬取和搜索：

- `run_search.py`
- `run_crawl.py`
- `search/`
- `crawl/`
- 浏览器模式仍沿用现有 Scrapling/browser 抓取框架，不要替换爬虫核心。

任务封装：

- `tasks/handlers.py`
- `tasks/runner.py`
- 当前默认是 inline 模式。
- Celery 文件已存在，但不是当前主流程。

## 3. 数据库连接

本机 PostgreSQL 当前使用：

```text
postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen
```

常用环境变量：

```bash
export DATABASE_URL='postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen'
```

迁移命令必须在 worktree 目录运行：

```bash
cd "/Users/zhize/The Eyes of God/.worktrees/database-foundation"
alembic upgrade head
```

曾经出现过的问题：

- 在项目根目录直接跑 `alembic upgrade head` 会报 `No 'script_location' key found in configuration`，因为根目录没有当前 worktree 的 `alembic.ini`。
- `DATABASE_URL` 不要换行，之前用户误把换行放进连接串，导致用户名变成 `"\n  leadgen"`。

## 4. 当前服务状态

截至本次交接，服务正在运行：

```text
FastAPI: http://127.0.0.1:8000
Vue:     http://127.0.0.1:5173
```

后端启动命令：

```bash
cd "/Users/zhize/The Eyes of God/.worktrees/database-foundation"
DATABASE_URL='postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen' \
  /Users/zhize/Desktop/Test/Cybersecurity/.venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000
```

前端启动命令：

```bash
cd "/Users/zhize/The Eyes of God/.worktrees/database-foundation/frontend"
npm run dev -- --host 127.0.0.1
```

健康检查：

```bash
curl http://127.0.0.1:8000/runtime
```

预期：

```json
{"task_execution_mode":"inline"}
```

## 5. 当前数据库状态

2026-06-30 查询结果：

```text
domains: 1367
search_results: 2432
crawl_results: 2415
contacts: 20468
profile_packages: 1855
country_signals: 6781
keyword_groups: 6
candidate_groups: 2
candidate_group_items: 144
task_runs: 8
task_items: 320
```

关键词组：

```text
1 keywords_france              France          90 combinations
2 keywords_france_complement   France          60 combinations
3 keywords_uk                  United Kingdom  80 combinations
4 keywords_uk_complement       United Kingdom  120 combinations
5 澳大利亚泳池机               Australia       6 combinations
6 意大利泳池机                 Italy           60 combinations
```

候选组：

```text
1 澳大利亚泳池机 search #2
  total: 52
  historically crawled: 52
  uncrawled: 0

2 意大利泳池机 search #7
  total: 92
  historically crawled: 92
  uncrawled: 0
```

最近关键任务：

```text
#7 search 意大利泳池机
status: partial_failed
result: 56 success, 4 failed
candidate group: #2

#8 crawl 意大利泳池机 candidate group #2
status: success
result: 59 success, 22 empty
profile_input_dir: /Users/zhize/The Eyes of God/profile_inputs/Italy

#6 search 意大利泳池机 Bing
status: cancelled
result: 5 failed, 55 cancelled
原因：Bing captcha/challenge

#5 search 意大利泳池机 DuckDuckGo
status: failed
result: 60 failed
原因：DuckDuckGo throttle / timeout
```

Italy JSON 数量：

```text
/Users/zhize/The Eyes of God/profile_inputs/Italy/*.json = 59
```

## 6. 关键表设计

阶段 A：找官网

- `domains`
- `search_results`
- `country_signals`
- `candidate_groups`
- `candidate_group_items`

阶段 B：抓官网

- `crawl_results`
- `contacts`
- `profile_packages`
- `country_signals`

任务记录：

- `task_runs`
- `task_items`

阶段 C：后续 AI / 人工确认，表已规划或部分存在，但当前未接入完整业务流程：

- `qualified_leads`
- `company_profiles`
- `lead_scores`

重要逻辑：

- `domains` 按标准化域名 upsert，不应重复创建同一家公司。
- `search_results` 会保留每次搜索任务的命中证据。相同域名在新任务中再次被搜到，会新增一条 `source_file = task:search:<id>` 的搜索证据。
- `crawl_results` 记录抓取结果。默认抓官网时 `recrawl_existing=false`，会跳过已有抓取结果的域名。
- 候选组中的“已抓”实际含义是“历史已有 crawl_results”，不是“本轮已经抓过”。建议前端文案后续改为“历史已抓”。

## 7. 最近重要更改

### 7.1 数据库化

项目已经从本地 CSV 小工具升级为数据库驱动：

- 搜索结果直接写入数据库。
- 抓取结果直接写入数据库。
- CSV 仍保留为 CLI 兼容和审计备份，不是主流程必需输入。

相关文件：

- `database/models.py`
- `database/importers.py`
- `database/stage_persistence.py`
- `alembic/versions/*.py`
- `scripts/import_existing_data.py`

### 7.2 Vue 控制台

前端已改成 Vue3 中文控制台，左侧导航包括：

- 任务控制台
- 企业库
- 候选组
- 关键词配置中心
- 任务中心
- 客户池

相关文件：

- `frontend/src/App.vue`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/style.css`

### 7.3 关键词配置中心

关键词组不再必须写 YAML，已存数据库：

- 新增关键词组
- 保存关键词组
- 备注关键词组
- 删除关键词组
- 关键词组合数只读展示

相关文件：

- `database/keyword_groups.py`
- `api/app.py`
- `api/schemas.py`
- `frontend/src/App.vue`

### 7.4 候选组

搜索任务完成后创建候选组，抓取任务可以以后再选择某个候选组来抓。

用户明确不要“一搜完立刻抓”这种一次性按钮，而是要候选组长期保存。

相关文件：

- `database/candidate_groups.py`
- `alembic/versions/20260629_0005_candidate_groups.py`
- `tasks/handlers.py`
- `api/app.py`
- `frontend/src/App.vue`

### 7.5 实时进度

控制台现在会轮询 `task_runs` 和 `task_items` 显示实时进度：

- 已处理 / 总数
- 各状态计数
- 最近执行项

这是为了替代命令行里能看到 `[1/60] ...` 的运行反馈。

### 7.6 取消任务按钮

已实现协作式取消：

- `POST /task-runs/{task_run_id}/cancel`
- 前端实时进度面板有“取消任务”
- 任务中心详情也有“取消任务”
- 状态包含 `cancelling` / `cancelled`

注意：

- 不会强杀当前正在执行的单个 HTTP/browser 请求。
- 搜索会在当前关键词完成或超时后停止。
- 抓取会在当前域名完成或超时后停止。
- 未开始的 `task_items` 会标记为 `cancelled`。

相关文件：

- `database/task_batches.py`
- `tasks/handlers.py`
- `tasks/runner.py`
- `tasks/models.py`
- `run_search.py`
- `run_crawl.py`
- `api/app.py`
- `frontend/src/api.ts`
- `frontend/src/App.vue`

### 7.7 抓取参数灰度禁用

前端抓官网表单做了上下文禁用：

- 选择候选组后，候选国家和候选关键词不可编辑。
- `requests` 模式下，browser-only 参数禁用。
- `browser` 模式下，requests-only 参数禁用。

## 8. 搜索引擎封禁情况

近期遇到明显搜索源限制：

```text
DuckDuckGo:
HTTP 202 challenge/throttle page
Read timed out against html.duckduckgo.com

Bing:
captcha/challenge page marker
```

对应任务：

- `task_run #5`: DuckDuckGo 全失败
- `task_run #6`: Bing captcha 后被用户取消
- `task_run #7`: DuckDuckGo 后来跑出 56 success / 4 failed

建议：

- 不要短时间高频压 DuckDuckGo / Bing。
- 大批量搜索前先小批量 smoke test。
- 如果继续扩大规模，优先考虑代理池、正式搜索 API 或更稳的搜索数据源。
- `browser` 模式可以尝试，但不能保证绕过 captcha，而且更慢。

## 9. 当前推荐操作方式

前端控制台优先：

1. 打开 `http://127.0.0.1:5173`
2. 关键词配置中心创建 / 选择关键词组。
3. 任务控制台执行“找官网”。
4. 搜索完成后看“候选组”。
5. 任务控制台执行“抓官网”，选择候选组。
6. 企业库查看阶段 A / B。
7. 客户池查看单个域名详情。

CLI 仍可用，但不是当前推荐主流程。

## 10. 推荐测试命令

后端完整测试：

```bash
cd "/Users/zhize/The Eyes of God/.worktrees/database-foundation"
python -B -m unittest discover -s tests
```

前端构建：

```bash
cd "/Users/zhize/The Eyes of God/.worktrees/database-foundation/frontend"
npm run build
```

空白检查：

```bash
cd "/Users/zhize/The Eyes of God/.worktrees/database-foundation"
git diff --check
```

最近一次完整验证：

```text
python -B -m unittest discover -s tests
135 tests OK

npm run build
passed

git diff --check
passed
```

## 11. 文件说明入口

继续工作前建议读：

```text
PROJECT_FILE_GUIDE.md
README.md
AI_WORKLOG.md
docs/superpowers/specs/
docs/superpowers/plans/
```

特别重要的代码入口：

```text
api/app.py
tasks/handlers.py
database/models.py
database/task_batches.py
database/candidate_groups.py
database/keyword_groups.py
run_search.py
run_crawl.py
frontend/src/App.vue
frontend/src/api.ts
```

## 12. 已知问题和下一步建议

### 12.1 前端文案

候选组里的“已抓”建议改成“历史已抓”，避免用户误以为本轮已经抓过。

### 12.2 任务实时进度绑定

当前 inline 模式下，前端启动任务后会轮询“最新 running 的同类型任务”。单用户使用基本够用，但多任务并发时可能绑定到错误任务。

更稳方案：

- 前端启动任务时生成 `client_request_id`。
- 后端把它写入 `task_runs.params_json`。
- 前端按 `client_request_id` 查自己的任务。

### 12.3 搜索源稳定性

DuckDuckGo / Bing 容易 throttle/captcha。后续需要：

- 代理支持和代理质量评估。
- 搜索 API 备选。
- 失败熔断，例如连续 captcha 超过 N 次自动停止任务。

### 12.4 Celery 队列

项目已有 Celery 文件，但主流程还没切到队列。

用户之前明确说：“后面再增加一个 Celery”，所以当前没有把所有逻辑重写成 Celery。

未来建议：

- search/crawl 每个关键词/域名单独成 task item。
- worker 从数据库领取任务。
- 前端只创建任务批次，不阻塞 HTTP 请求。

### 12.5 AI 画像评分

当前只生成画像 JSON 和数据库 B 阶段数据，还没真正接 AI 推理。

未来接入点：

```text
profile_packages / crawl_results -> AI 分析 -> company_profiles / lead_scores / qualified_leads
```

用户计划另开一个 Codex 主要培训它分析画像。已有 skill：

```text
/Users/zhize/.codex/skills/analyze-heat-pump-lead-profile/SKILL.md
```

项目内也有：

```text
docs/profile-analysis-agent-prompt.md
profile_inputs/.codex/skills/analyze-heat-pump-lead-profile/
```

## 13. 不要误删的内容

不要删：

- `profile_inputs/**`，这是画像素材。
- `company_websites*.csv` 和 `company_info*.csv`，虽然主流程不再依赖，但仍是历史审计和导入来源。
- `AI_WORKLOG.md`，用户要求记录关键对话和工作过程。
- `docs/superpowers/**`，记录设计和实现计划。
- `.worktrees/database-foundation`，这是当前主要实现。

可以忽略：

- `__pycache__/`
- `.DS_Store`
- `frontend/dist/`

当前 git status 里很多文件是 untracked，是因为这个 worktree 承载了大量新实现，不代表这些文件没用。不要因为看到 untracked 就删除。

## 14. 最近 Italy 流程说明

用户新跑了“意大利泳池机”：

1. `task_run #7` 找官网：
   - 60 关键词组合。
   - 56 success。
   - 4 failed。
   - 写入 `source_file = task:search:7` 的搜索证据。
   - 生成候选组 `#2`。

2. 候选组 `#2`：
   - 92 个候选域名。
   - 一开始有 11 个历史已抓。
   - 后续抓完后 92 个都已有历史抓取结果。

3. `task_run #8` 抓官网：
   - 从候选组 `#2` 抓取未抓的 81 个。
   - 59 success。
   - 22 empty。
   - JSON 输出目录：`/Users/zhize/The Eyes of God/profile_inputs/Italy`

4. Italy JSON 当前 59 个。

## 15. 给接手 AI 的工作原则

- 先读代码，再给建议。
- 不要绕过现有 `run_search.py` / `run_crawl.py` 框架。
- 不要把 CSV 临时文件重新作为主流程，主流程已经数据库化。
- 不要把 `search_results` 的重复命中误判为重复公司；公司实体以 `domains` 为准。
- 用户偏好中文说明和直接可执行的方案。
- 用户关注业务逻辑是否清楚，尤其是“阶段 A/B/C”和“哪些数据进哪张表”。
- 前端应保持中文、控制台式、偏工具产品，不做营销页。
- 做代码改动要加测试，至少跑相关单测和 `npm run build`。
