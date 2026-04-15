"""
Audit RTOFS/in-situ temporal overlap before rebuilding the training dataset.

This script intentionally does not download RTOFS fields. It answers the first
planning question: which observation dates would have same-day RTOFS candidates
locally and/or in the public NOAA RTOFS S3 bucket using the current product key
pattern.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.paths import AUDITS_DIR, DATASETS_DIR, SOURCE_REPORTS_DIR

logger = logging.getLogger(__name__)

DEFAULT_TRAINING_CSV = DATASETS_DIR / "training_data.csv"
DEFAULT_RTOFS_DIR = Path("/data/suramya/rtofs_snapshots")
DEFAULT_REPORT = SOURCE_REPORTS_DIR / "rtofs_temporal_audit.md"
DEFAULT_CSV = AUDITS_DIR / "rtofs_temporal_audit.csv"
RTOFS_S3_BASE = "https://noaa-nws-rtofs-pds.s3.amazonaws.com"
DEFAULT_LEADS = (6, 12, 18, 24)
OBSERVED_PUBLIC_BUCKET_START = "2024-01-27"


@dataclass(frozen=True)
class S3Check:
    available: bool
    url: str | None
    status_code: int | None
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-csv", type=Path, default=DEFAULT_TRAINING_CSV)
    parser.add_argument("--rtofs-dir", type=Path, default=DEFAULT_RTOFS_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check-s3", action="store_true", help="Probe NOAA RTOFS S3 keys with HEAD requests.")
    parser.add_argument("--max-s3-dates", type=int, default=0, help="Limit S3 probes; 0 checks all observation dates.")
    parser.add_argument("--leads", default="6,12,18,24", help="Comma-separated forecast lead hours to probe.")
    parser.add_argument("--timeout", type=float, default=10.0)
    return parser.parse_args()


def local_rtofs_dates(rtofs_dir: Path) -> set[str]:
    dates: set[str] = set()
    for path in rtofs_dir.glob("rtofs_*_US_east.nc"):
        parts = path.stem.split("_")
        dates.update(part for part in parts if len(part) == 8 and part.isdigit())
    return dates


def format_rtofs_key(date_yyyymmdd: str, lead_hour: int) -> str:
    return f"rtofs.{date_yyyymmdd}/rtofs_glo_3dz_f{lead_hour:03d}_6hrly_hvr_US_east.nc"


def check_s3_date(date_yyyymmdd: str, leads: Iterable[int], timeout: float) -> S3Check:
    last_status = None
    last_url = None
    for lead in leads:
        key = format_rtofs_key(date_yyyymmdd, lead)
        url = f"{RTOFS_S3_BASE}/{key}"
        last_url = url
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
        except requests.RequestException as exc:
            return S3Check(False, url, last_status, str(exc))

        last_status = response.status_code
        if response.status_code == 200:
            return S3Check(True, url, response.status_code)

    return S3Check(False, last_url, last_status)


def value_counts_dict(values: pd.Series) -> dict[str, int]:
    return {str(key): int(value) for key, value in values.value_counts().items()}


def date_window_match(obs_dates: pd.Series, available_dates: set[str], tolerance_hours: int) -> pd.Series:
    tolerance_days = max(0, tolerance_hours // 24)
    matches = []
    for obs_date in pd.to_datetime(obs_dates, format="%Y%m%d"):
        matched = False
        for day_offset in range(-tolerance_days, tolerance_days + 1):
            candidate = (obs_date + timedelta(days=day_offset)).strftime("%Y%m%d")
            if candidate in available_dates:
                matched = True
                break
        matches.append(matched)
    return pd.Series(matches, index=obs_dates.index)


def write_report(
    report_path: Path,
    df: pd.DataFrame,
    date_df: pd.DataFrame,
    local_dates: set[str],
    s3_checked: bool,
) -> None:
    source_counts = df["source_family"].value_counts().to_dict()
    year_counts = df["obs_year"].value_counts().sort_index().to_dict()
    local_same_day_rows = int(df["local_same_day_rtofs"].sum())
    local_24h_rows = int(df["local_24h_rtofs"].sum())

    with report_path.open("w") as f:
        f.write("# RTOFS / In-Situ Temporal Matching Audit\n\n")
        f.write("## Summary\n")
        f.write(f"- Training rows audited: {len(df)}\n")
        f.write(f"- Observation date range: {df['obs_time'].min()} to {df['obs_time'].max()}\n")
        f.write(f"- Observation years: {year_counts}\n")
        f.write(f"- Source families: {source_counts}\n")
        f.write(f"- Unique observation dates: {df['obs_date'].nunique()}\n")
        f.write(f"- Local RTOFS dates available: {sorted(local_dates)}\n")
        f.write(f"- Rows with same-day local RTOFS: {local_same_day_rows}\n")
        f.write(f"- Rows with +/-24h local RTOFS: {local_24h_rows}\n")
        if s3_checked:
            s3_available_dates = int(date_df["s3_current_pattern_available"].sum())
            s3_rows = int(df["s3_current_pattern_available"].sum())
            f.write(f"- NOAA S3 current-pattern dates available: {s3_available_dates}\n")
            f.write(f"- Rows with NOAA S3 current-pattern same-day availability: {s3_rows}\n")
            f.write(f"- Observed public RTOFS bucket start from prefix listing: {OBSERVED_PUBLIC_BUCKET_START}\n")
        else:
            f.write("- NOAA S3 current-pattern availability: not checked in this run\n")

        f.write("\n## Interpretation\n")
        f.write(
            "- The current local RTOFS cache is a 2026 window, so same-day matches are expected "
            "to be zero for the present 2015/2023/2024 in-situ table.\n"
        )
        f.write(
            "- NOAA S3 current-pattern availability is partial for this table. If the dense "
            "observation blocks are unavailable, the current public operational bucket is not a "
            "sufficient historical archive by itself; we should search NCEI/NOMADS archives or "
            "use a forward-rolling collector/reanalysis fallback.\n"
        )
        f.write(
            "- In this audit, the public bucket covers the sparse 2024 WOD rows but not the dense "
            "2023 WOD block or the 2015 ERDDAP glider smoke-test deployment.\n"
        )
        f.write(
            "- Do not combine this temporally decoupled smoke-test dataset with a future "
            "time-coincident benchmark as if they were equivalent validation evidence.\n"
        )

        if s3_checked:
            f.write("\n## NOAA S3 Same-Day Matches\n\n")
            f.write("| Date | Rows | Source families | Example S3 URL |\n")
            f.write("| :--- | ---: | :--- | :--- |\n")
            available_rows = date_df[date_df["s3_current_pattern_available"]].sort_values("obs_date")
            for _, row in available_rows.iterrows():
                f.write(
                    f"| {row['obs_date']} | {int(row['rows'])} | "
                    f"{row['source_families']} | {row.get('s3_example_url', '') or ''} |\n"
                )

        f.write("\n## Top Observation Dates\n\n")
        f.write("| Date | Rows | Source families | Local same-day | S3 current-pattern | Example S3 URL |\n")
        f.write("| :--- | ---: | :--- | :--- | :--- | :--- |\n")
        for _, row in date_df.head(25).iterrows():
            f.write(
                f"| {row['obs_date']} | {int(row['rows'])} | {row['source_families']} | "
                f"{row['local_same_day_rtofs']} | {row.get('s3_current_pattern_available', 'not_checked')} | "
                f"{row.get('s3_example_url', '') or ''} |\n"
            )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    leads = [int(value.strip()) for value in args.leads.split(",") if value.strip()]

    df = pd.read_csv(args.training_csv, parse_dates=["obs_time"])
    df["obs_date"] = df["obs_time"].dt.strftime("%Y%m%d")
    df["obs_year"] = df["obs_time"].dt.year

    local_dates = local_rtofs_dates(args.rtofs_dir)
    df["local_same_day_rtofs"] = df["obs_date"].isin(local_dates)
    df["local_24h_rtofs"] = date_window_match(df["obs_date"], local_dates, tolerance_hours=24)

    date_df = (
        df.groupby("obs_date")
        .agg(
            rows=("obs_date", "size"),
            source_families=("source_family", value_counts_dict),
            local_same_day_rtofs=("local_same_day_rtofs", "any"),
            local_24h_rtofs=("local_24h_rtofs", "any"),
        )
        .reset_index()
        .sort_values(["rows", "obs_date"], ascending=[False, True])
    )

    if args.check_s3:
        s3_limit = None if args.max_s3_dates <= 0 else args.max_s3_dates
        dates_to_check = date_df["obs_date"].tolist()[:s3_limit]
        checks: dict[str, S3Check] = {}
        for index, obs_date in enumerate(dates_to_check, start=1):
            if index % 25 == 0:
                logger.info("Checked %d/%d S3 dates...", index, len(dates_to_check))
            checks[obs_date] = check_s3_date(obs_date, leads, args.timeout)

        date_df["s3_current_pattern_available"] = date_df["obs_date"].map(
            lambda value: checks[value].available if value in checks else False
        )
        date_df["s3_status_code"] = date_df["obs_date"].map(
            lambda value: checks[value].status_code if value in checks else None
        )
        date_df["s3_example_url"] = date_df["obs_date"].map(
            lambda value: checks[value].url if value in checks else None
        )
        date_df["s3_error"] = date_df["obs_date"].map(
            lambda value: checks[value].error if value in checks else None
        )
        available_s3_dates = set(date_df.loc[date_df["s3_current_pattern_available"], "obs_date"])
        df["s3_current_pattern_available"] = df["obs_date"].isin(available_s3_dates)
    else:
        df["s3_current_pattern_available"] = False

    date_df.to_csv(args.output_csv, index=False)
    write_report(args.output_report, df, date_df, local_dates, args.check_s3)

    logger.info("Rows audited: %d", len(df))
    logger.info("Unique observation dates: %d", df["obs_date"].nunique())
    logger.info("Local same-day RTOFS rows: %d", int(df["local_same_day_rtofs"].sum()))
    logger.info("Local +/-24h RTOFS rows: %d", int(df["local_24h_rtofs"].sum()))
    if args.check_s3:
        logger.info(
            "NOAA S3 current-pattern same-day dates: %d",
            int(date_df["s3_current_pattern_available"].sum()),
        )
    logger.info("Wrote %s", args.output_csv)
    logger.info("Wrote %s", args.output_report)


if __name__ == "__main__":
    main()
