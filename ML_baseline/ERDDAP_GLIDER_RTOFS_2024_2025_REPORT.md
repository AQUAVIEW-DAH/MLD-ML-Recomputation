# ERDDAP Glider 2024-2025 Same-Day RTOFS Audit

## Summary
- ERDDAP dataset cap: all audited candidates
- ERDDAP profiles extracted after 10m/profile QC: 18485
- Profiles with valid 10m temperature-threshold MLD (10-100m): 13518
- Eligible profiles with same-day public RTOFS S3 file: 13518
- Rows with RTOFS features extracted: 2715
- RTOFS feature extraction skips: 1617
- RTOFS feature extraction date cap: top 40 dates by platform count, then row count
- Observation date range: 2024-02-16T16:25:06Z to 2025-05-20T07:43:22Z
- Platforms in extracted profiles: 18
- Extracted platform counts: {'usf-sam-20240216T0000': 2362, 'mote-dora-20241016T0000': 2125, 'usf-stella-20250206T0000': 2048, 'mote-holly-20250429T0000': 1788, 'mote-holly-20250319T0000': 1705, 'mote-dora-20241112T0000': 1698, 'mote-holly-20250219T0000': 1636, 'mote-dora-20240418T0000': 1214, 'mote-dora-20240716T0000': 1171, 'mote-SeaXplorer-20240318T0000': 635, 'mote-dora-20240307T0000': 564, 'mote-dora-20240819T0000': 334}
- Training date range: 2024-03-07T00:02:22Z to 2025-02-26T23:37:52Z
- Training platforms: 12
- Training 0.25-degree cells: 29
- Training 0.5-degree cells: 14
- Training 1.0-degree cells: 9
- Training platform counts: {'usf-sam-20240216T0000': 742, 'mote-holly-20250219T0000': 480, 'mote-dora-20240307T0000': 479, 'usf-stella-20250206T0000': 300, 'mote-dora-20240819T0000': 296, 'mote-dora-20240716T0000': 190, 'sedna-20241001T0000': 83, 'Nori-20240816T0000': 72, 'mote-SeaXplorer-20240318T0000': 41, 'ori-20240731T0000': 15, 'Nori-20241008T0000': 14, 'Nori-20241101T0000': 3}

## By Year

| Year | Extracted | Valid MLD 10-100m | Same-day RTOFS eligible | RTOFS feature rows |
| ---: | ---: | ---: | ---: | ---: |
| 2024 | 11308 | 7635 | 7635 | 1935 |
| 2025 | 7177 | 5883 | 5883 | 780 |

## Interpretation
- This is a tmux-friendly ERDDAP glider audit and should remain separate from the main training CSV.
- ERDDAP glider datasets vary substantially by variable naming/QC conventions; failed datasets should be inspected before judging source value.
- Compare final platform and grid-cell coverage against WOD-XBT and Argo GDAC before merging source families.
