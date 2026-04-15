# Profile Method Fit Summary

**Date:** 2026-04-07  
**Purpose:** Estimate how many additional in-situ profiles become usable if we relax the current 10m temperature-threshold MLD requirement or switch to a density-threshold method.

## Scope

This audit is exploratory and does not modify `training_data.csv` or `model.pkl`.

Provider inventory included:

- cached WOD provider files in `/data/suramya/wod_cache`,
- cached Argo GDAC NetCDF profile files in `/data/suramya/argo_cache`,
- a limited live ERDDAP glider fetch over 5 candidate datasets from the existing ERDDAP audit CSVs.

Generated artifacts:

- `ML_baseline/profile_method_fit_audit.py`
- `ML_baseline/profile_method_fit_audit.csv`
- `ML_baseline/profile_method_fit_audit_erddap.csv`
- `ML_baseline/profile_method_fit_audit_combined.csv`
- `ML_baseline/profile_method_fit_audit_combined_summary.csv`
- `ML_baseline/PROFILE_METHOD_FIT_AUDIT.md`
- `ML_baseline/PROFILE_METHOD_FIT_AUDIT_ERDDAP.md`

One ERDDAP dataset failed both salinity and temperature queries with HTTP 400 and is excluded from the ERDDAP counts:

`axiom-netcdf-harvest-socan-RB-GOMECC-1184127540-1186098120`

## Method Definitions

| Method | Meaning | Production Readiness |
|---|---|---|
| `temp_mld_ref10` | Current 10m, 0.2 C temperature-threshold MLD | Standard/current target |
| `density_mld_ref10` | 10m, 0.03 kg/m^3 density-threshold MLD | Standard alternative, requires salinity |
| `*_shallowest_ref` | Threshold relative to the shallowest valid profile sample | Exploratory only; not comparable to current target |
| `temp_profile_basic` | Temperature-depth profile with at least 5 levels and max depth >= 15m | Inventory only; not necessarily an MLD label |

Density in this audit used an EOS-80 surface-density approximation because TEOS-10/GSW is not installed in the local environment. If density MLD becomes a production path, install/use GSW and rerun.

## Scientific Reference Point

The current 10m temperature threshold is not arbitrary. The de Boyer Montegut-style threshold method uses the 10m reference to avoid the diurnal mixing layer while retaining longer-term mixed-layer variability, with a common temperature threshold of 0.2 C. Density-threshold methods are also common but need salinity and are usually still based on a near-surface reference such as 10m.

Useful references:

- de Boyer Montegut et al. 2004 reference via DOI: <https://doi.org/10.1029/2004JC002378>
- Ocean Science example summarizing the 10m, 0.2 C threshold and density-threshold comparison: <https://os.copernicus.org/articles/14/503/2018/>
- Holte and Talley 2009 hybrid Argo MLD algorithm: <https://doi.org/10.1175/2009JTECHO543.1>
- UCSD Argo Mixed Layer database: <https://mixedlayer.ucsd.edu/>

## Overall Result

| Eligibility Class | Profiles |
|---|---:|
| Profiles audited | 2,490 |
| Basic temperature-depth profiles | 2,320 |
| Current standard temp 10m MLD labels | 1,516 |
| Density 10m MLD labels | 726 |
| Standard temp-or-density 10m labels | 1,593 |
| Standard temp-or-density 10m labels under 100m | 1,586 |
| Exploratory shallowest-reference labels | 2,145 |

The key result is that density-based 10m MLD only adds 77 standard-label profiles over the current temperature 10m threshold in this explored provider set:

`1,593 temp-or-density standard labels - 1,516 temp-only standard labels = 77 additional standard-label profiles`

Relaxing to a shallowest-reference threshold would add far more:

`2,145 exploratory labels - 1,516 temp-only standard labels = 629 additional profiles`

But that would change the target definition and should not be mixed with the current 10m MLD labels.

## Provider Summary

| Provider | Profiles | Basic Temp Profiles | Temp 10m | Density 10m | Standard Temp-or-Density 10m | Exploratory Shallowest Ref |
|---|---:|---:|---:|---:|---:|---:|
| WOD cached files | 1,565 | 1,399 | 1,342 | 486 | 1,353 | 1,347 |
| Argo GDAC cached files | 71 | 71 | 58 | 64 | 64 | 64 |
| ERDDAP glider limited fetch | 854 | 850 | 116 | 176 | 176 | 734 |

Interpretation:

- WOD does not gain much from density because many useful WOD rows are XBT temperature-only, and WOD glider/APB density-capable rows mostly overlap the temperature 10m labels.
- Argo gains modestly from density, from 58 temp-10m labels to 64 standard temp-or-density labels.
- ERDDAP is the big difference: many fetched glider profiles are profile-shaped and density-capable, but they often do not bracket 10m. Standard density 10m increases labels from 116 to 176, while shallowest-reference labels would increase to 734.

## Source Summary

| Source | Profiles | Temp Basic | Temp 10m | Density 10m | Standard Temp-or-Density 10m | Exploratory Shallowest Ref | Key Caveat |
|---|---:|---:|---:|---:|---:|---:|---|
| WOD_GLD_2023 | 1,208 | 1,042 | 1,014 | 422 | 1,025 | 994 | Dense but dominated by MOTE-DORA and US055862 |
| ERDDAP Murphy 20170426 | 334 | 334 | 0 | 0 | 0 | 332 | Mostly starts below/does not bracket 10m |
| ERDDAP USF Bass 20191022 | 242 | 238 | 65 | 125 | 125 | 121 | Density helps, but shallow max depth median ~31.6m |
| ERDDAP Murphy 20150809 | 189 | 189 | 51 | 51 | 51 | 188 | Current ERDDAP source in `training_data.csv` |
| WOD_APB_2023 | 166 | 166 | 164 | 64 | 164 | 165 | Useful, but one platform class |
| WOD_XBT_2023 | 109 | 109 | 97 | 0 | 97 | 102 | XBT has no salinity, so density cannot help |
| ERDDAP Murphy 20160810 | 89 | 89 | 0 | 0 | 0 | 89 | Mostly starts below/does not bracket 10m |
| WOD_XBT_2024 | 82 | 82 | 67 | 0 | 67 | 71 | RTOFS-compatible subset remains sparse |
| Argo GDAC cached sample | 71 | 71 | 58 | 64 | 64 | 64 | Good salinity/depth, but only cached smoke sample |

## Conclusion

Removing the current 10m temperature-threshold requirement does reveal more profile-shaped data, especially from ERDDAP gliders. However, most of the large gain comes from exploratory shallowest-reference labels, not from a standard alternative MLD method.

Recommended interpretation:

- Keep the 10m threshold label as the production target for now.
- Consider adding a standard density-threshold 10m label as a separate experiment; it adds some profiles, especially for Argo and ERDDAP, but not enough to solve the core data bottleneck by itself.
- Do not mix shallowest-reference labels with 10m labels in the same training target.
- If shallowest-reference labels are explored, treat them as a separate target family and benchmark/report them separately.
- The biggest remaining blocker is still time-coincident and spatially diverse observations, not only the label method.
