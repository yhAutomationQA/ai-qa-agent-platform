# AI QA Agent Platform

Enterprise-grade AI-powered testing and quality assurance platform built with a modular monorepo architecture.
Features automated test execution (Playwright + API), AI-driven failure analysis, and a real-time QA dashboard.

## Architecture

```
ai-qa-agent-platform/
├── frontend/                 # React + Next.js dashboard
├── backend/                  # FastAPI REST API
│   ├── execution/            # Test execution engine (Playwright, API, parallel, retries)
│   └── analysis/             # AI failure analysis (root cause, risk, categorization)
├── ai-orchestrator/          # AI orchestration & pipeline management
├── agents/                   # Agent framework (browser, API, planner, reporter)
├── test-generation/          # AI test case generation service
├── playwright-tests/         # Playwright UI automation tests
├── api-tests/                # API integration test suites
├── prompt-manager/           # Prompt template management
├── config/                   # Environment-specific YAML configuration
├── logging/                  # Centralized structured logging
├── docker/                   # Docker Compose & Dockerfiles
├── .github/workflows/        # CI/CD pipelines
└── scripts/                  # Development utility scripts
```

### Modules

| Module | Stack | Purpose |
|--------|-------|---------|
| **frontend** | Next.js 14, React 18, Tailwind CSS, Recharts, TanStack Query | QA dashboard with pass/fail charts, risk indicators, AI insights, recent failures, quality trends |
| **backend** | FastAPI, SQLAlchemy (async), Celery, Redis | REST API for CRUD, auth, background jobs |
| **backend/execution** | asyncio, subprocess, JUnit XML parser | Test execution engine — runs Playwright/pytest, captures logs/screenshots, handles retries + parallel execution |
| **backend/analysis** | OpenAI, Pydantic, pattern matching | AI failure analysis — root cause suggestions, failure categorization, risk scoring, retry recommendations |
| **ai-orchestrator** | OpenAI, Anthropic, Redis | AI pipeline: plan → execute → analyze → report |
| **agents** | Playwright, httpx | Extensible agent framework (browser, API, planner, reporter, requirement analysis) |
| **test-generation** | OpenAI, Jinja2 | AI-powered generation of Playwright tests, API tests, and test data |
| **playwright-tests** | Playwright, TypeScript | Page object model UI test suites with custom fixtures and reporters |
| **api-tests** | pytest, httpx, jsonschema | API integration tests with response validation |
| **prompt-manager** | Jinja2, YAML | Versioned prompt template library |
| **logging** | structlog, OpenTelemetry, Sentry | Structured JSON logging with tracing |

## Features

### Test Execution Engine
- Execute Playwright browser tests and pytest API tests via subprocess
- Parallel execution with configurable worker pool
- Automatic retries with exponential backoff per test
- Real-time log capture (stdout/stderr) with byte-level limits
- Screenshot and artifact collection on failure
- JUnit XML and Playwright JSON report parsing
- Execution summaries with pass/fail/skip/error counts and duration

### AI Failure Analysis
- **Root cause analysis** — pattern-based + LLM-powered root cause suggestions with evidence
- **Failure categorization** — 13 categories (assertion, timeout, flaky, infrastructure, permission, etc.) with hybrid pattern/AI classification
- **Risk assessment** — score-based (0–1) with modifiers for retries, severity tags, status codes; aggregates across batch runs
- **Retry advisor** — 3-tier policy (non-retryable / always-retry / conditional) with per-category delay and exhaustion detection
- **AI insights** — optional OpenAI integration for deeper analysis; graceful fallback to pattern-only mode when unavailable

### QA Dashboard
- Real-time execution summary cards (total, passed, failed, runs, active agents)
- Pass/fail donut chart with percentage breakdown
- Quality trend area chart (14-day pass/fail/pass-rate history)
- Risk indicators sorted by score with color-coded severity bars
- AI insights panel (anomalies, patterns, suggestions, warnings, improvements)
- Recent failures list with category badges, retry counts, and relative timestamps
- Time-range selector (24h/7d/30d/90d)
- Loading skeleton and error states

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/execution/execute` | Execute a single test |
| `POST` | `/api/v1/execution/execute/batch` | Execute tests in parallel |
| `GET` | `/api/v1/execution/config` | View execution config |
| `PUT` | `/api/v1/execution/config` | Update execution config |
| `POST` | `/api/v1/failure-analysis/analyze` | Analyze a single test failure |
| `POST` | `/api/v1/failure-analysis/analyze/batch` | Analyze multiple failures |
| `GET` | `/api/v1/failure-analysis/config` | View analysis config |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (for services)
- PostgreSQL 16 (via Docker)
- Redis 7 (via Docker)

### Setup

```bash
# Clone and enter the repo
git clone <repo-url> && cd ai-qa-agent-platform

# Full automated setup
make setup

# Or manually:
./scripts/setup.sh

# Start infrastructure (Postgres, Redis)
make docker-dev

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, etc.)
```

### Run

```bash
# Start all services with Docker
make docker-up

# Or run locally:
source .venv/bin/activate
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev

# Open the dashboard:
open http://localhost:3000/dashboard

# Run tests
make test
```

### Try the Execution Engine

```bash
# Execute a Playwright test (requires Playwright installed)
curl -X POST http://localhost:8000/api/v1/execution/execute \
  -H "Content-Type: application/json" \
  -d '{
    "test_case_id": "demo-1",
    "test_case_name": "Demo Login Test",
    "execution_type": "playwright",
    "test_file": "tests/login.spec.ts",
    "max_retries": 1
  }'

# Analyze a test failure (no AI, pattern-based)
curl -X POST "http://localhost:8000/api/v1/failure-analysis/analyze?use_ai=false" \
  -H "Content-Type: application/json" \
  -d '{
    "test_name": "user_login_test",
    "error_message": "AssertionError: Expected 200, got 500",
    "execution_type": "api",
    "api_status_code": 500
  }'
```

## Development

### Available Commands

```bash
make install-dev      # Install all dependencies
make lint             # Run all linters
make format           # Format all code
make typecheck        # Type checking
make test             # Run all tests
make test-backend     # Backend tests only
make test-e2e         # Playwright e2e tests only
make docker-up        # Start all services
make docker-dev       # Start dev infrastructure
make clean            # Clean build artifacts
```

### Testing

```bash
# All backend tests (unit + execution + analysis)
cd backend && pytest --cov=app -v

# Specific test suites
cd backend && pytest tests/test_execution.py -v   # 63 tests — execution engine
cd backend && pytest tests/test_analysis.py -v    # 57 tests — AI failure analysis
cd backend && pytest tests/test_health.py -v      # health endpoints

# API integration tests
cd api-tests && pytest -v

# E2E tests (requires frontend running)
cd playwright-tests && npx playwright test

# AI orchestrator tests
cd ai-orchestrator && pytest -v

# Test generation service
cd test-generation && pytest -v
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — LLM provider keys
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `NEXT_PUBLIC_API_URL` — Frontend API endpoint (default: `http://localhost:8000/api/v1`)
- `ANALYSIS_ENABLE_AI` — Enable AI-powered failure analysis (default: `true`)
- `ANALYSIS_AI_FALLBACK` — Fall back to pattern-only when AI fails (default: `true`)

## Docker

```bash
# Build all images
make docker-build

# Start all services
make docker-up

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop
make docker-down
```

Single service:

```bash
docker compose -f docker/docker-compose.yml up backend
```

## CI/CD

The project includes GitHub Actions workflows:

- **CI** (`.github/workflows/ci.yml`): Lint, test, build on every push/PR
- **CD** (`.github/workflows/cd.yml`): Build & push Docker images, create GitHub release on version tags

## License

This project is licensed under the terms of the LICENSE file.
