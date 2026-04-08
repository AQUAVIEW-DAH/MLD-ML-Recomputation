"""
MLD ML Data Builder — v3 (Direct Source Ingestion)

Primary training data now comes directly from WOD public S3 bucket
(XBT + Glider profiles), bypassing Aquaview's incomplete index.
Aquaview is no longer used as a primary training data source.

Architecture:
  WOD S3 (XBT/GLD/CTD/PFL/etc.) → download → filter GoM → compute_mld → training_data.csv
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import xarray as xr
import numpy as np
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

from mld_core import compute_mld_temp_threshold
from ML_baseline.argo_gdac_source import extract_argo_gdac_profiles
from ML_baseline.features import extract_ml_features
from ML_baseline.erddap_glider_source import extract_erddap_glider_profiles
from ML_baseline.wod_source import extract_all_wod_gom_profiles, WODProfile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Gulf of Mexico bounding box
GOM_BBOX = [-98.0, 18.0, -80.0, 31.0]

# Multi-day RTOFS snapshot directory
RTOFS_SNAPSHOT_DIR = Path("/data/suramya/rtofs_snapshots")

# WOD data configuration. Override with env vars for source audits, e.g.
#   WOD_INSTRUMENTS=xbt,gld,apb,ctd WOD_YEARS=2023,2024 python ML_baseline/data_builder.py
WOD_YEARS = [int(v) for v in os.getenv("WOD_YEARS", "2023,2024").split(",") if v.strip()]
WOD_INSTRUMENTS = [v.strip().lower() for v in os.getenv("WOD_INSTRUMENTS", "xbt,gld,apb").split(",") if v.strip()]
INCLUDE_ERDDAP_GLIDERS = os.getenv("INCLUDE_ERDDAP_GLIDERS", "0").lower() in {"1", "true", "yes"}
ERDDAP_MAX_DATASETS = int(os.getenv("ERDDAP_MAX_DATASETS", "5"))
INCLUDE_ARGO_GDAC = os.getenv("INCLUDE_ARGO_GDAC", "0").lower() in {"1", "true", "yes"}
ARGO_MAX_PROFILES = int(os.getenv("ARGO_MAX_PROFILES", "25"))
ARGO_MAX_PER_PLATFORM = int(os.getenv("ARGO_MAX_PER_PLATFORM", "5"))
ARGO_START = os.getenv("ARGO_START", "20230101")
ARGO_END = os.getenv("ARGO_END", "20241231")
MAX_OBSERVED_MLD_M = 100.0  # QC cap: remove implausibly deep GoM mixed layers

# Output
OUTPUT_DIR = Path(os.path.dirname(__file__))


def find_nearest_rtofs_snapshot(
    snapshots: dict[str, xr.Dataset],
    obs_time_str: str,
) -> tuple[str, xr.Dataset] | None:
    """
    Find the RTOFS snapshot closest in time to an observation.
    Returns (date_str, dataset) or None if no snapshots are loaded.
    """
    if not snapshots:
        return None

    try:
        obs_dt = np.datetime64(obs_time_str.replace("Z", ""))
    except Exception:
        # Fall back to first available snapshot
        first_key = next(iter(snapshots))
        return first_key, snapshots[first_key]

    best_key = None
    best_delta = None

    for date_str, ds in snapshots.items():
        snap_dt = np.datetime64(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}")
        delta = abs(obs_dt - snap_dt)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_key = date_str

    if best_key is None:
        return None
    return best_key, snapshots[best_key]


def extract_date_from_filename(filepath: Path) -> str:
    """Extract YYYYMMDD from filenames like rtofs_20260401_US_east.nc"""
    stem = filepath.stem
    parts = stem.split("_")
    for part in parts:
        if len(part) == 8 and part.isdigit():
            return part
    raise ValueError(f"Cannot extract date from {filepath.name}")


def source_family(source: str) -> str:
    if str(source).startswith("WOD_"):
        return "WOD"
    if str(source).startswith("ERDDAP_GLIDER_"):
        return "ERDDAP_GLIDER"
    if str(source).startswith("ARGO_GDAC"):
        return "ARGO_GDAC"
    return "UNKNOWN"


def build_dataset():
    logger.info("=" * 60)
    logger.info("MLD ML Data Builder — v3 (Direct Source Ingestion)")
    logger.info("=" * 60)

    # ---------------------------------------------------------------
    # STEP 1: Load RTOFS snapshots into memory
    # ---------------------------------------------------------------
    snapshot_files = sorted(RTOFS_SNAPSHOT_DIR.glob("rtofs_*_US_east.nc"))
    if not snapshot_files:
        logger.error(f"No RTOFS snapshots found in {RTOFS_SNAPSHOT_DIR}")
        return

    logger.info(f"Loading {len(snapshot_files)} RTOFS daily snapshots...")
    snapshots: dict[str, xr.Dataset] = {}
    for f in snapshot_files:
        date_str = extract_date_from_filename(f)
        try:
            snapshots[date_str] = xr.open_dataset(f)
            model_time = str(snapshots[date_str]["MT"].isel(MT=0).values)
            logger.info(f"  → {f.name} (model time: {model_time})")
        except Exception as e:
            logger.error(f"  Failed to open {f.name}: {e}")

    if not snapshots:
        logger.error("No RTOFS snapshots loaded — cannot compute features")
        return
    logger.info(
        "Phase 5 choice: WOD observations are temporally decoupled from the "
        "available 2026 RTOFS snapshots; selecting the nearest available "
        "snapshot for spatial/physical feature extraction."
    )
    logger.info(
        "Source strategy: bypassing Aquaview for training labels; using direct "
        "provider ingestion. WOD years=%s instruments=%s ERDDAP gliders=%s max_datasets=%s",
        WOD_YEARS,
        WOD_INSTRUMENTS,
        INCLUDE_ERDDAP_GLIDERS,
        ERDDAP_MAX_DATASETS,
    )
    logger.info(
        "Argo GDAC direct ingestion enabled=%s max_profiles=%s max_per_platform=%s date=%s/%s",
        INCLUDE_ARGO_GDAC,
        ARGO_MAX_PROFILES,
        ARGO_MAX_PER_PLATFORM,
        ARGO_START,
        ARGO_END,
    )

    # ---------------------------------------------------------------
    # STEP 2: Download & extract WOD profiles from S3
    # ---------------------------------------------------------------
    logger.info("")
    logger.info("=" * 60)
    logger.info("PASS 1: WOD S3 Direct Source")
    logger.info("=" * 60)

    wod_profiles = extract_all_wod_gom_profiles(
        years=WOD_YEARS,
        instruments=WOD_INSTRUMENTS,
        bbox=GOM_BBOX,
    )

    all_profiles = list(wod_profiles)
    logger.info(f"Total WOD profiles to process: {len(wod_profiles)}")

    if INCLUDE_ERDDAP_GLIDERS:
        logger.info("")
        logger.info("=" * 60)
        logger.info("PASS 2: Direct ERDDAP Glider Sources")
        logger.info("=" * 60)
        erddap_profiles = extract_erddap_glider_profiles(
            bbox=GOM_BBOX,
            max_datasets=ERDDAP_MAX_DATASETS,
        )
        all_profiles.extend(erddap_profiles)
        logger.info("Total ERDDAP glider profiles to process: %d", len(erddap_profiles))
    else:
        logger.info("Skipping ERDDAP glider ingestion; set INCLUDE_ERDDAP_GLIDERS=1 to enable.")

    if INCLUDE_ARGO_GDAC:
        logger.info("")
        logger.info("=" * 60)
        logger.info("PASS 3: Direct Argo GDAC Sources")
        logger.info("=" * 60)
        argo_profiles = extract_argo_gdac_profiles(
            bbox=GOM_BBOX,
            start_yyyymmdd=ARGO_START,
            end_yyyymmdd=ARGO_END,
            max_profiles=ARGO_MAX_PROFILES,
            max_per_platform=ARGO_MAX_PER_PLATFORM,
        )
        all_profiles.extend(argo_profiles)
        logger.info("Total Argo GDAC profiles to process: %d", len(argo_profiles))
    else:
        logger.info("Skipping Argo GDAC ingestion; set INCLUDE_ARGO_GDAC=1 to enable.")

    logger.info("Total direct-source profiles to process: %d", len(all_profiles))

    # ---------------------------------------------------------------
    # STEP 3: For each direct-source profile, compute observed MLD + model features
    # ---------------------------------------------------------------
    dataset_rows = []
    total_mld_computed = 0
    total_features_extracted = 0
    skipped_no_mld = 0
    skipped_outlier_mld = 0
    skipped_no_features = 0

    for idx, profile in enumerate(all_profiles):
        if idx > 0 and idx % 100 == 0:
            logger.info(
                f"  Processing profile {idx}/{len(all_profiles)} "
                f"(MLD computed: {total_mld_computed}, features: {total_features_extracted})"
            )

        # Compute observed MLD from the WOD profile
        obs_mld = compute_mld_temp_threshold(profile.depth_m, profile.temperature_c)
        if obs_mld is None:
            skipped_no_mld += 1
            continue
        if obs_mld > MAX_OBSERVED_MLD_M:
            skipped_outlier_mld += 1
            logger.warning(
                "Dropping observed-MLD outlier cast_id=%s source=%s instrument=%s "
                "observed_mld=%.2fm max_depth=%.1fm platform=%s",
                profile.cast_id,
                profile.source,
                profile.instrument,
                obs_mld,
                max(profile.depth_m),
                profile.platform or profile.cruise_id or "unknown",
            )
            continue
        total_mld_computed += 1

        # Find nearest RTOFS snapshot and extract model features
        match = find_nearest_rtofs_snapshot(snapshots, profile.obs_time)
        if match is None:
            skipped_no_features += 1
            continue
        rtofs_date, rtofs_ds = match

        feat = extract_ml_features(rtofs_ds, profile.lat, profile.lon)
        if feat is None:
            skipped_no_features += 1
            continue
        total_features_extracted += 1

        dataset_rows.append({
            "rtofs_date": rtofs_date,
            "wod_source": profile.source,
            "source_family": source_family(profile.source),
            "instrument": profile.instrument,
            "cast_id": profile.cast_id,
            "cruise_id": profile.cruise_id,
            "platform_id": profile.platform or profile.cruise_id or f"wod_{profile.cast_id}",
            "data_type": "depth_profile",
            "lat": round(profile.lat, 4),
            "lon": round(profile.lon, 4),
            "obs_time": profile.obs_time,
            "n_depth_levels": len(profile.depth_m),
            "max_depth_m": round(max(profile.depth_m), 1),
            "model_sst": round(feat.model_sst, 4),
            "sst_gradient": round(feat.sst_gradient, 6),
            "model_salinity": round(feat.model_salinity, 4),
            "kinetic_energy": round(feat.kinetic_energy, 6),
            "model_mld": round(feat.model_mld, 4),
            "observed_mld": round(obs_mld, 4),
            "target_delta_mld": round(obs_mld - feat.model_mld, 4),
        })

    logger.info("")
    logger.info(f"Direct-source processing summary:")
    logger.info(f"  Profiles with valid MLD: {total_mld_computed}")
    logger.info(f"  Features extracted: {total_features_extracted}")
    logger.info(f"  Skipped (no MLD computable): {skipped_no_mld}")
    logger.info(f"  Skipped (observed MLD > {MAX_OBSERVED_MLD_M:.0f}m sanity cap): {skipped_outlier_mld}")
    logger.info(f"  Skipped (no RTOFS features): {skipped_no_features}")

    # ---------------------------------------------------------------
    # STEP 4: Save results
    # ---------------------------------------------------------------
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"Total training rows: {len(dataset_rows)}")
    logger.info("=" * 60)

    out_path = OUTPUT_DIR / "training_data.csv"
    df = pd.DataFrame(dataset_rows)
    df.to_csv(out_path, index=False)
    logger.info(f"Saved training data to: {out_path}")

    if len(df) > 0:
        logger.info(f"\nProvenance Summary:")
        logger.info(f"  Sources: {df['wod_source'].value_counts().to_dict()}")
        logger.info(f"  Source families: {df['source_family'].value_counts().to_dict()}")
        logger.info(f"  Instruments: {df['instrument'].value_counts().to_dict()}")
        logger.info(f"  Unique platforms: {df['platform_id'].nunique()}")
        logger.info(f"  Lat range: {df['lat'].min():.2f} to {df['lat'].max():.2f}")
        logger.info(f"  Lon range: {df['lon'].min():.2f} to {df['lon'].max():.2f}")
        logger.info(f"  Observed MLD range: {df['observed_mld'].min():.1f} to {df['observed_mld'].max():.1f} m")
        logger.info(f"  Model MLD range: {df['model_mld'].min():.1f} to {df['model_mld'].max():.1f} m")
        logger.info(f"  Target delta range: {df['target_delta_mld'].min():.1f} to {df['target_delta_mld'].max():.1f} m")
    else:
        logger.warning("No training rows generated!")

    # Close RTOFS datasets
    for ds in snapshots.values():
        ds.close()


if __name__ == "__main__":
    build_dataset()
