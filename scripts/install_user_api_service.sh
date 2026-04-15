#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_NAME="mld-replay-api.service"

mkdir -p "$UNIT_DIR" "$ROOT_DIR/logs"
cp "$ROOT_DIR/deploy/systemd/user/$UNIT_NAME" "$UNIT_DIR/$UNIT_NAME"

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME"
systemctl --user status "$UNIT_NAME" --no-pager

cat <<'MSG'

User service installed. For true boot-persistent 24/7 operation, an admin should also run:
  sudo loginctl enable-linger suramya

Without linger, user services may stop after logout depending on server policy.
MSG
