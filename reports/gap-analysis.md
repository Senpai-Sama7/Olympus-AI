# Gap Analysis

## Target vs Current

- UI: Chat UI with modes (Observe/Draft/Autopilot)
  - Current: React SPA for ecommerce admin with auth and products
  - Gap: No Chat UI, modes, previews, Flow Builder, or dashboard

- Local Code Interpreter (sandboxed Python with safe I/O)
  - Current: `services/exec-service` can run code in Docker with limits
  - Gap: Not integrated into a unified API/worker; no iterative loop, artifacts packaging, or Ask-before-doing guardrails

- Web Automation (Playwright + artifacts + MCP)
  - Current: `services/webbot-service` supports actions + audit
  - Gap: No resilient selector heuristics, retry/backoff policy, MCP adapter, or integration into plan/executor

- Private Memory (SQLite + vector index)
  - Current: Retrieval service uses Postgres + pgvector; no local SQLite vector index; no conversations/tasks schema
  - Gap: Need SQLite schema, migrations, embeddings pipeline (sentence-transformers), and ANN search with sqlite-vec/SQLite-Vector

- LLM Router (local-first Ollama → cloud fallback)
  - Current: No centralized router; some docs around models
  - Gap: Need router with budgets, backoff, confidence/complexity routing, and graceful fallback

- Plans-as-code (DSL + simulator + idempotence + rollback)
  - Current: Temporal workflows exist but not the requested Plan DSL
  - Gap: Need Pydantic Plan/Step models, dry-run diffs, idempotence utilities, compensation/rollback patterns

- Visual Flow Builder
  - Current: None
  - Gap: Canvas + nodes + NL→plan compile + save/load as Plan JSON

- Security & Modes
  - Current: JWT auth (server), rate-limit, helmet; no cookie sessions/CSRF; no allow-list enforcement for writes/domains
  - Gap: Hashed passphrase login, signed HTTP-only cookies, CSRF, per-IP rate limit at API, ask-before-doing ON, allow-lists

- Observability and Acceptance Tests
  - Current: Some tracing infra (otel/jaeger), no unified metrics dashboard for TSR/FAP, no acceptance tests for features
  - Gap: Dashboard and test suites per acceptance criteria

## Dev Experience / Monorepo

- Current: Mixed stacks and multiple docker-compose files; no unified Python workspace or Makefile for dev
- Gap: Monorepo layout with `/apps/*` and `/packages/*`, `make dev`, `make test`, pre-commit hooks, `.env.example`, and `infra/init.sh`
