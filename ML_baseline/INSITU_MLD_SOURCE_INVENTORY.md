# Gulf of Mexico In-Situ MLD Source Inventory

Date: 2026-04-07

Purpose: identify all realistic in-situ observation source families that could support Gulf of Mexico mixed-layer-depth labels, and separate direct profile-label sources from products that are only auxiliary or require major reshaping.

## Summary

The best MLD-label sources are still vertical temperature profiles, ideally with salinity so density-based MLD can be evaluated too. The high-priority source families are:

1. NOAA/NCEI World Ocean Database (WOD): broad, quality-controlled aggregator for historical and recent ocean profiles.
2. Argo GDAC direct profile files: best source for profiling-float pressure/temperature/salinity profiles.
3. IOOS National Glider DAC / gliders.ioos.us: centralized glider deployment profiles, including Gulf deployments.
4. SECOORA and GCOOS ERDDAP profile datasets: regional access points that expose gliders, AUV/CTD, GOMECC, SEAMAP-like, and other Gulf profile candidates.
5. NCEI accession/cruise datasets: source-level CTD/XBT/GOMECC/SEAMAP datasets that can be useful if WOD lags or if source metadata is needed.
6. GTSPP: global temperature/salinity profile program that can provide near-real-time and best-copy XBT/CTD/profile feeds.
7. AOML XBT / AXBT / Ship-of-Opportunity data: useful for temperature-threshold MLD, but not density MLD without salinity.
8. Animal-borne profiler / MEOP-style data: profile-capable where available, but often already duplicated through WOD/APB.
9. Multi-depth moorings and coastal arrays: possible only when they have enough vertical levels around 10m and below; most station/buoy records are not direct MLD labels.
10. GRIIDC/GoMRI and project-level Gulf cruise archives: valuable CTD/XBT/MVP/glider datasets, especially LASER, DEEPEND, LADC-GEMM, and DWH-era cruises, but they need duplicate checks against NCEI/WOD.
11. USF COMPS and BSEE/NTL/GulfHub fixed platforms: potentially valuable fixed-location water-column temperature records, but only if the station has multiple useful depths around and below 10m.

Surface-only buoys, CO-OPS water-level stations, HF radar, and satellite products should not be used as observed MLD labels. They can be useful as features or context only.

## Local Evidence From Current Repo

Already ingested into `training_data.csv`:

| Source family | Rows | Notes |
| --- | ---: | --- |
| WOD glider (`gld`) | 963 | Dominated by 2023 glider deployments, not RTOFS-time-compatible yet. |
| WOD XBT (`xbt`) | 95 | Useful for temperature MLD only; 2024 XBT has the current clean RTOFS smoke set. |
| WOD APB (`apb`) | 92 | Animal-borne profiler data, some salinity/density support depending on record. |
| ERDDAP glider | 51 | One SECOORA Murphy deployment currently in main CSV. |
| Argo GDAC direct | 32 | Small opt-in smoke sample from direct GDAC files. |

Local source-audit inventory:

| Audit file | Candidate count | Notes |
| --- | ---: | --- |
| `source_audit_results.csv` | 21 WOD year/instrument entries | WOD 2023/2024 XBT/GLD/CTD/PFL/MRB/DRB/APB checked; 2025 S3 missing but THREDDS probe found 2025 XBT candidates. |
| `source_audit_erddap_ioos_gliders.csv` | 73 profile candidates | All marked `profile_candidate`; many expose `profile_id`, `depth`, `conductivity`, `density`, pressure/QC variables. |
| `source_audit_erddap_secoora.csv` | 35 profile candidates + 1 metadata-only | Includes Murphy, USF bass/sam/stella/jaialai gliders, GOMECC-like datasets, SEAMAP/AUV/CTD-style endpoints. |
| `profile_method_fit_audit_combined.csv` | 2,490 audited profiles | 2,320 basic temp-depth profiles; 1,516 current temp-10m labels; 726 density-10m labels; 1,593 temp-or-density 10m labels. |

## Source Inventory

| Source / product | Access path | Profile variables likely available | Gulf relevance | MLD-label suitability | Pipeline status | Main risk / next action |
| --- | --- | --- | --- | --- | --- | --- |
| NOAA/NCEI WOD | WODSelect, WOD yearly NetCDF, WOD THREDDS/S3 where available | Temperature, salinity, oxygen, nutrients by instrument; instruments include XBT, CTD, PFL, GLD, APB, MRB, DRB, OSD/MBT/UOR depending on year | High | High for temp MLD; high for density MLD when salinity exists | Active for XBT/GLD/APB 2023/2024; 2025 needs THREDDS fallback | Avoid double-counting source datasets also seen in Argo/NGDAC/GTSPP; prioritize same-day RTOFS years. |
| Argo GDAC direct | GDAC profile files, profile index | PRES, TEMP, PSAL; adjusted variables/QC; BGC/synthetic profiles when needed | Medium to high depending float presence in Gulf | High for temp and density MLD | Opt-in smoke ingestion exists | Scale direct profile-index scan; use adjusted/QC variables and deduplicate against WOD PFL. |
| IOOS National Glider DAC | `https://gliders.ioos.us/`, ERDDAP, THREDDS | Time, lat/lon, profile_id, depth/pressure, temperature, conductivity/salinity, density, QC variables | High; many Gulf glider deployments | High when profile brackets 10m; density possible where salinity/density present | ERDDAP smoke exists; IOOS audit has 73 profile candidates | Per-deployment parsing/QC required; many profiles may not bracket 10m. |
| SECOORA ERDDAP | `https://erddap.secoora.org/erddap/` | Glider CTD variables; some GOMECC/SEAMAP/AUV-style CTD endpoints | High for eastern Gulf and Florida shelf | High for gliders/CTD when profile-shaped; variable-specific for cruise/AUV products | Audit has 35 profile candidates; limited live fetch tested 5 datasets | Need dataset-specific variable mapping; one GOMECC query failed during method-fit audit due endpoint variable mismatch. |
| GCOOS ERDDAP / inventory | GCOOS data inventory and ERDDAP endpoints | Gliders, water temperature, salinity, currents; station/platform metadata | High Gulf focus | High for profile/glider endpoints; low for single-depth stations | Not yet integrated as its own provider; GCOOS appears in IOOS/NGDAC metadata | Identify profile-capable GCOOS endpoints separately from station time series. |
| NCEI NGDAC archive | NCEI archive of IOOS NGDAC deployments | Full/low-resolution glider trajectory profiles, temperature, salinity, conductivity, density | High where deployments enter Gulf | High | Not separately integrated; overlaps IOOS Glider DAC | Use as fallback/archive path if ERDDAP/THREDDS endpoints change. |
| NCEI cruise/accession CTD datasets | NCEI accession pages, HTTPS/THREDDS/download packages | CTD temperature, salinity, oxygen, bottle data; per-cruise metadata | Medium to high; examples include SEAMAP and GOMECC | High if station casts include 10m and below | Not integrated as direct accession provider | Useful to recover cruise/profile data missing from WOD; high duplicate risk with WOD. |
| GTSPP | NCEI GTSPP interface, HTTP/FTP/THREDDS | Temperature/salinity profiles, real-time and best-copy data, shipboard XBT/CTD | Medium | High for XBT/CTD profiles, if Gulf subset accessible | Not integrated | Use as supplemental discovery feed; deduplicate against WOD and Argo. |
| AOML XBT / AXBT / SOOP | AOML XBT/Ship-of-Opportunity sources, possibly NCEI/WOD/GTSPP downstream | Temperature vs depth, cruise/profile metadata | Medium to high for shipping lanes and hurricane/airborne work | High for temperature MLD; no density MLD unless paired salinity exists | Indirectly included through WOD XBT | Search for Gulf-specific 2024/2025 tracks; deduplicate with WOD/GTSPP. |
| WOD PFL / Argo via WOD | WOD `pfl` instrument files | Temperature/salinity profile floats | Medium | High | WOD PFL files available for 2023/2024 but very large; direct Argo preferred | Avoid downloading multi-GB WOD PFL unless needed; direct GDAC index is cleaner. |
| WOD CTD | WOD `ctd` files | Temperature/salinity/pressure profiles | Medium | High | WOD CTD 2023/2024 available but not downloaded in current pipeline | Good candidate after RTOFS-time-compatible years are prioritized. |
| WOD APB / animal-borne profilers | WOD `apb`; possible direct MEOP-style feeds | Temperature and sometimes salinity/density by animal-borne sensors | Medium | Medium to high depending sensor variables and QC | WOD APB ingested for 2023 | Direct-source path could expand coverage, but WOD likely already aggregates many. |
| WOD MRB/DRB/MBT/OSD/UOR variants | WOD instrument-specific files | Mixed: moored/drifting/bottle/MBT/underway observations | Low to medium for MLD labels | Case-by-case; many are too sparse vertically or surface-like | WOD MRB/DRB availability audited but not ingested | Audit with method-fit script before using; do not assume profile suitability. |
| GOMECC / GOMECC2 CTD products | SECOORA ERDDAP and NCEI accession archives | CTD temperature, salinity, oxygen, nutrients/carbon | Medium; Gulf cruise sections | High when z/temperature/salinity station profiles are accessible | Seen in SECOORA audit; not parsed robustly yet | Build a cruise-CTD parser or use WOD/NCEI version; avoid source duplication. |
| SEAMAP CTD products | NCEI accessions; possibly SECOORA/ERDDAP mirrors | CTD temperature/salinity/oxygen station profiles | Medium; Gulf fisheries cruises | High for station profiles | Not integrated | Search NCEI by Gulf bbox/date and accession; likely useful for historical, less for near-real-time. |
| AUV / autonomous vehicle CTD datasets | SECOORA ERDDAP examples, local project archives | Temperature, salinity/conductivity, pressure/z, trajectory | Localized | Medium; can be profile-like but may be transect/time-series shaped | Seen in SECOORA audit | Needs binning into vertical profiles and duplicate/QC checks. |
| OSMC profilers | OSMC/NOAA profile discovery feeds | Platform-level profile observations from multiple systems | Medium | Medium to high as discovery/secondary feed | Not integrated | Useful for finding platforms, but may duplicate Argo/GTSPP/WOD/NGDAC. |
| GRIIDC / GoMRI project datasets | GRIIDC portal and ERDDAP/NCEI-linked datasets | CTD, XBT, glider, MVP, VMP, temperature, salinity, pressure/depth, density in project-specific formats | High for DWH-era and northern/deep Gulf process studies | High for CTD/XBT/MVP profile datasets | Not integrated | Add targeted discovery for CTD/XBT/MVP/glider datasets; expect heterogeneous formats and duplicates with NCEI/WOD. |
| LASER / CARTHE MVP and CTD products | GRIIDC LASER datasets | Moving Vessel Profiler and CTD temperature/conductivity/pressure, often gridded to 1m bins with salinity/density derived | High for northern Gulf frontal/submesoscale windows | High for process-study MLD labels, but limited dates/regions | Not integrated | Good historical/process-study source; not useful for 2024+ RTOFS if dated 2016 unless model archive changes. |
| DEEPEND CTD and glider products | GRIIDC and sometimes ERDDAP/remotely hosted datasets | CTD temperature, salinity, dissolved oxygen, density, fluorescence; some glider temperature/salinity | High for deep pelagic Gulf cruises | High for profile labels | Not integrated | Strong historical source; likely overlaps SECOORA Murphy/glider and NCEI/WOD in places. |
| SEAMAP CTD accession series | NCEI accession `NMFS-SEFSC-SEAMAP-CTD` and yearly accessions | Sea-Bird CTD temperature, salinity, dissolved oxygen; northern Gulf survey station casts | High for shelf/slope Gulf surveys from 1992-present | High for CTD MLD when 10m is present | Not integrated directly; represented only generically by NCEI cruise/accession row | Promote to targeted source; parse Sea-Bird CNV and deduplicate against WOD CTD. |
| USF COMPS subsurface-temperature products | USF OCL/COMPS pages and SECOORA ERDDAP | Fixed mooring water temperature and sometimes salinity at selected depths; station metadata and historical products | High on West Florida Shelf | Medium; useful if enough vertical levels bracket 10m and expected MLD depth | Not integrated | Treat separately from standard profiles; current COMPS/NDBC surface feed alone is insufficient, but subsurface products can help fixed-location MLD/heat-content analysis. |
| BSEE/NTL and GulfHub industry platforms | GCOOS NTL repository, GCOOS ERDDAP/WAF, GulfHub | Seawater temperature, salinity on some platforms, ADCP/current profiles, station metadata; Shell Alcyone has reported water temperature to 300m in a technical paper | High for deepwater oil/gas corridor | Medium to high only for platforms with multi-depth temperature/salinity sensors | Not integrated | First audit station-level depth coverage; many NTL pages expose current profiles but not necessarily enough temperature depths for MLD. |
| Flower Garden Banks monitoring | NOAA sanctuary/NCRMP and cruise CTD/YSI records | Subsurface temperature recorders at reef depths; occasional vertical CTD profiles | Localized NW Gulf banks | Low for fixed STRs alone; medium for opportunistic CTD profiles | Not integrated | Use CTD profiles only for labels; benthic fixed-temperature sensors are context, not standard 10m MLD labels. |
| Multi-depth moorings / TABS / oil-platform arrays | GCOOS inventory, ERDDAP, NDBC/partner station feeds | Water temperature/salinity at fixed depths, sometimes currents | High geographically | Usually low for standard MLD, unless enough vertical levels bracket 10m and below | Not integrated | Treat as a separate "fixed-platform stratification" experiment, not standard profile labels by default. |
| NDBC standard buoys and CO-OPS/PORTS | NDBC/CO-OPS station APIs | Mostly surface or near-surface met/ocean variables | High geographically | Low for MLD labels | Not integrated as labels | Use only as features/validation context; not vertical MLD labels. |
| HF radar and satellite SST/SSS/SLA/ocean color | IOOS HF radar, NASA/NOAA products | Surface fields only | High | Not valid observed MLD labels | Not label sources | Potential features, not target labels. |

## Additions From Deep-Research Cross-Check

The external deep-research report mostly reinforces the existing inventory, but it usefully upgrades several broad categories into named targets:

| Added / refined target | Why it matters | Caution |
| --- | --- | --- |
| SEAMAP CTD, 1992-present | NCEI explicitly exposes northern Gulf CTD profile data in Sea-Bird CNV format, which should be MLD-capable when casts bracket 10m. | Mostly historical and seasonal; likely duplicated in WOD CTD. |
| GRIIDC / GoMRI | Hosts many Gulf CTD/XBT/glider/MVP datasets from DWH-era process studies. | Heterogeneous project formats; mostly pre-2024, so not directly useful for current public RTOFS windows unless we find historical model archives. |
| LASER MVP CTD | High-resolution moving-vessel profiles gridded to 1m vertical bins in the northern Gulf. | Great for 2016 process studies, not current RTOFS residual training. |
| DEEPEND CTD/glider | Deep Gulf CTD and glider profiles with temperature/salinity/density. | Duplicates likely through SECOORA/NCEI/WOD; must deduplicate. |
| USF COMPS subsurface-temperature products | West Florida Shelf fixed-location subsurface temperature records can help with hurricane/heat-content and possibly fixed-location MLD. | Not all COMPS/NDBC feeds expose full vertical strings; surface-only buoy records remain insufficient. |
| BSEE/NTL and GulfHub | Industry platforms expand deepwater fixed-location coverage; GCOOS now manages NTL data and GulfHub aggregates/QCs industry datasets. | Station-by-station depth audit is mandatory; ADCP current-depth profiles do not automatically mean temperature-depth profiles. |
| AOML HD XBT | Stronger evidence for high-density XBT as a temperature-profile source family. | Need Gulf-relevant transects or Gulf-specific XBT products; XBT still lacks salinity for density MLD. |

## Practical Priority Order

1. Finish WOD THREDDS fallback for 2025 XBT and build the clean 2024+2025 same-day RTOFS XBT dataset.
2. Scale direct Argo GDAC profile-index ingestion for 2024+2025 Gulf profiles, with adjusted/QC variables and same-day RTOFS matching.
3. Add IOOS Glider DAC provider search for 2024+2025 Gulf deployments and run the method-fit audit before ingestion.
4. Add SECOORA/GCOOS ERDDAP source-specific parsers for the strongest Gulf CTD/glider endpoints surfaced by the audits.
5. Evaluate WOD CTD 2024/2025 and NCEI SEAMAP CTD through THREDDS/WODSelect/accession downloads before downloading large all-year products.
6. Add a source-discovery audit for GRIIDC/GoMRI CTD/XBT/MVP/glider datasets, especially LASER and DEEPEND, while marking them historical unless a same-time model archive is found.
7. Add a GCOOS/COMPS/BSEE fixed-platform depth audit that asks: does each station have enough water-temperature depths around 10m and below to compute a comparable MLD?
8. Use NCEI accession/GOMECC/SEAMAP/GTSPP/AOML XBT sources as targeted fallback and gap-fill sources, with strict duplicate detection.
9. Keep surface-only products out of the observed-MLD label table unless a separate fixed-platform stratification experiment is explicitly defined.

## MLD Method Implications

Temperature-threshold MLD:

- Works with XBT, CTD, glider, Argo, APB if temperature/depth profiles bracket the reference depth.
- XBT can be valuable because it often has deep temperature profiles and broad ship-track spread.

Density-threshold MLD:

- Requires salinity or density, so XBT-only profiles usually do not qualify.
- Still usually uses a near-surface reference such as 10m; it does not remove the need for near-surface profile coverage.

Relaxed shallowest-reference labels:

- Can recover many more profiles in the method-fit audit, especially gliders that start below 10m.
- This changes the target and should be stored as a separate experiment, not mixed with the current 10m MLD label.

## References / Access Points

- NOAA/NCEI World Ocean Database: https://www.ncei.noaa.gov/products/world-ocean-database
- WOD instrument code table: https://www.ncei.noaa.gov/access/world-ocean-database/CODES/v_5_instrument.html
- Argo GDAC profile-file guidance: https://argo.ucsd.edu/data/how-to-use-argo-files/
- Argo data FAQ and MLD-sensitive QC guidance: https://argo.ucsd.edu/data/data-faq/
- IOOS National Glider DAC: https://gliders.ioos.us/
- IOOS NGDAC documentation: https://ioos.github.io/glider-dac/
- NCEI NGDAC archive catalog: https://catalog.data.gov/dataset/full-resolution-and-low-resolution-real-time-physical-trajectory-profile-data-from-gliders-subm
- SECOORA Glider Observatory: https://secoora.org/data/secoora-glider-observatory/
- SECOORA ERDDAP: https://erddap.secoora.org/erddap/
- GCOOS ERDDAP: https://erddap.gcoos.org/erddap/
- GCOOS asset inventory: https://data.gcoos.org/inventory.php
- GCOOS BSEE/NTL transition note: https://gcoos.org/bsee-ntl-data-moves-to-gcoos/
- GulfHub: https://gulfhub.gcoos.org/
- BSEE/NTL Shell Alcyone station example: https://ntl.gcoos.org/station_details.php?station=42395
- Shell Alcyone technical-paper page: https://www.fugro.com/expertise/technical-papers/four-years-metocean-support-shell-stones-field-asset-integrity-collaborative-research-fugro
- USF COMPS subsurface temperature product: https://ocl.marine.usf.edu/Products/tp.html
- SEAMAP CTD NCEI series: https://www.ncei.noaa.gov/archive/accession/NMFS-SEFSC-SEAMAP-CTD
- GRIIDC LASER CTD/VMP example: https://data.griidc.org/data/R4.x265.000:0081
- GRIIDC DEEPEND glider example: https://data.griidc.org/data/R4.x257.230:0021
- NCEI GTSPP: https://www.ncei.noaa.gov/products/global-temperature-and-salinity-profile-programme
- AOML High Density XBT transects: https://www.aoml.noaa.gov/phod/hdenxbt/index.php
- AOML XBT QC/database notes: https://www.aoml.noaa.gov/phod/xbt.html
- Example NCEI SEAMAP Gulf CTD accession: https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.nodc%3A0156169/html
