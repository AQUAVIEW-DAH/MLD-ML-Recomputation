#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_NAME="mld-replay-ngrok.service"

mkdir -p "$UNIT_DIR" "$ROOT_DIR/logs"
cp "$ROOT_DIR/deploy/systemd/user/$UNIT_NAME" "$UNIT_DIR/$UNIT_NAME"

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME"
systemctl --user status "$UNIT_NAME" --no-pager

cat <<'MSG'

ngrok user service installed. To keep it alive across logout/reboot, an admin should run:
  sudo loginctl enable-linger suramya

Check the public URL with:
  ./scripts/get_ngrok_url.sh
MSG
