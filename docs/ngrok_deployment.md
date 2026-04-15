# ngrok Deployment

Use this when the server does not have a public IP or inbound firewall access. ngrok creates an outbound tunnel from the server to a public HTTPS URL.

## Recommended Shape

```text
Browser
  |
  | https://random-or-reserved.ngrok-free.app
  v
ngrok tunnel
  |
  v
FastAPI on 127.0.0.1:8001
  |-- serves API routes: /health, /metadata, /mld, /map_layer
  |-- serves built frontend from mld-dashboard/dist
```

This avoids nginx entirely for the no-public-IP prototype path. The FastAPI backend becomes the single local app server, and ngrok exposes that one port.

## Token Safety

Do not commit ngrok auth tokens. Configure the token only in the local user environment or ngrok's user config.

The scripts expect `NGROK_AUTHTOKEN` to be exported when configuring ngrok, but they do not store it in the repository.

## First-Time Setup

From the repo root:

```bash
git pull origin main
./scripts/build_frontend.sh
./scripts/install_ngrok_local.sh
export NGROK_AUTHTOKEN='<your-ngrok-token>'
./scripts/configure_ngrok_token.sh
./scripts/install_user_api_service.sh
./scripts/install_ngrok_user_service.sh
./scripts/get_ngrok_url.sh
```

The final command prints the public ngrok URL.

## Keep Services Alive Across Logout

The API and ngrok tunnel are installed as user systemd services. For true 24/7 behavior, an admin should enable linger:

```bash
sudo loginctl enable-linger suramya
```

Without linger, user services may stop when the user logs out depending on server policy.

## Health Checks

Direct local backend:

```bash
curl http://127.0.0.1:8001/health
```

ngrok public URL:

```bash
PUBLIC_URL="$(./scripts/get_ngrok_url.sh)"
curl "$PUBLIC_URL/health"
curl "$PUBLIC_URL/metadata"
```

Open the app:

```bash
xdg-open "$PUBLIC_URL/"
```

or paste the URL into a browser.

## Service Commands

```bash
systemctl --user status mld-replay-api.service
systemctl --user status mld-replay-ngrok.service
systemctl --user restart mld-replay-api.service
systemctl --user restart mld-replay-ngrok.service
journalctl --user -u mld-replay-api.service -f
journalctl --user -u mld-replay-ngrok.service -f
```

Local logs are also appended to:

```text
logs/api_replay_8001.log
logs/ngrok.log
```

## Development vs ngrok Production

Development path:

```bash
./scripts/restart_replay_app.sh
```

This uses tmux and Vite on `127.0.0.1:5174`.

ngrok prototype path:

```bash
./scripts/build_frontend.sh
./scripts/install_user_api_service.sh
./scripts/install_ngrok_user_service.sh
```

This uses a built frontend served by FastAPI on `127.0.0.1:8001`, plus ngrok as the public HTTPS tunnel.

## Free ngrok URL Caveat

Free ngrok URLs usually change when the tunnel restarts. For a stable demo URL, reserve a static domain in ngrok and update `scripts/run_ngrok_tunnel.sh` to include the assigned domain flag.
