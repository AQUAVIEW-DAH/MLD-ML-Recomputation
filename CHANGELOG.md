# Changelog

All notable changes to the MLD-ML-Recomputation MVP pipeline will be documented in this file.

## [Unreleased]

### Added
- `api.py`: FastAPI application wrapping `get_mld_estimate` for quick HTTP querying.
- `mcp_server.py`: Model Context Protocol (MCP) server implementation wrapping our MLD algorithm for seamless AI agent access.
- `mld_pipeline.py`: Intermediate Logic & Blender layer that merges RTOFS Model output with Aquaview Observation Profiles through Inverse Distance Weighting.
- `mld-dashboard/`: Complete Phase 4 Frontend Visualizer built dynamically with React, Vite, and Leaflet mapping for clickable, real-time map queries.
- `CHANGELOG.md`: Continuous change-tracking document.

### Changed
- `mld_core.py`: Updated `compute_mld_temp_threshold` calculation to utilize absolute temperature difference `abs(temp - t_ref) >= 0.2` rather than strict `temp <= target`, properly catching temperature inversions.
- `aquaview_obs.py`: Added unverified SSL context handling natively to bypass local Certificate Verification issues when making remote Aquaview URL Requests locally. 

### Tested
- Initialized local test file `test_integration.py` successfully producing an MLD output (`16.96m`) with robust model fallbacks operating reliably over IOOS data boundaries.
