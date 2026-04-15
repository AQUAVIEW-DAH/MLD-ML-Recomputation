# Historical Replay Sandbox

## Purpose

The historical replay sandbox is the current MVP shape for ML-corrected mixed layer depth estimates. It demonstrates the full product loop using a frozen historical window instead of claiming real-time operation before the live in-situ data path is ready.

## Why We Chose Replay Instead Of Live

The original vision was a live query service: users request MLD at a location and time, and the app combines a model forecast with nearby in-situ observations. That is still the product direction, but the current live in-situ path is not mature enough for reliable 2026 operation.

The replay sandbox solves this by using a period where we have both sides of the correction problem:

- Same-day RTOFS model fields
- In-situ profile observations
- A strict train/holdout split
- A frontend that shows correction, confidence, and provenance

This makes the prototype honest: it demonstrates the target product behavior without overstating operational readiness.

## Current Frozen Window

- Replay holdout: 2025-07-07 to 2025-08-31
- Train rows: 796
- Train sources: 713 Argo GDAC rows and 83 WOD rows
- Holdout rows: 269
- Holdout source: Argo GDAC
- Holdout dates: 11
- Holdout platforms: 21

The holdout rows are excluded from training and used as the replay observation/provenance source in the app.

## Frozen Artifact

```text
artifacts/models/model_historical_replay_2025_jul_aug.pkl
```

This is the current app model for historical replay mode.

## Validation Snapshot

Raw RTOFS on the replay holdout:

- MAE: 7.112m
- RMSE: 9.274m
- R2: -0.003

ML-corrected replay artifact:

- MAE: 6.431m
- RMSE: 8.355m
- R2: 0.186

The improvement is modest but real enough for a prototype demo. It is not production acceptance.

## App Behavior

The app defaults to historical replay mode and exposes:

- `/health` for backend status
- `/metadata` for replay date/model metadata
- `/mld` for point estimates
- `/map_layer` for model, correction, corrected, and observation layers

The frontend uses the Vite proxy so browser requests go to same-origin paths like `/metadata` and `/mld`, then Vite forwards them to the backend on port 8001.

## Product Interpretation

The replay sandbox should be presented as:

> A faithful historical time capsule of the intended live product experience.

It should not be presented as:

> A real-time operational MLD correction service.
