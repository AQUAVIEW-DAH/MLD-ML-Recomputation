# Combined WOD XBT + Argo GDAC 2024-2025 Same-Day RTOFS Benchmark

Timestamp: 2026-04-07 21:42

Data path: `ML_baseline/training_data_combined_rtofs_2024_2025.csv`

Dataset: 1,065 same-day RTOFS profiles from `WOD_XBT_2024`, `WOD_XBT_2025`, and the Argo GDAC top-40-date subset.

Validation: repeated `GroupShuffleSplit` by platform/cruise, 48 groups, 10 splits, `test_size=0.20`.

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| LinearRegression | 8.509m | 0.692m | 11.278m | 1.203m | 0.076 | 0.116 | 7.287m-9.205m |
| RandomForest | 9.025m | 0.662m | 12.136m | 1.211m | -0.075 | 0.155 | 7.907m-10.270m |
| XGBoost | 9.838m | 0.765m | 13.179m | 1.061m | -0.279 | 0.254 | 8.393m-11.143m |
| HistGradientBoosting | 9.841m | 0.804m | 12.975m | 1.093m | -0.234 | 0.210 | 8.428m-11.341m |

## Data Summary

- Total rows: 1,065
- Source families: `{'ARGO_GDAC': 982, 'WOD': 83}`
- Instruments: `{'pfl': 982, 'xbt': 83}`
- Platforms: 48
- Dates: 55
- Test rows per split: min 111, max 275
- Observed MLD range: 10.2m to 93.5m
- Model MLD range: 10.6m to 102.3m

## Interpretation

- The combined table slightly improves mean R² over the Argo-only benchmark: 0.076 vs 0.043 for LinearRegression.
- The result is still dominated by Argo profiles because the clean WOD-XBT block contributes only 83 rows.
- This is the best current same-day RTOFS prototype, but it is not production-acceptance evidence yet.
- Do not freeze or accept a new `model.pkl` from this dataset alone.
