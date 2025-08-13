# Olympus AI — Full-Stack Enterprise AI System

Olympus AI is a production-ready, modular enterprise system that blends a secure web app (users, products, admin), an AI data plane (ingest, embeddings, retrieval), and controlled broad capabilities (sandboxed local code execution and controlled web automation). It’s designed for security-first, observable, and scalable operation using containers.

## What’s inside

- Web App (React + Express + MongoDB)
  - Authentication with JWT + refresh tokens
  - Role-based access control (user/admin)
  - Products CRUD with validation and caching
  - Swagger/OpenAPI docs at `/api-docs`
  - Security middleware: Helmet, input sanitization, CORS, rate limiting, advanced Redis rate limiter (optional)
  - Structured logging with console logs and daily-rotated files (production)
- AI Data Plane
  - Control Plane (Rust, gRPC) for task submission and event streaming (Redis Streams)
  - Temporal Worker (TypeScript) to ingest raw docs → chunk → deterministic embeddings → upsert into pgvector
  - Retrieval Service (FastAPI) executes ANN search in Postgres pgvector
- Controlled Broad Capabilities
  - Controlled Local Code Execution Service (FastAPI)
    - POST `/execute-local-code` executes Python 3.x, Node.js 18.x, or Bash in a short-lived Docker container
    - Strict sandboxing to `/sandbox/workspace` with cpu/memory/time limits; network off by default
    - Requires API key and explicit confirmation for sensitive operations
    - Full stdout/stderr capture and SQLite audit logs
  - Controlled Web Interaction Service (FastAPI + Playwright)
    - POST `/interact-web` performs headless browser automation (goto, click, type, select, extract, upload, download, screenshot/PDF, cookies/local storage)
    - Runs isolated with shared sandbox volume for file I/O (e.g., screenshots)
    - Requires API key and confirmation for sensitive interactions; SQLite audit logs
- DevOps & Security
  - Docker Compose stacks for infra and apps
  - Production-grade Dockerfiles
  - CI workflow builds images and runs Trivy container scans

## Key capabilities and use cases

- Enterprise Web App
  - User onboarding, login, profile management
  - Role-based admin panel for user management and system stats
  - Product catalog with filtering, pagination, ownership checks, and caching
- Data Ingest & Retrieval (CPU-only starter)
  - Deterministic embedding pipeline for reproducible indexing and search
  - Temporal orchestrates ingest workflows with durable execution
  - Vector similarity search for knowledge retrieval
- Controlled Local Code Execution (Secure Automation)
  - Safely run scripts that manipulate files inside an isolated workspace (reports, ETL helpers)
  - Optionally allow egress for HTTP calls (feature flags + confirmation)
  - Ideal for self-service automation with strict guardrails
- Controlled Web Interaction (Browser RPA)
  - Headless workflows: logins, form submissions, scraping, screenshots, PDF exports
  - File upload/download limited to sandbox volume
  - Use session persistence (cookies, local storage) for repeatable tasks

## Architecture overview

- client/ (React, Vite)
- server/ (Node/Express, MongoDB via Mongoose)
- services/
  - retrieval/ (FastAPI)
  - exec-service/ (FastAPI): sandboxed local code execution
  - webbot-service/ (FastAPI + Playwright): controlled web automation
- control-plane/ (Rust + tonic)
- workflows/ingest/ (Temporal Worker TypeScript)
- bridge/ingest-consumer/ (Redis→Temporal bridge)
- docker-compose.infra.yml (Postgres + pgvector, Redis, Temporal, OTEL + Jaeger)
- docker-compose.app.yml (control-plane, retrieval, worker, bridge, exec-service, webbot-service)

## Security features

- API key auth on new microservices (`x-api-key` header)
- JWT-based auth on web API; role checks, resource ownership checks
- Helmet, CORS, input sanitization, error handling middleware
- Basic rate limiting and optional Redis-backed advanced rate limiting
- Sandboxing: `/sandbox/workspace` volume only, Docker resource limits
- Auditing: SQLite audit DB per microservice (`/app/data/audit.db`)

## Getting started

1) Prerequisites

- Docker and Docker Compose

2) Bring up infra

```bash
cp .env.example .env  # optional if you keep defaults
docker compose -f docker-compose.infra.yml up -d
```

3) Seed Postgres vector demo (optional)

```bash
docker exec -i cp-postgres psql -U postgres -d cognitive < scripts/seed_pgvector.sql
docker exec -i cp-postgres psql -U postgres -d cognitive < scripts/seed_docs.sql
```

4) Bring up app stack (includes exec-service and webbot-service)

```bash
docker compose -f docker-compose.app.yml up -d --build
```

5) Access

- Client (React): <http://localhost>
- Server health: <http://localhost:5000/health>
- Swagger: <http://localhost:5000/api-docs>
- Retrieval API (FastAPI): <http://localhost:8081>
- Exec Service: <http://localhost:8082>
- WebBot Service: <http://localhost:8083>

Note: Set API keys via environment when running compose:

- `EXEC_API_KEY` for exec-service
- `WEBBOT_API_KEY` for webbot-service

## Using the Controlled Local Code Execution Service

- Endpoint: `POST /execute-local-code`
- Header: `x-api-key: <your EXEC_API_KEY>`
- Body fields:
  - `language`: `python` | `node` | `bash`
  - `code`: the code snippet to run
  - `workdir`: relative path under `/sandbox/workspace`
  - `allow_network`: default false; set true to enable outbound egress
  - `confirm_sensitive`: must be true if `allow_network=true` or long code
- Response: `{ stdout, stderr, exit_code }`

Example request:

```json
{
  "language": "python",
  "code": "print('hello from sandbox')",
  "workdir": "demo",
  "allow_network": false,
  "confirm_sensitive": true
}
```

Audit logging: SQLite at `/app/data/audit.db` table `exec_audit` (ts, params, exit code, previews).

## Using the Controlled Web Interaction Service

- Endpoint: `POST /interact-web`
- Header: `x-api-key: <your WEBBOT_API_KEY>`
- Body fields:
  - `actions`: list of steps, each with a `type` and optional fields (e.g., selector/url/path/value)
  - `confirm_sensitive`: must be true for actions like `type`, `upload`, `pdf`
- Supported actions: `goto`, `click`, `type`, `select`, `extract`, `upload`, `download`, `screenshot`, `pdf`, `set_cookies`, `get_cookies`, `clear_storage`
- Files are stored/read inside `/sandbox/workspace`

Example request:

```json
{
  "actions": [
    { "type": "goto", "url": "https://example.org" },
    { "type": "screenshot", "path": "shots/example.png" }
  ],
  "confirm_sensitive": true
}
```

Audit logging: SQLite at `/app/data/audit.db` table `web_audit` (ts, counts, sensitivity, status, error).

## Postman collections

Import these collections and set environment variables for API keys:

- `postman/exec-service.postman_collection.json`
- `postman/webbot-service.postman_collection.json`

## CI and container security scanning

- GitHub Actions workflow `.github/workflows/ci.yml` builds images and runs Trivy scans for HIGH/CRITICAL issues on every push/PR

## Production hardening recommendations

- Secrets Management: move creds and JWT secrets to a secure store (Docker/K8s secrets, Vault)
- Temporal Persistence: use MySQL/Postgres instead of SQLite for Temporal in prod
- Embedding Model: replace deterministic hash embeddings with a pre-trained model for better recall/precision
- gRPC Security: enable mTLS and auth for the Rust control plane
- Integration Tests: add compose-based E2E tests and DAST/SAST in CI
- Error Handling: keep structured, contextual logs and avoid swallowing root causes

---

# Non‑Technical Quick Guide (Overview)

This is a business-friendly overview. See `docs/User-Guide.md` for the full step‑by‑step guide.

- Login & Accounts: Use the website, create an account, sign in, access your dashboard
- Products: Browse, search, filter, and manage your own products; admins can manage all users/products
- Knowledge Search: The system can ingest documents and let you search them (IT sets this up)
- Secure Automation:
  - “Run a snippet” (IT configures this) performs small, safe tasks in a controlled workspace
  - “Web tasks” let a headless browser do routine steps (e.g., grab a screenshot) with safety checks

For detailed instructions with pictures and plain language, read `docs/User-Guide.md`.
