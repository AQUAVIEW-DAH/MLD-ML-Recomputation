# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)

**Timestamp:** 2026-04-07 22:09
**Data path:** `ML_baseline/training_data_combined_rtofs_2024_2025_all_sources.csv`
**Dataset:** 3780 profiles from direct sources (WOD_XBT_2024, WOD_XBT_2025, ARGO_GDAC, ERDDAP_GLIDER_mote-dora-20240307T0000, ERDDAP_GLIDER_usf-sam-20240216T0000, ERDDAP_GLIDER_mote-SeaXplorer-20240318T0000, ERDDAP_GLIDER_ori-20240731T0000, ERDDAP_GLIDER_mote-dora-20240716T0000, ERDDAP_GLIDER_Nori-20240816T0000, ERDDAP_GLIDER_mote-dora-20240819T0000, ERDDAP_GLIDER_Nori-20241008T0000, ERDDAP_GLIDER_sedna-20241001T0000, ERDDAP_GLIDER_Nori-20241101T0000, ERDDAP_GLIDER_mote-holly-20250219T0000, ERDDAP_GLIDER_usf-stella-20250206T0000)
**Region:** Gulf of Mexico (-98,18,-80,31)
**Validation:** Repeated GroupShuffleSplit by platform/cruise (60 groups, 10 splits, test_size=0.20)

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LinearRegression** | 5.186m | 0.536m | 7.421m | 0.834m | -0.05 | 0.095 | 4.314m-5.889m |
| **RandomForest** | 6.358m | 0.977m | 8.794m | 1.154m | -0.472 | 0.186 | 5.004m-7.747m |
| **HistGradientBoosting** | 6.665m | 1.067m | 9.217m | 1.156m | -0.623 | 0.236 | 5.058m-8.349m |
| **XGBoost** | 6.883m | 1.851m | 9.555m | 2.096m | -0.812 | 0.827 | 4.973m-11.939m |

## Validation Interpretation
- Best repeated grouped MAE: LinearRegression at 5.186m mean MAE with mean R²=-0.05.
- This repeated grouped result is a data-coverage diagnostic, not a production-ready model acceptance result; cross-platform generalization remains unstable.
- Do not freeze or accept a new `model.pkl` from this run.

## Data Summary
- Total profiles: 3780
- Source families: {'ERDDAP_GLIDER': 2715, 'ARGO_GDAC': 982, 'WOD': 83}
- Instruments: {'erddap_gld': 2715, 'pfl': 982, 'xbt': 83}
- First split train/test: 3172/608
- First split held-out platforms: {'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, '4903279': 26, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16, '2904010': 14, 'Nori-20241008T0000': 14, '4903278': 13}
- Test rows per split: min=569, max=1955
- Observed MLD range: 10.0m to 93.5m
- Model MLD range: 10.6m to 102.3m

## Split Diagnostics

| Model | Split | Test rows | Test groups | MAE | RMSE | R² | Held-out platforms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| HistGradientBoosting | 1 | 608 | 12 | 8.001m | 10.348m | -1.017 | {'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, '4903279': 26} |
| HistGradientBoosting | 2 | 981 | 12 | 6.912m | 9.92m | -0.556 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, '4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| HistGradientBoosting | 3 | 1955 | 12 | 5.701m | 7.876m | -0.605 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| HistGradientBoosting | 4 | 569 | 12 | 7.414m | 10.499m | -0.24 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, '4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26} |
| HistGradientBoosting | 5 | 715 | 12 | 8.349m | 10.425m | -1.002 | {'usf-stella-20250206T0000': 300, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41, '4903471': 36, '4903240': 34, '4903353': 28} |
| HistGradientBoosting | 6 | 1329 | 12 | 5.058m | 7.235m | -0.394 | {'usf-sam-20240216T0000': 742, 'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, '4903550': 52, '4903557': 44, '4903248': 31} |
| HistGradientBoosting | 7 | 1445 | 12 | 5.362m | 8.168m | -0.416 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'sedna-20241001T0000': 83, 'mote-SeaXplorer-20240318T0000': 41, '4903279': 26, '4903563': 25} |
| HistGradientBoosting | 8 | 801 | 12 | 5.858m | 8.448m | -0.655 | {'mote-dora-20240307T0000': 479, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72, '4903556': 50, '4903559': 33, '4903466': 26} |
| HistGradientBoosting | 9 | 1181 | 12 | 6.821m | 9.018m | -0.631 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, '4903232': 40, '4903240': 34} |
| HistGradientBoosting | 10 | 801 | 12 | 7.176m | 10.229m | -0.714 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, '4903553': 54, '4903557': 44, '4903232': 40} |
| LinearRegression | 1 | 608 | 12 | 5.889m | 8.05m | -0.221 | {'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, '4903279': 26} |
| LinearRegression | 2 | 981 | 12 | 5.565m | 8.076m | -0.031 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, '4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| LinearRegression | 3 | 1955 | 12 | 4.314m | 6.329m | -0.036 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| LinearRegression | 4 | 569 | 12 | 5.651m | 8.871m | 0.115 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, '4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26} |
| LinearRegression | 5 | 715 | 12 | 5.456m | 6.997m | 0.098 | {'usf-stella-20250206T0000': 300, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41, '4903471': 36, '4903240': 34, '4903353': 28} |
| LinearRegression | 6 | 1329 | 12 | 4.475m | 6.308m | -0.06 | {'usf-sam-20240216T0000': 742, 'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, '4903550': 52, '4903557': 44, '4903248': 31} |
| LinearRegression | 7 | 1445 | 12 | 4.759m | 7.073m | -0.062 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'sedna-20241001T0000': 83, 'mote-SeaXplorer-20240318T0000': 41, '4903279': 26, '4903563': 25} |
| LinearRegression | 8 | 801 | 12 | 4.766m | 6.817m | -0.077 | {'mote-dora-20240307T0000': 479, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72, '4903556': 50, '4903559': 33, '4903466': 26} |
| LinearRegression | 9 | 1181 | 12 | 5.224m | 7.309m | -0.071 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, '4903232': 40, '4903240': 34} |
| LinearRegression | 10 | 801 | 12 | 5.757m | 8.382m | -0.151 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, '4903553': 54, '4903557': 44, '4903232': 40} |
| RandomForest | 1 | 608 | 12 | 7.24m | 9.573m | -0.726 | {'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, '4903279': 26} |
| RandomForest | 2 | 981 | 12 | 6.976m | 9.847m | -0.533 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, '4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| RandomForest | 3 | 1955 | 12 | 5.264m | 7.571m | -0.483 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| RandomForest | 4 | 569 | 12 | 7.525m | 10.345m | -0.203 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, '4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26} |
| RandomForest | 5 | 715 | 12 | 7.747m | 9.911m | -0.809 | {'usf-stella-20250206T0000': 300, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41, '4903471': 36, '4903240': 34, '4903353': 28} |
| RandomForest | 6 | 1329 | 12 | 5.004m | 6.797m | -0.231 | {'usf-sam-20240216T0000': 742, 'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, '4903550': 52, '4903557': 44, '4903248': 31} |
| RandomForest | 7 | 1445 | 12 | 5.299m | 7.917m | -0.33 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'sedna-20241001T0000': 83, 'mote-SeaXplorer-20240318T0000': 41, '4903279': 26, '4903563': 25} |
| RandomForest | 8 | 801 | 12 | 5.44m | 7.704m | -0.376 | {'mote-dora-20240307T0000': 479, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72, '4903556': 50, '4903559': 33, '4903466': 26} |
| RandomForest | 9 | 1181 | 12 | 6.423m | 8.765m | -0.541 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, '4903232': 40, '4903240': 34} |
| RandomForest | 10 | 801 | 12 | 6.657m | 9.512m | -0.482 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, '4903553': 54, '4903557': 44, '4903232': 40} |
| XGBoost | 1 | 608 | 12 | 7.25m | 9.762m | -0.795 | {'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, '4903557': 44, '4903232': 40, '4903279': 26} |
| XGBoost | 2 | 981 | 12 | 6.742m | 10.157m | -0.632 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, '4903552': 54, '4903550': 52, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| XGBoost | 3 | 1955 | 12 | 5.985m | 8.597m | -0.912 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51} |
| XGBoost | 4 | 569 | 12 | 6.285m | 9.33m | 0.021 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, '4903549': 36, '4903551': 32, '4903279': 26, '4903466': 26} |
| XGBoost | 5 | 715 | 12 | 11.939m | 15.021m | -3.156 | {'usf-stella-20250206T0000': 300, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41, '4903471': 36, '4903240': 34, '4903353': 28} |
| XGBoost | 6 | 1329 | 12 | 4.973m | 6.817m | -0.238 | {'usf-sam-20240216T0000': 742, 'mote-dora-20240819T0000': 296, 'sedna-20241001T0000': 83, '4903550': 52, '4903557': 44, '4903248': 31} |
| XGBoost | 7 | 1445 | 12 | 5.762m | 8.266m | -0.45 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'sedna-20241001T0000': 83, 'mote-SeaXplorer-20240318T0000': 41, '4903279': 26, '4903563': 25} |
| XGBoost | 8 | 801 | 12 | 5.401m | 7.863m | -0.433 | {'mote-dora-20240307T0000': 479, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72, '4903556': 50, '4903559': 33, '4903466': 26} |
| XGBoost | 9 | 1181 | 12 | 7.139m | 9.392m | -0.769 | {'mote-holly-20250219T0000': 480, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, '4903552': 54, '4903232': 40, '4903240': 34} |
| XGBoost | 10 | 801 | 12 | 7.356m | 10.346m | -0.754 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, '4903553': 54, '4903557': 44, '4903232': 40} |
