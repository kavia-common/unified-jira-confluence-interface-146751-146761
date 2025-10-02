#!/usr/bin/env bash
set -euo pipefail

export $(grep -v '^#' .env 2>/dev/null | xargs -r) || true

HOST="${APP_HOST:-0.0.0.0}"
PORT="${APP_PORT:-8000}"

exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
