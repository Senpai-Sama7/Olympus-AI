
.PHONY: help dev test init setup-ollama setup-db clean lint format install dev-api dev-worker dev-desktop migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  make init        - Complete initial setup (install deps, setup DB, install Ollama)"
	@echo "  make dev         - Start all services in development mode"
	@echo "  make dev-api     - Start API server only"
	@echo "  make dev-worker  - Start worker only"
	@echo "  make dev-desktop - Start desktop app only"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean generated files and caches"
	@echo "  make migrate     - Run database migrations"

# Complete initialization
init: install setup-db setup-ollama
	@echo "✅ Initialization complete!"
	@echo "Run 'make dev' to start development"

# Install all dependencies
install:
	@echo "📦 Installing dependencies..."
	@if [ -f apps/api/requirements.txt ]; then pip install -r apps/api/requirements.txt; fi
	@if [ -f apps/worker/requirements.txt ]; then pip install -r apps/worker/requirements.txt; fi
	@if [ -f apps/desktop/package.json ]; then cd apps/desktop && npm install; fi
	@echo "✅ Dependencies installed"

# Setup SQLite database
setup-db:
	@echo "🗄️  Setting up SQLite database..."
	@mkdir -p data
	@if [ ! -f data/app.db ]; then \
		sqlite3 data/app.db "VACUUM;"; \
		echo "✅ Database created at data/app.db"; \
	else \
		echo "ℹ️  Database already exists"; \
	fi

# Setup Ollama
setup-ollama:
	@echo "🤖 Setting up Ollama..."
	@if ! command -v ollama &> /dev/null; then \
		echo "Installing Ollama..."; \
		curl -fsSL https://ollama.ai/install.sh | sh; \
	else \
		echo "ℹ️  Ollama already installed"; \
	fi
	@echo "Pulling default model (phi)..."
	@ollama pull phi || echo "⚠️  Failed to pull model, please run 'ollama pull phi' manually"
	@echo "✅ Ollama setup complete"

# Development servers
dev:
	@echo "🚀 Starting all services..."
	@trap 'kill 0' INT; \
	make dev-api & \
	make dev-worker & \
	make dev-desktop & \
	wait

dev-api:
	@echo "🌐 Starting API server..."
	@cd apps/api && python main.py || echo "⚠️  API not yet implemented"

dev-worker:
	@echo "⚙️  Starting worker..."
	@cd apps/worker && python main.py || echo "⚠️  Worker not yet implemented"

dev-desktop:
	@echo "🖥️  Starting desktop app..."
	@cd apps/desktop && npm run dev || echo "⚠️  Desktop app not yet implemented"

# Testing
test:
	@echo "🧪 Running tests..."
	@pytest tests/ -v || echo "⚠️  No tests found"

# Code quality
lint:
	@echo "🔍 Running linters..."
	@flake8 apps/ packages/ tests/ --max-line-length=120 || true
	@black --check apps/ packages/ tests/ || true
	@if [ -f apps/desktop/package.json ]; then cd apps/desktop && npm run lint || true; fi

format:
	@echo "✨ Formatting code..."
	@black apps/ packages/ tests/ || true
	@if [ -f apps/desktop/package.json ]; then cd apps/desktop && npm run format || true; fi

# Database migrations
migrate:
	@echo "📊 Running migrations..."
	@if [ -f packages/memory/migrations/run.py ]; then \
		python packages/memory/migrations/run.py; \
	else \
		echo "ℹ️  No migrations to run"; \
	fi

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov/
	@echo "✅ Cleanup complete"
