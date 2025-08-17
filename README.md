# Olympus AI — Private AI Assistant (Easy Guide)

Olympus AI is a private assistant that runs on your computer. It understands plain English, proposes a plan, asks for permission when needed, and does the work locally (no cloud by default).

This guide is written for everyone — you don’t need to be a developer to try it.

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

## Quick Start (10–15 minutes)

You will start two things:
- a small “brain” (the local model) using llama.cpp
- the Olympus assistant

Before you begin: make sure you have Python 3.11+ installed.

1) Install
- Open a terminal in this folder:
  - `pip install -r requirements-dev.txt`

2) Start the local brain (llama.cpp)
- Put your GGUF model file in: `/home/donovan/Documents/LocalLLMs` (or change later)
- Start the model server and keep it running:
  - `make llamacpp-run MODEL=YourModel.gguf`

3) Start the assistant
- Open a second terminal and run:
  - `make dev`
- The assistant API runs at `http://127.0.0.1:8000`

Open a browser at `http://127.0.0.1:8000/ui` for a simple chat page.

4) Talk to Olympus in natural language
- In a third terminal, try:
  - `curl -sS -X POST http://127.0.0.1:8000/v1/agent/chat -H 'content-type: application/json' -d '{"message":"Format, type‑check and test the project"}' | jq .`
- Olympus will reply. If a task needs permission (like writing files or running commands), it will ask first.

## LLM Setup (your local model)

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

## Useful Endpoints (optional)

- Health/metrics/config
  - `GET /health` → `{status: ok}`
  - `GET /metrics` → Prometheus text
  - `GET /v1/config` → redacted settings + `LLM_USAGE_TODAY`
  - `GET /v1/llm/health`, `GET /v1/llm/usage`
- Chat: `POST /v1/agent/chat` → send natural language, agent replies or acts (with your permission)
- Plans: `POST /v1/plan/submit`, `POST /v1/plan/{id}/run`, `GET /v1/plan/{id}`
- Direct action: `POST /v1/act` (advanced)

## Consent & Safety

Set `OLY_REQUIRE_CONSENT=true` to enforce consent for tools. Scopes:
- File system: `read_fs`, `write_fs`, `delete_fs`, `list_fs`
- Search: `search_fs`
- Shell: `exec_shell`
- Git: `git_ops`
- Network: `net_get`

- In development, you may set `OLY_AUTO_CONSENT=true`, but for safety it is off by default.

## What tools can it use? (catalog)

- fs: `fs.read`, `fs.write`, `fs.delete`, `fs.list` (sandboxed under `.sandbox`)
- search: `fs.glob`, `fs.search`
- shell: `shell.run` (cwd inside sandbox)
- git: `git.status`, `git.add`, `git.commit`
- net: `net.http_get`

## Example: Give permission and run a task

- First request (no permission yet):
  - `curl -sS -X POST http://127.0.0.1:8000/v1/agent/chat -H 'content-type: application/json' -d '{"message":"Format and test the project"}' | jq .`
- If it asks for permission, repeat with scopes:
  - `curl -sS -X POST http://127.0.0.1:8000/v1/agent/chat -H 'content-type: application/json' -d '{"message":"Format and test the project","consent_scopes":["exec_shell","write_fs","git_ops"]}' | jq .`
  - Olympus will run the plan and reply with a status.

## Make Targets (for convenience)

- `make fmt` → ruff --fix + black
- `make lint` → ruff + black --check (+ client/server lint if present)
- `make type` → mypy (if installed)
- `make test` → pytest
- `make smoke` → boot API briefly and check `/health` and `/metrics`
- `make llamacpp-run MODEL=YourModel.gguf` → run llama-cpp-python server (uses `LLAMA_CPP_MODEL_DIR`, default `/home/donovan/Documents/LocalLLMs`)

## Learn More

- Architecture overview: `ARCHITECTURE.md`
- Llama.cpp setup: `docs/LLM-Setup-llamacpp.md`
- Advanced capabilities: `docs/Agent-Capabilities.md`

## Notes

- Dead/placeholder code is quarantined under `deadcode/20250817/` to avoid conflicts.
- The sandbox folder is `.sandbox`. Your GGUF model files live outside the repo (e.g., `/home/donovan/Documents/LocalLLMs`).
