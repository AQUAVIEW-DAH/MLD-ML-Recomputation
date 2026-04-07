# Changelog

All notable changes to the MLD-ML-Recomputation MVP pipeline will be documented in this file.

## [Unreleased] - Phase 5 Breakthrough: WOD S3 Direct Data Access

### Added
- **`ML_baseline/wod_source.py`**: Massive architectural shift bypassing the Aquaview indexer to download original World Ocean Database (WOD) NetCDF files directly from the NOAA public S3 bucket.
- **Direct Source Ingestion**: Implemented a robust "WOD Ragged Array" parser that extracts high-resolution XBT and Glider depth profiles directly from 2023/2024 NetCDF source files.
- **Data Volume Breakthrough**: Unlocked **1,399+ GoM depth profiles** (previously 0 from Aquaview) for high-fidelity training. This includes 191 high-res XBT profiles and 1,208 glider profiles from 2023-2024.
- **`ML_baseline/INSITU_SOURCE_REPORT.md`**: Added a provider/source audit comparing current CSV coverage against WOD, Argo GDAC, OSMC, IOOS Glider DAC, SECOORA/GCOOS ERDDAP, NDBC, TAO, and OceanSITES documentation.
- **`ML_baseline/source_audit.py`**: Added a direct-provider audit utility that checks WOD S3 instrument availability and can optionally count usable GoM profiles without using Aquaview.
- **Direct ERDDAP/Argo discovery audits**: Extended `source_audit.py` with ERDDAP glider candidate discovery and Argo GDAC profile-index counting.
- **`ML_baseline/erddap_glider_source.py`**: Added a direct ERDDAP glider parser that reads curated audit CSVs, queries tabledap `time,latitude,longitude,depth,temperature,profile_id`, groups rows by deployment/profile, and returns profile-shaped observations for the shared MLD builder.
- **`ML_baseline/argo_gdac_source.py`**: Added opt-in direct Argo GDAC ingestion using `ar_index_global_prof.txt` to select GoM profile NetCDF files, cache them locally, and parse QC'd pressure/temperature profiles without Aquaview metadata.

### Changed
- **`data_builder.py` (v3)**: Completely refactored to pull from `wod_source.py` as the primary training data stream. RTOFS model features are now matched to high-res WOD profiles to learn the physical mapping of SST/Salinity/Kinetics to MLD error. Default WOD instruments are now `xbt,gld,apb`.
- **ERDDAP Glider Option**: `data_builder.py` can now include direct ERDDAP glider profiles with `INCLUDE_ERDDAP_GLIDERS=1` and a controlled `ERDDAP_MAX_DATASETS` limit for incremental source expansion.
- **Argo GDAC Option**: `data_builder.py` can now include direct Argo profiles with `INCLUDE_ARGO_GDAC=1`, `ARGO_MAX_PROFILES`, `ARGO_MAX_PER_PLATFORM`, `ARGO_START`, and `ARGO_END` for controlled smoke tests before scaling.
- **WOD/RTOFS Temporal Decoupling**: `data_builder.py` now explicitly logs that historical WOD observations are matched to the nearest available 2026 RTOFS snapshot for spatial/physical feature extraction, rather than claiming true time co-location.
- **Observed MLD Sanity Filter**: Added a 100m observed-MLD cap for GoM training rows. Outlier WOD casts are logged with cast ID, source, instrument, max depth, platform, and computed MLD before being excluded.
- **10m Reference QC**: ERDDAP glider and Argo GDAC ingestion now reject otherwise profile-shaped observations that do not bracket the 10m reference depth required by the project MLD definition, and ERDDAP logs the skip counts by dataset.
- **`benchmark_models.py`**: Updated to support repeated grouped validation by WOD/ERDDAP/Argo platform metadata, with split-level diagnostics and explicit model-acceptance caveats in `benchmark_results.md`.
- **Temporal Matching Strategy**: Documented the 2023-2024 in-situ versus 2026 RTOFS snapshot mismatch in `INGESTION_PLAN.md` and `INSITU_SOURCE_REPORT.md`. The next modeling pivot is to audit historical/time-coincident Global RTOFS pairing before treating benchmark results as model-acceptance evidence.
- **`ML_baseline/rtofs_temporal_audit.py`**: Added a no-download temporal overlap audit for local RTOFS files and NOAA public RTOFS S3 current-pattern keys.
- **`ML_baseline/build_rtofs_time_matched_subset.py`**: Added a separate smoke-test builder that downloads same-day RTOFS files for available dates and writes `training_data_rtofs_time_matched_smoke.csv` without overwriting the main training table.
- **`aquaview_obs.py`**: Relocated to a secondary/validation role for real-time station data (e.g. SECOORA SST), allows the core ML engine to be decoupled from Aquaview indexing.

### Data
- **Filtered WOD training dataset**: `data_builder.py` now generates **1,150 QC-filtered rows** from WOD S3 after dropping 7 implausibly deep XBT MLD outliers (`observed_mld > 100m`). Final mix: 963 `WOD_GLD_2023`, 92 `WOD_APB_2023`, 59 `WOD_XBT_2023`, and 36 `WOD_XBT_2024` rows across 10 platforms.
- **Limited ERDDAP glider ingestion smoke test**: A two-dataset ERDDAP run added 51 final rows from `ioos-gliderdac-Murphy-20150809T1355`, producing **1,201 total QC-filtered rows** across 11 platforms. A second Murphy deployment fetched 334 candidate profiles but did not survive downstream MLD/RTOFS feature matching in this limited run, so it needs source-specific diagnosis before scaling.
- **Argo GDAC smoke test**: Direct GDAC extraction successfully parsed 45 usable profile records from 25 sampled GoM AOML profile files across 5 floats. The combined WOD + ERDDAP + Argo builder retained 32 Argo rows after observed-MLD and RTOFS feature gates, producing 1,233 total training rows.
- **Direct WOD source audit**: Lightweight S3 availability audit found 2023/2024 CTD, PFL, MRB, and APB files available, with PFL files at multi-GB scale. Counted small files showed 2023 APB had 166 usable GoM profiles before model-feature matching, while 2023/2024 CTD, MRB, and DRB yielded 0 GoM profiles in this audit.
- **Direct glider/Argo source audit**: First-page ERDDAP audits found 35 SECOORA and 73 IOOS Glider DAC profile-candidate datasets with depth/temperature/profile metadata. Argo GDAC `ar_index_global_prof.txt` contained 5,393 GoM profile-file entries for 2023-2024, mostly under AOML.

### Benchmarked
- **Grouped holdout benchmark**: Re-ran `benchmark_models.py` on the APB-expanded WOD dataset. `XGBoost` now leads with **MAE=10.126m, RMSE=11.907m, R²=0.062** under `GroupShuffleSplit` by platform/cruise. This is the first slightly positive grouped R², but still not production-ready for cross-platform generalization.
- **Limited ERDDAP benchmark**: Re-ran `benchmark_models.py` after the two-dataset ERDDAP smoke test. `XGBoost` led with **MAE=9.897m, RMSE=13.004m, R²=0.466**, but the grouped test fold had only 35 rows and did not hold out the new ERDDAP platform, so this is a smoke-test signal rather than final production validation.
- **Repeated grouped validation benchmark**: Re-ran `benchmark_models.py` after the WOD + ERDDAP + diversified Argo build using 10 repeated grouped splits across 16 platforms. `LinearRegression` had the lowest mean MAE (**13.604m**, mean R² **-0.084**) while `XGBoost` had mean **MAE=14.606m** and mean **R²=-0.060**. The negative mean grouped R² confirms this is not ready for `model.pkl` acceptance.
- **RTOFS temporal-match audit**: The current `training_data.csv` spans 1,233 rows across 121 observation dates: 51 rows from 2015, 1,146 from 2023, and 36 from 2024. The local 2026 RTOFS cache has 0 same-day matches. The NOAA public RTOFS S3 current-pattern keys are available for 10 sparse 2024 WOD dates, yielding 36 candidate same-day rows, but not for the dense 2023 WOD block.
- **Time-matched smoke benchmark**: Built `training_data_rtofs_time_matched_smoke.csv` with 35 same-day WOD XBT rows across 4 platforms after one row failed RTOFS feature extraction. This is too small for model acceptance; the grouped smoke benchmark had test folds as small as 1 row and best mean MAE **16.197m**.
- **Next-session handoff**: Added `NEXT_SESSION_HANDOFF.md` documenting that the dense 2023 WOD signal is mostly two glider deployments without public current-pattern RTOFS coverage, while the next RTOFS-compatible WOD path is sparse-but-clean 2024/2025 XBT via public RTOFS and NCEI THREDDS WOD. The handoff also notes that final in-situ sparsity is mostly after applying GoM/profile/10m-reference/MLD/RTOFS feature criteria, not necessarily raw source scarcity.
- **Diagnostic random split**: `XGBoost` reaches **MAE=3.496m, RMSE=8.053m, R²=0.637** under a random split, suggesting the feature set can learn the residual relationship but needs broader/better-balanced platform coverage before freezing `model.pkl`.

### [Phase 4] - Multi-Snapshot ML Scaling

### Added
- `ML_baseline/`: Completely encapsulated Machine Learning Engine directory for extracting gradients, building analytical datastores, and generating dynamic predictive models.
- **Data Provenance & Upscaling**: Integrated generalized ERDDAP `csvp` profile extraction scaling Aquaview pipelines (`WOD`, `GCOOS_HIST`, `NDBC`, `GADR`, `IOOS`) to tens of thousands of ground truth points, explicitly tracking `collection_id` and `institution` for end-to-end provenance mapping.
- **Oceanographic Benchmarking**: Formally standardized the ML Validation paradigm to implement `Spatial/Platform Block cross-validation` over random arrays, strictly avoiding oceanic data leakage.
- **Proxy Physics Parameters**: Injected `Surface Salinity` and `Surface Current Velocity` arrays into `features.py` to seamlessly proxy Sea Surface Height anomalous kinetics directly from local constraints.
- `api.py`: FastAPI application wrapping `get_mld_estimate` for quick HTTP querying.
- `mcp_server.py`: Model Context Protocol (MCP) server implementation wrapping our MLD algorithm for seamless AI agent access.
- `mld_pipeline.py`: Intermediate Logic & Blender layer that merges RTOFS Model output with Aquaview Observation Profiles through Inverse Distance Weighting.
- `mld-dashboard/`: Complete Phase 4 Frontend Visualizer built dynamically with React, Vite, and Leaflet mapping for clickable, real-time map queries.
- `CHANGELOG.md`: Continuous change-tracking document.

### Changed
- `data_builder.py`: Complete rewrite to iterate over a multi-day RTOFS snapshot directory (`/data/suramya/rtofs_snapshots/`), matching each day's model grid to a ±12hr Aquaview observation window. Outputs `rtofs_date`, `collection_id`, and `institution` columns for full provenance tracking.
- `aquaview_obs.py`: Generalized `extract_ioos_profiles` → `extract_erddap_profiles` to support WOD, GCOOS_HIST, NDBC, and IOOS collections uniformly. Added `collection` and `institution` fields to `ObservationProfile` dataclass.
- `train_ml.py`: Replaced random `train_test_split` with `GroupShuffleSplit` across `platform_id` to strictly prevent temporal and spatial data leakage between training and validation deployment regimes.
- `mld_core.py`: Updated `compute_mld_temp_threshold` calculation to utilize absolute temperature difference `abs(temp - t_ref) >= 0.2` rather than strict `temp <= target`, properly catching temperature inversions.

### Data
- Downloaded 7-day RTOFS 3D snapshot series (March 30 – April 5, 2026) from `s3://noaa-nws-rtofs-pds/` to `/data/suramya/rtofs_snapshots/` (~1.8GB, US East region, f006 6-hourly nowcast).

### Tested
- Initialized local test file `test_integration.py` successfully producing an MLD output (`16.96m`) with robust model fallbacks operating reliably over IOOS data boundaries.
