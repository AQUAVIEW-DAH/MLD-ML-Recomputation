# Local Operations

## Start Or Restart The Replay App

From the repo root:

```bash
./scripts/restart_replay_app.sh
```

This starts two tmux sessions:

- `mld_api_replay_8001`
- `mld_frontend_replay`

## Check Health

```bash
./scripts/check_replay_health.sh
```

Expected healthy behavior:

- Backend health returns HTTP 200 from `http://127.0.0.1:8001/health`
- Frontend metadata proxy returns HTTP 200 from `http://127.0.0.1:5174/metadata`

## Open The App

```text
http://127.0.0.1:5174/
```

## Stop Sessions Manually

```bash
tmux kill-session -t mld_api_replay_8001
tmux kill-session -t mld_frontend_replay
```

The restart script already handles this safely.

## Logs

Local runtime logs are written under `logs/`:

```text
logs/api_replay_8001.log
logs/frontend_replay.log
```

These are local run artifacts and should not be committed.
