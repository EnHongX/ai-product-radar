# AI Product Radar 开发任务记录

更新时间：2026-04-22

## 阶段 1：初始化后端、前端、数据库

状态：已完成基础骨架。

已完成：

- 创建 `apps/api` FastAPI 服务
- 创建 `apps/web` Next.js 前端
- 创建 `packages/shared` 共享常量包
- 创建 `docker-compose.yml`
- 接入 PostgreSQL 16 + pgvector 镜像
- 接入 Redis
- 接入 Celery worker
- 增加 `GET /health`
- API health 检查数据库和 Redis
- 增加 JSON 日志基础配置
- 增加 Dockerfile 和 compose 启动命令
- 增加 `.env.example`
- 增加 `.gitignore`，屏蔽本地 env、依赖目录、构建产物、日志、压缩包和安装包

未完成：

- 后端业务接口
- 前端后台 CRUD 页面
- shadcn/ui 组件初始化
- 生产 Nginx compose 服务
- 自动化测试

验收方式：

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8000/health
```

## 阶段 2：数据库模型设计

状态：已完成初始 schema 和 Alembic migration。

已完成表：

- `companies`
- `sources`
- `raw_articles`
- `products`
- `product_releases`
- `platforms`
- `release_platforms`
- `review_tasks`
- `crawl_logs`
- `extraction_logs`

已完成约束和索引：

- `companies.slug` 唯一
- `companies.name` 唯一
- `sources.url` 唯一
- `raw_articles.url` 唯一
- `raw_articles.content_hash` 唯一
- `products.company_id + products.slug` 唯一
- `products.official_url` 唯一
- `product_releases.release_url` 唯一
- `product_releases.raw_content_hash` 唯一
- 常用查询字段增加索引：公司类型、来源类型、启用状态、发布时间、审核状态、分类、状态等

设计结果：

- 一家公司可以有多个来源
- 一个产品可以有多次发布记录
- 一条发布记录可以关联多个平台
- 每条发布记录可以追溯到 source、raw article、release URL
- 抽取日志、抓取日志、审核任务单独保留

未完成：

- 种子数据
- 枚举表或数据库 enum
- embedding 字段
- 手动合并产品相关表
- 审核操作审计日志表

## 下一阶段建议

阶段 3 只做 `companies` 管理，不要提前做爬虫。

最小任务：

- `GET /admin/companies`
- `GET /admin/companies/{id}`
- `POST /admin/companies`
- `PATCH /admin/companies/{id}`
- `DELETE /admin/companies/{id}`
- 前端公司列表、新增、编辑页面

验收标准：

- 能新增 OpenAI、Anthropic、Google 等公司
- slug 不重复
- 删除前能判断是否已有 source 或 product
