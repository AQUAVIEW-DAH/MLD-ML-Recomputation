# Profile Method Fit Audit

**Date:** 2026-04-07

This report audits profile eligibility under multiple MLD label definitions. It is an inventory report, not a production model-training result.

## Method Notes

- `temp_mld_ref10` matches the current standard 10m, 0.2 C temperature-threshold label.
- `density_mld_ref10` uses a standard 10m, 0.03 kg/m^3 density-threshold label and requires salinity.
- `*_shallowest_ref` columns are exploratory relaxed labels using the shallowest valid sample as the reference; they are not directly comparable to the current 10m label.
- Density is computed with an EOS-80 surface-density approximation for audit purposes; production density MLD should use TEOS-10/GSW if available.

## Overall Counts

- Profiles audited: 1636
- Providers: {'NOAA_NCEI_WOD_CACHE': 1565, 'ARGO_GDAC_CACHE': 71}
- temp_profile_basic: 1470
- temp_mld_ref10: 1400
- temp_mld_ref10_under100m: 1393
- temp_mld_shallowest_ref: 1391
- density_profile_basic: 588
- density_mld_ref10: 550
- density_mld_ref10_under100m: 550
- density_mld_shallowest_ref: 567

## Source Summary

| provider | source | profiles | platforms | dates | median_temp_levels | median_density_levels | max_depth_median | reaches_10m | brackets_10m_temp | brackets_10m_density | temp_profile_basic | temp_mld_ref10 | temp_mld_ref10_under100m | temp_mld_shallowest_ref | density_profile_basic | density_mld_ref10 | density_mld_ref10_under100m | density_mld_shallowest_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ARGO_GDAC_CACHE | ARGO_GDAC | 71 | 5 | 39 | 518.0 | 518.0 | 1026.08 | 71 | 71 | 71 | 71 | 58 | 58 | 59 | 71 | 64 | 64 | 64 |
| NOAA_NCEI_WOD_CACHE | WOD_APB_2023 | 166 | 1 | 50 | 16.0 | 0.0 | 33.0 | 166 | 166 | 64 | 166 | 164 | 164 | 165 | 64 | 64 | 64 | 64 |
| NOAA_NCEI_WOD_CACHE | WOD_GLD_2023 | 1208 | 2 | 26 | 31.0 | 0.0 | 41.943 | 1206 | 988 | 432 | 1042 | 1014 | 1014 | 994 | 453 | 422 | 422 | 439 |
| NOAA_NCEI_WOD_CACHE | WOD_XBT_2023 | 109 | 7 | 19 | 599.0 | 0.0 | 510.0 | 109 | 109 | 0 | 109 | 97 | 94 | 102 | 0 | 0 | 0 | 0 |
| NOAA_NCEI_WOD_CACHE | WOD_XBT_2024 | 82 | 4 | 10 | 1448.0 | 0.0 | 921.6500000000001 | 82 | 82 | 0 | 82 | 67 | 63 | 71 | 0 | 0 | 0 | 0 |

Detailed CSV: `/home/suramya/MLD-ML-Recomputation/ML_baseline/profile_method_fit_audit.csv`
