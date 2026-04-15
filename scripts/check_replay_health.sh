#!/usr/bin/env bash
set -euo pipefail

API_URL="${MLD_API_HEALTH_URL:-http://127.0.0.1:8001/health}"
METADATA_URL="${MLD_METADATA_URL:-http://127.0.0.1:5174/metadata}"

printf 'Checking backend: %s\n' "$API_URL"
curl -fsS "$API_URL"
printf '\n\nChecking frontend proxy metadata: %s\n' "$METADATA_URL"
curl -fsS "$METADATA_URL"
printf '\n'
