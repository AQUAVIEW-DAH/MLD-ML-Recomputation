#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGROK_BIN="${NGROK_BIN:-$ROOT_DIR/bin/ngrok}"
PORT="${MLD_PUBLIC_PORT:-8001}"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

if [[ ! -x "$NGROK_BIN" ]]; then
  echo "ngrok binary not found. Run ./scripts/install_ngrok_local.sh first." >&2
  exit 1
fi

exec "$NGROK_BIN" http "http://127.0.0.1:${PORT}" --log stdout --log-level info
