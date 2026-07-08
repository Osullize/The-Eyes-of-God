# Sales AI Lead Generator

面向海外市场的企业客户线索采集工具。当前后台任务主流程是：

```text
数据库关键词组 -> 搜索企业官网 -> search_results / domains 入库 -> candidate_groups 沉淀候选组
候选组 / 阶段 A 官网候选库 -> 抓取企业官网页面 -> crawl_results / contacts / profile_packages 入库 -> 保留画像 JSON
搜索 / 抓取任务批次 -> task_runs / task_items 记录进度、失败项和统计
后续确认商机 -> qualified_leads / company_profiles / lead_scores（待实现，AI 推理接在这里）
```

当前重点行业包括 Heat Pump、HVAC、Mechanical Contractor、Distributor、Dealer 等。

## 当前状态

已实现：

- 按国家、行业、角色组合生成搜索关键词。
- 控制台提供关键词配置中心，关键词组存入数据库。
- 使用 DuckDuckGo / Bing 搜索企业官网。
- 过滤常见目录站、社交媒体、地图、搜索结果页等非企业官网。
- 搜索任务完成后可自动写入数据库的 `domains`、`search_results`、`country_signals`。
- 搜索任务完成后会自动生成 `candidate_groups` 和 `candidate_group_items`，用于长期保存本次搜索输出的域名组。
- 控制台搜索任务直接写入数据库；CLI 仍可增量写入 `company_websites.csv` 作为兼容备份。
- 抓取企业官网，探索 Contact / About / Dealer 等相关页面。
- 提取邮箱、电话、企业简介、可能地址、社交链接、联系人信息。
- 抓取任务完成后可自动写入数据库的 `crawl_results`、`contacts`、`profile_packages`、`country_signals`。
- 控制台抓取任务优先从候选组选择待抓取企业，也可从阶段 A 数据库按国家/关键词筛选候选企业。
- 保留 `profile_inputs/*.json` 作为后续 AI / Codex 画像分析素材。
- 可将现有搜索 CSV、爬取 CSV、profile JSON 导入 SQLite/PostgreSQL 数据库。
- 提供 FastAPI 读接口，用于查看数据库统计、域名列表和单个客户详情。
- 控制台搜索和抓取任务会写入 `task_runs`、`task_items`，用于记录任务批次、执行项、失败项和统计。
- CLI 仍保留 `.search_state` / `.crawl_state` 作为兼容断点续跑工具。

尚未在当前代码中完整实现：

- `company_info_filtered.csv` 数据清洗输出。
- `qualified_leads`、`company_profiles`、`lead_scores` 等确认商机 / AI 评分后的最终价值表。
- CRM、邮件发送、AI 开发信等后续销售流程。

## 环境准备

建议使用 Python 3.12+。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

说明：

- `pyyaml` 用于更完整地解析 YAML；控制台主流程使用数据库关键词组，YAML 仍用于旧配置导入和 CLI 兼容。
- `scrapling` 是 `run_search.py` 默认浏览器搜索后端所需依赖；如果改用 `--backend requests` 则不需要。
- `SQLAlchemy` / `alembic` / `psycopg` 用于数据库模型、迁移和 PostgreSQL 连接。

## 配置文件

### 关键词配置

控制台主流程使用数据库表 `keyword_groups` 管理关键词组，不再要求手写 YAML 文件。

可用导入脚本把旧 YAML 导入数据库：

```bash
python scripts/import_keyword_groups.py --database-url "$DATABASE_URL"
```

旧 CLI 仍支持文件：[config/keywords.yaml](config/keywords.yaml)

用于配置搜索目标国家、行业和关键词。例如：

```yaml
countries:
  Germany:
    terms:
      - Germany
      - Deutschland

industries:
  hvac:
    terms:
      - HVAC contractor
      - HVAC company
```

搜索脚本会把国家、行业、同义词等组合成搜索关键词。

### 搜索运行配置

文件：[config/search.yaml](config/search.yaml)

常用字段：

- `keyword_config`: 关键词配置路径。
- `output`: 官网搜索结果输出文件，默认 `company_websites.csv`。
- `state_dir`: 搜索状态目录，CLI 兼容模式默认 `.search_state`；控制台主流程改用数据库任务批次。
- `backend`: `browser` 或 `requests`，默认 `browser` 使用 Scrapling。
- `engines`: 搜索引擎列表，支持 `duckduckgo`、`bing`。
- `max_pages`: 每个搜索引擎抓取页数。
- `limit_keywords`: CLI/API 兼容参数，用于限制关键词组合数量；控制台主流程默认全量执行所选关键词组，并只展示组合总数。
- `keyword_delay`: 不同关键词之间的延迟秒数。
- `engine_request_delay`: 同一搜索引擎请求间隔秒数。
- `proxy`: HTTP/HTTPS 代理地址。
- `use_system_proxy`: 是否使用系统代理环境变量。

## 使用流程

### 1. 小规模测试搜索

先用 1-2 个关键词测试流程，避免一次跑太多：

```bash
python run_search.py --limit-keywords 2 --max-pages 1 --keyword-delay 0
```

输出：

```text
company_websites.csv
```

如果当前终端已设置 `DATABASE_URL`，或命令里传入 `--database-url`，同一批结果也会写入数据库。

主要字段：

```text
keyword,title,website,domain,source_url,engine,country,country_term,industry,industry_term,matched_keywords,matched_countries,matched_industries,matched_industry_terms
```

### 2. 正式搜索企业官网

```bash
python run_search.py --database-url "$DATABASE_URL"
```

不想写数据库时可以省略 `--database-url`，或在已设置 `DATABASE_URL` 的终端里加 `--no-persist-to-database`。

也可以使用兼容旧版本的入口：

```bash
python find_url.py
```

### 3. 抓取企业公开信息

默认读取 `company_websites.csv`，输出 `company_info.csv`：

```bash
python run_crawl.py --database-url "$DATABASE_URL"
```

不想写数据库时可以省略 `--database-url`，或在已设置 `DATABASE_URL` 的终端里加 `--no-persist-to-database`。

也可以使用兼容旧版本的入口：

```bash
python find_messsage.py
```

输出字段：

```text
keyword,company_name,website,domain,emails,phones,possible_address,description,crawled_pages,status,error,social_links,contacts,page_categories,country,industry,matched_keywords,matched_countries,matched_industries,matched_industry_terms
```

### 4. 导出画像分析输入包

`run_crawl.py` 默认会把抓取结果导出为画像分析流程 / Codex 可用的 JSON 输入包：

```bash
python run_crawl.py
```

输出：

```text
profile_inputs/<domain>.json
```

每个 JSON 文件包含：

- 公司官网、域名、搜索来源关键词和匹配到的国家/行业信息。
- 抓取到的页面 URL、页面类别、页面标题和可见文本。
- 规则提取出的邮箱、电话、社交链接和联系人。
- 抓取状态、页面数量和抓取时间。

这个 JSON 是给画像分析流程 / Codex 使用的输入包。当前项目只负责生成输入包，不直接判断客户优先级，也不调用 AI。

如需改用其他导出目录：

```bash
python run_crawl.py --profile-input-dir other_profile_inputs
```

如需限制每个页面写入的文本长度：

```bash
python run_crawl.py --profile-input-dir profile_inputs --profile-page-char-limit 5000
```

### 5. 导入数据库

默认导入当前项目里已存在的 `company_websites*.csv`、`company_info*.csv` 和 `profile_inputs`：

```bash
python scripts/import_existing_data.py --database-url sqlite:///leadgen.db
```

只导入某个国家/目录：

```bash
python scripts/import_existing_data.py \
  --database-url sqlite:///leadgen.db \
  --search-csv company_websites_france.csv \
  --crawl-csv company_info_france.csv \
  --profile-dir profile_inputs/france
```

服务器 PostgreSQL 连接示例：

```bash
python scripts/import_existing_data.py \
  --database-url postgresql+psycopg://user:password@host:5432/leadgen
```

数据库第一版使用 `domains` 全局按域名去重，并把搜索来源、爬取结果、联系人、profile JSON 路径和国家信号分别保存，方便后续后台任务/API/AI 画像分析复用。

### 6. 使用任务封装入口

`scripts/run_task.py` 是 CLI / FastAPI / Celery / 控制台共用的统一任务入口。控制台搜索和抓取任务在配置 `DATABASE_URL` 后会写入业务数据库，并通过 `task_runs` / `task_items` 记录任务批次和执行项状态；CSV/JSON 文件保留为兼容备份。

控制台主流程不再要求 CSV 文件：

- 找官网：不需要填写官网输出表，搜索结果直接进入阶段 A。
- 抓官网：不需要填写官网输入表或信息输出表，后端从阶段 A 数据库选择候选企业。
- 画像 JSON：继续保留，用作后续 AI / Codex 分析素材。

导入现有数据：

```bash
python scripts/run_task.py import-existing-data \
  --database-url "$DATABASE_URL" \
  --search-csv company_websites_france.csv \
  --crawl-csv company_info_france.csv \
  --profile-dir profile_inputs/france
```

封装后的爬取任务示例：

```bash
python scripts/run_task.py crawl \
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
  --profile-input-dir profile_inputs/france
```

封装后的搜索任务示例：

```bash
python scripts/run_task.py search \
  --database-url "$DATABASE_URL" \
  --config config/keywords_france.yaml \
  --backend requests \
  --max-pages 1 \
  --limit-keywords 2 \
  --keyword-delay 10
```

### 7. 启动 FastAPI 后端

当前 FastAPI 默认是同步接口：收到请求后直接调用 `tasks/handlers.py`，执行完成后返回本次任务结果 JSON。找官网和抓官网的业务执行进度会写入 `task_runs` / `task_items`；后续增加 Celery 时，只需要把调度层换成 Celery worker，业务 handler 继续复用。

启动 API：

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

查看后端任务执行模式：

```bash
curl http://127.0.0.1:8000/runtime
```

查看数据库统计：

```bash
curl http://127.0.0.1:8000/database/stats
```

查看客户域名列表：

```bash
curl "http://127.0.0.1:8000/domains?country=France&status=success&limit=20"
```

查看单个客户详情，返回基础信息、联系人、profile JSON 包和国家信号：

```bash
curl http://127.0.0.1:8000/domains/example.com
```

通过 API 执行导入任务：

```bash
curl -X POST http://127.0.0.1:8000/tasks/import-existing-data \
  -H "Content-Type: application/json" \
  -d '{
    "database_url": "postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen",
    "search_csvs": ["company_websites_france.csv"],
    "crawl_csvs": ["company_info_france.csv"],
    "profile_dirs": ["profile_inputs/france"]
  }'
```

### 8. 使用 Celery 队列

Celery 模式下，FastAPI 只负责提交任务，Celery worker 负责真正执行 `tasks/handlers.py`。Celery 自己的队列任务状态和返回结果暂存在 Redis result backend；找官网和抓官网的业务进度仍然写入数据库 `task_runs` / `task_items`。

启动 Redis：

```bash
docker run -d --name leadgen-redis -p 6379:6379 redis:7
```

如果容器已经存在：

```bash
docker start leadgen-redis
```

启动 Celery worker：

```bash
celery -A tasks.celery_app.celery_app worker --loglevel=INFO --pool=solo
```

用 Celery 模式启动 FastAPI：

```bash
TASK_EXECUTION_MODE=celery \
CELERY_BROKER_URL=redis://127.0.0.1:6379/0 \
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1 \
uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

提交任务后会返回 `task_id`：

```bash
curl -X POST http://127.0.0.1:8000/tasks/import-existing-data \
  -H "Content-Type: application/json" \
  -d '{
    "database_url": "sqlite:////private/tmp/leadgen_api_queue.db",
    "search_csvs": ["company_websites_success_missing_json.csv"]
  }'
```

查询任务状态：

```bash
curl http://127.0.0.1:8000/tasks/<task_id>
```

通过 API 执行爬取任务：

```bash
curl -X POST http://127.0.0.1:8000/tasks/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_country": "France",
    "candidate_limit": 5,
    "backend": "requests",
    "workers": 2,
    "max_depth": 1,
    "max_pages_per_site": 5,
    "global_delay": 1,
    "domain_delay": 3,
    "profile_input_dir": "profile_inputs/france"
  }'
```

### 9. 启动 Vue3 控制台

控制台代码在 `frontend/`，默认连接 `http://127.0.0.1:8000` 的 FastAPI。

先启动后端：

```bash
DATABASE_URL='postgresql+psycopg://leadgen:leadgen_dev_password@127.0.0.1:5432/leadgen' \
uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

再启动前端：

```bash
cd frontend
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:5173
```

如果后端地址不是默认值：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

第一版控制台包含：

- 数据库统计：域名、联系人、profile 包、国家信号。
- 关键词配置中心：新增、编辑、保存备注、删除数据库关键词组。
- 候选组：查看找官网任务沉淀的域名组、已抓/未抓统计和组内域名。
- 企业库：按阶段查看官网候选库 A、抓取画像库 B、优先客户库 C。
- 任务中心：查看数据库任务批次、执行项状态、成功/失败/跳过统计。
- 客户列表：按关键词、国家信号、爬取状态过滤，并支持分页。
- 客户详情：官网、描述、联系人、profile JSON 路径、国家信号。
- 任务面板：提交搜索、爬取、导入任务；Celery 模式下显示 task id 并轮询任务状态。

任务面板说明：

- 如果后端以普通模式启动，任务请求会直接在 FastAPI 进程内执行，长任务会阻塞接口直到完成。
- 如果后端以 `TASK_EXECUTION_MODE=celery` 启动，任务请求会进入 Redis/Celery 队列，控制台会用 `GET /tasks/<task_id>` 查询状态。
- 找官网 / 抓官网任务会在后端配置了 `DATABASE_URL` 时自动写入数据库；控制台主流程不再依赖 CSV。
- 找官网任务从关键词配置中心选择数据库关键词组，不再填写 YAML 路径。
- 抓官网优先选择候选组作为输入；未选择候选组时仍可从阶段 A 官网候选库按国家/关键词筛选。
- 第一版默认参数偏向 France 数据流；控制台主流程不再要求手填搜索/抓取状态目录。

## 常用命令

只重试搜索失败的关键词：

```bash
python run_search.py --retry-failed
```

只重试抓取失败的域名：

```bash
python run_crawl.py --retry-failed
```

搜索时指定 Bing 和 DuckDuckGo：

```bash
python run_search.py --engines duckduckgo,bing
```

限制抓取深度和每个网站页面数：

```bash
python run_crawl.py --max-depth 2 --max-pages-per-site 12
```

使用代理：

```bash
python run_search.py --proxy http://127.0.0.1:7890
python run_crawl.py --proxy http://127.0.0.1:7890
```

忽略系统代理：

```bash
python run_search.py --no-system-proxy
python run_crawl.py --no-system-proxy
```

使用浏览器模式抓取动态页面：

```bash
python run_crawl.py --backend browser
```

显示浏览器窗口调试：

```bash
python run_crawl.py --backend browser --headed
```

关闭 robots.txt 检查：

```bash
python run_crawl.py --no-robots
```

## 状态文件

搜索状态目录（CLI 兼容模式）：

```text
.search_state/
```

包含：

- `completed_keywords.txt`
- `failed_keywords.csv`

抓取状态目录（CLI 兼容模式）：

```text
.crawl_state/
```

包含：

- `completed_domains.txt`
- `failed_domains.csv`

这些文件用于 CLI 断点续跑和失败重试。控制台主流程的任务进度已经写入 `task_runs` / `task_items`，不再要求用户管理这些状态目录。

## 主要代码结构

```text
run_search.py                 搜索企业官网主入口
find_url.py                   兼容旧命令的搜索入口
run_crawl.py                  抓取企业信息主入口
find_messsage.py              兼容旧命令的抓取入口

config/keywords.py            关键词配置加载与组合
config/keywords.yaml          国家、行业、关键词配置
config/search.py              搜索运行配置加载
config/search.yaml            搜索默认参数

search/base.py                搜索结果和搜索引擎协议
search/aggregator.py          多搜索引擎聚合与错误隔离
search/url_utils.py           URL 清洗和企业官网过滤
search/engines/bing.py        Bing 搜索实现
search/engines/duckduckgo.py  DuckDuckGo 搜索实现
search/engines/common.py      搜索引擎共享抓取和阻断检测

crawl/fetcher.py              requests 抓取器、限速、重试、robots.txt
crawl/browser_fetcher.py      Scrapling 浏览器抓取器
crawl/link_explorer.py        站内链接探索
crawl/extractors.py           邮箱、电话、简介、地址、联系人提取

pipeline/csv_writer.py        CSV 追加和按域名去重
pipeline/search_state.py      搜索关键词状态
pipeline/state.py             抓取域名状态

database/models.py            SQLAlchemy 数据库模型
database/importers.py         搜索/爬取/profile 输出导入数据库
database/stage_persistence.py 搜索/抓取阶段共用落库工具
database/queries.py           后端读接口使用的数据库查询和序列化
database/session.py           数据库 engine/session 工具
api/app.py                    FastAPI 应用入口，包含 runtime、读接口和任务接口
api/schemas.py                FastAPI 请求模型
frontend/                     Vue3 控制台，读取 FastAPI 数据
tasks/handlers.py             可复用任务 handler，供 CLI / 后续 API / 后续 Celery 调用
tasks/runner.py               进程内任务执行器，返回 success/failed 结果
tasks/celery_app.py           Celery 应用配置
tasks/celery_tasks.py         Celery worker 任务入口，复用 tasks/handlers.py
scripts/import_existing_data.py 现有 CSV/JSON 数据导入入口
scripts/run_task.py           统一任务 CLI 入口
alembic/                      数据库迁移
```

## 测试

项目使用 `unittest`。

运行全部测试：

```bash
python -m unittest discover -s tests
```

运行单个测试文件：

```bash
python -m unittest tests/test_run_search.py
```

## 推荐操作顺序

1. 修改 `config/keywords.yaml`，先只保留少量国家和行业。
2. 设置 `DATABASE_URL`，或在命令里传入 `--database-url "$DATABASE_URL"`。
3. 用 `python run_search.py --limit-keywords 2 --max-pages 1 --keyword-delay 0 --database-url "$DATABASE_URL"` 试跑。
4. 检查数据库 `search_results` 和兼容备份 `company_websites.csv` 的质量。
5. 用 `python run_crawl.py --max-pages-per-site 5 --database-url "$DATABASE_URL"` 试抓少量官网。
6. 检查数据库 `crawl_results` / `contacts` 和兼容备份 `company_info.csv` 的质量。
7. 再放大关键词数量、搜索页数和抓取页面数。

## 后续规划

- 增加数据清洗输出 `company_info_filtered.csv`。
- 增加 MySQL 导入脚本。
- 增加 AI 企业分类、国家识别、企业类型识别。
- 增加联系人识别、LinkedIn 信息采集。
- 增加邮件发送、AI 开发信和跟进记录。
- 增加 CRM、WhatsApp、Google Maps、展会数据采集模块。
