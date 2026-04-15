#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGROK_BIN="${NGROK_BIN:-$ROOT_DIR/bin/ngrok}"

if [[ ! -x "$NGROK_BIN" ]]; then
  echo "ngrok binary not found. Run ./scripts/install_ngrok_local.sh first." >&2
  exit 1
fi

if [[ -z "${NGROK_AUTHTOKEN:-}" ]]; then
  echo "NGROK_AUTHTOKEN is not set. Export it in your shell, then rerun this script." >&2
  exit 1
fi

"$NGROK_BIN" config add-authtoken "$NGROK_AUTHTOKEN" >/dev/null
printf 'ngrok auth token configured in the local user config.\n'
