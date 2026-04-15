#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT_DIR/bin"
NGROK_BIN="$BIN_DIR/ngrok"
ARCH="$(uname -m)"

case "$ARCH" in
  x86_64|amd64) NGROK_ARCH="amd64" ;;
  aarch64|arm64) NGROK_ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

mkdir -p "$BIN_DIR"
if [[ -x "$NGROK_BIN" ]]; then
  "$NGROK_BIN" version
  exit 0
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
ZIP_PATH="$TMP_DIR/ngrok.zip"
URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-${NGROK_ARCH}.zip"

curl -fsSL "$URL" -o "$ZIP_PATH"
unzip -q "$ZIP_PATH" -d "$TMP_DIR"
install -m 0755 "$TMP_DIR/ngrok" "$NGROK_BIN"
"$NGROK_BIN" version
