# Historical Replay Split Report

- Input data: `ML_baseline/training_data_combined_rtofs_2024_2025.csv`
- Holdout window: `2025-07-07` to `2025-08-31`
- Train output: `ML_baseline/training_data_train_historical_replay_pre_2025_07_07.csv`
- Holdout output: `ML_baseline/training_data_holdout_historical_replay_2025_jul_aug.csv`

## Train Summary

- Rows: 796
- Dates: 44
- Platforms: 48
- Sources: {'ARGO_GDAC': 713, 'WOD': 83}
- Instruments: {'pfl': 713, 'xbt': 83}
- Min Date: 2024-03-02
- Max Date: 2025-07-02
- Top Dates: {'2024-03-07': 28, '2024-03-12': 32, '2024-03-17': 29, '2024-03-22': 36, '2024-04-01': 28, '2024-05-12': 26, '2024-08-04': 25, '2024-08-14': 26, '2024-08-30': 25, '2024-09-04': 28}

## Holdout Summary

- Rows: 269
- Dates: 11
- Platforms: 21
- Sources: {'ARGO_GDAC': 269}
- Instruments: {'pfl': 269}
- Min Date: 2025-07-07
- Max Date: 2025-08-31
- Top Dates: {'2025-07-07': 22, '2025-07-12': 28, '2025-07-22': 24, '2025-07-27': 22, '2025-08-01': 25, '2025-08-11': 26, '2025-08-16': 26, '2025-08-21': 26, '2025-08-26': 24, '2025-08-31': 24}

## Platform Overlap

- Holdout platforms also seen in train: 21
- Holdout platforms unseen in train: 0
