# Olympus AI — Local‑First Agentic Assistant + Enterprise Stack

Olympus AI is evolving into a local‑first, cloud‑fallback agentic assistant that you can run on your own machine, while keeping the existing enterprise web app and services. The goal is privacy, control, and great DX: use a local model by default, gracefully fall back to cloud providers when budgets allow.

This repository now contains:

- The original enterprise web app (React + Express + MongoDB) and microservices (Retrieval, Exec, WebBot, Temporal, Rust control-plane)
- A new monorepo skeleton for the assistant kernel: API, Worker, and core packages (Plan DSL, Memory/SQLite, LLM Router, Tools, Automation)

See the changelog for Phase 0 details.

- CHANGELOG: `CHANGELOG.md`

## What’s inside

- Enterprise Web App (existing)
  - React SPA, Express API, MongoDB
  - Auth (JWT), Products CRUD, Admin pages
  - Swagger at `/api-docs` with security middleware (Helmet, CORS, rate limits)
- AI Data & Automation (existing services)
  - Retrieval Service (FastAPI) with Postgres + pgvector
  - Exec Service (FastAPI) for sandboxed code execution
  - WebBot Service (FastAPI + Playwright) for controlled headless browser automation
  - Workflows (Temporal) and Rust control plane
- Agentic Assistant (new Phase 0 skeleton)
  - `apps/api` (FastAPI): health + basic config; future home of chat, plans, memory, router
  - `apps/worker` (Python): async daemon; future home of plan executor, code interpreter, web automation runner
  - `packages/plan` (Pydantic models for Plan/Step)
  - `packages/memory` (SQLite helpers; base schema)
  - `packages/llm` (Ollama‑first LLM Router with optional cloud fallback in later phases)
  - `packages/tools` (allow‑listed filesystem utilities)
  - `packages/automation` (artifact helpers under sandbox root)

## Monorepo layout (top‑level)

```
apps/
  api/                # FastAPI app (olympus_api)
  worker/             # Worker daemon (olympus_worker)
packages/
  plan/               # Plan DSL
  memory/             # SQLite helpers and (later) vector index
  llm/                # LLM router (Ollama-first)
  tools/              # Local tools (filesystem, http - coming)
  automation/         # Playwright/logging adapters (to be extended)
infra/
  init.sh             # Bootstraps .env, SQLite DB, pulls Ollama model if available
reports/
  repo-audit.md
  gap-analysis.md
plans/
  migration-plan.md   # Phased plan from skeleton → full assistant
```

Existing folders remain intact (client/, server/, services/, control-plane/, workflows/, bridge/). Use Docker Compose stacks for those as before.

## Quick start (local dev for the assistant)

Prereqs:

- Python 3.10+
- Optional: `ollama` CLI running locally (init will pull a small model if available)

1) Initialize environment and DB

```bash
bash infra/init.sh
```

2) Create venv and install editable packages

```bash
make venv
make install
```

3) Run API and Worker

```bash
make dev-api    # FastAPI at http://localhost:8000
make dev-worker # logs heartbeats every 5s
```

4) Smoke test the API

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/v1/ping
```

5) Run tests and set up pre-commit

```bash
make test       # runs unit tests (2 passing in Phase 0)
make precommit  # installs black/ruff hooks
```

Environment variables are managed via `.env` (generated from `.env.example` by `infra/init.sh`). Key entries:

- APP_SECRET: generated automatically
- OLLAMA_HOST, OLLAMA_MODEL: local LLM runtime defaults
- OLYMPUS_DB_PATH: local SQLite path (default `./data/olympus.db`)
- SANDBOX_ROOT: workspace directory (default `./workspace`)

## Using existing services (unchanged)

Follow the original compose flows for infra and app services.

1) Bring up infra (Postgres+pgvector, Redis, Temporal, OTEL/Jaeger)

```bash
docker compose -f docker-compose.infra.yml up -d
```

2) Seed Postgres vector demo (optional)

```bash
docker exec -i cp-postgres psql -U postgres -d cognitive < scripts/seed_pgvector.sql
docker exec -i cp-postgres psql -U postgres -d cognitive < scripts/seed_docs.sql
```

3) Bring up app stack (control-plane, retrieval, temporal worker, ingest bridge, exec-service, webbot-service)

```bash
docker compose -f docker-compose.app.yml up -d --build
```

4) Access endpoints

- Retrieval: <http://localhost:8081>
- Exec Service: <http://localhost:8082> (x-api-key)
- WebBot Service: <http://localhost:8083> (x-api-key)
- Temporal UI: <http://localhost:8080>

## Security (Phase 0)

- Allow‑listed writes via `ALLOW_WRITE_DIRS` for local tools
- Sandbox root `SANDBOX_ROOT` for artifacts
- API CORS limited to localhost by default (adjust via `CORS_ORIGINS`)

The enterprise server (`server/`) continues to use Helmet, rate limiters, and input sanitization. Future phases add cookie sessions, CSRF, and ask‑before‑doing for write actions across the assistant’s APIs.

## Roadmap and phases

- See `plans/migration-plan.md` for Phase 1–8 scope (Auth/Modes/Settings; Memory + Vector; Plan DSL + Executor; Code Interpreter; Web Automation + MCP; LLM Router + Budgets; Flow Builder; Observability + Golden Path).

## Reference

- Keep a Changelog: <https://keepachangelog.com/en/1.0.0/>
