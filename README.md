# Olympus AI

Local-first, secure, and extensible AI agent platform. Olympus AI provides a Codex-like developer experience, a CLI-like toolbelt, and an agentic execution loop with explicit consent and observability.

See also: [ARCHITECTURE.md](ARCHITECTURE.md) for diagrams and internals.

## Features

- Agentic execution
  - Plans-as-code (DAG with cycle detection, retries, deadlines)
  - Worker executor with backoff+jitter, transcript events, and persistence
  - REST API to submit/run/query plans and direct actions
- LLM routing
  - Backends: llama.cpp (preferred local), Ollama (local), OpenAI fallback (budgeted)
  - Caching and daily budgets (USD for cloud, tokens for llama.cpp)
  - Health and usage endpoints
- Tools (secure by default)
  - Files: read/write/delete/list with sandbox escape + symlink defense
  - Code context: glob + regex search
  - Shell: sandboxed command execution with timeout
  - Git: status/add/commit helpers
  - Network: HTTP GET (consent-gated)
  - Consent scopes enforced when `OLY_REQUIRE_CONSENT=true`
- Observability and ops
  - JSON logs, Prometheus metrics (`/metrics`), health checks
  - Request ID, rate limiting, timeouts, body-size limits
- Developer experience
  - Make targets for format/lint/type/test/smoke and llama.cpp dev server
  - CI with lint, tests, smoke, security scans

## Quick Start

Prerequisites: Python 3.11+, optional Node.js (client), optional Docker (infra), optional llama-cpp server

1) Install dev dependencies

```bash
pip install -r requirements-dev.txt
```

2) Start API and worker (dev)

```bash
make dev      # API on :8000, worker in background
make smoke    # quick health+metrics check
```

3) Run tests and linters

```bash
make fmt && make lint && make type && make test
```

## LLM Setup

Option A: llama.cpp (recommended local)
- Place GGUF models in `/home/donovan/Documents/LocalLLMs` (default) or set `LLAMA_CPP_MODEL_DIR`.
- Start a server using llama-cpp-python:
  - `make llamacpp-run MODEL=YourModel.gguf`
- Configure backend:
  - `export OLY_LLM_BACKEND=llamacpp`
  - `export LLAMA_CPP_URL=http://127.0.0.1:8080`
- Health and usage:
  - `curl localhost:8000/v1/llm/health`
  - `curl localhost:8000/v1/llm/usage` (or check `/v1/config` under `LLM_USAGE_TODAY`)
- Optional token budget:
  - `export OLY_DAILY_TOKEN_BUDGET=200000`

Option B: Ollama
- Import model with `ollama create` or pull defaults
- Configure:
  - `export OLY_LLM_BACKEND=ollama`
  - `export OLLAMA_URL=http://127.0.0.1:11434`
  - `export OLLAMA_MODEL=my-model`
  - Optional allowlist: `export OLLAMA_MODEL_ALLOWLIST=my-model`

Option C: Cloud fallback (OpenAI)
- Enable and set daily USD budget:
  - `export OLY_ENABLE_CLOUD=true`
  - `export OPENAI_API_KEY=...`
  - `export OLY_DAILY_USD_BUDGET=0.50`

## API Endpoints (core)

- Health/metrics/config
  - `GET /health` → `{status: ok}`
  - `GET /metrics` → Prometheus text
  - `GET /v1/config` → redacted settings + `LLM_USAGE_TODAY`
  - `GET /v1/llm/health`, `GET /v1/llm/usage`
- Plans
  - `POST /v1/plan/submit` → materialize plan
  - `GET /v1/plan/{id}` → plan/steps/events
  - `POST /v1/plan/{id}/run` → run async
- Direct actions
  - `POST /v1/act` → execute a capability with explicit consent token/scopes

## Consent & Security

Set `OLY_REQUIRE_CONSENT=true` to enforce consent for tools. Scopes:
- File system: `read_fs`, `write_fs`, `delete_fs`, `list_fs`
- Search: `search_fs`
- Shell: `exec_shell`
- Git: `git_ops`
- Network: `net_get`

In dev, `OLY_AUTO_CONSENT=true` auto-grants scopes; in prod it should be false.

## Tools Catalog

- fs: `fs.read`, `fs.write`, `fs.delete`, `fs.list` (sandboxed under `.sandbox`)
- search: `fs.glob`, `fs.search`
- shell: `shell.run` (cwd inside sandbox)
- git: `git.status`, `git.add`, `git.commit`
- net: `net.http_get`

## Example: Plan to format, lint, type-check, test, commit

1) Create a plan with steps:
- `fs.glob` to find files
- `shell.run` to call `ruff`, `black`, `mypy`, `pytest`
- `git.add` + `git.commit` if checks pass

2) Submit + run:
```
curl -sS -X POST localhost:8000/v1/plan/submit -H 'content-type: application/json' -d '{
  "title":"code quality pipeline",
  "steps":[
    {"name":"fmt","capability":"shell.run","input":{"cmd":"ruff check --fix apps packages tests && black apps packages tests"},"guard":{}},
    {"name":"type","capability":"shell.run","deps":["fmt"],"input":{"cmd":"mypy apps packages || true"}},
    {"name":"test","capability":"shell.run","deps":["type"],"input":{"cmd":"pytest -q"}},
    {"name":"git","capability":"shell.run","deps":["test"],"input":{"cmd":"git add -A && git commit -m 'quality: fmt+type+test' || true"}}
  ]
}' | jq .
```
Then `POST /v1/plan/{id}/run`.

## Make Targets

- `make fmt` → ruff --fix + black
- `make lint` → ruff + black --check (+ client/server lint if present)
- `make type` → mypy (if installed)
- `make test` → pytest
- `make smoke` → boot API briefly and check `/health` and `/metrics`
- `make llamacpp-run MODEL=YourModel.gguf` → run llama-cpp-python server (uses `LLAMA_CPP_MODEL_DIR`, default `/home/donovan/Documents/LocalLLMs`)

## CI Summary

GitHub Actions runs: lint, type (non-gating), pytest, smoke, security scans (pip-audit/bandit/detect-secrets) and image scans (Trivy). Node lint/audit run non-blocking if client/server present.

## Repository Notes

- Dead/placeholder code is quarantined under `deadcode/20250817/` to avoid conflicts.
- The filesystem sandbox root defaults to `.sandbox`; llama.cpp GGUF files live outside the repo.
