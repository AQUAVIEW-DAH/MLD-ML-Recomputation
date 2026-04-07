# Next Session Handoff

## Current Focus
- We are investigating whether the ML correction prototype can be trained on time-coincident in-situ profiles and Global RTOFS fields, instead of the current smoke-test setup that pairs 2023-2024 observations with a short local 2026 RTOFS cache.
- Do not accept or freeze `ML_baseline/model.pkl` yet. It was dirty before this work and should remain out of acceptance until time-coincident validation is stable.

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
- Add a WOD THREDDS fallback path for years/files not present in `noaa-wod-pds`, starting with 2025 XBT.
- Build a separate time-coincident WOD XBT dataset from 2024 + 2025 using same-day Global RTOFS, without overwriting the main temporally decoupled `training_data.csv`.
- Then benchmark that dataset separately and treat it as the cleaner RTOFS-residual prototype, while keeping the 2023 dense glider block parked until exact historical Global RTOFS access is found.
