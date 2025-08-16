# Enterprise Application Architecture

## 🏗️ System Architecture

### Overview

This system includes the original enterprise web application and services, plus a new local‑first agentic assistant skeleton. The assistant is designed to run primarily on local models (Ollama) with optional cloud fallbacks under budgets.

### Assistant Components (New)

- Apps
  - `apps/api` (Python FastAPI): Will expose chat, plans, memory, tools, and runs; currently ships health/config endpoints
  - `apps/worker` (Python): Async daemon for executing plans/tools, code interpreter, and web automation (future phases)
- Packages
  - `packages/plan`: Plan DSL with `Plan`, `Step`, `StepAction`, and budgets
  - `packages/memory`: SQLite helpers (later: conversations/docs/embeddings, sqlite-vec/SQLite-Vector)
  - `packages/llm`: Local‑first LLM Router (Ollama now; cloud fallback in later phases)
  - `packages/tools`: Allow‑listed filesystem and (later) HTTP/Email/Calendar/Sheets connectors
  - `packages/automation`: Artifact logging and (later) Playwright driver + MCP adapter
- Infra
  - `infra/init.sh`: Creates `.env`, initializes SQLite DB, and pulls a small Ollama model if available
- Tests/Docs
  - `tests/` with smoke tests; `reports/` for audit and gap analysis; `plans/` for migration plan

These are additive and do not break existing services.

## 🧭 Existing Technology Stack

### Backend

- **Runtime**: Node.js 18 (ES Modules)
- **Framework**: Express.js 4
- **Database**: MongoDB 7 with Mongoose ODM
- **Authentication**: JWT with refresh tokens
- **Validation**: Joi
- **Security**: Helmet, CORS, bcrypt, rate limiting
- **Logging**: Winston with file rotation
- **Caching**: Node-cache + Redis (optional)
- **Documentation**: Swagger/OpenAPI

### Frontend

- **Framework**: React 18 with Vite
- **State Management**: Redux Toolkit
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Forms**: React Hook Form
- **HTTP Client**: Axios with interceptors
- **Notifications**: React Hot Toast
- **Icons**: Heroicons

### Infrastructure

- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Reverse Proxy**: Nginx
- **SSL**: Let's Encrypt

## 📁 Project Structure

```
Olympus AI/
├── apps/
│   ├── api/                  # FastAPI (olympus_api)
│   └── worker/               # Worker daemon (olympus_worker)
├── packages/
│   ├── plan/                 # Plan DSL
│   ├── memory/               # SQLite + (later) vector index
│   ├── llm/                  # LLM Router (Ollama-first)
│   ├── tools/                # Allow-listed tools
│   └── automation/           # Artifacts & automation adapters
├── infra/
│   └── init.sh               # Env & DB bootstrap, Ollama pull
├── reports/                  # repo-audit.md, gap-analysis.md
├── plans/                    # migration-plan.md
├── client/                   # Frontend application
├── server/                   # Backend application
├── services/                 # Retrieval, Exec, Webbot
├── control-plane/            # Rust control plane
├── workflows/                # Temporal worker
├── bridge/                   # Ingest-bridge
└── docker-compose.*.yml      # Infra & app stacks
```

## 🔐 Security Architecture (Highlights)

- Assistant packages enforce sandboxing and allow-lists:
  - Writes constrained to `ALLOW_WRITE_DIRS`
  - Artifacts under `SANDBOX_ROOT`
- Existing server security remains: Helmet, input sanitization, IP rate-limits, optional Redis limiter
- Future phases will add cookie-based sessions, CSRF, and ask‑before‑doing confirmation for external writes/actions

## 🔄 Data Flow (Existing Web App)

```
Client Request
    ↓
Nginx (Reverse Proxy)
    ↓
Express Server
    ↓
Rate Limiter → Security Headers → CORS
    ↓
Request ID → Body Parser → Input Sanitization
    ↓
Authentication Middleware (if protected)
    ↓
Validation Middleware
    ↓
Cache Check (GET requests)
    ↓
Controller → Service → Model
    ↓
Database Query
    ↓
Cache Update
    ↓
Response Formatting
    ↓
Error Handler (if error)
    ↓
Client Response
```

## 🔌 API Architecture (Existing Web App)

The REST endpoints under `server/` are unchanged.

## 🧪 Testing

- `make test` runs Python tests for assistant components
- Existing JS tests and CI can be extended in later phases

## 📈 Roadmap

- See `plans/migration-plan.md` for Phase 1–8 including Memory+Vector, Plan DSL & Executor, Code Interpreter, Playwright/MCP, Router & Budgets, Flow Builder, and Observability.
