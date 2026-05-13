#!/usr/bin/env bash
set -euo pipefail

echo "=== Test: Backend ==="
cd backend && pytest --cov=app --cov-report=term-missing -v && cd ..

echo "=== Test: AI Orchestrator ==="
cd ai-orchestrator && pytest -v && cd ..

echo "=== Test: Agents ==="
cd agents && pytest -v && cd ..

echo "=== Test: Prompt Manager ==="
cd prompt-manager && pytest -v && cd ..

echo "=== Test: Logging ==="
cd logging && pytest -v && cd ..

echo "=== All tests complete ==="
