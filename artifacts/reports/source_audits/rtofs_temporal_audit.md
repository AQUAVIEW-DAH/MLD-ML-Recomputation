# RTOFS / In-Situ Temporal Matching Audit

## Summary
- Training rows audited: 1233
- Observation date range: 2015-08-10 00:37:41+00:00 to 2024-09-29 13:12:59+00:00
- Observation years: {2015: 51, 2023: 1146, 2024: 36}
- Source families: {'WOD': 1150, 'ERDDAP_GLIDER': 51, 'ARGO_GDAC': 32}
- Unique observation dates: 121
- Local RTOFS dates available: ['20260330', '20260331', '20260401', '20260402', '20260403', '20260404', '20260405']
- Rows with same-day local RTOFS: 0
- Rows with +/-24h local RTOFS: 0
- NOAA S3 current-pattern dates available: 10
- Rows with NOAA S3 current-pattern same-day availability: 36
- Observed public RTOFS bucket start from prefix listing: 2024-01-27

## Interpretation
- The current local RTOFS cache is a 2026 window, so same-day matches are expected to be zero for the present 2015/2023/2024 in-situ table.
- NOAA S3 current-pattern availability is partial for this table. If the dense observation blocks are unavailable, the current public operational bucket is not a sufficient historical archive by itself; we should search NCEI/NOMADS archives or use a forward-rolling collector/reanalysis fallback.
- In this audit, the public bucket covers the sparse 2024 WOD rows but not the dense 2023 WOD block or the 2015 ERDDAP glider smoke-test deployment.
- Do not combine this temporally decoupled smoke-test dataset with a future time-coincident benchmark as if they were equivalent validation evidence.

## NOAA S3 Same-Day Matches

| Date | Rows | Source families | Example S3 URL |
| :--- | ---: | :--- | :--- |
| 20240312 | 1 | {'WOD': 1} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240312/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240405 | 1 | {'WOD': 1} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240405/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240502 | 5 | {'WOD': 5} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240502/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240601 | 6 | {'WOD': 6} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240601/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240606 | 5 | {'WOD': 5} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240606/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240810 | 5 | {'WOD': 5} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240810/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240815 | 5 | {'WOD': 5} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240815/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240907 | 4 | {'WOD': 4} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240907/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240912 | 2 | {'WOD': 2} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240912/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |
| 20240929 | 2 | {'WOD': 2} | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20240929/rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc |

## Top Observation Dates

| Date | Rows | Source families | Local same-day | S3 current-pattern | Example S3 URL |
| :--- | ---: | :--- | :--- | :--- | :--- |
| 20230511 | 67 | {'WOD': 67} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230511/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230510 | 65 | {'WOD': 65} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230510/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230512 | 59 | {'WOD': 59} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230512/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230509 | 57 | {'WOD': 57} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230509/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230513 | 55 | {'WOD': 55} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230513/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230505 | 54 | {'WOD': 54} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230505/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230514 | 54 | {'WOD': 54} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230514/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230506 | 53 | {'WOD': 53} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230506/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230515 | 53 | {'WOD': 53} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230515/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230507 | 51 | {'WOD': 51} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230507/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230508 | 50 | {'WOD': 50} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230508/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230501 | 45 | {'WOD': 45} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230501/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230504 | 44 | {'WOD': 44} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230504/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230503 | 43 | {'WOD': 43} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230503/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230502 | 42 | {'WOD': 42} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230502/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230829 | 42 | {'WOD': 42} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230829/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230516 | 28 | {'WOD': 28} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230516/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230830 | 22 | {'WOD': 22} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230830/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230828 | 15 | {'WOD': 15} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230828/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230901 | 14 | {'WOD': 14} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230901/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230903 | 14 | {'WOD': 14} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230903/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230904 | 14 | {'WOD': 14} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230904/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230831 | 13 | {'WOD': 13} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230831/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230902 | 13 | {'WOD': 13} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230902/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
| 20230430 | 11 | {'WOD': 11} | False | False | https://noaa-nws-rtofs-pds.s3.amazonaws.com/rtofs.20230430/rtofs_glo_3dz_f024_6hrly_hvr_US_east.nc |
