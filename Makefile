.PHONY: help init venv install dev-api dev-worker test modelfile precommit lint typecheck

PY?=python3
PIP?=$(PY) -m pip
VENVDIR=.venv
ACTIVATE=. $(VENVDIR)/bin/activate;

help:
	@echo "Targets:"
	@echo "  make init         - bootstrap .env (from .env.dev), SQLite DB"
	@echo "  make venv         - create Python venv"
	@echo "  make install      - install API, worker, and packages (editable) + dev deps"
	@echo "  make dev-api      - run FastAPI dev server"
	@echo "  make dev-worker   - run worker daemon"
	@echo "  make test         - run tests"
	@echo "  make lint         - run ruff and black --check"
	@echo "  make typecheck    - (optional) mypy"
	@echo "  make modelfile    - generate an Ollama Modelfile (MODEL_FULL_PATH=/abs/path.gguf)"
	@echo "  make precommit    - install pre-commit hooks"

init:
	bash infra/init.sh

venv:
	$(PY) -m venv $(VENVDIR)
	$(ACTIVATE) $(PIP) install -U pip setuptools wheel

install: venv
	$(ACTIVATE) $(PIP) install -e apps/api -e apps/worker -e packages/plan -e packages/memory -e packages/llm -e packages/tools -e packages/automation
	$(ACTIVATE) $(PIP) install -r requirements-dev.txt

dev-api:
	$(ACTIVATE) uvicorn olympus_api.main:app --reload --host $${UVICORN_HOST:-0.0.0.0} --port $${UVICORN_PORT:-8000} --app-dir apps/api

dev-worker:
	$(ACTIVATE) python -m olympus_worker.main

test:
	$(ACTIVATE) pytest -q

lint:
	$(ACTIVATE) ruff check . --fix
	$(ACTIVATE) black --check .

typecheck:
	@if command -v mypy >/dev/null 2>&1; then $(ACTIVATE) mypy .; else echo "mypy not installed"; fi

# Generate a Modelfile which points to a local GGUF model file
# Usage: make modelfile MODEL_FULL_PATH=/abs/path/to/model.gguf
modelfile:
	@if [ -z "$(MODEL_FULL_PATH)" ]; then echo "MODEL_FULL_PATH is required"; exit 1; fi
	@echo "Creating Modelfile pointing to $(MODEL_FULL_PATH)..."
	@echo "FROM $(MODEL_FULL_PATH)\n\nSYSTEM \"\nYou are Lexi-Llama, an uncensored and helpful AI assistant. Provide factual and direct responses.\n\"" > Modelfile
	@echo "Wrote Modelfile"

precommit:
	$(ACTIVATE) pre-commit install
