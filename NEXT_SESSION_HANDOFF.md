# Next Session Handoff

## Current Focus
- We are investigating whether the ML correction prototype can be trained on time-coincident in-situ profiles and Global RTOFS fields, instead of the current smoke-test setup that pairs 2023-2024 observations with a short local 2026 RTOFS cache.
- Do not accept or freeze `ML_baseline/model.pkl` yet. It was dirty before this work and should remain out of acceptance until time-coincident validation is stable.

## Current Session Checkpoint: Same-Day RTOFS Prototypes
- WOD XBT 2024/2025 same-day prototype is complete and committed in `8aebe15`.
- Argo GDAC 2024/2025 same-day prototype is complete and committed in `ec7b4f5`.
- ERDDAP glider 2024/2025 same-day prototype finished in tmux and produced final artifacts:
  - `ML_baseline/ERDDAP_GLIDER_RTOFS_2024_2025_REPORT.md`
  - `ML_baseline/erddap_glider_2024_2025_profile_audit.csv`
  - `ML_baseline/training_data_erddap_glider_rtofs_2024_2025.csv`
  - `ML_baseline/benchmark_results_erddap_glider_rtofs_2024_2025.md`
- The tmux session exited; `tmux ls` now reports no tmux server.
- The raw tmux log is `ML_baseline/erddap_glider_rtofs_2024_2025_tmux.log`; do not commit it unless we explicitly decide to keep raw run logs in git.
- A rare invalid-label issue was caught after the first ERDDAP run: some noisy glider profiles produced MLD values shallower than the 10m reference. The ERDDAP builder now requires valid observed MLD in the 10-100m range, and the generated ERDDAP CSV/report were repaired accordingly.

## Same-Day RTOFS Data Results So Far
- WOD XBT 2024/2025:
  - 138 GoM XBT profiles extracted.
  - 106 profiles had 10m temperature-threshold MLD <=100m and same-day public RTOFS availability.
  - 83 rows retained with RTOFS features.
  - Coverage: 6 platforms, 14 half-degree cells.
  - Benchmark: RandomForest mean MAE 9.305m, mean R² -0.244.
- Argo GDAC 2024/2025:
  - 5,371 GoM profile files in the Argo global profile index across 51 platforms.
  - 10,165 usable 10m/profile-QC profile records extracted.
  - 9,177 valid MLD<=100m labels.
  - 8,894 profiles had same-day public RTOFS availability.
  - Top-40-date bounded feature pass produced 982 rows.
  - Coverage: 42 platforms, 172 half-degree cells.
  - Benchmark: LinearRegression mean MAE 8.508m, mean R² 0.043.
- Combined WOD-XBT + Argo:
  - 1,065 rows across 48 platforms and 55 dates.
  - Benchmark: LinearRegression mean MAE 8.509m, mean R² 0.076.
  - This remains the best positive-R² same-day RTOFS prototype, but still do not freeze `model.pkl`.
- ERDDAP glider:
  - 18,485 profiles extracted after profile/10m QC.
  - 13,518 valid 10m-reference labels in the 10-100m range.
  - Top-40-date bounded feature pass produced 2,715 rows.
  - Coverage: 12 platforms, 14 half-degree cells.
  - Benchmark: LinearRegression mean MAE 3.927m, mean R² -0.196.
  - Interpretation: much more row volume, but strongly clustered by glider deployment.
- Combined WOD-XBT + Argo + ERDDAP:
  - 3,780 rows across 60 platforms and 92 dates.
  - Coverage: 192 half-degree cells.
  - Benchmark: LinearRegression mean MAE 5.186m, mean R² -0.050.
  - Interpretation: more rows and broader source mix, but grouped generalization is still not stable enough for model acceptance.
- Balanced ERDDAP variants:
  - Cap rule: keep all WOD-XBT + Argo rows, then cap ERDDAP rows by platform/date/0.25-degree cell.
  - Cap1: 1,158 rows, 93 ERDDAP rows, LinearRegression mean MAE 7.827m, mean R² 0.022.
  - Cap2: 1,243 rows, 178 ERDDAP rows, LinearRegression mean MAE 7.715m, mean R² -0.017.
  - Cap3: 1,327 rows, 262 ERDDAP rows, LinearRegression mean MAE 7.647m, mean R² -0.050.
  - Interpretation: light ERDDAP use can keep R² barely positive, but none of the balanced variants beats the WOD-XBT + Argo baseline R² of 0.076.
- Separate WOD+Argo candidate artifact:
  - Artifact: `ML_baseline/model_wod_argo_rtofs_2024_2025_linear.pkl`
  - Training report: `ML_baseline/train_ml_report_wod_argo_rtofs_2024_2025_linear.md`
  - Model type: `LinearRegression`
  - Data: `ML_baseline/training_data_combined_rtofs_2024_2025.csv`
  - One grouped split result: MAE 8.939m, R² 0.267.
  - Interpretation: promising candidate artifact for the best current same-day source mix, but still not a production freeze or replacement for `model.pkl`.

## Key Finding: 2023 WOD Density
- The dense 2023 WOD block is not broad year-round density. It is mostly one glider deployment.
- Current WOD rows in `ML_baseline/training_data.csv`: 1,150.
- 2023 WOD rows: 1,114. 2024 WOD rows: 36 in the finalized CSV.
- `WOD_GLD_2023` contributes 963 rows.
- `MOTE-DORA (Slocum G3 glider; WMO4802994)` contributes 831 rows from 2023-04-30 to 2023-05-16.
- `US055862` contributes 132 glider rows from 2023-08-28 to 2023-09-05.
- The main 2023 consecutive-date blocks are:
  - 2023-04-30 to 2023-05-16: 831 rows, mostly MOTE-DORA glider.
  - 2023-08-28 to 2023-09-05: 151 rows, mostly US055862 glider plus some XBT.
- Public NOAA Global RTOFS S3 current-pattern keys did not exist for these 2023 dates in our checks, so we should not use these rows for RTOFS-residual model acceptance unless we find a real historical Global RTOFS archive.

## Key Finding: Next Closest RTOFS-Compatible WOD Blocks
- Public Global RTOFS S3 appears available from about 2024-01-27 onward.
- Current finalized 2024 WOD rows are sparse because WOD GLD 2024 and WOD APB 2024 had zero GoM profiles in our cached audit; usable 2024 WOD rows were XBT-only.
- A raw 2024 WOD XBT re-check found 63 GoM profiles with valid observed MLD under the 100m sanity cap, and 54 of those had same-day RTOFS features using already-downloaded 2024 RTOFS files.
- 2024 time-matchable WOD XBT rows are concentrated on 2024-06-01, 2024-06-06, 2024-08-10, 2024-08-15, 2024-09-07, and 2024-09-12.
- NCEI THREDDS now exposes 2025 WOD files even though `noaa-wod-pds` S3 still returned 404 for 2025 WOD keys in our probe.
- Lightweight 2025 THREDDS probe found:
  - `wod_xbt_2025.nc`: 43 GoM profiles with valid observed MLD under 100m.
  - `wod_gld_2025.nc`: 0 GoM profiles.
  - `wod_apb_2025.nc`: 0 GoM profiles.
- 2025 WOD XBT valid rows cluster on 2025-01-25, 2025-01-30, 2025-02-06, 2025-05-08, 2025-05-14, and 2025-05-19.
- Matching RTOFS S3 files exist for those 2025 dates under the `noaa-nws-rtofs-pds` bucket.

## Important Nuance To Carry Forward
- The in-situ sources are not necessarily intrinsically too sparse. The sparse training set is the subset that survives all of our requirements:
  - Gulf of Mexico bbox.
  - Vertical temperature/depth profile.
  - Enough valid depth-temperature levels.
  - Coverage around the 10m reference depth for our MLD definition.
  - Observed MLD can be computed and is not an obvious outlier over 100m.
  - Matching RTOFS feature extraction succeeds at the profile lat/lon and valid date.
- The 10m reference requirement is especially important: our observed MLD label uses the temperature threshold relative to temperature at 10m. Profiles that start deeper than 10m can look profile-shaped but cannot produce a comparable label.
- This explains why some candidate sources are dense before QC but sparse afterward. Call this out next session before interpreting sparse final-row counts as raw source scarcity.

## Recommended Next Step
- Use the completed WOD-XBT, Argo, and ERDDAP reports to decide whether to keep ERDDAP in the final same-day training mix or treat it as a separate glider-only diagnostic due to clustering.
- Add/standardize a spatial coverage diagnostic for every same-day training CSV, ideally including unique RTOFS cells and not just half-degree cells.
- Use Argo+WOD as the primary same-day prototype for now, and keep ERDDAP as a sidecar/diagnostic until validation can handle deployment clustering better.
- If we want a next technical step, extend `train_ml.py` or a new trainer to save scaler/metadata consistently and evaluate repeated grouped splits before promoting any candidate artifact.
- Keep the 2023 dense glider block parked until exact historical Global RTOFS access is found.
