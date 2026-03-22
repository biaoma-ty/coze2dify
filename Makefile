.PHONY: help install dev build test lint format clean docker-up docker-down docker-build ci-local e2e-smoke install-githooks

# ── Default ──────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Install ──────────────────────────────────────────
install: ## Install all dependencies (backend + frontend)
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

# ── Dev Servers ──────────────────────────────────────
dev: ## Start backend + frontend dev servers
	@echo "Starting backend..."
	cd backend && uvicorn main:app --reload --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev

dev-backend: ## Start backend dev server only
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend: ## Start frontend dev server only
	cd frontend && npm run dev

# ── Build ────────────────────────────────────────────
build: build-frontend ## Build all

build-frontend: ## Build frontend for production
	cd frontend && npm run build

# ── Test ─────────────────────────────────────────────
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && pytest -v --tb=short

test-frontend: ## Run frontend type check
	cd frontend && npx tsc --noEmit

# ── Lint & Format ────────────────────────────────────
lint: lint-backend lint-frontend ## Lint all

lint-backend: ## Lint backend (ruff)
	cd backend && ruff check .

lint-frontend: ## Lint frontend (eslint)
	cd frontend && npm run lint

format: ## Format backend code (ruff)
	cd backend && ruff format .

check: lint test build ## Run all checks (lint + test + build)

ci-local: ## Run the local CI gate before pushing (Python matrix import + lint + tests + build)
	./scripts/ci-local.sh

e2e-smoke: ## Run the browser-level migration smoke gate against an ephemeral Dify stack
	./scripts/e2e-smoke.sh

install-githooks: ## Install repository git hooks (pre-push runs local CI gate)
	git config core.hooksPath .githooks

# ── Docker ───────────────────────────────────────────
docker-up: ## Start all services via Docker Compose
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-build: ## Build Docker images
	docker compose build

docker-logs: ## Tail Docker logs
	docker compose logs -f

docker-restart: ## Restart all services
	docker compose down && docker compose up -d

# ── Clean ────────────────────────────────────────────
clean: ## Clean build artifacts
	rm -rf frontend/dist
	rm -rf backend/__pycache__ backend/**/__pycache__
	rm -rf backend/*.egg-info
	find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
