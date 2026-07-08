# 候选组机制设计

## 背景

搜索任务和抓取任务之间需要一个稳定的业务对象。用户可能今天跑完找官网任务，明天或下周才决定抓取其中一批域名。如果只在任务详情页提供“抓取本任务产出的域名”按钮，候选结果会像一次性动作，不适合长期管理、复用、合并和筛选。

本设计把找官网任务的输出沉淀为长期存在的候选组。

## 目标

第一版实现：

- 找官网任务完成后自动生成一个候选组。
- 候选组保存本次搜索产生的 `domain_id` 和 `search_result_id` 索引。
- 抓官网任务可以选择一个候选组作为输入。
- 前端新增候选组模块，抓官网表单改为选择候选组。
- 支持默认只抓未抓取域名，必要时允许重抓。

暂不实现：

- 多候选组合并。
- 手动编辑候选组条目。
- 候选组归档、复制、备注。
- Celery 分布式队列。现有 `task_runs` / `task_items` 仍作为业务任务状态；Celery 后续只作为调度执行层。

## 数据模型

### `candidate_groups`

候选组是一批长期保存的官网候选集合。

字段：

- `id`
- `name`
- `group_type`：`search_output` / `manual` / `merged`
- `source_task_run_id`：来源搜索任务，可为空
- `keyword_group_id`：来源关键词组，可为空
- `country`
- `status`：`active` / `archived`
- `params_json`
- `created_at`
- `updated_at`

### `candidate_group_items`

候选组条目记录组内域名和搜索证据。

字段：

- `id`
- `group_id`
- `domain_id`
- `search_result_id`
- `source_task_item_id`
- `status`：`active` / `excluded`
- `rank`
- `created_at`
- `updated_at`

约束：

- 同一候选组内同一个 `domain_id` 只保留一条有效索引，避免抓官网重复抓同一域名。
- `search_result_id` 用作证据来源；抓官网按 `domain_id` 去重执行。

## 数据流

```text
找官网任务
  -> run_search 返回 rows
  -> search_results 入库
  -> 根据本次 rows 关联到数据库 search_results
  -> 自动创建 candidate_group
  -> candidate_group_items 保存 domain_id/search_result_id

抓官网任务
  -> 用户选择 candidate_group_id
  -> 后端读取 candidate_group_items
  -> 过滤 excluded 项
  -> 默认过滤已存在 crawl_results 的域名
  -> 生成 crawl task_items
  -> 复用现有 run_crawl 抓取引擎
```

## 前端

新增左侧导航模块：

- `候选组`

候选组列表展示：

- 名称
- 类型
- 国家
- 来源任务
- 域名数
- 已抓取数
- 未抓取数
- 创建时间

抓官网表单主入口改为：

- 候选组下拉选择
- 候选数量
- 允许重抓
- 抓取参数

保留 `候选国家` / `候选关键词` 作为兼容/备用筛选，但候选组是首选入口。

## 错误处理

- 找官网任务无结果时，不创建候选组，任务仍可成功结束。
- 抓官网选择不存在的候选组时返回错误。
- 候选组内没有可抓域名时，抓官网任务创建空任务批次并返回 `selected_companies: 0`。
- 已抓取域名默认跳过；打开允许重抓后重新进入候选。

## 验证

- 数据库模型测试确认新表可创建。
- 候选组服务测试覆盖创建、去重、统计、按组选择抓取候选。
- 任务 handler 测试覆盖搜索后生成候选组、抓取从候选组读取域名。
- API 测试覆盖候选组列表与详情。
- 前端构建通过。
