#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MLD_BASE_URL:-http://127.0.0.1}"
API_URL="${MLD_API_HEALTH_URL:-http://127.0.0.1:8001/health}"

printf 'Checking backend directly: %s\n' "$API_URL"
curl -fsS "$API_URL"
printf '\n\nChecking nginx health proxy: %s/health\n' "$BASE_URL"
curl -fsS "$BASE_URL/health"
printf '\n\nChecking nginx metadata proxy: %s/metadata\n' "$BASE_URL"
curl -fsS "$BASE_URL/metadata" >/dev/null
printf 'metadata ok\n'
printf '\nChecking frontend shell: %s/\n' "$BASE_URL"
curl -fsS "$BASE_URL/" | head -5
