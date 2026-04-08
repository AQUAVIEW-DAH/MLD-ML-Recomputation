# Argo GDAC 2024-2025 Same-Day RTOFS Benchmark

Timestamp: 2026-04-07 21:41

Data path: `ML_baseline/training_data_argo_gdac_rtofs_2024_2025.csv`

Dataset: 982 same-day RTOFS/Argo GDAC profiles from the top 40 profile-dense/platform-diverse RTOFS-eligible dates.

Validation: repeated `GroupShuffleSplit` by platform/cruise, 42 groups, 10 splits, `test_size=0.20`.

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| LinearRegression | 8.508m | 0.429m | 11.714m | 0.866m | 0.043 | 0.094 | 7.868m-9.319m |
| RandomForest | 9.144m | 0.445m | 12.586m | 0.732m | -0.107 | 0.106 | 8.559m-9.913m |
| XGBoost | 9.665m | 0.581m | 13.155m | 0.887m | -0.207 | 0.104 | 8.569m-10.755m |
| HistGradientBoosting | 9.837m | 0.496m | 13.458m | 0.712m | -0.273 | 0.183 | 9.149m-10.751m |

## Data Summary

- Total rows: 982
- Source families: `{'ARGO_GDAC': 982}`
- Instruments: `{'pfl': 982}`
- Platforms: 42
- Dates: 40
- First split train/test: 760/222
- Test rows per split: min 161, max 280
- Observed MLD range: 10.4m to 93.5m
- Model MLD range: 10.7m to 102.3m
- Training 0.25-degree cells: 302
- Training 0.5-degree cells: 172
- Training 1.0-degree cells: 78

## Interpretation

- LinearRegression had the best mean MAE at 8.508m and the first positive mean grouped R² seen in the same-day RTOFS prototypes, at 0.043.
- This is a meaningful improvement over the WOD-XBT-only same-day prototype, which had 83 rows, 6 platforms, and negative mean R².
- This is still a prototype: only the top 40 Argo dates were feature-extracted, and the benchmark is Argo-only rather than a full mixed-source training table.
- Do not freeze or accept a new `model.pkl` from this dataset alone.
