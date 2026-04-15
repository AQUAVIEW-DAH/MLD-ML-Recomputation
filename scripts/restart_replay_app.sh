#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_SESSION="${MLD_API_SESSION:-mld_api_replay_8001}"
FRONTEND_SESSION="${MLD_FRONTEND_SESSION:-mld_frontend_replay}"

if tmux has-session -t "$API_SESSION" 2>/dev/null; then
  tmux kill-session -t "$API_SESSION"
fi

if tmux has-session -t "$FRONTEND_SESSION" 2>/dev/null; then
  tmux kill-session -t "$FRONTEND_SESSION"
fi

tmux new-session -d -s "$API_SESSION" "cd '$ROOT_DIR' && ./scripts/run_replay_api.sh"
tmux new-session -d -s "$FRONTEND_SESSION" "cd '$ROOT_DIR' && ./scripts/run_replay_frontend.sh"

printf 'Started replay app:\n'
printf '  API session:      %s on http://127.0.0.1:8001\n' "$API_SESSION"
printf '  Frontend session: %s on http://127.0.0.1:5174\n' "$FRONTEND_SESSION"
printf '\nRun ./scripts/check_replay_health.sh to verify readiness.\n'
