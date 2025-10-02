#!/usr/bin/env bash
set -euo pipefail

# Load .env if present, ignore if missing
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs -r) || true
  set +a
fi

# If a platform provides PORT, map it to APP_PORT unless APP_PORT explicitly set
if [ -n "${PORT:-}" ] && [ -z "${APP_PORT:-}" ]; then
  export APP_PORT="${PORT}"
fi

HOST="${APP_HOST:-0.0.0.0}"
# Default to 3001 to satisfy orchestrator expectations
PORT_EFFECTIVE="${APP_PORT:-3001}"

echo "[run.sh] Starting FastAPI on ${HOST}:${PORT_EFFECTIVE}"
exec uvicorn app.main:app --host "${HOST}" --port "${PORT_EFFECTIVE}"
