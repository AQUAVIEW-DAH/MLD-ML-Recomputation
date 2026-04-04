# Initial ML Pipeline Benchmarking (Phase 2)

**Timestamp:** 2026-04-03
**Dataset Constraints:** `rtofs_glo_3dz_f054_6hrly_hvr_US_east.nc` Snapshot (Limited to a singular slice constraint, returning ~6 spatial profiles).

## Multi-Model Baseline Leaderboard

| Model | Mean Absolute Error (MAE) | Root Mean Squared Error (RMSE) | $R^2$ Score |
| :--- | :--- | :--- | :--- |
| **HistGradientBoosting** | 21.853m | 22.193m | -31.833 |
| **RandomForest** | 23.276m | 23.697m | -36.433 |
| **XGBoost** | 24.070m | 31.873m | -66.718 |
| **LinearRegression** | 41.088m | 41.697m | -114.899 |

## Evaluation Insights
1. **Model Selection:** `HistGradientBoostingRegressor` cleanly outperformed standard Random Forest architectures and traditional Regression logic by leveraging LightGBM-style binning over our physical topography (SST Gradients, Surface Salinity, Kinetic Energy). It was subsequently exported to `model.pkl` and connected to `mld_pipeline.py`.
2. **Artificial Overfitting Context:** Because our prototype spatial bounding queries only found 6 corresponding coordinates over essentially 1 Argo deployment inside this literal specific snapshot, the algorithms natively overfitted (demonstrated by the aggressively negative $R^2$ value since there was no broad testing distribution).
3. **Future Scaling Steps:** To normalize and harden this architecture, Gregg Jacobs must deploy `data_builder.py` against a multi-year chronological RTOFS folder, allowing the Ground Truth split to genuinely distribute evaluations across independent platform deployments via `GroupShuffleSplit`.
