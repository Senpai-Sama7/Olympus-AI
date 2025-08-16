# Repository Audit

## Overview

This repository currently contains a traditional web application (Node.js/Express backend + React frontend) alongside several experimental/services components (Python FastAPI services for execution and web automation, a retrieval service targeting Postgres/pgvector, a Rust control-plane, and workflow/ingest pieces with Temporal).

## Applications and Services

- server (Node.js/Express)
  - Entry: `server/server.js`, app: `server/app.js`
  - Security: helmet, IP rate limiting, input sanitization, request ID, compression, CORS
  - APIs: `/api/auth`, `/api/users`, `/api/admin`, `/api/products`, `/api-docs` (Swagger)
  - Logging: winston (daily rotate), request logs
  - DB: MongoDB (via `mongoose`), connection configured via `server/config/db.js`
  - Auth: JWT-based

- client (React + Vite)
  - SPA with pages for Home, Dashboard, Admin, Login/Register, Products
  - State: Redux Toolkit
  - Tailwind setup present

- services/exec-service (Python FastAPI)
  - Endpoint: POST `/execute-local-code`
  - Runs code in Docker containers with resource limits (no network by default)
  - Audit trail persisted to SQLite file (`/app/data/audit.db`)

- services/webbot-service (Python FastAPI)
  - Endpoint: POST `/interact-web`
  - Uses Playwright to automate web actions (goto/click/type/select/extract/screenshot/pdf/...)
  - Audit trail persisted to SQLite file (`/app/data/audit.db`)

- services/retrieval (Python FastAPI)
  - Endpoint: POST `/v1/retrieval/search`
  - Embeddings: via local `embed.py`
  - Storage: Postgres with pgvector (`doc_chunks.embedding`), nearest neighbor via `<->`

- control-plane (Rust)
  - Minimal skeleton with `src/main.rs` and Dockerfile

- bridge/ingest-consumer (Node/TypeScript)
  - Temporal worker/bridge sidecar

- workflows/ingest (TypeScript/Temporal)
  - Activities and workflows for ingest; Dockerfile provided

## Orchestration

- docker-compose.yml
  - `mongodb`, `redis`, `server`, `client`
- docker-compose.infra.yml
  - `postgres` (pgvector), `redis`, `temporal`, `temporal-ui`, `jaeger`, `otel-collector`
- docker-compose.app.yml
  - `control-plane`, `retrieval-service`, `temporal-worker`, `ingest-bridge`, `exec-service`, `webbot-service`

## Storage and Databases

- MongoDB (primary for existing server)
- Redis (rate limiter/cache)
- Postgres with pgvector (retrieval)
- SQLite (audit logs for exec/webbot)

## Authentication and Security

- Server uses JWT for auth with express middlewares: helmet, CORS, express-rate-limit, input sanitization, security headers
- No cookie-based session; no CSRF protection wired for form actions
- Rate limiting present (basic and optional Redis-backed advanced limiter)

## RPA / Automation / Tooling

- Web automation via Playwright in `webbot-service`
- Local code interpreter via `exec-service` (Docker run sandbox)

## Dev Tooling

- Root `Makefile` currently a shell script for creating an Ollama Modelfile
- Multiple Dockerfiles across services
- `run.sh` simple helper
- No unified monorepo Python workspace/venv or pre-commit hooks

## Docs

- `ARCHITECTURE.md`, `Tactical Implementation.md`, `DEPLOYMENT.md`, `README.md`, `SUMMARY.md`, `docs/`
