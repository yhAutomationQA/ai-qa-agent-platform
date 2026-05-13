.PHONY: help install-dev lint format test build clean docker-up docker-down

SHELL := /bin/bash

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install all development dependencies
	@echo "Installing backend dependencies..."
	pip install -r backend/requirements.txt
	pip install -r ai-orchestrator/requirements.txt
	pip install -r agents/requirements.txt
	pip install -r api-tests/requirements.txt
	pip install -r prompt-manager/requirements.txt
	pip install -r logging/requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	cd playwright-tests && npm install

install-dev-python: ## Install Python dev dependencies only
	pip install -r backend/requirements.txt
	pip install -r ai-orchestrator/requirements.txt
	pip install -r agents/requirements.txt
	pip install -r api-tests/requirements.txt
	pip install -r prompt-manager/requirements.txt
	pip install -r logging/requirements.txt

install-dev-node: ## Install Node dev dependencies only
	cd frontend && npm install
	cd playwright-tests && npm install

lint: ## Run all linters
	cd backend && ruff check .
	cd ai-orchestrator && ruff check .
	cd agents && ruff check .
	cd api-tests && ruff check .
	cd prompt-manager && ruff check .
	cd logging && ruff check .
	cd frontend && npx tsc --noEmit
	cd frontend && npx next lint

format: ## Format all code
	cd backend && black .
	cd ai-orchestrator && black .
	cd agents && black .
	cd api-tests && black .
	cd prompt-manager && black .
	cd logging && black .
	cd frontend && npx prettier --write .

typecheck: ## Run type checking
	cd backend && mypy .
	cd ai-orchestrator && mypy .
	cd agents && mypy .
	cd frontend && npx tsc --noEmit

test: ## Run all tests
	cd backend && pytest
	cd ai-orchestrator && pytest
	cd agents && pytest
	cd api-tests && pytest
	cd prompt-manager && pytest
	cd logging && pytest
	cd playwright-tests && npx playwright test

test-backend: ## Run backend tests only
	cd backend && pytest

test-frontend: ## Run frontend tests only
	cd frontend && npm test

test-e2e: ## Run Playwright e2e tests only
	cd playwright-tests && npx playwright test

build: ## Build all artifacts
	cd frontend && npm run build
	cd backend && pip wheel -w dist .

clean: ## Clean build artifacts
	rm -rf **/__pycache__ **/.pytest_cache **/*.egg-info **/dist **/build
	rm -rf frontend/.next frontend/out
	rm -rf playwright-tests/test-results playwright-tests/playwright-report

docker-build: ## Build all Docker images
	docker compose -f docker/docker-compose.yml build

docker-up: ## Start all services
	docker compose -f docker/docker-compose.yml up -d

docker-down: ## Stop all services
	docker compose -f docker/docker-compose.yml down

docker-dev: ## Start dev services
	docker compose -f docker/docker-compose.dev.yml up

setup: ## Full project setup
	@echo "Setting up AI QA Agent Platform..."
	cp .env.example .env || true
	cp config/base.yaml config/local.yaml || true
	make install-dev
	@echo "Setup complete!"

.PHONY: help install-dev install-dev-python install-dev-node lint format typecheck test test-backend test-frontend test-e2e build clean docker-build docker-up docker-down docker-dev setup
