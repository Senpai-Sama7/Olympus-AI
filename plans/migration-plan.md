# Migration Plan

This plan introduces a local-first, cloud-fallback agentic assistant with the specified architecture. Phases are sequential; each phase ships executable code, tests, and docs.

## Phase 0 — Skeleton & Dev UX

- Add monorepo layout: `/apps/api`, `/apps/worker`, `/packages/{plan,memory,llm,tools,automation}`, `/infra`, `/tests`, `/docs`
- Makefile targets: `make init`, `make venv`, `make install`, `make dev-api`, `make dev-worker`, `make test`
- `.env.example` and `infra/init.sh` to bootstrap SQLite, workspace dirs, and a small Ollama model
- Pre-commit hooks

## Phase 1 — Auth, Modes, Settings

- API: hashed passphrase login (Argon2/bcrypt), signed HTTP-only cookies, CSRF protection, per-IP rate limit
- Modes: Observe/Draft/Autopilot stored per plan/run, default Draft
- Settings endpoints and basic Settings UI (local model, cloud keys, budgets)

## Phase 2 — Memory & Vector Search

- SQLite schema and migrations for conversations, docs, chunks, embeddings, tasks, insights
- sqlite-vec or SQLite-Vector integration; ANN search with top-k + MMR
- Ingestors: PDF/DOCX/MD; embeddings via sentence-transformers

## Phase 3 — Plan DSL & Executor

- Pydantic models: Step and Plan with preconditions/postconditions, rollback, idem_key
- Dry-run simulator with readable diffs
- Worker executes plan with retries and compensation; idempotence guarantees

## Phase 4 — Code Interpreter (Local)

- Sandboxed Python runner (no-net by default), CPU/mem/time caps, safe workspace I/O
- Iterative loop: run → test → refine, artifact packaging

## Phase 5 — Web Automation

- Playwright driver with resilient selectors, retries/backoff, artifact logs
- MCP adapter exposing structured page state; API fallback

## Phase 6 — LLM Router & Budgets

- Local-first (Ollama) with optional cloud fallback (OpenAI/Anthropic/Gemini)
- Per-task and daily token/time budgets; circuit breaker; graceful degrade

## Phase 7 — Flow Builder (MVP)

- Canvas with nodes: Search Docs, Generate, Automate Web
- NL → flow compile; flows saved as Plan JSON; preview + dry-run

## Phase 8 — Observability & Golden Path

- Dashboard for TSR/FAP/runtime; weekly report
- Golden path recipe: job application workflow with dry-run/preview/Autopilot

## Rollback Strategy

- Each phase ships idempotent migrations; rollback scripts to revert DB schema changes
- Feature flags/gates to disable new components if needed
