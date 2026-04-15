#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/mld-env/bin/python}"
PORT="${MLD_API_PORT:-8001}"
LOG_FILE="${MLD_API_LOG:-$ROOT_DIR/logs/api_replay_8001.log}"

cd "$ROOT_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

APP_MODE=historical_replay "$PYTHON_BIN" -m uvicorn api:app --host 127.0.0.1 --port "$PORT" > "$LOG_FILE" 2>&1
