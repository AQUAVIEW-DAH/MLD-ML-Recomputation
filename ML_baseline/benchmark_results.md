# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)

**Timestamp:** 2026-04-07 01:19
**Data path:** `/home/suramya/MLD-ML-Recomputation/ML_baseline/training_data.csv`
**Dataset:** 1233 profiles from direct sources (WOD_XBT_2023, WOD_GLD_2023, WOD_APB_2023, WOD_XBT_2024, ERDDAP_GLIDER_ioos-gliderdac-Murphy-20150809T1355, ARGO_GDAC)
**Region:** Gulf of Mexico (-98,18,-80,31)
**Validation:** Repeated GroupShuffleSplit by platform/cruise (16 groups, 10 splits, test_size=0.20)

## Multi-Model Leaderboard

| Model | MAE mean | MAE std | RMSE mean | RMSE std | R² mean | R² std | MAE range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LinearRegression** | 13.604m | 5.084m | 18.417m | 7.155m | -0.084 | 0.42 | 7.004m-22.193m |
| **XGBoost** | 14.606m | 6.021m | 19.22m | 7.943m | -0.06 | 0.308 | 8.889m-23.319m |
| **RandomForest** | 14.713m | 5.82m | 19.435m | 7.863m | -0.119 | 0.485 | 8.212m-22.649m |
| **HistGradientBoosting** | 18.336m | 6.228m | 23.207m | 8.84m | -0.562 | 0.451 | 7.847m-26.779m |

## Validation Interpretation
- Best repeated grouped MAE: LinearRegression at 13.604m mean MAE with mean R²=-0.084.
- This repeated grouped result is a data-coverage diagnostic, not a production-ready model acceptance result; cross-platform generalization remains unstable.
- Do not freeze or accept a new `model.pkl` from this run.

## Data Summary
- Total profiles: 1233
- Source families: {'WOD': 1150, 'ERDDAP_GLIDER': 51, 'ARGO_GDAC': 32}
- Instruments: {'gld': 963, 'xbt': 95, 'apb': 92, 'erddap_gld': 51, 'pfl': 32}
- First split train/test: 1188/45
- First split held-out platforms: {'AIRPLANE': 33, '4902349': 6, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1}
- Test rows per split: min=29, max=1034
- Observed MLD range: 7.2m to 94.5m
- Model MLD range: 13.4m to 100.2m

## Split Diagnostics

| Model | Split | Test rows | Test groups | MAE | RMSE | R² | Held-out platforms |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| HistGradientBoosting | 1 | 45 | 4 | 24.092m | 32.26m | -0.348 | {'AIRPLANE': 33, '4902349': 6, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| HistGradientBoosting | 2 | 233 | 4 | 16.611m | 19.684m | -0.85 | {'US055862': 132, 'AUTONOMOUS PINNIPED': 92, '4902350': 8, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| HistGradientBoosting | 3 | 172 | 4 | 14.82m | 16.961m | -0.464 | {'US055862': 132, 'AIRPLANE': 33, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| HistGradientBoosting | 4 | 47 | 4 | 26.711m | 35.511m | -1.173 | {'AIRPLANE': 33, '4902350': 8, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| HistGradientBoosting | 5 | 58 | 4 | 26.779m | 33.303m | 0.29 | {'ioos-gliderdac-Murphy-20150809T1355': 51, '4902352': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1, 'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| HistGradientBoosting | 6 | 29 | 4 | 23.493m | 32.867m | -0.208 | {'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902350': 8, '4902352': 5, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| HistGradientBoosting | 7 | 149 | 4 | 13.717m | 16.784m | -1.161 | {'US055862': 132, '4902350': 8, '4902351': 8, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| HistGradientBoosting | 8 | 1034 | 4 | 12.116m | 14.03m | -0.726 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, 'US055862': 132, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 38, 'AIRPLANE': 33} |
| HistGradientBoosting | 9 | 846 | 4 | 7.847m | 10.231m | -0.121 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, '4902351': 8, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| HistGradientBoosting | 10 | 186 | 4 | 17.172m | 20.441m | -0.86 | {'US055862': 132, 'AIRPLANE': 33, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902349': 6} |
| LinearRegression | 1 | 45 | 4 | 22.193m | 30.461m | -0.202 | {'AIRPLANE': 33, '4902349': 6, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| LinearRegression | 2 | 233 | 4 | 14.613m | 17.323m | -0.433 | {'US055862': 132, 'AUTONOMOUS PINNIPED': 92, '4902350': 8, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| LinearRegression | 3 | 172 | 4 | 9.992m | 13.767m | 0.035 | {'US055862': 132, 'AIRPLANE': 33, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| LinearRegression | 4 | 47 | 4 | 18.224m | 25.921m | -0.158 | {'AIRPLANE': 33, '4902350': 8, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| LinearRegression | 5 | 58 | 4 | 10.426m | 16.711m | 0.821 | {'ioos-gliderdac-Murphy-20150809T1355': 51, '4902352': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1, 'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| LinearRegression | 6 | 29 | 4 | 21.542m | 29.74m | 0.011 | {'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902350': 8, '4902352': 5, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| LinearRegression | 7 | 149 | 4 | 7.004m | 9.167m | 0.355 | {'US055862': 132, '4902350': 8, '4902351': 8, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| LinearRegression | 8 | 1034 | 4 | 12.567m | 13.68m | -0.641 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, 'US055862': 132, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 38, 'AIRPLANE': 33} |
| LinearRegression | 9 | 846 | 4 | 8.837m | 12.252m | -0.608 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, '4902351': 8, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| LinearRegression | 10 | 186 | 4 | 10.639m | 15.155m | -0.022 | {'US055862': 132, 'AIRPLANE': 33, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902349': 6} |
| RandomForest | 1 | 45 | 4 | 19.72m | 26.728m | 0.074 | {'AIRPLANE': 33, '4902349': 6, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| RandomForest | 2 | 233 | 4 | 11.18m | 13.542m | 0.125 | {'US055862': 132, 'AUTONOMOUS PINNIPED': 92, '4902350': 8, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| RandomForest | 3 | 172 | 4 | 9.116m | 12.597m | 0.192 | {'US055862': 132, 'AIRPLANE': 33, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| RandomForest | 4 | 47 | 4 | 21.83m | 29.186m | -0.468 | {'AIRPLANE': 33, '4902350': 8, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| RandomForest | 5 | 58 | 4 | 22.649m | 28.912m | 0.465 | {'ioos-gliderdac-Murphy-20150809T1355': 51, '4902352': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1, 'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| RandomForest | 6 | 29 | 4 | 22.06m | 30.537m | -0.043 | {'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902350': 8, '4902352': 5, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| RandomForest | 7 | 149 | 4 | 8.685m | 11.189m | 0.04 | {'US055862': 132, '4902350': 8, '4902351': 8, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| RandomForest | 8 | 1034 | 4 | 13.732m | 16.464m | -1.377 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, 'US055862': 132, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 38, 'AIRPLANE': 33} |
| RandomForest | 9 | 846 | 4 | 8.212m | 11.001m | -0.296 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, '4902351': 8, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| RandomForest | 10 | 186 | 4 | 9.948m | 14.198m | 0.103 | {'US055862': 132, 'AIRPLANE': 33, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902349': 6} |
| XGBoost | 1 | 45 | 4 | 17.888m | 25.025m | 0.189 | {'AIRPLANE': 33, '4902349': 6, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| XGBoost | 2 | 233 | 4 | 11.652m | 14.166m | 0.042 | {'US055862': 132, 'AUTONOMOUS PINNIPED': 92, '4902350': 8, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| XGBoost | 3 | 172 | 4 | 9.755m | 13.099m | 0.127 | {'US055862': 132, 'AIRPLANE': 33, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| XGBoost | 4 | 47 | 4 | 23.319m | 30.827m | -0.637 | {'AIRPLANE': 33, '4902350': 8, '4901716': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| XGBoost | 5 | 58 | 4 | 22.902m | 27.646m | 0.511 | {'ioos-gliderdac-Murphy-20150809T1355': 51, '4902352': 5, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1, 'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| XGBoost | 6 | 29 | 4 | 22.791m | 31.21m | -0.089 | {'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902350': 8, '4902352': 5, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| XGBoost | 7 | 149 | 4 | 9.668m | 13.258m | -0.348 | {'US055862': 132, '4902350': 8, '4902351': 8, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1} |
| XGBoost | 8 | 1034 | 4 | 8.889m | 11.432m | -0.146 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, 'US055862': 132, 'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 38, 'AIRPLANE': 33} |
| XGBoost | 9 | 846 | 4 | 9.054m | 11.132m | -0.327 | {'MOTE-DORA (Slocum G3 glider;WMO4802994;operated by MOTE Marine Lab.)\\0': 831, '4902351': 8, '4902349': 6, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| XGBoost | 10 | 186 | 4 | 10.144m | 14.408m | 0.076 | {'US055862': 132, 'AIRPLANE': 33, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 15, '4902349': 6} |
