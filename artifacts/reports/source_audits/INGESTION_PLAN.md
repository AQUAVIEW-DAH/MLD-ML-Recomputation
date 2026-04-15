# Mission Plan: High-Fidelity In-Situ Data Ingestion

**Status:** Phase 5 direct-source ingestion and validation pivot
**Objective:** Replace the unreliable Aquaview index/proxy with a robust, direct-access pipeline that ensures 1,000+ depth profiles for the Gulf of Mexico (GoM), then pair those profiles to temporally valid model states before accepting any ML correction model.

---

## 1. Multi-Source Architecture

We move from a single-point-of-failure (Aquaview) to a resilient multi-source ingestion layer:

### A. World Ocean Database (WOD) S3 Direct
*   **Role:** Primary training data volume (XBT, Glider, CTD).
*   **Mechanism:** Direct HTTPS fetch from `noaa-wod-pds.s3.amazonaws.com`.
*   **Implementation:** `ML_baseline/wod_source.py`
*   **Yield:** Verified **1,399+ profiles** for GoM (2023-2024).

### B. Argo GDAC Direct
*   **Role:** Recent, high-precision calibration points.
*   **Mechanism:** Ifremer GDAC global profile index discovery of GoM profile NetCDF files, with local caching and profile QC.
*   **Status:** Implemented as an opt-in source via `ML_baseline/argo_gdac_source.py` and `INCLUDE_ARGO_GDAC=1`.

### C. Aquaview (Metadata & Validation)
*   **Role:** Secondary validation and real-time SST station discovery.
*   **Mechanism:** Python `requests.Session` with exponential backoff for SECOORA/IOOS metadata.

---

## 2. Ingestion Pipeline Workflow

The pipeline is formalized in `ML_baseline/data_builder.py` (v3+). It extracts high-res direct-source profiles, computes observed MLD, and currently matches them to the nearest locally available RTOFS snapshot for feature learning.

**Important temporal caveat:** the current local RTOFS snapshot cache is a short 2026 window, while the strongest direct in-situ sources currently come from 2023-2024. This is acceptable as a source-ingestion smoke test, but it is not a best-case ML correction dataset because the feature vector is not paired to the model state valid at the observation time.

The preferred prototype strategy is now to move RTOFS backward to match the in-situ profile dates, not to move/force the in-situ data onto the 2026 RTOFS window. A same-date RTOFS/observation pairing should use a documented tolerance such as same analysis day, +/-12 hours, or +/-24 hours, then benchmark separately from the temporally decoupled smoke-test CSV.

---

## 3. Implementation Milestones

### Phase 5.1: WOD Integration (Status: ✅ Complete)
*   [x] Research S3 bucket naming conventions.
*   [x] Implement `wod_source.py` ragged array parsing logic.
*   [x] Update `data_builder.py` to bridge WOD obs with RTOFS snapshots.
*   [x] Verify GoM yield (current: **1,233 rows** in first run).

### Phase 5.2: Argo GDAC Expansion (Status: ✅ Prototype Complete)
*   [x] Build an automated Ifremer index reader to find Argo profile files in GoM bbox.
*   [x] Add direct Argo profile extraction in `ML_baseline/argo_gdac_source.py`.
*   [x] Add diversified float sampling with `ARGO_MAX_PER_PLATFORM`.
*   [ ] Scale beyond the 25-profile smoke test after temporal RTOFS matching is audited.

### Phase 5.3: Automated Benchmarking (Status: ✅ Repeated Validation Implemented)
*   [x] Refactor `benchmark_models.py` to handle large multi-source datasets.
*   [x] Re-run full 4-model leaderboard on 1,000+ data points.
*   [x] Add repeated grouped validation and split diagnostics.
*   [ ] Generate production `model.pkl` only after temporally matched validation shows stable cross-platform skill.

### Phase 5.4: RTOFS / In-Situ Temporal Matching (Status: 🕒 Next)
*   [ ] Audit official/current historical Global RTOFS access paths for 2023-2024 and/or the best-overlap in-situ profile window.
*   [ ] Count how many current WOD, ERDDAP, and Argo profiles can be paired to same-day or +/-24h RTOFS fields.
*   [ ] Add `rtofs_valid_time`, `obs_model_time_delta_hours`, `rtofs_source`, and, if available, `forecast_lead_hours` to `training_data.csv`.
*   [ ] Keep the temporally decoupled CSV/report as a source-ingestion smoke test, not a production model-training benchmark.
*   [ ] Later, analyze real-time feasibility by source: update latency, QC latency, GDAC/ERDDAP/WOD publication lag, and whether the profile would be available before or after the target RTOFS cycle.
*   [ ] If real-time latency is unclear or source-specific, prepare a short list of questions for domain experts before committing to an operational strategy.
