#!/usr/bin/env bash
set -euo pipefail

API_URL="${NGROK_API_URL:-http://127.0.0.1:4040/api/tunnels}"

python - <<'PY'
import json
import os
import sys
import urllib.request

api_url = os.getenv("NGROK_API_URL", "http://127.0.0.1:4040/api/tunnels")
try:
    with urllib.request.urlopen(api_url, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
except Exception as exc:
    raise SystemExit(f"Could not read ngrok tunnel API at {api_url}: {exc}")

for tunnel in payload.get("tunnels", []):
    url = tunnel.get("public_url")
    if url and url.startswith("https://"):
        print(url)
        sys.exit(0)
for tunnel in payload.get("tunnels", []):
    url = tunnel.get("public_url")
    if url:
        print(url)
        sys.exit(0)
raise SystemExit("No ngrok public_url found.")
PY
