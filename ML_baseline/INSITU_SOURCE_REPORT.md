# In-Situ Observation Source Report

**Date:** 2026-04-06  
**Project:** MLD ML recomputation pipeline  
**Region of interest:** Gulf of Mexico / Gulf of America (`[-98, 18, -80, 31]`)  
**Current training file:** `ML_baseline/training_data.csv`

## Executive Summary

The current ML training dataset is not a complete inventory of all possible in-situ sources. It is the subset we have already implemented and verified end-to-end: WOD glider (`gld`), WOD XBT (`xbt`), WOD autonomous pinniped/animal-borne profiler (`apb`), a limited direct ERDDAP glider smoke-test source, and a diversified direct Argo GDAC smoke-test source, QC-filtered to 1,233 rows.

Provider documentation confirms that more in-situ profile sources exist, especially WOD profiling floats (`pfl`), WOD CTD (`ctd`) across a broader year range, Argo GDAC profile NetCDF files, IOOS Glider DAC, SECOORA glider ERDDAP, and OSMC profiler data. However, not every in-situ source is useful for MLD labels. For our target, a source must provide latitude, longitude, time, a vertical temperature/depth profile, enough levels around and below 10m, and platform metadata for grouped validation.

The biggest gap in the current dataset is not general in-situ availability; it is discovery and parsing of additional usable vertical-profile feeds. Buoys and surface stations are valuable for SST validation, but most do not provide full vertical temperature profiles for MLD training.

Direct-source audits now confirm three useful paths beyond the original XBT/glider WOD setup: WOD APB is already ingested, ERDDAP glider servers expose many profile-candidate datasets, and Argo GDAC's global profile index contains thousands of GoM profile-file entries for 2023-2024. The first limited ERDDAP ingestion run added 51 final Murphy glider rows, and a diversified Argo GDAC smoke test added 32 final profile-float rows. These are valid in-situ label sources, but the current builder still uses a short 2026 RTOFS snapshot cache, so the resulting ML table is temporally decoupled from the observation dates.

The next modeling priority is therefore not just more in-situ rows. It is a time-coincident RTOFS audit: determine whether 2023-2024 or another high-overlap in-situ window can be paired to historical Global RTOFS fields at the same valid time. Until that is done, the current `training_data.csv` should be treated as a source-ingestion and feature-extraction smoke test rather than a production-ready correction-training set.

## 2026-04-07 Update: Same-Day RTOFS Source Expansion

The 2024/2025 same-day Global RTOFS path has now moved beyond the 35-row smoke test.

| Source family | Audit result | Same-day RTOFS prototype | Coverage | Benchmark signal |
|---|---:|---:|---|---|
| WOD XBT 2024/2025 | 138 GoM XBT profiles; 106 valid MLD<=100m labels | 83 rows | 6 platforms, 14 half-degree cells | RandomForest MAE 9.305m, mean R² -0.244 |
| Argo GDAC 2024/2025 | 5,371 profile files; 10,165 usable 10m/profile-QC records; 9,177 valid MLD<=100m labels; 8,894 same-day RTOFS eligible | 982 rows from a bounded top-40-date RTOFS feature pass | 42 platforms, 172 half-degree cells | LinearRegression MAE 8.508m, mean R² 0.043 |
| Combined WOD-XBT + Argo | WOD-XBT plus Argo top-40-date subset | 1,065 rows | 48 platforms, 55 dates | LinearRegression MAE 8.509m, mean R² 0.076 |
| ERDDAP gliders | 108 audited candidate datasets selected by the tmux job | Running | TBD | TBD |

The Argo result materially changes the Gulf-only viability picture. The bottleneck is no longer "only ~90 clean same-day rows" once direct Argo GDAC is scaled. However, the current best same-day RTOFS benchmark still has low positive R² and is Argo-dominated. It should be treated as the best prototype so far, not as production model-acceptance evidence.

Active ERDDAP glider run:

- `tmux` session: `mld_erddap_glider`
- Log path: `ML_baseline/erddap_glider_rtofs_2024_2025_tmux.log`
- Builder: `ML_baseline/build_erddap_glider_rtofs_2024_2025.py`
- Command: `--max-datasets 0 --max-rtofs-dates 40`
- Scope: 2024-01-01 through 2025-12-31, GoM bbox, top 40 RTOFS-eligible dates for feature extraction.
- Live progress when this report was updated: 18,485 ERDDAP glider profiles extracted after profile/10m QC; 4,377 profiles selected for the bounded top-40-date RTOFS feature pass; feature extraction had reached at least date 19/40.

## Current Dataset Snapshot

| Category | Current Count | Notes |
|---|---:|---|
| Total QC-filtered rows | 1,233 | `training_data.csv` after dropping observed MLD > 100m outliers |
| WOD glider (`gld`) | 963 | Dominated by MOTE-DORA and US055862 |
| WOD XBT (`xbt`) | 95 | Ship/aircraft transects after QC outlier removal |
| WOD APB (`apb`) | 92 | New direct WOD source from 2023 autonomous pinniped profiles |
| ERDDAP glider (`erddap_gld`) | 51 | Limited two-dataset smoke test retained one Murphy deployment |
| Argo / profiling float rows | 32 | Diversified direct Argo GDAC smoke test across 5 floats |
| Unique platforms/cruises | 16 | Still too few and imbalanced for strong grouped generalization |
| CTD rows | 0 | Parser supports WOD `ctd`, but data builder does not enable it yet |
| Buoy/NDBC rows | 0 | Not currently used for MLD-label training |
| Surface station rows | 0 | Aquaview/SECOORA kept secondary for validation, not MLD labels |

## Temporal Matching Caveat

The current Phase 5 builder matches historical direct-source observations to the nearest locally available RTOFS snapshot, but the local snapshot cache is a short 2026 window and most current in-situ profiles are from 2023-2024. This mismatch means `target_delta_mld = observed_mld - model_mld` is not yet a same-time RTOFS residual. It is useful for testing source ingestion, feature extraction, and validation plumbing, but it is not a best-case correction model target.

For the next prototype, prefer moving RTOFS backward to match the in-situ observation dates. The target audit should answer:

- How many current direct-source profiles can be paired with same-day historical Global RTOFS fields?
- How much yield changes under +/-12h and +/-24h tolerances?
- Which product should define the feature state: analysis/nowcast, a specific forecast lead, or both as separate experiments?
- Can `rtofs_valid_time`, `obs_model_time_delta_hours`, `rtofs_source`, and `forecast_lead_hours` be recorded for every row?
- Which in-situ sources are near-real-time enough for future operational use, and what is their typical publication/QC lag?

If historical RTOFS access for the best in-situ window is incomplete, keep the source-ingestion dataset separate and either start a forward-rolling collector or use a consistent reanalysis/hindcast product as a pretraining experiment. Do not collapse temporally decoupled and time-coincident benchmarks into a single model-acceptance result.

## Provider and Source Comparison

| Provider / Source | Provider-Documented Availability | MLD Label Suitability | Current Pipeline Status | Evidence / Notes | Next Action |
|---|---|---|---|---|---|
| NOAA/NCEI WOD | WOD is a uniformly formatted, quality-controlled public ocean profile database spanning historical to contemporary Argo-era observations. It supports search by date, geography, probe type, and measured variables. | High, when profiles include temperature vs depth and pass QC. | Active for `xbt`, `gld`, and `apb`; not active for `ctd`, `pfl`, `mrb`, or `drb`. | WOD source: <https://www.ncei.noaa.gov/products/world-ocean-database> | Expand WOD instruments and years in a controlled audit before adding to production CSV. |
| WOD XBT (`xbt`) | WOD dataset code table lists XBT as expendable bathythermograph data. Temperature is available for XBT. | High vertical resolution, but needs outlier/QC filtering. | Active. 95 rows after QC. | WOD dataset codes: <https://www.ncei.noaa.gov/access/world-ocean-database/CODES/wod-datasets.html>; WOD variables: <https://www.ncei.noaa.gov/access/world-ocean-database/CODES/depth-dependent-variables.html> | Keep active; add stronger QC around near-isothermal or suspicious deep-profile behavior. |
| WOD Glider (`gld`) | WOD dataset code table lists GLD as glider data; temperature and salinity are available for GLD. | High. Good for MLD if profiles reach sufficient depth. | Active. 963 rows after QC. | Same WOD code tables as above. | Keep active; add more glider platforms/years to reduce MOTE-DORA dominance. |
| WOD CTD (`ctd`) | WOD dataset code table lists CTD as high-resolution CTD/XCTD data; temperature/salinity are available. | High when spatial coverage exists. | Supported by `wod_source.py`, not enabled in `data_builder.py`. Earlier local audit found low 2023/2024 GoM yield. | Same WOD code tables as above. | Run a wider-year CTD audit, not just 2023/2024. |
| WOD Profiling Float (`pfl`) | WOD dataset code table lists PFL as profiling float data; temperature/salinity are available. | High, if profiles are in/near GoM and QC flags are usable. | Supported by `wod_source.py`, not enabled in `data_builder.py`. | Same WOD code tables as above. | Audit WOD `pfl` by year with GoM bbox; compare to direct Argo GDAC. |
| WOD Moored Buoy (`mrb`) / Drifting Buoy (`drb`) | WOD includes moored and drifting buoy datasets, and WOD variables table lists temperature for MRB/DRB. | Mixed. Could help if vertical depth samples exist; many buoy records may be surface or sparse. | Not currently implemented. | WOD dataset code table lists MRB/DRB; WOD variables table lists temperature for them. | Probe WOD MRB/DRB for GoM profiles with >=5 depth levels and max depth >=15m. |
| WOD APB (`apb`) | WOD dataset code table lists APB as autonomous pinniped/animal-borne profiler data; temperature is available in WOD depth-dependent variables. | Moderate to high when profiles are inside GoM and pass QC. | Active. 2023 APB added 92 final training rows; 2024 APB had 0 GoM profiles in this audit. | `source_audit_counts_small.csv`; WOD code tables above. | Keep active, but watch grouped validation because APB residuals are systematically negative in the current split. |
| Argo GDAC direct | Argo GDACs provide complete Argo profile, trajectory, metadata, and technical data in NetCDF, with index files and tools for location/time searches. | High. Argo profile files contain PRES/TEMP/PSAL and QC fields. | Implemented as an opt-in smoke-test source; current diversified run retained 32 rows from 5 floats. Aquaview GADR path was misleading for GoM. | Argo GDAC docs: <https://argo.ucsd.edu/data/data-from-gdacs/>; profile docs: <https://argo.ucsd.edu/data/how-to-use-argo-files/> | Scale only after time-coincident RTOFS matching is solved or separated from source-ingestion smoke tests. |
| OSMC profilers | OSMC provides global in-situ observing-system monitoring and an ERDDAP profiler table with profile coordinates, depth, parameter name, and observation values. | Potentially high for profiler discovery, but may require reshaping from observation rows into profiles. | Not implemented. | OSMC: <https://www.osmc.noaa.gov/>; OSMC profiler ERDDAP example: <https://osmc.noaa.gov/erddap/tabledap/OSMC_PROFILERS> | Test as a discovery and/or lightweight profile feed; verify if it has enough levels for MLD. |
| IOOS Glider DAC | IOOS describes a Glider DAC for centralized glider data distribution, visualization, web services, GTS, and NCEI archive. | High. Glider ERDDAP datasets expose depth, temperature, lat/lon, time, and QC flags. | Discovery implemented in `source_audit.py`; 73 profile candidates found in a first-page audit. Direct parser is implemented, but the current smoke test used SECOORA Murphy deployments first. | IOOS access: <https://ioos.noaa.gov/data/access-ioos-data/>; audit CSV: `source_audit_erddap_ioos_gliders.csv` | Run limited IOOS Glider DAC ingestion next and compare retained profiles/platforms. |
| SECOORA glider ERDDAP | Search results show SECOORA glider datasets with Gulf/Gulf Stream tracks, depth, temperature, salinity, and QARTOD fields. | High for glider profile datasets; surface station datasets remain validation-only. | Discovery implemented in `source_audit.py`; 35 profile candidates found in a first-page audit. Direct parser smoke test added 51 final rows from `ioos-gliderdac-Murphy-20150809T1355`; `ioos-gliderdac-Murphy-20170426T1610` fetched 334 candidate profiles but did not survive downstream matching in this limited run. | SECOORA glider example: <https://erddap.secoora.org/erddap/tabledap/ioos-gliderdac-Murphy-20170426T1610.html>; audit CSV: `source_audit_erddap_secoora.csv` | Diagnose candidate-to-final-row attrition, then scale curated deployments incrementally. |
| GCOOS ERDDAP / regional portals | GCOOS/ERDDAP portals provide regional in-situ and metocean data, but dataset-by-dataset variable/depth checks are required. | Mixed. Some data are surface-only; glider/profile datasets are useful if present. | Not implemented beyond previous Aquaview/SECOORA attempts. | GCOOS ERDDAP endpoint: <https://erddap.gcoos.org/erddap/> | Search for GoM datasets with `cdm_data_type=Profile` or variables `depth` + `temperature`. |
| NDBC standard buoys | NDBC active station metadata includes indicators for meteorology, single-point/profile currents, water quality, and DART. | Usually low for MLD labels because water temperature is often surface or sparse, and current profiles are not temperature profiles. | Not included. | NDBC FAQ: <https://www.ndbc.noaa.gov/faq/activestations.shtml> | Use for SST/surface validation unless a station has actual multi-depth temperature. |
| NDBC TAO / tropical moorings | TAO moored buoys collect surface meteorology, near-surface water temperature, subsurface temperature/salinity at depths, and select current profiles. | Potentially high in tropical Pacific, but not GoM-focused. | Not included. | NDBC TAO: <https://tao.ndbc.noaa.gov/index.shtml> | Not a priority for GoM unless widening domain or using generic ocean physics. |
| NDBC OceanSITES | OceanSITES examples provide time-series/profile temperature/salinity from moored reference stations. | Potentially high, but locations are fixed and often outside GoM. | Not included. | NDBC OceanSITES example: <https://dods.ndbc.noaa.gov/thredds/dodsC/data/oceansites/deployment_data/NTAS/OS_NTAS_2016_D_TS.nc.html> | Evaluate only if target domain expands beyond GoM or a GoM OceanSITES station exists. |
| Surface-only station networks | Includes many coastal stations from IOOS/GCOOS/SECOORA/NDBC/CO-OPS style feeds. | Low for direct MLD labels; useful for SST validation and model sanity checks. | Not in current training CSV. | NDBC and regional ERDDAP portals expose many time-series station feeds. | Keep as secondary validation, not target training data. |
| Satellite / HF radar / gridded products | Provide SST/current fields or surface currents; not in-situ vertical profiles. | Not suitable for observed MLD labels. | Not in current training CSV. | IOOS HF radar and model/data product docs. | Use as optional feature/validation context only. |

## Key Findings from Additional Web Search

1. **Direct glider sources are stronger than our current pipeline uses.** IOOS Glider DAC and SECOORA glider ERDDAP examples expose depth, temperature, profile time, profile lat/lon, salinity, and QC fields. These are highly relevant for MLD labels and may add platform diversity beyond the two WOD glider platforms currently present.

2. **Argo should be added through GDAC/index discovery, not Aquaview metadata.** Argo docs explicitly point to GDAC profile files and index files for region/time searches. Our prior Aquaview GADR issue was an index/metadata mismatch, not evidence that Argo profile data are unavailable in general.

3. **Buoys are not all equivalent.** NDBC standard station and surface/water-quality feeds are often insufficient for MLD because they lack vertical temperature profiles. TAO and OceanSITES can provide subsurface time-series/profile data, but these are not necessarily GoM-local.

4. **WOD remains the broadest single historical archive.** The WOD tables confirm the relevant dataset families (`XBT`, `GLD`, `CTD`, `PFL`, `MRB`, `DRB`, `APB`) and that temperature is stored across these families. The practical next task is coverage/QC auditing by instrument/year/region, not source discovery from scratch.

5. **WOD APB is now confirmed useful for GoM.** A direct WOD audit found 166 usable 2023 GoM APB profiles before model-feature matching. The full builder retained 92 QC-filtered APB rows after observed-MLD and RTOFS feature checks. CTD, MRB, and DRB had 0 usable GoM rows for 2023/2024 in the same audit.

6. **ERDDAP glider discovery is concrete, not speculative.** First-pass metadata audits found 35 SECOORA and 73 IOOS Glider DAC profile candidates. A sample SECOORA DEEPEND query returned CSV rows with `time`, `latitude`, `longitude`, `depth`, `temperature`, and `profile_id`, which is enough to build MLD profiles after grouping by deployment/profile.

7. **Limited ERDDAP ingestion is now implemented.** A two-dataset smoke test extracted 523 candidate ERDDAP glider profiles and retained 51 final training rows after MLD/QC/RTOFS feature checks. The one-shot grouped XGBoost benchmark after this run was MAE 9.897m and R² 0.466, but the held-out fold had only 35 rows and did not hold out the new ERDDAP platform, so repeated/grouped validation is still required before treating this as a generalization gain.

8. **Argo GDAC index discovery found substantial GoM coverage.** Parsing `ar_index_global_prof.txt` for 2023-2024 inside the GoM bbox returned 5,393 profile-file entries, mostly from the AOML DAC. A 25-file diversified smoke test parsed 45 usable profile records and retained 32 final rows after observed-MLD and RTOFS feature checks.

## Recommended Next Audit Order

| Priority | Candidate Source | Reason | Proposed Test |
|---:|---|---|---|
| 1 | IOOS Glider DAC / SECOORA glider ERDDAP | Confirmed candidate datasets with depth+temperature+profile_id; likely adds platform diversity. | Implement tabledap parser that groups rows by `dataset_id/profile_id`, computes observed MLD, and writes source-tagged rows. |
| 2 | Historical/time-coincident RTOFS | Current 2026 local snapshots are temporally decoupled from the strongest 2023-2024 in-situ rows; NOAA public RTOFS S3 current-pattern keys only cover the sparse 2024 subset in this table. | Find a 2023 historical RTOFS archive path or choose a forward-collection/reanalysis fallback before model acceptance. |
| 3 | Argo GDAC direct | 5,393 GoM profile-file entries found in the 2023-2024 global profile index; best authoritative route for profiling floats and QC fields. | Scale beyond the 25-file smoke test once time-coincident model matching is available. |
| 4 | WOD `pfl` | Easier than direct GDAC if WOD yearly files have GoM floats. | Run WOD `pfl` bbox audit by year, but be careful about large file sizes. |
| 5 | WOD `ctd` across broader years | High-quality profiles, but 2023/2024 GoM coverage looked sparse. | Run count-only scans across 2018-2024 if file sizes are manageable. |
| 6 | WOD `mrb` / `drb` | Could provide buoy depth samples but 2023/2024 GoM audit yielded 0 usable rows. | Revisit only for broader year ranges or wider domains. |
| 7 | NDBC/OceanSITES/TAO | Useful if domain expands, but not immediately GoM-focused. | Search for GoM-local timeSeriesProfile temperature stations. |

## Working Conclusion

Our current model weakness is plausibly due to data imbalance, not just model choice. The current dataset is dominated by one glider platform and now includes a useful APB block, but grouped holdout still has strong target-distribution shift. Before major architecture changes, the best simple-model path is to add more verified depth-profile sources while preserving grouped validation:

- direct IOOS/SECOORA glider profiles,
- direct Argo GDAC or WOD `pfl`,
- WOD CTD over a wider year range,
- carefully audited buoy/mooring profiles only if they include vertical temperature profiles.
