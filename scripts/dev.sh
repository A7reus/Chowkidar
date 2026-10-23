#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cleanup() {
  kill "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd apps/api
  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
API_PID=$!

(
  pnpm --filter @chowkidar/web dev
) &
WEB_PID=$!

echo "API:  http://localhost:8000/docs"
echo "Web:  http://localhost:3000"
wait
