# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)

**Timestamp:** 2026-04-07 22:09
**Data path:** `ML_baseline/training_data_erddap_glider_rtofs_2024_2025.csv`
**Dataset:** 2715 profiles from direct sources (ERDDAP_GLIDER_mote-dora-20240307T0000, ERDDAP_GLIDER_usf-sam-20240216T0000, ERDDAP_GLIDER_mote-SeaXplorer-20240318T0000, ERDDAP_GLIDER_ori-20240731T0000, ERDDAP_GLIDER_mote-dora-20240716T0000, ERDDAP_GLIDER_Nori-20240816T0000, ERDDAP_GLIDER_mote-dora-20240819T0000, ERDDAP_GLIDER_Nori-20241008T0000, ERDDAP_GLIDER_sedna-20241001T0000, ERDDAP_GLIDER_Nori-20241101T0000, ERDDAP_GLIDER_mote-holly-20250219T0000, ERDDAP_GLIDER_usf-stella-20250206T0000)
**Region:** Gulf of Mexico (-98,18,-80,31)
**Validation:** Repeated GroupShuffleSplit by platform/cruise (12 groups, 10 splits, test_size=0.20)

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LinearRegression** | 3.927m | 0.605m | 5.266m | 1.037m | -0.196 | 0.221 | 3.203m-4.937m |
| **RandomForest** | 4.658m | 1.395m | 6.098m | 1.828m | -0.717 | 0.932 | 3.227m-7.469m |
| **HistGradientBoosting** | 5.711m | 1.396m | 7.0m | 1.657m | -1.229 | 1.039 | 3.84m-7.812m |
| **XGBoost** | 5.764m | 1.239m | 7.091m | 1.302m | -1.336 | 1.067 | 3.928m-7.595m |

## Validation Interpretation
- Best repeated grouped MAE: LinearRegression at 3.927m mean MAE with mean R²=-0.196.
- This repeated grouped result is a data-coverage diagnostic, not a production-ready model acceptance result; cross-platform generalization remains unstable.
- Do not freeze or accept a new `model.pkl` from this run.

## Data Summary
- Total profiles: 2715
- Source families: {'ERDDAP_GLIDER': 2715}
- Instruments: {'erddap_gld': 2715}
- First split train/test: 1818/897
- First split held-out platforms: {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72}
- Test rows per split: min=207, max=1701
- Observed MLD range: 10.0m to 70.5m
- Model MLD range: 10.6m to 60.3m

## Split Diagnostics

| Model | Split | Test rows | Test groups | MAE | RMSE | R² | Held-out platforms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| HistGradientBoosting | 1 | 897 | 3 | 3.84m | 5.622m | -0.322 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| HistGradientBoosting | 2 | 897 | 3 | 3.84m | 5.622m | -0.322 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| HistGradientBoosting | 3 | 1701 | 3 | 6.531m | 7.929m | -1.201 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240307T0000': 479} |
| HistGradientBoosting | 4 | 287 | 3 | 7.812m | 10.286m | -1.723 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'Nori-20241008T0000': 14} |
| HistGradientBoosting | 5 | 265 | 3 | 5.786m | 6.335m | -1.02 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| HistGradientBoosting | 6 | 288 | 3 | 6.595m | 8.261m | -0.727 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'ori-20240731T0000': 15} |
| HistGradientBoosting | 7 | 371 | 3 | 4.055m | 4.773m | -0.201 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| HistGradientBoosting | 8 | 265 | 3 | 5.786m | 6.335m | -1.02 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| HistGradientBoosting | 9 | 207 | 3 | 5.241m | 5.965m | -1.866 | {'mote-dora-20240716T0000': 190, 'Nori-20241008T0000': 14, 'Nori-20241101T0000': 3} |
| HistGradientBoosting | 10 | 527 | 3 | 7.623m | 8.872m | -3.892 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41} |
| LinearRegression | 1 | 897 | 3 | 3.704m | 5.47m | -0.251 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| LinearRegression | 2 | 897 | 3 | 3.704m | 5.47m | -0.251 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| LinearRegression | 3 | 1701 | 3 | 4.236m | 5.743m | -0.155 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240307T0000': 479} |
| LinearRegression | 4 | 287 | 3 | 4.791m | 6.895m | -0.224 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'Nori-20241008T0000': 14} |
| LinearRegression | 5 | 265 | 3 | 3.203m | 3.967m | 0.208 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| LinearRegression | 6 | 288 | 3 | 4.937m | 7.046m | -0.256 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'ori-20240731T0000': 15} |
| LinearRegression | 7 | 371 | 3 | 4.389m | 5.064m | -0.352 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| LinearRegression | 8 | 265 | 3 | 3.203m | 3.967m | 0.208 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| LinearRegression | 9 | 207 | 3 | 3.276m | 4.302m | -0.491 | {'mote-dora-20240716T0000': 190, 'Nori-20241008T0000': 14, 'Nori-20241101T0000': 3} |
| LinearRegression | 10 | 527 | 3 | 3.831m | 4.734m | -0.393 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41} |
| RandomForest | 1 | 897 | 3 | 3.559m | 5.3m | -0.174 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| RandomForest | 2 | 897 | 3 | 3.559m | 5.3m | -0.174 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| RandomForest | 3 | 1701 | 3 | 7.469m | 9.079m | -1.887 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240307T0000': 479} |
| RandomForest | 4 | 287 | 3 | 5.798m | 8.373m | -0.805 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'Nori-20241008T0000': 14} |
| RandomForest | 5 | 265 | 3 | 3.227m | 3.901m | 0.234 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| RandomForest | 6 | 288 | 3 | 4.956m | 7.657m | -0.484 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'ori-20240731T0000': 15} |
| RandomForest | 7 | 371 | 3 | 3.577m | 4.178m | 0.08 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| RandomForest | 8 | 265 | 3 | 3.227m | 3.901m | 0.234 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| RandomForest | 9 | 207 | 3 | 5.012m | 5.718m | -1.634 | {'mote-dora-20240716T0000': 190, 'Nori-20241008T0000': 14, 'Nori-20241101T0000': 3} |
| RandomForest | 10 | 527 | 3 | 6.193m | 7.566m | -2.559 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41} |
| XGBoost | 1 | 897 | 3 | 4.056m | 5.974m | -0.492 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| XGBoost | 2 | 897 | 3 | 4.056m | 5.974m | -0.492 | {'usf-sam-20240216T0000': 742, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72} |
| XGBoost | 3 | 1701 | 3 | 5.836m | 7.458m | -0.947 | {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240307T0000': 479} |
| XGBoost | 4 | 287 | 3 | 7.595m | 9.663m | -1.404 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'Nori-20241008T0000': 14} |
| XGBoost | 5 | 265 | 3 | 6.201m | 6.767m | -1.304 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| XGBoost | 6 | 288 | 3 | 6.095m | 7.921m | -0.588 | {'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'ori-20240731T0000': 15} |
| XGBoost | 7 | 371 | 3 | 3.928m | 4.747m | -0.188 | {'mote-dora-20240819T0000': 296, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| XGBoost | 8 | 265 | 3 | 6.201m | 6.767m | -1.304 | {'mote-dora-20240716T0000': 190, 'Nori-20240816T0000': 72, 'Nori-20241101T0000': 3} |
| XGBoost | 9 | 207 | 3 | 6.833m | 7.465m | -3.488 | {'mote-dora-20240716T0000': 190, 'Nori-20241008T0000': 14, 'Nori-20241101T0000': 3} |
| XGBoost | 10 | 527 | 3 | 6.837m | 8.174m | -3.153 | {'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'mote-SeaXplorer-20240318T0000': 41} |
