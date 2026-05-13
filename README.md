# AI QA Agent Platform

Enterprise-grade AI-powered testing and quality assurance platform built with a modular monorepo architecture.

## Architecture

```
ai-qa-agent-platform/
├── frontend/                 # React + Next.js dashboard
├── backend/                  # FastAPI REST API
├── ai-orchestrator/          # AI orchestration & pipeline management
├── agents/                   # Agent framework (browser, API, planner, reporter)
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
| **frontend** | Next.js 14, React 18, Tailwind CSS, TanStack Query | Dashboard UI for managing tests, agents, runs |
| **backend** | FastAPI, SQLAlchemy (async), Celery, Redis | REST API for CRUD operations, auth, background jobs |
| **ai-orchestrator** | OpenAI, Anthropic, Redis | AI pipeline: plan → execute → analyze → report |
| **agents** | Playwright, httpx | Extensible agent framework (browser, API, planner, reporter) |
| **playwright-tests** | Playwright, TypeScript | Page object model UI test suites |
| **api-tests** | pytest, httpx, jsonschema | API integration tests with response validation |
| **prompt-manager** | Jinja2, YAML | Versioned prompt template library |
| **logging** | structlog, OpenTelemetry, Sentry | Structured JSON logging with tracing |

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

# Run tests
make test
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
# Backend unit tests
cd backend && pytest --cov=app -v

# API integration tests
cd api-tests && pytest -v

# E2E tests (requires frontend running)
cd playwright-tests && npx playwright test

# AI orchestrator tests
cd ai-orchestrator && pytest -v
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — LLM provider keys
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `NEXT_PUBLIC_API_URL` — Frontend API endpoint

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
