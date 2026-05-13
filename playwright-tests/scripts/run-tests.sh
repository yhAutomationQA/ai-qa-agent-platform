#!/usr/bin/env bash
# ─────────────────────────────────────────────────
# Local Test Runner
# Convenience wrapper for common test scenarios
# ─────────────────────────────────────────────────

set -euo pipefail

usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  --headed      Run in headed mode"
  echo "  --ui          Open Playwright UI"
  echo "  --debug       Run in debug mode"
  echo "  --chrome      Chromium only"
  echo "  --firefox     Firefox only"
  echo "  --webkit      WebKit only"
  echo "  --smoke       Smoke tests only"
  echo "  --api         API tests only"
  echo "  --update      Update Playwright"
  echo "  --clean       Clean artifacts"
  echo "  -h, --help    Show this help"
  exit 0
}

# Parse args
ARGS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --headed) ARGS+=("--headed") ;;
    --ui)     ARGS+=("--ui") ;;
    --debug)  ARGS+=("--debug") ;;
    --chrome) ARGS+=("--project=chromium") ;;
    --firefox) ARGS+=("--project=firefox") ;;
    --webkit) ARGS+=("--project=webkit") ;;
    --smoke)  ARGS+=("--grep @smoke") ;;
    --api)    ARGS+=("--grep @api") ;;
    --update) npx playwright install --with-deps; exit 0 ;;
    --clean)  rm -rf test-results playwright-report; exit 0 ;;
    -h|--help) usage ;;
    *) ARGS+=("$1") ;;
  esac
  shift
done

echo "═══════════════════════════════════════════"
echo "  Playwright Test Runner"
echo "═══════════════════════════════════════════"
echo "  Node: $(node -v)"
echo "═══════════════════════════════════════════"

npx playwright test "${ARGS[@]}"
