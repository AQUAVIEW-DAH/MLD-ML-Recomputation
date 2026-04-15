# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)

**Timestamp:** 2026-04-07 01:19
**Data path:** `ML_baseline/training_data_rtofs_time_matched_smoke.csv`
**Dataset:** 35 profiles from direct sources (WOD_XBT_2024)
**Region:** Gulf of Mexico (-98,18,-80,31)
**Validation:** Repeated GroupShuffleSplit by platform/cruise (4 groups, 4 splits, test_size=0.20)

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HistGradientBoosting** | 16.197m | 3.92m | 19.958m | 6.092m | -0.053 | 0.0 | 9.407m-18.46m |
| **RandomForest** | 17.114m | 6.015m | 19.855m | 7.597m | -0.123 | 0.0 | 6.696m-20.587m |
| **LinearRegression** | 17.608m | 1.043m | 21.267m | 3.155m | -0.019 | 0.0 | 15.802m-18.211m |
| **XGBoost** | 18.921m | 4.572m | 22.874m | 6.854m | -0.376 | 0.0 | 11.002m-21.56m |

## Validation Interpretation
- Best repeated grouped MAE: HistGradientBoosting at 16.197m mean MAE with mean R²=-0.053.
- This repeated grouped result is a data-coverage diagnostic, not a production-ready model acceptance result; cross-platform generalization remains unstable.
- R² was undefined for 4 model/split evaluations because the grouped test fold had fewer than two rows.
- Do not freeze or accept a new `model.pkl` from this run.

## Data Summary
- Total profiles: 35
- Source families: {'WOD': 35}
- Instruments: {'xbt': 35}
- First split train/test: 32/3
- First split held-out platforms: {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3}
- Test rows per split: min=1, max=3
- Observed MLD range: 10.6m to 60.0m
- Model MLD range: 10.7m to 40.7m

## Split Diagnostics

| Model | Split | Test rows | Test groups | MAE | RMSE | R² | Held-out platforms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| HistGradientBoosting | 1 | 3 | 1 | 18.46m | 23.475m | -0.053 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| HistGradientBoosting | 2 | 3 | 1 | 18.46m | 23.475m | -0.053 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| HistGradientBoosting | 3 | 1 | 1 | 9.407m | 9.407m | nan | {'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| HistGradientBoosting | 4 | 3 | 1 | 18.46m | 23.475m | -0.053 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| LinearRegression | 1 | 3 | 1 | 18.211m | 23.089m | -0.019 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| LinearRegression | 2 | 3 | 1 | 18.211m | 23.089m | -0.019 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| LinearRegression | 3 | 1 | 1 | 15.802m | 15.802m | nan | {'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| LinearRegression | 4 | 3 | 1 | 18.211m | 23.089m | -0.019 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| RandomForest | 1 | 3 | 1 | 20.587m | 24.241m | -0.123 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| RandomForest | 2 | 3 | 1 | 20.587m | 24.241m | -0.123 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| RandomForest | 3 | 1 | 1 | 6.696m | 6.696m | nan | {'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| RandomForest | 4 | 3 | 1 | 20.587m | 24.241m | -0.123 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| XGBoost | 1 | 3 | 1 | 21.56m | 26.831m | -0.376 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| XGBoost | 2 | 3 | 1 | 21.56m | 26.831m | -0.376 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
| XGBoost | 3 | 1 | 1 | 11.002m | 11.002m | nan | {'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| XGBoost | 4 | 3 | 1 | 21.56m | 26.831m | -0.376 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3} |
