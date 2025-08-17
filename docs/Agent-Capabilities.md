Agent Capabilities

This repo now includes building blocks for:

- Codex-like code understanding
  - Tools: `fs.glob`, `fs.search`, `fs.read`, `fs.list`
  - Use these to fetch relevant snippets and project structure
  - Run `make fmt`, `make lint`, `make type`, and `make test` to enforce syntax/semantics

- CLI-like interaction
  - Tool: `shell.run` to execute commands inside the sandbox (`.sandbox`)
  - Git tools: `git.status`, `git.add`, `git.commit`

- Agentic planning and execution
  - Models: `packages/plan/olympus_plan/models.py`
  - Executor: `apps/worker/olympus_worker/main.py` (PlanExecutor)
  - API: `/v1/plan/submit`, `/v1/plan/{id}/run`, `/v1/act`

Consent scopes (set `OLY_REQUIRE_CONSENT=true` to enforce):
- File system: `read_fs`, `write_fs`, `delete_fs`, `list_fs`
- Search: `search_fs`
- Shell: `exec_shell`
- Git: `git_ops`
- Network: `net_get`

LLM setup (Ollama):
- Import your `.gguf` via `ollama create <name> -f Modelfile`
- Set `OLLAMA_MODEL=<name>` and (optionally) `OLLAMA_MODEL_ALLOWLIST=<name>`
- Set `OLLAMA_URL=http://127.0.0.1:11434` if non-default

