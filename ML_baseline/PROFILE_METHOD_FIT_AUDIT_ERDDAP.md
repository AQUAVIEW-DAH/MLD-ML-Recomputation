# Profile Method Fit Audit

**Date:** 2026-04-07

This report audits profile eligibility under multiple MLD label definitions. It is an inventory report, not a production model-training result.

## Method Notes

- `temp_mld_ref10` matches the current standard 10m, 0.2 C temperature-threshold label.
- `density_mld_ref10` uses a standard 10m, 0.03 kg/m^3 density-threshold label and requires salinity.
- `*_shallowest_ref` columns are exploratory relaxed labels using the shallowest valid sample as the reference; they are not directly comparable to the current 10m label.
- Density is computed with an EOS-80 surface-density approximation for audit purposes; production density MLD should use TEOS-10/GSW if available.

## Overall Counts

- Profiles audited: 854
- Providers: {'ERDDAP_GLIDER_FETCH': 854}
- temp_profile_basic: 850
- temp_mld_ref10: 116
- temp_mld_ref10_under100m: 116
- temp_mld_shallowest_ref: 692
- density_profile_basic: 850
- density_mld_ref10: 176
- density_mld_ref10_under100m: 176
- density_mld_shallowest_ref: 730

## Source Summary

| provider | source | profiles | platforms | dates | median_temp_levels | median_density_levels | max_depth_median | reaches_10m | brackets_10m_temp | brackets_10m_density | temp_profile_basic | temp_mld_ref10 | temp_mld_ref10_under100m | temp_mld_shallowest_ref | density_profile_basic | density_mld_ref10 | density_mld_ref10_under100m | density_mld_shallowest_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ERDDAP_GLIDER_FETCH | ERDDAP_GLIDER_ioos-gliderdac-Murphy-20150809T1355 | 189 | 1 | 11 | 196.0 | 196.0 | 306.56 | 189 | 51 | 51 | 189 | 51 | 51 | 185 | 189 | 51 | 51 | 188 |
| ERDDAP_GLIDER_FETCH | ERDDAP_GLIDER_ioos-gliderdac-Murphy-20170426T1610 | 334 | 1 | 12 | 145.5 | 145.5 | 409.9085 | 334 | 0 | 0 | 334 | 0 | 0 | 332 | 334 | 0 | 0 | 332 |
| ERDDAP_GLIDER_FETCH | ERDDAP_GLIDER_ioos-gliderdac-murphy-20160810T2233 | 89 | 1 | 8 | 205.0 | 205.0 | 403.343 | 89 | 0 | 0 | 89 | 0 | 0 | 88 | 89 | 0 | 0 | 89 |
| ERDDAP_GLIDER_FETCH | ERDDAP_GLIDER_ioos-gliderdac-usf-bass-20191022T1200 | 242 | 1 | 2 | 23.0 | 23.0 | 31.577 | 240 | 238 | 238 | 238 | 65 | 65 | 87 | 238 | 125 | 125 | 121 |

Detailed CSV: `ML_baseline/profile_method_fit_audit_erddap.csv`
