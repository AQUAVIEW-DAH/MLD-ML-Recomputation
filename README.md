# MLD Historical Replay Prototype

This repository contains a prototype for machine-learning-corrected mixed layer depth (MLD) estimates in the Gulf of Mexico.

The current app is intentionally a **historical replay sandbox**, not a live 2026 operational service. It replays a dense Jul-Aug 2025 holdout window where same-day RTOFS model fields and in-situ profile observations are available, then demonstrates the product loop: query a point, correct the model estimate, show confidence, and explain provenance.

## Current Prototype

- **Mode:** historical replay sandbox
- **Replay window:** 2025-07-07 to 2025-08-31
- **Training data:** same-day RTOFS + WOD/Argo rows before 2025-07-07
- **Holdout data:** Jul-Aug 2025 Argo rows excluded from training
- **Frozen replay model:** `artifacts/models/model_historical_replay_2025_jul_aug.pkl`
- **Raw RTOFS holdout:** MAE 7.112m, RMSE 9.274m, R2 -0.003
- **Corrected replay holdout:** MAE 6.431m, RMSE 8.355m, R2 0.186

## What The App Shows

The dashboard lets a user select a replay date, click the Gulf of Mexico map, and inspect an MLD estimate with provenance.

Current map layers include:

- Nearby in-situ observations used for the clicked estimate
- All replay in-situ points for the selected date
- Raw model MLD background field
- ML correction hotspot field
- Final corrected MLD field

The goal is to make the correction explainable, not just numerical: users should see where the model started, which observations informed the estimate, how large the correction was, and how confident the system is.

## Why Historical Replay

The original product idea was a live AQUAVIEW-style endpoint that combines model forecasts with nearby in-situ observations. During discovery, we found that the live in-situ path is not reliable enough yet for real-time ML correction. The historical replay sandbox gives us a truthful MVP:

- RTOFS fields exist for the replay dates.
- In-situ profiles exist for the replay dates.
- The holdout window was excluded from model training.
- The app can demonstrate the intended user experience without pretending to be operationally live.

See `docs/historical_sandbox.md` for the full rationale. For no-public-IP deployment, see `docs/ngrok_deployment.md`.

## Run The Replay App

From the repo root:

```bash
./scripts/restart_replay_app.sh
./scripts/check_replay_health.sh
```

Then open:

```text
http://127.0.0.1:5174/
```

The backend runs on `127.0.0.1:8001`; the Vite frontend runs on `127.0.0.1:5174` and proxies API requests to the backend.

## Important Paths

```text
api.py                                      FastAPI replay/runtime API
historical_replay.py                        Replay metadata, date, RTOFS, and holdout helpers
mld_pipeline.py                             MLD estimate pipeline and provenance assembly
mld_core.py                                 Core RTOFS and MLD calculation helpers
mcp_server.py                               MCP wrapper for agent access
mld-dashboard/                              React/Vite/Leaflet frontend
ml/                                         ML processing, training, source, and audit code
artifacts/                                  Frozen models, datasets, audit CSVs, and generated reports
docs/                                       Human-facing prototype docs
scripts/                                    Local run/check helpers
NEXT_SESSION_HANDOFF.md                     Working-session continuity notes
CHANGELOG.md                               Historical project log
```

The research-era `ML_baseline/` directory has been split into `ml/` source code and `artifacts/` generated outputs.

## In-Situ Profile Requirements

For the current MLD label, a candidate profile generally needs:

- Gulf of Mexico location
- Timestamp
- Latitude and longitude
- Vertical depth or pressure coordinate
- Temperature values through and below the 10m reference depth
- Enough valid depth-temperature levels to compute a 0.2C threshold MLD
- Observed MLD in a sane range, currently 10-100m for the GoM prototype
- Matching same-day RTOFS availability and successful feature extraction

See `docs/insitu_requirements.md` for details.

## Prototype Caveats

- This is not a live operational product.
- AQUAVIEW is not the replay observation source.
- ERDDAP gliders are currently treated as diagnostic/sidecar data because deployment clustering hurt grouped generalization.
- The replay model is prototype-ready for the app, not production accepted.
- The current repo layout still preserves several research artifacts so the analysis trail remains auditable.

