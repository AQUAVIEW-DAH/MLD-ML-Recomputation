# WOD XBT 2024-2025 Same-Day RTOFS Benchmark

Timestamp: 2026-04-07 20:00

Data path: `ML_baseline/training_data_wod_xbt_rtofs_2024_2025.csv`

Dataset: 83 same-day RTOFS/WOD XBT profiles from `WOD_XBT_2024` and `WOD_XBT_2025`.

Validation: repeated `GroupShuffleSplit` by platform/cruise, 6 groups, 10 splits, `test_size=0.20`.

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| RandomForest | 9.305m | 3.904m | 12.975m | 4.424m | -0.244 | 0.250 | 4.870m-18.249m |
| HistGradientBoosting | 9.413m | 3.590m | 13.272m | 4.449m | -0.338 | 0.369 | 6.326m-18.999m |
| LinearRegression | 9.868m | 2.990m | 13.566m | 4.378m | -0.409 | 0.487 | 5.693m-16.173m |
| XGBoost | 10.879m | 4.374m | 15.060m | 4.704m | -0.680 | 0.259 | 4.791m-19.817m |

## Data Summary

- Total rows: 83
- Source families: `{'WOD': 83}`
- Instruments: `{'xbt': 83}`
- Sources: `{'WOD_XBT_2024': 54, 'WOD_XBT_2025': 29}`
- Platforms: 6
- First split train/test: 69/14
- First split held-out platforms: `{'AIRPLANE': 11, 'BREMEN EXPRESS': 3}`
- Test rows per split: min 4, max 62
- Observed MLD range: 10.2m to 90.0m
- Model MLD range: 10.6m to 73.0m

## Interpretation

- RandomForest had the best mean MAE at 9.305m, but mean R² was still negative at -0.244.
- The grouped validation is unstable because the dataset has only 6 platform groups and one platform, EL COQUI, contributes 51/83 rows.
- This benchmark is useful as a clean time-coincident RTOFS prototype diagnostic, not a production model acceptance result.
- Do not freeze or accept a new `model.pkl` from this dataset alone.
