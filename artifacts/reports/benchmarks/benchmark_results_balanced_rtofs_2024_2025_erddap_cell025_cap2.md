# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)

**Timestamp:** 2026-04-07 22:28
**Data path:** `ML_baseline/training_data_balanced_rtofs_2024_2025_erddap_cell025_cap2.csv`
**Dataset:** 1243 profiles from direct sources (WOD_XBT_2024, WOD_XBT_2025, ARGO_GDAC, ERDDAP_GLIDER_Nori-20240816T0000, ERDDAP_GLIDER_Nori-20241008T0000, ERDDAP_GLIDER_Nori-20241101T0000, ERDDAP_GLIDER_mote-SeaXplorer-20240318T0000, ERDDAP_GLIDER_mote-dora-20240307T0000, ERDDAP_GLIDER_mote-dora-20240716T0000, ERDDAP_GLIDER_mote-dora-20240819T0000, ERDDAP_GLIDER_mote-holly-20250219T0000, ERDDAP_GLIDER_ori-20240731T0000, ERDDAP_GLIDER_sedna-20241001T0000, ERDDAP_GLIDER_usf-sam-20240216T0000, ERDDAP_GLIDER_usf-stella-20250206T0000)
**Region:** Gulf of Mexico (-98,18,-80,31)
**Validation:** Repeated GroupShuffleSplit by platform/cruise (60 groups, 10 splits, test_size=0.20)

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LinearRegression** | 7.715m | 0.544m | 10.243m | 1.116m | -0.017 | 0.136 | 6.811m-8.555m |
| **RandomForest** | 8.206m | 0.632m | 11.209m | 1.131m | -0.219 | 0.149 | 7.178m-9.438m |
| **HistGradientBoosting** | 8.745m | 0.508m | 11.841m | 0.988m | -0.372 | 0.216 | 7.708m-9.66m |
| **XGBoost** | 8.777m | 0.703m | 11.98m | 1.204m | -0.4 | 0.231 | 7.524m-9.835m |

## Validation Interpretation
- Best repeated grouped MAE: LinearRegression at 7.715m mean MAE with mean R²=-0.017.
- This repeated grouped result is a data-coverage diagnostic, not a production-ready model acceptance result; cross-platform generalization remains unstable.
- Do not freeze or accept a new `model.pkl` from this run.

## Data Summary
- Total profiles: 1243
- Source families: {'ARGO_GDAC': 982, 'ERDDAP_GLIDER': 178, 'WOD': 83}
- Instruments: {'pfl': 982, 'erddap_gld': 178, 'xbt': 83}
- First split train/test: 969/274
- First split held-out platforms: {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903279': 26, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16, 'mote-dora-20240819T0000': 16, '2904010': 14, '4903278': 13, '4903554': 10}
- Test rows per split: min=188, max=321
- Observed MLD range: 10.1m to 93.5m
- Model MLD range: 10.6m to 102.3m

## Split Diagnostics

| Model | Split | Test rows | Test groups | MAE | RMSE | R² | Held-out platforms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| HistGradientBoosting | 1 | 274 | 12 | 8.92m | 11.726m | -0.667 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903279': 26, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16} |
| HistGradientBoosting | 2 | 279 | 12 | 8.702m | 12.083m | -0.418 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 25, '4903468': 24, '4903548': 22} |
| HistGradientBoosting | 3 | 321 | 12 | 7.708m | 10.453m | -0.491 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903232': 40, '4903471': 36, '4903559': 33, 'usf-sam-20240216T0000': 28} |
| HistGradientBoosting | 4 | 231 | 12 | 9.351m | 13.285m | 0.076 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, '4903356': 22} |
| HistGradientBoosting | 5 | 198 | 12 | 8.852m | 11.382m | -0.25 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| HistGradientBoosting | 6 | 281 | 12 | 8.38m | 11.172m | -0.402 | {'4903550': 52, '4903557': 44, 'sedna-20241001T0000': 34, '4903248': 31, '4903353': 28, 'usf-sam-20240216T0000': 28} |
| HistGradientBoosting | 7 | 188 | 12 | 8.766m | 11.89m | -0.146 | {'sedna-20241001T0000': 34, 'usf-sam-20240216T0000': 28, '4903279': 26, '4903563': 25, 'mote-holly-20250219T0000': 25, '4903548': 22} |
| HistGradientBoosting | 8 | 245 | 12 | 8.397m | 10.907m | -0.28 | {'4903556': 50, 'sedna-20241001T0000': 34, '4903559': 33, 'mote-dora-20240307T0000': 30, '4903466': 26, '4903563': 25} |
| HistGradientBoosting | 9 | 262 | 12 | 8.718m | 11.65m | -0.644 | {'4903552': 54, '4903232': 40, '4903240': 34, '4903248': 31, 'mote-holly-20250219T0000': 25, '4903469': 18} |
| HistGradientBoosting | 10 | 279 | 12 | 9.66m | 13.866m | -0.495 | {'4903553': 54, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903468': 24, '4903548': 22} |
| LinearRegression | 1 | 274 | 12 | 7.699m | 10.013m | -0.216 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903279': 26, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16} |
| LinearRegression | 2 | 279 | 12 | 7.248m | 9.746m | 0.078 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 25, '4903468': 24, '4903548': 22} |
| LinearRegression | 3 | 321 | 12 | 6.811m | 9.099m | -0.13 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903232': 40, '4903471': 36, '4903559': 33, 'usf-sam-20240216T0000': 28} |
| LinearRegression | 4 | 231 | 12 | 8.555m | 12.627m | 0.165 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, '4903356': 22} |
| LinearRegression | 5 | 198 | 12 | 7.461m | 9.398m | 0.148 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| LinearRegression | 6 | 281 | 12 | 7.993m | 10.277m | -0.186 | {'4903550': 52, '4903557': 44, 'sedna-20241001T0000': 34, '4903248': 31, '4903353': 28, 'usf-sam-20240216T0000': 28} |
| LinearRegression | 7 | 188 | 12 | 8.072m | 10.353m | 0.131 | {'sedna-20241001T0000': 34, 'usf-sam-20240216T0000': 28, '4903279': 26, '4903563': 25, 'mote-holly-20250219T0000': 25, '4903548': 22} |
| LinearRegression | 8 | 245 | 12 | 7.843m | 9.99m | -0.074 | {'4903556': 50, 'sedna-20241001T0000': 34, '4903559': 33, 'mote-dora-20240307T0000': 30, '4903466': 26, '4903563': 25} |
| LinearRegression | 9 | 262 | 12 | 7.05m | 9.005m | 0.018 | {'4903552': 54, '4903232': 40, '4903240': 34, '4903248': 31, 'mote-holly-20250219T0000': 25, '4903469': 18} |
| LinearRegression | 10 | 279 | 12 | 8.415m | 11.928m | -0.106 | {'4903553': 54, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903468': 24, '4903548': 22} |
| RandomForest | 1 | 274 | 12 | 7.706m | 10.342m | -0.297 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903279': 26, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16} |
| RandomForest | 2 | 279 | 12 | 8.28m | 11.785m | -0.349 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 25, '4903468': 24, '4903548': 22} |
| RandomForest | 3 | 321 | 12 | 7.178m | 10.021m | -0.37 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903232': 40, '4903471': 36, '4903559': 33, 'usf-sam-20240216T0000': 28} |
| RandomForest | 4 | 231 | 12 | 9.438m | 13.429m | 0.056 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, '4903356': 22} |
| RandomForest | 5 | 198 | 12 | 8.629m | 11.123m | -0.193 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| RandomForest | 6 | 281 | 12 | 7.681m | 10.06m | -0.137 | {'4903550': 52, '4903557': 44, 'sedna-20241001T0000': 34, '4903248': 31, '4903353': 28, 'usf-sam-20240216T0000': 28} |
| RandomForest | 7 | 188 | 12 | 8.209m | 10.887m | 0.039 | {'sedna-20241001T0000': 34, 'usf-sam-20240216T0000': 28, '4903279': 26, '4903563': 25, 'mote-holly-20250219T0000': 25, '4903548': 22} |
| RandomForest | 8 | 245 | 12 | 8.333m | 11.112m | -0.328 | {'4903556': 50, 'sedna-20241001T0000': 34, '4903559': 33, 'mote-dora-20240307T0000': 30, '4903466': 26, '4903563': 25} |
| RandomForest | 9 | 262 | 12 | 7.722m | 10.339m | -0.295 | {'4903552': 54, '4903232': 40, '4903240': 34, '4903248': 31, 'mote-holly-20250219T0000': 25, '4903469': 18} |
| RandomForest | 10 | 279 | 12 | 8.882m | 12.991m | -0.312 | {'4903553': 54, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903468': 24, '4903548': 22} |
| XGBoost | 1 | 274 | 12 | 8.699m | 11.58m | -0.626 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903279': 26, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16} |
| XGBoost | 2 | 279 | 12 | 9.448m | 13.703m | -0.824 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 25, '4903468': 24, '4903548': 22} |
| XGBoost | 3 | 321 | 12 | 7.846m | 10.675m | -0.555 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903232': 40, '4903471': 36, '4903559': 33, 'usf-sam-20240216T0000': 28} |
| XGBoost | 4 | 231 | 12 | 9.835m | 13.877m | -0.008 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, '4903356': 22} |
| XGBoost | 5 | 198 | 12 | 8.894m | 12.189m | -0.433 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| XGBoost | 6 | 281 | 12 | 7.524m | 10.152m | -0.157 | {'4903550': 52, '4903557': 44, 'sedna-20241001T0000': 34, '4903248': 31, '4903353': 28, 'usf-sam-20240216T0000': 28} |
| XGBoost | 7 | 188 | 12 | 9.04m | 12.086m | -0.184 | {'sedna-20241001T0000': 34, 'usf-sam-20240216T0000': 28, '4903279': 26, '4903563': 25, 'mote-holly-20250219T0000': 25, '4903548': 22} |
| XGBoost | 8 | 245 | 12 | 9.113m | 11.843m | -0.509 | {'4903556': 50, 'sedna-20241001T0000': 34, '4903559': 33, 'mote-dora-20240307T0000': 30, '4903466': 26, '4903563': 25} |
| XGBoost | 9 | 262 | 12 | 8.086m | 10.7m | -0.387 | {'4903552': 54, '4903232': 40, '4903240': 34, '4903248': 31, 'mote-holly-20250219T0000': 25, '4903469': 18} |
| XGBoost | 10 | 279 | 12 | 9.282m | 12.992m | -0.312 | {'4903553': 54, '4903557': 44, '4903232': 40, 'sedna-20241001T0000': 34, '4903468': 24, '4903548': 22} |
