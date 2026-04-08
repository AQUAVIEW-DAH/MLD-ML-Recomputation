# Balanced Same-Day RTOFS Dataset Audit

## Purpose
Build source-balanced variants from completed WOD-XBT, Argo GDAC, and ERDDAP glider same-day RTOFS datasets. These variants keep all WOD-XBT and Argo rows, then cap repeated ERDDAP glider observations within platform/date/0.25-degree cells.

## Dataset Variants

| Variant | Rows | Source Families | Platforms | Dates | 0.25° Cells | 0.5° Cells | 1.0° Cells |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| `erddap_cell025_cap1` | 1158 | {'ARGO_GDAC': 982, 'ERDDAP_GLIDER': 93, 'WOD': 83} | 60 | 92 | 346 | 192 | 90 |
| `erddap_cell025_cap2` | 1243 | {'ARGO_GDAC': 982, 'ERDDAP_GLIDER': 178, 'WOD': 83} | 60 | 92 | 346 | 192 | 90 |
| `erddap_cell025_cap3` | 1327 | {'ARGO_GDAC': 982, 'ERDDAP_GLIDER': 262, 'WOD': 83} | 60 | 92 | 346 | 192 | 90 |

## Variant Details

## Benchmark Results

Benchmarks use the same repeated grouped validation path as the other same-day RTOFS prototypes.

| Dataset | Rows | ERDDAP Rows | Best Model | Mean MAE | Mean R² | Interpretation |
| :--- | ---: | ---: | :--- | ---: | ---: | :--- |
| WOD-XBT + Argo baseline | 1,065 | 0 | LinearRegression | 8.509m | 0.076 | Best positive-R² same-day prototype before ERDDAP balancing. |
| All-source uncapped | 3,780 | 2,715 | LinearRegression | 5.186m | -0.050 | More rows but ERDDAP clustering pulls grouped R² negative. |
| `erddap_cell025_cap1` | 1,158 | 93 | LinearRegression | 7.827m | 0.022 | Only balanced ERDDAP variant with positive mean R², but still below Argo+WOD. |
| `erddap_cell025_cap2` | 1,243 | 178 | LinearRegression | 7.715m | -0.017 | Slightly lower MAE than cap1, but grouped R² turns negative. |
| `erddap_cell025_cap3` | 1,327 | 262 | LinearRegression | 7.647m | -0.050 | More glider rows reduce MAE but match uncapped all-source R² direction. |

Current read: ERDDAP glider rows are useful as a sidecar diagnostic and may help if used very lightly, but this first balancing pass does not beat the Argo+WOD same-day baseline under grouped validation.

### erddap_cell025_cap1
- Path: `ML_baseline/training_data_balanced_rtofs_2024_2025_erddap_cell025_cap1.csv`
- Description: All WOD+Argo rows plus at most 1 ERDDAP row per platform/date/0.25-degree cell.
- Top platforms: {4903553: 54, 4903552: 54, 4903550: 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 4903556: 50, 4903545: 44, 4903557: 44, 4903232: 40}
- Observed MLD range: 10.135m to 93.460m

### erddap_cell025_cap2
- Path: `ML_baseline/training_data_balanced_rtofs_2024_2025_erddap_cell025_cap2.csv`
- Description: All WOD+Argo rows plus at most 2 ERDDAP rows per platform/date/0.25-degree cell.
- Top platforms: {4903553: 54, 4903552: 54, 4903550: 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 4903556: 50, 4903545: 44, 4903557: 44, 4903232: 40}
- Observed MLD range: 10.076m to 93.460m

### erddap_cell025_cap3
- Path: `ML_baseline/training_data_balanced_rtofs_2024_2025_erddap_cell025_cap3.csv`
- Description: All WOD+Argo rows plus at most 3 ERDDAP rows per platform/date/0.25-degree cell.
- Top platforms: {4903553: 54, 4903552: 54, 4903550: 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 4903556: 50, 'sedna-20241001T0000': 49, 'mote-dora-20240307T0000': 45, 4903545: 44}
- Observed MLD range: 10.021m to 93.460m

## Interpretation
- These datasets are not production model artifacts. They are controlled coverage experiments for grouped validation.
- Compare benchmark results against the all-source and Argo+WOD baselines before deciding whether ERDDAP should enter the main candidate mix.
- Based on this run, prefer Argo+WOD as the primary same-day candidate and keep ERDDAP as a separate diagnostic until a validation strategy better handles dense glider deployments.
