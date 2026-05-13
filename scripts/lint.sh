#!/usr/bin/env bash
set -euo pipefail

echo "=== Lint: Python ==="
ruff check backend/ ai-orchestrator/ agents/ api-tests/ prompt-manager/ logging/ --fix

echo "=== Format: Python ==="
black backend/ ai-orchestrator/ agents/ api-tests/ prompt-manager/ logging/

echo "=== Type Check: Python ==="
mypy backend/ ai-orchestrator/ agents/ --ignore-missing-imports || true

echo "=== Lint: Frontend ==="
cd frontend && npx tsc --noEmit && cd ..

echo "=== Format: Frontend ==="
cd frontend && npx prettier --write . && cd ..

echo "=== Lint complete ==="
