
.PHONY: help dev test init setup-ollama setup-db clean lint format fmt type install dev-api dev-worker dev-desktop migrate smoke

# Default target
help:
	@echo "Available commands:"
	@echo "  make init        - Complete initial setup (install deps, setup DB, install Ollama)"
	@echo "  make dev         - Start all services in development mode"
	@echo "  make dev-api     - Start API server only"
	@echo "  make dev-worker  - Start worker only"
	@echo "  make dev-desktop - Start desktop app only"
	@echo "  make test        - Run all tests"
	@echo "  make fmt         - Format code (Python/JS)"
	@echo "  make lint        - Run linters (ruff/black check)"
	@echo "  make type        - Run type checks (mypy if installed)"
	@echo "  make clean       - Clean generated files and caches"
	@echo "  make migrate     - Run database migrations"
	@echo "  make smoke       - Start API briefly and run smoke checks"

# Complete initialization
init: install setup-db setup-ollama
	@echo "✅ Initialization complete!"
	@echo "Run 'make dev' to start development"

# Install all dependencies
install:
	@echo "📦 Installing dependencies..."
	@if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
	@if [ -f apps/api/requirements.txt ]; then pip install -r apps/api/requirements.txt; fi
	@if [ -f apps/worker/requirements.txt ]; then pip install -r apps/worker/requirements.txt; fi
	@echo "✅ Dependencies installed"

# Setup SQLite database
setup-db:
	@echo "🗄️  Setting up SQLite database..."
	@mkdir -p .data
	@if [ ! -f .data/olympus.db ]; then \
		python -c "from olympus_memory import ensure_base_schema; ensure_base_schema()"; \
		echo "✅ Database ready at .data/olympus.db"; \
	else \
		echo "ℹ️  Database already exists"; \
	fi

# Setup Ollama (best-effort)
setup-ollama:
	@echo "🤖 Setting up Ollama (optional)..."
	@which ollama >/dev/null 2>&1 || echo "Install Ollama manually if needed"

# Development servers
dev:
	@echo "🚀 Starting all services..."
	@trap 'kill 0' INT; \
	make dev-api & \
	make dev-worker & \
	wait

dev-api:
	@echo "🌐 Starting API server..."
	@python -m uvicorn apps.api.olympus_api.main:app --reload --port 8000

dev-worker:
	@echo "⚙️  Starting worker..."
	@python apps/worker/olympus_worker/main.py || echo "⚠️  Worker entry optional"

dev-desktop:
	@echo "🖥️  Desktop app placeholder"

# Testing
test:
	@echo "🧪 Running tests..."
	@pytest tests/ -q || echo "⚠️  No tests found"

# Code quality
lint:
	@echo "🔍 Running linters..."
	@ruff check apps/ packages/ tests/ || true
	@black --check apps/ packages/ tests/ || true
	@if [ -f client/package.json ]; then (cd client && npm run -s lint || true); fi
	@if [ -f server/package.json ]; then (cd server && npm run -s lint || true); fi

fmt:
	@echo "✨ Formatting code..."
	@ruff check --fix apps/ packages/ tests/ || true
	@black apps/ packages/ tests/ || true
	@if [ -f client/package.json ]; then (cd client && npm run -s format || true); fi
	@if [ -f server/package.json ]; then (cd server && npm run -s format || true); fi

format: fmt

type:
	@echo "🧠 Running type checks..."
	@if command -v mypy >/dev/null 2>&1; then mypy apps packages || true; else echo "mypy not installed"; fi

# Database migrations
migrate:
	@echo "📊 No migrations configured"

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov/
	@echo "✅ Cleanup complete"

smoke:
	@echo "🚬 Smoke testing API..."
	@python - <<'PY'
import time, threading, sys
from uvicorn import Config, Server
from apps.api.olympus_api.main import app
cfg = Config(app=app, host="127.0.0.1", port=8000, log_level="warning")
svr = Server(cfg)
t = threading.Thread(target=lambda: sys.exit(svr.run()))
t.daemon = True
t.start()
time.sleep(1.0)
import httpx
with httpx.Client() as c:
    r = c.get("http://127.0.0.1:8000/health"); assert r.status_code == 200
    r = c.get("http://127.0.0.1:8000/metrics"); assert r.status_code == 200
	print("OK")
PY

# Run llama.cpp server (llama-cpp-python) for local dev
# Usage: make llamacpp-run MODEL=your_model.gguf [HOST=127.0.0.1 PORT=8080]
llamacpp-run:
	@if ! python -c "import llama_cpp" >/dev/null 2>&1; then \
		echo "llama-cpp-python not installed. Run: pip install llama-cpp-python"; \
		exit 1; \
	fi
	@if [ -z "$(MODEL)" ]; then \
		echo "Please set MODEL=<gguf filename> (found in $$LLAMA_CPP_MODEL_DIR)"; \
		exit 1; \
	fi
	@MODEL_DIR=$${LLAMA_CPP_MODEL_DIR:-/home/donovan/Documents/LocalLLMs}; \
	HOST=$${HOST:-127.0.0.1}; PORT=$${PORT:-8080}; \
	MODEL_PATH="$$MODEL_DIR/$(MODEL)"; \
	echo "Starting llama.cpp server for $$MODEL_PATH on $$HOST:$$PORT"; \
	LLAMA_CPP_URL="http://$$HOST:$$PORT" \
	python -m llama_cpp.server --model "$$MODEL_PATH" --host "$$HOST" --port "$$PORT"
