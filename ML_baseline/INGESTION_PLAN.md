# Mission Plan: High-Fidelity In-Situ Data Ingestion

**Status:** Initializing Phase 5 (Direct Source)  
**Objective:** Replace the unreliable Aquaview index/proxy with a robust, direct-access pipeline that ensures 1,000+ depth profiles for the Gulf of Mexico (GoM).

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
*   **Mechanism:** Ifremer/NCEI Mirror scraping of AOML-deployed floats.
*   **Status:** Prototyped successfully; next step is automated float-ID extraction for GoM bounds.

### C. Aquaview (Metadata & Validation)
*   **Role:** Secondary validation and real-time SST station discovery.
*   **Mechanism:** Python `requests.Session` with exponential backoff for SECOORA/IOOS metadata.

---

## 2. Ingestion Pipeline Workflow

The pipeline is formalized in `ML_baseline/data_builder.py` (v3+). It extracts high-res WOD profiles, computes observed MLD, and matches them to the nearest available RTOFS snapshot for feature learning.

---

## 3. Implementation Milestones

### Phase 5.1: WOD Integration (Status: ✅ Complete)
*   [x] Research S3 bucket naming conventions.
*   [x] Implement `wod_source.py` ragged array parsing logic.
*   [x] Update `data_builder.py` to bridge WOD obs with RTOFS snapshots.
*   [x] Verify GoM yield (current: **1,233 rows** in first run).

### Phase 5.2: Argo GDAC Expansion (Status: 🕒 Pending)
*   [ ] Build an automated Ifremer index scraper to find AOML floats in GoM bbox.
*   [ ] Add `ArgoProfile` extraction to `wod_source.py`.

### Phase 5.3: Automated Benchmarking (Status: 🚀 In Progress)
*   [x] Refactor `benchmark_models.py` to handle large multi-source datasets.
*   [ ] Re-run full 4-model leaderboard on 1,000+ data points.
*   [ ] Generate production `model.pkl` with non-negative R² validation.
