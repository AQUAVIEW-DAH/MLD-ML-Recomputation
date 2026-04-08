# In-Situ Spatial Coverage Report

**Date:** 2026-04-07  
**Purpose:** Document the spatial-density blocker for ML correction training, especially the difference between raw in-situ row count and unique RTOFS grid coverage.

## Executive Summary

The lack of time-coincident and spatially diverse in-situ observations is a real blocker for Gulf-wide ML correction training.

The confirmed 2024 time-matched smoke dataset has 35 observations, but those observations hit only 19 unique RTOFS ocean grid cells inside the Gulf bbox, or about 0.063% of the available Gulf-domain RTOFS cells. The larger 2023 observation set has 1,146 rows, but it is not currently time-compatible with public current-pattern RTOFS and still hits only 174 unique RTOFS cells, or about 0.576% of the Gulf-domain cells. The dense 831-row MOTE-DORA glider block is especially clustered: it hits only 36 RTOFS cells and is from one platform over a narrow deployment track.

This means the main blocker is not just total row count. It is the combination of:

- too few time-coincident rows,
- repeated observations in the same or nearby RTOFS cells,
- strong platform/deployment clustering,
- sparse coverage of the Gulf RTOFS grid,
- and, for the best-volume 2023 data, no verified same-time Global RTOFS archive in the public current-pattern S3 path.

## RTOFS Grid Reference

Spatial coverage was measured against a cached public Global RTOFS US East file:

`/data/suramya/rtofs_time_matched/rtofs.20240312/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc`

The Gulf bounding box used by the pipeline is `[-98, 18, -80, 31]`.

| Quantity | Value |
|---|---:|
| RTOFS ocean cells inside Gulf bbox | 30,212 |
| Median grid spacing | ~8.1 km x ~8.1 km |
| Approximate cell area | ~65.8 km² |
| Approximate Gulf-domain ocean-cell area in bbox | ~1,986,942 km² |

These values make unique RTOFS-cell hits a more useful metric than raw observation count.

## Coverage Comparison

| Dataset | Rows | Platforms | Dates | Unique RTOFS Cells Hit | Fraction of Gulf RTOFS Cells | Approx Unique Cell Area | Mean Obs Per Hit Cell | Max Obs In One Cell | Unique 0.5° Obs Cells |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Confirmed 2024 RTOFS-time-matched smoke set | 35 | 4 | 10 | 19 | 0.0629% | ~1,250 km² | 1.84 | 6 | 8 |
| All 2023 rows, spatial reference only | 1,146 | 14 | 101 | 174 | 0.5759% | ~11,443 km² | 6.59 | 50 | 60 |
| 2023 dense MOTE-DORA block, spatial reference only | 831 | 1 | 17 | 36 | 0.1192% | ~2,368 km² | 23.08 | 50 | 4 |
| 2023 WOD XBT rows, spatial reference only | 59 | 6 | 15 | 42 | 0.1390% | ~2,762 km² | 1.40 | 5 | 27 |

Important caveat: the 2023 rows are not model-acceptance training rows for an RTOFS residual model unless a valid 2023 Global RTOFS archive is found. They are included here only to show spatial coverage relative to the confirmed 2024 time-matched smoke set.

## Confirmed 2024 Time-Matched Dataset

The confirmed time-matched dataset is:

`ML_baseline/training_data_rtofs_time_matched_smoke.csv`

It spans 2024-03-12 to 2024-09-29 and has 35 rows.

| Quantity | Value |
|---|---:|
| North-south span | ~475 km |
| East-west span at mid-latitude | ~827 km |
| Bounding-box diagonal | ~953 km |
| Max pairwise observation distance | ~860 km |

The large bounding-box span is misleading because the observations are not evenly distributed. The set is dominated by one platform:

| Platform | Rows |
|---|---:|
| EL COQUI | 26 |
| AIRPLANE | 5 |
| BREMEN EXPRESS | 3 |
| F. G. WALTON SMITH | 1 |

The top RTOFS hit cells show repeated sampling near the eastern edge of the domain:

| RTOFS Cell `(Y, X)` | Rows | Approx Grid Lat/Lon |
|---|---:|---|
| `(387, 247)` | 6 | `(29.5548, -80.2400)` |
| `(386, 249)` | 4 | `(29.4852, -80.0800)` |
| `(393, 241)` | 3 | `(29.9715, -80.7200)` |
| `(334, 250)` | 2 | `(25.8010, -80.0000)` |
| `(359, 145)` | 2 | `(27.5877, -88.4000)` |
| `(394, 240)` | 2 | `(30.0408, -80.8000)` |
| `(391, 243)` | 2 | `(29.8328, -80.5601)` |
| `(388, 247)` | 2 | `(29.6244, -80.2400)` |

This dataset should be treated as a clean temporal smoke test, not a Gulf-wide training set.

## 2023 Dataset Spatial Reference

The full 2023 set in `ML_baseline/training_data.csv` has 1,146 rows across 14 platforms and 101 observation dates.

| Quantity | Value |
|---|---:|
| North-south span | ~1,323 km |
| East-west span at mid-latitude | ~1,626 km |
| Bounding-box diagonal | ~2,092 km |
| Max pairwise observation distance | ~1,921 km |

This is spatially broader than the confirmed 2024 set, but it remains clustered and platform-imbalanced:

| Platform | Rows |
|---|---:|
| MOTE-DORA | 831 |
| US055862 | 132 |
| AUTONOMOUS PINNIPED | 92 |
| AIRPLANE | 28 |
| TAINO | 15 |
| EL COQUI | 11 |

The top RTOFS hit cells in 2023 are dominated by the MOTE-DORA deployment:

| RTOFS Cell `(Y, X)` | Rows | Approx Grid Lat/Lon |
|---|---:|---|
| `(346, 211)` | 50 | `(26.6621, -83.1200)` |
| `(342, 213)` | 44 | `(26.3758, -82.9600)` |
| `(343, 212)` | 41 | `(26.4475, -83.0400)` |
| `(345, 211)` | 41 | `(26.5906, -83.1200)` |
| `(339, 214)` | 40 | `(26.1606, -82.8800)` |
| `(347, 209)` | 38 | `(26.7336, -83.2800)` |
| `(340, 214)` | 37 | `(26.2324, -82.8800)` |
| `(339, 212)` | 34 | `(26.1606, -83.0400)` |

## Dense 2023 MOTE-DORA Block

The 831-row MOTE-DORA block is the clearest example of why raw row count can mislead.

| Quantity | Value |
|---|---:|
| Rows | 831 |
| Platforms | 1 |
| Dates | 17 |
| North-south span | ~102 km |
| East-west span at mid-latitude | ~57 km |
| Bounding-box diagonal | ~117 km |
| Max pairwise observation distance | ~115 km |
| Unique RTOFS cells hit | 36 |
| Fraction of Gulf RTOFS cells | 0.1192% |
| Unique 0.5° obs cells | 4 |
| Mean observations per hit cell | 23.08 |
| Max observations in one cell | 50 |

This block is scientifically useful as a local deployment, but it does not provide broad Gulf-wide training coverage.

## 2023 WOD XBT Contrast

The 2023 WOD XBT rows are much smaller in raw count but more spatially efficient:

| Quantity | Value |
|---|---:|
| Rows | 59 |
| Platforms | 6 |
| Dates | 15 |
| Unique RTOFS cells hit | 42 |
| Fraction of Gulf RTOFS cells | 0.1390% |
| Unique 0.5° obs cells | 27 |
| Mean observations per hit cell | 1.40 |

This suggests that future source expansion should optimize for unique RTOFS grid cells and platform diversity, not just total profile count.

## Working Conclusion

The in-situ observation blocker is real. For model acceptance, the dataset needs more than a higher row count. It needs more unique time-coincident RTOFS cells, more independent platforms, and better geographic spread across the Gulf.

Recommended next actions:

- Keep the 2024/2025 RTOFS-compatible WOD XBT build as a clean temporal prototype.
- Add spatial coverage diagnostics to every future training CSV and benchmark report.
- Report unique RTOFS cells hit, obs-per-cell concentration, platform counts, and coarse-grid occupancy before interpreting benchmark metrics.
- Continue searching for a valid 2023 Global RTOFS archive because the 2023 data are spatially broader than the confirmed 2024 smoke set, even though the largest 2023 block is still highly clustered.
- Avoid treating the dense 831-row MOTE-DORA block as broad Gulf coverage.
