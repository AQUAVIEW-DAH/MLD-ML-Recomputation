#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_NAME="mld-replay-api.service"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must be run as root, e.g. sudo ./scripts/install_system_api_service.sh" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/logs"
install -m 0644 "$ROOT_DIR/deploy/systemd/system/$UNIT_NAME" "/etc/systemd/system/$UNIT_NAME"
systemctl daemon-reload
systemctl enable --now "$UNIT_NAME"
systemctl status "$UNIT_NAME" --no-pager
