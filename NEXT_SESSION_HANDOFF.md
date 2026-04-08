# Next Session Handoff

## Current Focus
- We are investigating whether the ML correction prototype can be trained on time-coincident in-situ profiles and Global RTOFS fields, instead of the current smoke-test setup that pairs 2023-2024 observations with a short local 2026 RTOFS cache.
- Do not accept or freeze `ML_baseline/model.pkl` yet. It was dirty before this work and should remain out of acceptance until time-coincident validation is stable.

## Current Session Checkpoint: Same-Day RTOFS Prototypes
- WOD XBT 2024/2025 same-day prototype is complete and committed in `8aebe15`.
- Argo GDAC 2024/2025 same-day prototype is complete and committed in `ec7b4f5`.
- ERDDAP glider 2024/2025 same-day prototype is currently running in tmux:
  - Session: `mld_erddap_glider`
  - Log: `ML_baseline/erddap_glider_rtofs_2024_2025_tmux.log`
  - Command: `/home/suramya/MLD-ML-Recomputation/mld-env/bin/python ML_baseline/build_erddap_glider_rtofs_2024_2025.py --max-datasets 0 --max-rtofs-dates 40`
- Check tmux status with `tmux ls`.
- Attach with `tmux attach -t mld_erddap_glider` if needed.
- Follow the log with `tail -f ML_baseline/erddap_glider_rtofs_2024_2025_tmux.log`.
- Early log note: older Murphy/Bass deployments can return 404 under the 2024/2025 time-filtered ERDDAP query; do not interpret those as source-wide failure without checking later 2024/2025 glider deployments.
- Live progress at documentation update:
  - 108 ERDDAP candidates selected.
  - 18,485 ERDDAP glider profiles extracted after profile/10m QC.
  - 276 unique ERDDAP observation dates checked for same-day RTOFS availability.
  - Top 40 RTOFS-eligible dates selected for feature extraction.
  - 4,377 profiles selected for the bounded feature pass.
  - The run had reached at least date 19/40 (`20241017`) in the log at this handoff update.

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
  - This is the best current same-day RTOFS prototype, but still do not freeze `model.pkl`.

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
- Let the `mld_erddap_glider` tmux job finish.
- Inspect `ERDDAP_GLIDER_RTOFS_2024_2025_REPORT.md`, `erddap_glider_2024_2025_profile_audit.csv`, and `training_data_erddap_glider_rtofs_2024_2025.csv` if they were created.
- If the glider job produced useful rows, benchmark it separately and then rebuild a combined same-day table with WOD-XBT + Argo + ERDDAP glider.
- After the tmux run finishes, commit generated ERDDAP glider artifacts only after inspecting them. Avoid committing `ML_baseline/erddap_glider_rtofs_2024_2025_tmux.log` unless we explicitly want run logs in git.
- Keep the 2023 dense glider block parked until exact historical Global RTOFS access is found.
