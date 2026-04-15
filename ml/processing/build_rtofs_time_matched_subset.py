"""
Build a small time-coincident RTOFS training subset from already-ingested profiles.

This is a smoke-test bridge, not the final production builder. It reuses the
observed MLD labels in training_data.csv, downloads same-date public RTOFS files
found by rtofs_temporal_audit.py, recomputes the model-side features, and writes
a separate CSV so the temporally decoupled baseline is not overwritten.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.features import extract_ml_features
from ml.paths import AUDITS_DIR, DATASETS_DIR


logger = logging.getLogger(__name__)

DEFAULT_TRAINING_CSV = DATASETS_DIR / "training_data.csv"
DEFAULT_AUDIT_CSV = AUDITS_DIR / "rtofs_temporal_audit.csv"
DEFAULT_OUTPUT_CSV = DATASETS_DIR / "training_data_rtofs_time_matched_smoke.csv"
DEFAULT_CACHE_DIR = Path("/data/suramya/rtofs_time_matched")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-csv", type=Path, default=DEFAULT_TRAINING_CSV)
    parser.add_argument("--audit-csv", type=Path, default=DEFAULT_AUDIT_CSV)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def download_rtofs(url: str, cache_dir: Path, timeout: float) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = Path(urlparse(url).path.lstrip("/"))
    if len(parsed_path.parts) >= 2:
        local_path = cache_dir / parsed_path.parts[-2] / parsed_path.name
    else:
        local_path = cache_dir / parsed_path.name
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if local_path.exists() and local_path.stat().st_size > 0:
        logger.info("Using cached RTOFS file: %s", local_path)
        return local_path

    logger.info("Downloading %s -> %s", url, local_path)
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        tmp_path = local_path.with_suffix(local_path.suffix + ".tmp")
        with tmp_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        tmp_path.replace(local_path)
    return local_path


def model_valid_time(ds: xr.Dataset) -> pd.Timestamp | None:
    if "MT" not in ds:
        return None
    value = ds["MT"].isel(MT=0).values
    return pd.Timestamp(value).tz_localize("UTC")


def build_subset() -> None:
    args = parse_args()
    df = pd.read_csv(args.training_csv, parse_dates=["obs_time"])
    audit = pd.read_csv(args.audit_csv)

    df["obs_date"] = df["obs_time"].dt.strftime("%Y%m%d")
    available = audit.loc[audit["s3_current_pattern_available"], ["obs_date", "s3_example_url"]]
    if available.empty:
        logger.error("No S3-available dates found in %s. Run rtofs_temporal_audit.py --check-s3 first.", args.audit_csv)
        return

    url_by_date = dict(zip(available["obs_date"].astype(str), available["s3_example_url"]))
    subset = df[df["obs_date"].isin(url_by_date)].copy()
    logger.info("Building same-date subset from %d rows across %d dates.", len(subset), subset["obs_date"].nunique())

    rows = []
    skipped_no_features = 0
    for obs_date, group in subset.groupby("obs_date"):
        rtofs_url = url_by_date[str(obs_date)]
        rtofs_path = download_rtofs(rtofs_url, args.cache_dir, args.timeout)
        ds = xr.open_dataset(rtofs_path)
        valid_time = model_valid_time(ds)

        try:
            for _, row in group.iterrows():
                feat = extract_ml_features(ds, float(row["lat"]), float(row["lon"]))
                if feat is None:
                    skipped_no_features += 1
                    continue

                out = row.to_dict()
                out["rtofs_date"] = str(obs_date)
                out["rtofs_valid_time"] = valid_time.isoformat() if valid_time is not None else ""
                out["rtofs_source"] = rtofs_url
                out["forecast_lead_hours"] = 6
                if valid_time is not None:
                    out["obs_model_time_delta_hours"] = round(
                        abs((row["obs_time"] - valid_time).total_seconds()) / 3600.0,
                        3,
                    )
                else:
                    out["obs_model_time_delta_hours"] = ""
                out["model_sst"] = round(feat.model_sst, 4)
                out["sst_gradient"] = round(feat.sst_gradient, 6)
                out["model_salinity"] = round(feat.model_salinity, 4)
                out["kinetic_energy"] = round(feat.kinetic_energy, 6)
                out["model_mld"] = round(feat.model_mld, 4)
                out["target_delta_mld"] = round(float(row["observed_mld"]) - feat.model_mld, 4)
                rows.append(out)
        finally:
            ds.close()

    out_df = pd.DataFrame(rows)
    out_df.to_csv(args.output_csv, index=False)
    logger.info("Wrote %d time-matched rows to %s", len(out_df), args.output_csv)
    logger.info("Skipped rows with no RTOFS features: %d", skipped_no_features)
    if not out_df.empty:
        logger.info("Source families: %s", out_df["source_family"].value_counts().to_dict())
        logger.info("Platforms: %d", out_df["platform_id"].nunique())
        logger.info(
            "Obs/model time delta hours: min=%.2f median=%.2f max=%.2f",
            out_df["obs_model_time_delta_hours"].min(),
            out_df["obs_model_time_delta_hours"].median(),
            out_df["obs_model_time_delta_hours"].max(),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    build_subset()
