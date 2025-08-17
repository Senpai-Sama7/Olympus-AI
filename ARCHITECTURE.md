# Architecture

Olympus AI is a modular, service-oriented agent platform designed for local-first operation with explicit consent and strong observability. Components can run together for development or be deployed independently.

## System Overview

Core runtime components and their responsibilities:

```
+-----------------+      +-----------------+      +-----------------+
|   Desktop App   |----->|      API        |----->|      Worker     |
+-----------------+      +-----------------+      +-----------------+
        |                      |                      |
        |                      |                      v
        |                      |              +-----------------+
        |                      |              |      Tools      |
        |                      |              +-----------------+
        |                      |
        |                      v
        |              +-----------------+
        |              |   LLM Router    |
        |              +-----------------+
        |
        v
+-----------------+
|     Memory      |
+-----------------+
        |
        v
+-----------------+
|    Retrieval    |
+-----------------+
```

## Components

### Services

- `apps/api` (FastAPI): REST entrypoint for health/metrics/config, plan submit/run/query, and direct actions with consent. Middlewares: request ID, rate limit, timeouts, body-size limit. Exposes LLM health/usage endpoints.
- `apps/worker` (Python): PlanExecutor executes DAGs with retry/backoff/jitter and persists transcript events into the memory DB. Registers secure tools (fs/search/shell/git/net) with consent scopes.
- `services/retrieval` (FastAPI): Optional service for vector search (Postgres + pgvector).

### Packages

- `packages/plan`: Pydantic models for Plan/Step/Guard/Budget with DAG cycle detection and runnable-step selection.
- `packages/memory`: SQLite-based MemoryDB (WAL) persisting plans/steps/events and simple cache for budgets/usage.
- `packages/llm`: Router supporting local-first llama.cpp, Ollama, and cloud fallback. Adds caching, allowlist, usage budgets, async chat API (plus test stubs), and health/usage visibility through API.
- `packages/tools`: Secure tools with explicit consent scopes. Filesystem (`.sandbox` root, symlink/path-escape defense), search (glob/regex), shell execution (cwd in sandbox), git helpers, and network GET.

### Desktop App

`desktop/` (pywebview) provides a simple UI for start/stop, health, and consent prompts. It boots API and worker for local operation and can display links to docs/config.

## Security Model

- Consent first: `OLY_REQUIRE_CONSENT=true` enforces explicit scopes for all sensitive tools (fs write/delete, shell, git, network, search). Dev auto-consent is permitted via `OLY_AUTO_CONSENT=true` but should be off in prod.
- Filesystem sandbox: All fs ops are confined to `.sandbox` with hard path normalization and symlink traversal prevention.
- Network: Disabled unless `net_get` consent provided.

## LLM Backends

- llama.cpp: Preferred; run local GGUF models via API server (`/v1/chat/completions` or `/completion`). Usage tracked with a daily token budget (`OLY_DAILY_TOKEN_BUDGET`).
- Ollama: Local model runner using `/api/generate`. Optional allowlist via `OLLAMA_MODEL_ALLOWLIST` ensures only approved models are used.
- Cloud fallback (OpenAI): Disabled by default. When enabled, USD spend is tracked per-day and cached responses avoid duplicate spend.

## Observability

- Metrics: `/metrics` Prometheus exposition; histograms and counters for request volume, latency, errors.
- Health: `/health` + `/v1/llm/health`; config echo shows non-sensitive runtime config and LLM usage snapshot.
- Logging: JSON logs with timestamps and correlation IDs.

## CI/CD

GitHub Actions runs formatting, linting, type checks, unit tests, smoke tests, secret and dependency audits, and container image scans.

## Repository Hygiene

Dead/placeholder modules are quarantined under `deadcode/` to avoid conflicting APIs and reduce drift. The sandbox root `.sandbox` is used for all tool-side file operations; LLAMA GGUF files live outside the repo.
