#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${MLD_FRONTEND_LOG:-$ROOT_DIR/logs/frontend_replay.log}"

cd "$ROOT_DIR/mld-dashboard"
mkdir -p "$(dirname "$LOG_FILE")"

npm run dev -- --host 127.0.0.1 > "$LOG_FILE" 2>&1
