#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_NAME="mld-replay"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must be run as root, e.g. sudo ./scripts/install_nginx_site.sh" >&2
  exit 1
fi

if ! command -v nginx >/dev/null 2>&1; then
  apt-get update
  apt-get install -y nginx
fi

if [[ ! -f "$ROOT_DIR/mld-dashboard/dist/index.html" ]]; then
  cat >&2 <<MSG
Missing frontend build at mld-dashboard/dist/index.html.
Run this as the repo user first:
  ./scripts/build_frontend.sh
Then rerun:
  sudo ./scripts/install_nginx_site.sh
MSG
  exit 1
fi

install -m 0644 "$ROOT_DIR/deploy/nginx/mld-replay.conf" "/etc/nginx/sites-available/$SITE_NAME"
ln -sfn "/etc/nginx/sites-available/$SITE_NAME" "/etc/nginx/sites-enabled/$SITE_NAME"

# Disable the default site when present so this app owns port 80 by default.
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl reload nginx || systemctl restart nginx
systemctl status nginx --no-pager
