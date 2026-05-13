#!/usr/bin/env bash
# ─────────────────────────────────────────────────
# CI Test Runner
# Runs Playwright tests with CI-optimized settings
# ─────────────────────────────────────────────────

set -euo pipefail

echo "═══════════════════════════════════════════"
echo "  Playwright CI Runner"
echo "═══════════════════════════════════════════"

# Set CI mode
export CI=true

# Load env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "  Node:    $(node -v)"
echo "  Project: ${PROJECT:-all}"
echo "  Retries: 2"
echo "═══════════════════════════════════════════"

# Install dependencies if not cached
if [ ! -d "node_modules" ]; then
  echo "[CI] Installing dependencies..."
  npm ci
fi

# Install browsers if not cached
if [ ! -d "~/.cache/ms-playwright" ]; then
  echo "[CI] Installing Playwright browsers..."
  npx playwright install --with-deps
fi

# Determine test filter
FILTER=""
if [ -n "${SMOKE:-}" ]; then
  FILTER="--grep @smoke"
  echo "[CI] Running smoke tests only"
elif [ -n "${API:-}" ]; then
  FILTER="--grep @api"
  echo "[CI] Running API tests only"
elif [ -n "${LOGIN:-}" ]; then
  FILTER="tests/login/"
  echo "[CI] Running login tests only"
fi

# Run tests
echo "[CI] Starting test execution..."
npx playwright test $FILTER --reporter=list,json,junit

echo "═══════════════════════════════════════════"
echo "  CI Run Complete"
echo "═══════════════════════════════════════════"
