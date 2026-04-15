# Nginx Deployment

This document describes the 24/7 deployment shape for the MLD historical replay app on the remote server.

## Production Shape

```text
Browser
  |
  | http://server/
  v
nginx :80
  |-- serves static frontend from mld-dashboard/dist
  |-- proxies /health, /metadata, /mld, /map_layer
          |
          v
      FastAPI uvicorn on 127.0.0.1:8001
```

The Vite development server on port 5174 should not be used for 24/7 production. It is fine for local development, but nginx should serve the built frontend.

## Files Added

```text
deploy/nginx/mld-replay.conf                  nginx site config
deploy/systemd/system/mld-replay-api.service  system-level API service
deploy/systemd/user/mld-replay-api.service    user-level fallback API service
scripts/build_frontend.sh                     build frontend dist
scripts/install_system_api_service.sh         install API as system service, requires root
scripts/install_user_api_service.sh           install API as user service, no root but needs linger for boot persistence
scripts/install_nginx_site.sh                 install nginx site, requires root
scripts/check_production_health.sh            smoke checks for nginx + API
```

## Recommended Install With Admin/Sudo

From the repo root:

```bash
git pull origin main
./scripts/build_frontend.sh
sudo ./scripts/install_system_api_service.sh
sudo ./scripts/install_nginx_site.sh
./scripts/check_production_health.sh
```

Expected service layout:

```bash
systemctl status mld-replay-api
systemctl status nginx
```

Expected URLs:

```text
http://SERVER_IP/
http://SERVER_IP/metadata
http://SERVER_IP/health
```

## User-Service Fallback

If root access is not available for the API service, install the backend as a user service:

```bash
./scripts/install_user_api_service.sh
```

For true boot-persistent operation, an admin still needs to run:

```bash
sudo loginctl enable-linger suramya
```

Without linger, the service may stop when the user logs out depending on server policy.

## Nginx Notes

`deploy/nginx/mld-replay.conf` uses:

```nginx
server_name _;
```

That means it answers as the default site on port 80. When DNS is ready, replace `_` with the real hostname and optionally add TLS with Certbot.

The nginx config assumes the repo path is:

```text
/home/suramya/MLD-ML-Recomputation
```

If the repo moves, update:

```nginx
root /home/suramya/MLD-ML-Recomputation/mld-dashboard/dist;
```

and the systemd unit paths.

## Development vs Production

Development:

```bash
./scripts/restart_replay_app.sh
```

This uses tmux and Vite on `127.0.0.1:5174`.

Production:

```bash
./scripts/build_frontend.sh
sudo ./scripts/install_system_api_service.sh
sudo ./scripts/install_nginx_site.sh
```

This uses systemd and nginx. No Vite dev server is needed.

## Health Checks

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1/health
curl http://127.0.0.1/metadata
```

The app page should load at:

```text
http://127.0.0.1/
```

or from another machine:

```text
http://SERVER_IP/
```

assuming firewall/security-group rules allow inbound port 80.
