# Historical Replay Training Report

- Train data: `ML_baseline/training_data_train_historical_replay_pre_2025_07_07.csv`
- Holdout data: `ML_baseline/training_data_holdout_historical_replay_2025_jul_aug.csv`
- Output artifact: `ML_baseline/model_historical_replay_2025_jul_aug.pkl`
- Train rows: 796
- Holdout rows: 269
- Train platforms: 48
- Holdout platforms: 21
- Train source families: {'ARGO_GDAC': 713, 'WOD': 83}
- Holdout source families: {'ARGO_GDAC': 269}
- Selected model: `LinearRegression`

## Raw RTOFS Holdout Baseline

- Raw MAE: 7.112m
- Raw RMSE: 9.274m
- Raw R²: -0.003

## Corrected Holdout Leaderboard

| Model | Corrected MAE | Corrected RMSE | Corrected R² | Residual MAE | Mean Correction |
| :--- | ---: | ---: | ---: | ---: | ---: |
| LinearRegression | 6.431m | 8.355m | 0.186 | 6.431m | 3.287m |
| RandomForest | 6.848m | 8.734m | 0.11 | 6.848m | 3.121m |
| XGBoost | 7.569m | 9.609m | -0.077 | 7.569m | 3.162m |
| HistGradientBoosting | 8.065m | 10.115m | -0.193 | 8.065m | 3.261m |

## Interpretation

- This artifact is trained strictly on pre-holdout rows and evaluated on the frozen historical replay window.
- Best corrected holdout result: `LinearRegression` with MAE 6.431m versus raw RTOFS MAE 7.112m.
- Best corrected holdout R²: 0.186 versus raw RTOFS R² -0.003.
- Use this artifact for historical replay mode, not as a claim of real-time 2026 readiness.
