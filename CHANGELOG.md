# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

## [Unreleased]

- Planned Phase 1–8 features per `plans/migration-plan.md`.

## [0.1.0] - 2025-08-13

### Added

- Monorepo skeleton aligned to target architecture:
  - `apps/api` (FastAPI) and `apps/worker` (Python daemon)
  - `packages/plan`, `packages/memory`, `packages/llm`, `packages/tools`, `packages/automation`
  - `infra/` for local init and setup, `tests/`, `plans/`, and `reports/`
- API application (`olympus_api`):
  - Endpoints: `GET /health`, `GET /v1/ping`, `GET /v1/config`
  - CORS middleware with dev-friendly defaults
  - Editable install via `apps/api/pyproject.toml`
- Worker daemon (`olympus_worker`):
  - Async heartbeat loop and environment bootstrap
  - Editable install via `apps/worker/pyproject.toml`
- Plan DSL (`olympus_plan`):
  - Pydantic models `Plan`, `Step`, `StepAction`, and `PlanBudget`
- Memory package (`olympus_memory`):
  - SQLite helpers: `get_connection()`, `ensure_base_schema()`
- LLM router (`olympus_llm`):
  - Local-first chat via Ollama `/api/chat` with model override and options
- Tools package (`olympus_tools`):
  - Allow‑listed filesystem utilities (`resolve_for_write`, `write_text`, `read_text`)
- Automation package (`olympus_automation`):
  - Artifact helpers writing under `SANDBOX_ROOT` (`save_text`, `save_bytes`)
- Infra and Dev UX:
  - `infra/init.sh` bootstraps `.env`, initializes SQLite DB, and pulls a small Ollama model if available
  - New `Makefile` with `init`, `venv`, `install`, `dev-api`, `dev-worker`, `test`, `modelfile`, `precommit`
  - Pre-commit config (`.pre-commit-config.yaml`) with Black and Ruff
  - Dev requirements (`requirements-dev.txt`)
  - Smoke tests: API health and SQLite base schema
- Documentation and planning:
  - `reports/repo-audit.md`, `reports/gap-analysis.md`
  - `plans/migration-plan.md`

### Changed

- Replaced the previous root `Makefile` script with a proper multi-target Makefile and preserved model Modelfile generation via `make modelfile`.
- Consolidated Python packages as editable installs to improve local dev workflow.

### Removed

- Removed misplaced `apps/api/app/*` stubs in favor of `apps/api/olympus_api/*`.

### Security

- Introduced filesystem allow-listing via `ALLOW_WRITE_DIRS` for local tools and sandboxed artifacts under `SANDBOX_ROOT`.

### CI/Tests

- Added initial tests; `make test` runs and passes locally (2 tests).

### Files (summary)

- Added
  - `reports/repo-audit.md`
  - `reports/gap-analysis.md`
  - `plans/migration-plan.md`
  - `infra/init.sh`
  - `apps/api/pyproject.toml`
  - `apps/api/olympus_api/__init__.py`
  - `apps/api/olympus_api/main.py`
  - `apps/worker/pyproject.toml`
  - `apps/worker/olympus_worker/__init__.py`
  - `apps/worker/olympus_worker/main.py`
  - `packages/plan/pyproject.toml`
  - `packages/plan/olympus_plan/__init__.py`
  - `packages/plan/olympus_plan/models.py`
  - `packages/memory/pyproject.toml`
  - `packages/memory/olympus_memory/__init__.py`
  - `packages/memory/olympus_memory/db.py`
  - `packages/llm/pyproject.toml`
  - `packages/llm/olympus_llm/__init__.py`
  - `packages/llm/olympus_llm/router.py`
  - `packages/tools/pyproject.toml`
  - `packages/tools/olympus_tools/__init__.py`
  - `packages/tools/olympus_tools/fs.py`
  - `packages/automation/pyproject.toml`
  - `packages/automation/olympus_automation/__init__.py`
  - `packages/automation/olympus_automation/artifacts.py`
  - `.pre-commit-config.yaml`
  - `requirements-dev.txt`
  - `tests/test_api_health.py`
  - `tests/test_memory_db.py`
- Modified
  - `Makefile`
- Removed
  - `apps/api/app/__init__.py`
  - `apps/api/app/main.py`

[Unreleased]: ./CHANGELOG.md#unreleased
[0.1.0]: ./CHANGELOG.md#010---2025-08-13
