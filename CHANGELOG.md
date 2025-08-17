# Changelog

## [Unreleased]

### Added
- **Assistant Kernel**: Implemented the core assistant functionality, including plan execution and tool adapters.
- **Memory Stack**: Added a memory stack with a PostgreSQL backend, including schemas for events, facts, embeddings, and more.
- **LLM Router**: Implemented an LLM router with support for multiple providers, budget management, and caching.
- **Tools & Consent**: Added a tool package with file system tools, consent management, and security features.
- **Desktop App**: Created a desktop application for interacting with the assistant, including settings, task queue, and consent prompts.
- **Observability**: Implemented structured logging across all services.

## [2025-08-17] Major hardening + llama.cpp backend + dev UX

### Added
- LLM backend: llama.cpp provider with OpenAI-compatible and native `/completion` support.
- LLM usage endpoints: `/v1/llm/health`, `/v1/llm/usage`, and `LLM_USAGE_TODAY` in `/v1/config`.
- Daily token budget for llama.cpp via `OLY_DAILY_TOKEN_BUDGET` and cached accounting.
- Developer tools: `fs.glob`, `fs.search`, `shell.run`, `git.status/add/commit`; consent scopes added for each.
- Make target `llamacpp-run` to start llama-cpp-python server with model directory default `/home/donovan/Documents/LocalLLMs`.
- Docs: `docs/LLM-Setup-llamacpp.md`, `docs/Agent-Capabilities.md`. README revamped.

### Changed
- API: Added `/health`, `/v1/config`, `/v1/dev/sleep` and consolidated middlewares (rate limit, timeouts, body-size, request ID).
- Tools: Filesystem sandbox hardened (realpath + symlink traversal prevention). Network tool enforces consent.
- MemoryDB: Fixed events iterator bug; added helpers `get_connection()` and `ensure_base_schema()`; default DB path `.data/olympus.db`.
- LLM router: Async chat API (tests), allowlist enforcement, cache; backends are switchable via `OLY_LLM_BACKEND`.
- CI/Make: Added `fmt`, `lint`, `type`, `smoke`; CI now runs lint/type/test/smoke and security scans.

### Removed
- Quarantined conflicting placeholder modules into `deadcode/20250817/`.
