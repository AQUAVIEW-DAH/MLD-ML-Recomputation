# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)

**Timestamp:** 2026-04-07 22:28
**Data path:** `ML_baseline/training_data_balanced_rtofs_2024_2025_erddap_cell025_cap3.csv`
**Dataset:** 1327 profiles from direct sources (WOD_XBT_2024, WOD_XBT_2025, ARGO_GDAC, ERDDAP_GLIDER_Nori-20240816T0000, ERDDAP_GLIDER_Nori-20241008T0000, ERDDAP_GLIDER_Nori-20241101T0000, ERDDAP_GLIDER_mote-SeaXplorer-20240318T0000, ERDDAP_GLIDER_mote-dora-20240307T0000, ERDDAP_GLIDER_mote-dora-20240716T0000, ERDDAP_GLIDER_mote-dora-20240819T0000, ERDDAP_GLIDER_mote-holly-20250219T0000, ERDDAP_GLIDER_ori-20240731T0000, ERDDAP_GLIDER_sedna-20241001T0000, ERDDAP_GLIDER_usf-sam-20240216T0000, ERDDAP_GLIDER_usf-stella-20250206T0000)
**Region:** Gulf of Mexico (-98,18,-80,31)
**Validation:** Repeated GroupShuffleSplit by platform/cruise (60 groups, 10 splits, test_size=0.20)

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LinearRegression** | 7.647m | 0.614m | 10.187m | 1.108m | -0.05 | 0.155 | 6.497m-8.499m |
| **RandomForest** | 8.098m | 0.643m | 11.048m | 1.122m | -0.232 | 0.141 | 6.975m-9.151m |
| **HistGradientBoosting** | 8.58m | 0.661m | 11.647m | 1.099m | -0.383 | 0.235 | 7.366m-10.105m |
| **XGBoost** | 8.742m | 0.691m | 11.985m | 1.15m | -0.453 | 0.191 | 7.872m-9.861m |

## Validation Interpretation
- Best repeated grouped MAE: LinearRegression at 7.647m mean MAE with mean R²=-0.05.
- This repeated grouped result is a data-coverage diagnostic, not a production-ready model acceptance result; cross-platform generalization remains unstable.
- Do not freeze or accept a new `model.pkl` from this run.

## Data Summary
- Total profiles: 1327
- Source families: {'ARGO_GDAC': 982, 'ERDDAP_GLIDER': 262, 'WOD': 83}
- Instruments: {'pfl': 982, 'erddap_gld': 262, 'xbt': 83}
- First split train/test: 1027/300
- First split held-out platforms: {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903279': 26, 'mote-dora-20240819T0000': 24, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16, '2904010': 14, '4903278': 13, 'Nori-20241008T0000': 12}
- Test rows per split: min=205, max=359
- Observed MLD range: 10.0m to 93.5m
- Model MLD range: 10.6m to 102.3m

## Split Diagnostics

| Model | Split | Test rows | Test groups | MAE | RMSE | R² | Held-out platforms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| HistGradientBoosting | 1 | 300 | 12 | 9.035m | 11.653m | -0.68 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903279': 26, 'mote-dora-20240819T0000': 24} |
| HistGradientBoosting | 2 | 303 | 12 | 8.471m | 12.036m | -0.452 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 37, '4903468': 24, '4903548': 22} |
| HistGradientBoosting | 3 | 359 | 12 | 7.366m | 10.027m | -0.425 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'usf-sam-20240216T0000': 42, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903471': 36} |
| HistGradientBoosting | 4 | 245 | 12 | 8.774m | 12.697m | 0.112 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, 'mote-dora-20240819T0000': 24} |
| HistGradientBoosting | 5 | 205 | 12 | 8.547m | 11.012m | -0.2 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| HistGradientBoosting | 6 | 321 | 12 | 8.155m | 10.981m | -0.438 | {'4903550': 52, 'sedna-20241001T0000': 49, '4903557': 44, 'usf-sam-20240216T0000': 42, '4903248': 31, '4903353': 28} |
| HistGradientBoosting | 7 | 230 | 12 | 8.638m | 11.442m | -0.147 | {'sedna-20241001T0000': 49, 'usf-sam-20240216T0000': 42, 'mote-holly-20250219T0000': 37, '4903279': 26, '4903563': 25, '4903548': 22} |
| HistGradientBoosting | 8 | 281 | 12 | 8.248m | 10.982m | -0.353 | {'4903556': 50, 'sedna-20241001T0000': 49, 'mote-dora-20240307T0000': 45, '4903559': 33, '4903466': 26, '4903563': 25} |
| HistGradientBoosting | 9 | 285 | 12 | 8.457m | 11.389m | -0.589 | {'4903552': 54, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903240': 34, '4903248': 31, 'mote-dora-20240819T0000': 24} |
| HistGradientBoosting | 10 | 308 | 12 | 10.105m | 14.256m | -0.663 | {'4903553': 54, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903468': 24, 'mote-dora-20240819T0000': 24} |
| LinearRegression | 1 | 300 | 12 | 7.96m | 10.28m | -0.308 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903279': 26, 'mote-dora-20240819T0000': 24} |
| LinearRegression | 2 | 303 | 12 | 7.08m | 9.601m | 0.076 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 37, '4903468': 24, '4903548': 22} |
| LinearRegression | 3 | 359 | 12 | 6.497m | 8.824m | -0.104 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'usf-sam-20240216T0000': 42, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903471': 36} |
| LinearRegression | 4 | 245 | 12 | 8.37m | 12.409m | 0.152 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, 'mote-dora-20240819T0000': 24} |
| LinearRegression | 5 | 205 | 12 | 7.378m | 9.34m | 0.137 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| LinearRegression | 6 | 321 | 12 | 7.969m | 10.27m | -0.258 | {'4903550': 52, 'sedna-20241001T0000': 49, '4903557': 44, 'usf-sam-20240216T0000': 42, '4903248': 31, '4903353': 28} |
| LinearRegression | 7 | 230 | 12 | 7.894m | 10.302m | 0.071 | {'sedna-20241001T0000': 49, 'usf-sam-20240216T0000': 42, 'mote-holly-20250219T0000': 37, '4903279': 26, '4903563': 25, '4903548': 22} |
| LinearRegression | 8 | 281 | 12 | 7.873m | 10.009m | -0.124 | {'4903556': 50, 'sedna-20241001T0000': 49, 'mote-dora-20240307T0000': 45, '4903559': 33, '4903466': 26, '4903563': 25} |
| LinearRegression | 9 | 285 | 12 | 6.95m | 8.959m | 0.017 | {'4903552': 54, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903240': 34, '4903248': 31, 'mote-dora-20240819T0000': 24} |
| LinearRegression | 10 | 308 | 12 | 8.499m | 11.877m | -0.154 | {'4903553': 54, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903468': 24, 'mote-dora-20240819T0000': 24} |
| RandomForest | 1 | 300 | 12 | 7.727m | 10.307m | -0.315 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903279': 26, 'mote-dora-20240819T0000': 24} |
| RandomForest | 2 | 303 | 12 | 8.247m | 11.646m | -0.359 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 37, '4903468': 24, '4903548': 22} |
| RandomForest | 3 | 359 | 12 | 6.975m | 9.694m | -0.332 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'usf-sam-20240216T0000': 42, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903471': 36} |
| RandomForest | 4 | 245 | 12 | 9.151m | 13.076m | 0.058 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, 'mote-dora-20240819T0000': 24} |
| RandomForest | 5 | 205 | 12 | 8.601m | 11.166m | -0.234 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| RandomForest | 6 | 321 | 12 | 7.426m | 9.809m | -0.147 | {'4903550': 52, 'sedna-20241001T0000': 49, '4903557': 44, 'usf-sam-20240216T0000': 42, '4903248': 31, '4903353': 28} |
| RandomForest | 7 | 230 | 12 | 8.019m | 10.766m | -0.015 | {'sedna-20241001T0000': 49, 'usf-sam-20240216T0000': 42, 'mote-holly-20250219T0000': 37, '4903279': 26, '4903563': 25, '4903548': 22} |
| RandomForest | 8 | 281 | 12 | 8.207m | 10.864m | -0.324 | {'4903556': 50, 'sedna-20241001T0000': 49, 'mote-dora-20240307T0000': 45, '4903559': 33, '4903466': 26, '4903563': 25} |
| RandomForest | 9 | 285 | 12 | 7.683m | 10.254m | -0.288 | {'4903552': 54, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903240': 34, '4903248': 31, 'mote-dora-20240819T0000': 24} |
| RandomForest | 10 | 308 | 12 | 8.942m | 12.902m | -0.362 | {'4903553': 54, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903468': 24, 'mote-dora-20240819T0000': 24} |
| XGBoost | 1 | 300 | 12 | 8.731m | 11.567m | -0.656 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903279': 26, 'mote-dora-20240819T0000': 24} |
| XGBoost | 2 | 303 | 12 | 8.347m | 12.138m | -0.477 | {'4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'mote-holly-20250219T0000': 37, '4903468': 24, '4903548': 22} |
| XGBoost | 3 | 359 | 12 | 8.107m | 11.044m | -0.729 | {'4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'usf-sam-20240216T0000': 42, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903471': 36} |
| XGBoost | 4 | 245 | 12 | 9.861m | 14.155m | -0.104 | {'4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26, '4903563': 25, 'mote-dora-20240819T0000': 24} |
| XGBoost | 5 | 205 | 12 | 9.839m | 13.252m | -0.737 | {'4903471': 36, '4903240': 34, '4903353': 28, '4903279': 26, '4903563': 25, '4903278': 13} |
| XGBoost | 6 | 321 | 12 | 8.06m | 10.675m | -0.359 | {'4903550': 52, 'sedna-20241001T0000': 49, '4903557': 44, 'usf-sam-20240216T0000': 42, '4903248': 31, '4903353': 28} |
| XGBoost | 7 | 230 | 12 | 9.402m | 12.637m | -0.399 | {'sedna-20241001T0000': 49, 'usf-sam-20240216T0000': 42, 'mote-holly-20250219T0000': 37, '4903279': 26, '4903563': 25, '4903548': 22} |
| XGBoost | 8 | 281 | 12 | 8.423m | 11.225m | -0.413 | {'4903556': 50, 'sedna-20241001T0000': 49, 'mote-dora-20240307T0000': 45, '4903559': 33, '4903466': 26, '4903563': 25} |
| XGBoost | 9 | 285 | 12 | 7.872m | 10.399m | -0.324 | {'4903552': 54, '4903232': 40, 'mote-holly-20250219T0000': 37, '4903240': 34, '4903248': 31, 'mote-dora-20240819T0000': 24} |
| XGBoost | 10 | 308 | 12 | 8.781m | 12.757m | -0.332 | {'4903553': 54, 'sedna-20241001T0000': 49, '4903557': 44, '4903232': 40, '4903468': 24, 'mote-dora-20240819T0000': 24} |
