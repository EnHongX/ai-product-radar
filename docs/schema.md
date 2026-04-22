# 数据库 Schema 说明

## 设计目标

数据库第一版只服务官方 AI 产品发布情报库，不做新闻聚合、评分、排行榜或社区投稿。

核心目标：

- 官方来源可追溯
- 原文可保存
- 候选发布可审核
- 正式产品和发布记录可查询
- 抓取、抽取、审核过程可排错

## 核心关系

```text
companies 1 --- n sources
companies 1 --- n products
sources 1 --- n raw_articles
sources 1 --- n product_releases
raw_articles 1 --- n extraction_logs
products 1 --- n product_releases
product_releases n --- n platforms
product_releases 1 --- n review_tasks
sources 1 --- n crawl_logs
```

## 表说明

### companies

发布方基础资料，例如 OpenAI、Anthropic、Google。

关键约束：

- `name` 唯一
- `slug` 唯一

### sources

官方来源，例如 RSS、newsroom、blog、changelog。

关键约束：

- `url` 唯一
- 归属一个 `company`

### raw_articles

从官方来源抓取的原始文章。

关键约束：

- `url` 唯一
- `content_hash` 唯一

### products

正式产品库。

关键约束：

- 同公司下 `slug` 唯一
- `official_url` 唯一

### product_releases

产品发布记录，可先进入 `pending` 状态等待审核。

关键约束：

- `release_url` 唯一
- `raw_content_hash` 唯一

### platforms 和 release_platforms

维护一条发布记录支持哪些端或集成平台。

### review_tasks

审核任务表，记录候选项的审核状态、负责人、备注和审核时间。

### crawl_logs

抓取日志，用于追踪每个来源的抓取结果。

### extraction_logs

结构化抽取日志，用于排查 LLM 或规则抽取失败。
