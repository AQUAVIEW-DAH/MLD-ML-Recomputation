# WOD XBT 2024-2025 Same-Day RTOFS Audit

## Summary
- WOD XBT profiles extracted in GoM bbox: 138
- Profiles with 10m temperature-threshold MLD <= 100m: 106
- Eligible profiles with same-day public RTOFS S3 file: 106
- Rows with RTOFS features extracted: 83
- Observation date range: 2024-03-12T15:23:59Z to 2025-05-19T12:50:59Z
- Source counts: {'WOD_XBT_2024': 82, 'WOD_XBT_2025': 56}
- Platform counts: {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 95, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 27, 'AIRPLANE': 11, 'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3, 'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1}
- Training date range: 2024-03-12T15:23:59Z to 2025-05-19T08:32:00Z
- Training platforms: 6
- Training 0.25-degree cells: 22
- Training 0.5-degree cells: 14
- Training 1.0-degree cells: 8
- Training platform counts: {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 51, 'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 16, 'AIRPLANE': 11, 'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 3, 'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1, 'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1}
- RTOFS feature extraction skipped 23 otherwise eligible profiles. Skipped rows were near the eastern boundary (`29.887N` to `30.398N`, `-81.618W` to `-80.318W`) and came from EL COQUI (18) and TAINO (5).

## By Year

| Year | Extracted | MLD <=100m | Same-day RTOFS eligible | RTOFS feature rows |
| ---: | ---: | ---: | ---: | ---: |
| 2024 | 82 | 63 | 63 | 54 |
| 2025 | 56 | 43 | 43 | 29 |

## Date Counts For RTOFS-Eligible Profiles

| Date | Rows | Platforms |
| :--- | ---: | :--- |
| 20240312 | 1 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 1} |
| 20240405 | 1 | {'F. G. WALTON SMITH (R/V;c.s.WCZ6292/WDL9255;b.1999;IMO8964501;operated by RSMAS)': 1} |
| 20240502 | 5 | {'AIRPLANE': 5} |
| 20240601 | 10 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 10} |
| 20240606 | 8 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 8} |
| 20240810 | 11 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 11} |
| 20240815 | 11 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 11} |
| 20240907 | 8 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 8} |
| 20240912 | 6 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 6} |
| 20240929 | 2 | {'BREMEN EXPRESS (Cont.s.;c.s.5LJY8;b.2008;flag Germany by 02.2023;IMO9343728)\\0': 2} |
| 20250125 | 7 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 7} |
| 20250130 | 8 | {'EL COQUI (Cargo ship;c.s.WDJ4838;built 2018;IMO9721968;MMSI367781630)': 8} |
| 20250206 | 1 | {'CHICAGO EXPRESS (Cont.ship;c.s.DCUJ2;built 2006;IMO9295268)\\0': 1} |
| 20250508 | 6 | {'AIRPLANE': 6} |
| 20250514 | 11 | {'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 11} |
| 20250519 | 10 | {'TAINO (Cont.ship;c.s.WDJ6598;b.2018;IMO9721970;MMSI367799380)': 10} |

## Interpretation
- This dataset is cleaner than the temporally decoupled main training CSV because it uses same-day Global RTOFS files when available.
- It remains XBT-only, so it supports temperature-threshold MLD but not density MLD.
- Platform and spatial clustering should be evaluated before accepting any model trained on this table.
- This is still not production-scale: 83 final rows, 6 platforms, 14 half-degree cells, and 51/83 final rows from EL COQUI.
- A diagnostic grouped benchmark on this CSV gave best mean MAE `9.305m` from RandomForest, but mean R² was still negative (`-0.244`), so this should remain a clean prototype dataset rather than a frozen model source.
