# AI Product Radar

AI Product Radar is a backend-first product intelligence system for tracking official AI product releases.

The MVP goal is not to build another news site. The first goal is to create a reliable pipeline that can:

- maintain official companies and sources
- crawl official release content
- store raw articles with traceable URLs
- extract structured product release data
- support human review before publishing
- expose approved product and release data later

## Current Status

Completed:

- Phase 1: backend, frontend, database, Redis, worker, Docker Compose foundation
- Phase 2: initial PostgreSQL schema and Alembic migration

Not completed yet:

- companies admin CRUD
- sources admin CRUD
- crawler implementation
- AI release classification and extraction
- review workflow
- public product/release API
- public frontend pages

See [development tasks](docs/development-tasks.md) for the detailed task record.

## Tech Stack

Backend:

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16 with pgvector
- Redis
- Celery

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- TanStack Query

Infrastructure:

- Docker Compose
- PostgreSQL
- Redis
- Nginx config placeholder

## Repository Layout

```text
ai-product-radar/
  apps/
    api/        FastAPI service, Alembic migrations, Celery worker
    web/        Next.js admin/frontend shell
  packages/
    shared/     shared TypeScript constants and types
  infra/
    docker/     deployment-related config
  docs/         development task records and schema notes
```

## Local Development

Create a local environment file:

```bash
cp .env.example .env
```

Start the full local stack:

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- Web: `http://localhost:3000`
- PostgreSQL: `localhost:55432`
- Redis: `localhost:6380`

Run migrations manually if needed:

```bash
docker compose run --rm api alembic upgrade head
```

Stop services:

```bash
docker compose down
```

## GitHub Hygiene

The repository commits `.env.example` only. Local `.env` files, dependency folders, build outputs, logs, database volumes, archives, and installer packages are ignored by `.gitignore`.
