"""
WOD S3 Direct Source — Downloads World Ocean Database NetCDF files
from the NOAA public S3 bucket and extracts depth/temperature profiles
for the Gulf of Mexico region.

This bypasses the Aquaview indexer entirely, going straight to the
original data.  WOD files use a contiguous ragged-array layout:
  - Per-cast arrays:  lat, lon, time, z_row_size, Temperature_row_size
  - Flat observation arrays:  z, Temperature
  - Profile i spans z[cum_z[i]:cum_z[i+1]] / Temperature[cum_t[i]:cum_t[i+1]]
"""
from __future__ import annotations

import logging
import os
import ssl
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)

# ---- configuration --------------------------------------------------------
WOD_S3_BASE = "https://noaa-wod-pds.s3.amazonaws.com"
WOD_CACHE_DIR = Path("/data/suramya/wod_cache")

# Instrument codes and their expected GoM yield
WOD_INSTRUMENTS = {
    "xbt": "Expendable Bathythermograph",
    "gld": "Glider",
    "ctd": "Conductivity-Temperature-Depth",
    "pfl": "Profiling Float (Argo)",
}

# Minimum depth levels for a profile to be useful for MLD computation
MIN_DEPTH_LEVELS = 5
# Minimum max-depth for MLD to be meaningful (metres)
MIN_MAX_DEPTH_M = 15.0

ssl_ctx = ssl._create_unverified_context()


# ---- data classes ----------------------------------------------------------
@dataclass(frozen=True)
class WODProfile:
    """One depth-temperature profile extracted from a WOD NetCDF file."""
    source: str          # e.g. "WOD_XBT_2023"
    instrument: str      # xbt | gld | ctd | pfl
    cast_id: int         # wod_unique_cast
    cruise_id: str       # WOD_cruise_identifier
    platform: str        # Platform name
    lat: float
    lon: float
    obs_time: str        # ISO-8601
    depth_m: list[float]
    temperature_c: list[float]


# ---- download helpers ------------------------------------------------------
def _wod_url(year: int, instrument: str) -> str:
    return f"{WOD_S3_BASE}/{year}/wod_{instrument}_{year}.nc"


def download_wod_file(year: int, instrument: str) -> Path:
    """Download a WOD NetCDF file from S3, caching locally."""
    WOD_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = WOD_CACHE_DIR / f"wod_{instrument}_{year}.nc"

    if local_path.exists():
        logger.info("Using cached %s (%d MB)", local_path.name, local_path.stat().st_size // 1_000_000)
        return local_path

    url = _wod_url(year, instrument)
    logger.info("Downloading %s ...", url)

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=300, context=ssl_ctx) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError(f"WOD file not available: {url}") from e
        raise

    local_path.write_bytes(data)
    logger.info("Saved %s (%d MB)", local_path.name, len(data) // 1_000_000)
    return local_path


# ---- profile extraction ----------------------------------------------------
def extract_wod_profiles(
    year: int,
    instrument: str,
    bbox: list[float],
    min_depth_levels: int = MIN_DEPTH_LEVELS,
    min_max_depth: float = MIN_MAX_DEPTH_M,
) -> list[WODProfile]:
    """
    Download a WOD file and extract all profiles inside *bbox* that pass
    quality filters.

    Parameters
    ----------
    year : int
        Data year (e.g. 2023).
    instrument : str
        One of xbt, gld, ctd, pfl.
    bbox : list[float]
        [west, south, east, north] bounding box.
    min_depth_levels : int
        Minimum number of valid depth/temperature pairs.
    min_max_depth : float
        Profile must reach at least this depth (metres).

    Returns
    -------
    list[WODProfile]
    """
    local_path = download_wod_file(year, instrument)
    ds = xr.open_dataset(local_path, decode_timedelta=False)

    lats = ds["lat"].values
    lons = ds["lon"].values
    n_casts = len(lats)

    # Spatial filter
    west, south, east, north = bbox
    in_bbox = (lats >= south) & (lats <= north) & (lons >= west) & (lons <= east)
    n_bbox = int(in_bbox.sum())
    logger.info(
        "WOD %s %d: %d total casts, %d inside bbox [%.0f,%.0f,%.0f,%.0f]",
        instrument.upper(), year, n_casts, n_bbox, west, south, east, north,
    )
    if n_bbox == 0:
        ds.close()
        return []

    # Pre-compute ragged-array cumulative offsets
    z_rs = ds["z_row_size"].values.astype(int)
    t_rs = ds["Temperature_row_size"].values.astype(int)
    z_cum = np.concatenate([[0], np.cumsum(z_rs)])
    t_cum = np.concatenate([[0], np.cumsum(t_rs)])

    z_all = ds["z"].values
    temp_all = ds["Temperature"].values
    times = ds["time"].values

    # Optional metadata
    cast_ids = ds["wod_unique_cast"].values if "wod_unique_cast" in ds else np.arange(n_casts)
    cruise_ids = ds["WOD_cruise_identifier"].values if "WOD_cruise_identifier" in ds else np.full(n_casts, b"")
    platforms = ds["Platform"].values if "Platform" in ds else np.full(n_casts, b"")

    source_tag = f"WOD_{instrument.upper()}_{year}"
    profiles: list[WODProfile] = []
    skipped_shallow = 0
    skipped_sparse = 0

    for i in np.where(in_bbox)[0]:
        z_start, z_end = z_cum[i], z_cum[i + 1]
        t_start, t_end = t_cum[i], t_cum[i + 1]

        depth_arr = z_all[z_start:z_end]
        temp_arr = temp_all[t_start:t_end]

        # Align: if depth and temp have different lengths, use the shorter
        n_levels = min(len(depth_arr), len(temp_arr))
        if n_levels == 0:
            skipped_sparse += 1
            continue

        depth_arr = depth_arr[:n_levels]
        temp_arr = temp_arr[:n_levels]

        # Remove NaN pairs
        valid = np.isfinite(depth_arr) & np.isfinite(temp_arr)
        depth_clean = depth_arr[valid]
        temp_clean = temp_arr[valid]

        if len(depth_clean) < min_depth_levels:
            skipped_sparse += 1
            continue

        if depth_clean.max() < min_max_depth:
            skipped_shallow += 1
            continue

        # Sort by depth
        order = np.argsort(depth_clean)
        depth_clean = depth_clean[order]
        temp_clean = temp_clean[order]

        # Format time
        try:
            t_val = np.datetime_as_string(times[i], unit="s") + "Z"
        except Exception:
            t_val = str(times[i])

        # Decode bytes metadata
        try:
            cruise_str = cruise_ids[i].decode().strip() if isinstance(cruise_ids[i], bytes) else str(cruise_ids[i])
        except Exception:
            cruise_str = ""
        try:
            platform_str = platforms[i].decode().strip() if isinstance(platforms[i], bytes) else str(platforms[i])
        except Exception:
            platform_str = ""

        profiles.append(WODProfile(
            source=source_tag,
            instrument=instrument,
            cast_id=int(cast_ids[i]),
            cruise_id=cruise_str,
            platform=platform_str,
            lat=float(lats[i]),
            lon=float(lons[i]),
            obs_time=t_val,
            depth_m=depth_clean.tolist(),
            temperature_c=temp_clean.tolist(),
        ))

    ds.close()

    logger.info(
        "  → Extracted %d usable profiles (skipped: %d sparse, %d shallow)",
        len(profiles), skipped_sparse, skipped_shallow,
    )
    return profiles


def extract_all_wod_gom_profiles(
    years: list[int] | None = None,
    instruments: list[str] | None = None,
    bbox: list[float] | None = None,
) -> list[WODProfile]:
    """
    Convenience: download multiple WOD files and extract all GoM profiles.
    """
    if years is None:
        years = [2023, 2024]
    if instruments is None:
        instruments = ["xbt", "gld"]
    if bbox is None:
        bbox = [-98.0, 18.0, -80.0, 31.0]

    all_profiles: list[WODProfile] = []
    for year in years:
        for inst in instruments:
            try:
                profiles = extract_wod_profiles(year, inst, bbox)
                all_profiles.extend(profiles)
            except FileNotFoundError:
                logger.warning("WOD %s %d not available on S3, skipping", inst.upper(), year)
            except Exception as e:
                logger.error("Failed to process WOD %s %d: %s", inst.upper(), year, e)

    logger.info(
        "Total WOD profiles extracted: %d across %d year/instrument combos",
        len(all_profiles), len(years) * len(instruments),
    )
    return all_profiles
