# ML Pipeline Benchmarking — v3 (Direct Source Ingestion)

**Timestamp:** 2026-04-06 22:13
**Dataset:** 1201 profiles from direct sources (WOD_XBT_2023, WOD_GLD_2023, WOD_APB_2023, WOD_XBT_2024, ERDDAP_GLIDER_ioos-gliderdac-Murphy-20150809T1355)
**Region:** Gulf of Mexico (-98,18,-80,31)
**Validation:** GroupShuffleSplit by platform/cruise (11 groups)

## Multi-Model Leaderboard

| Model | MAE | RMSE | R² |
| :--- | :--- | :--- | :--- |
| **XGBoost** | 9.897m | 13.004m | 0.466 |
| **RandomForest** | 10.863m | 15.836m | 0.208 |
| **HistGradientBoosting** | 13.725m | 18.876m | -0.125 |
| **LinearRegression** | 13.867m | 19.867m | -0.247 |

## Data Summary
- Total profiles: 1201
- Source families: {'WOD': 1150, 'ERDDAP_GLIDER': 51}
- Instruments: {'gld': 963, 'xbt': 95, 'apb': 92, 'erddap_gld': 51}
- Train/Test split: 1166/35
- Held-out platforms: {'AIRPLANE': 33, 'VIENNA EXPRESS (Cont.ship;c.s.DGWF2;b.2010;IMO9450416;MMSI218355000)': 1, 'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1}
- Observed MLD range: 7.2m to 77.7m
- Model MLD range: 13.4m to 100.2m
