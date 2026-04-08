"""
Explore and build a same-day RTOFS dataset from Argo GDAC 2024+2025 GoM profiles.

This is separate from data_builder.py and never overwrites training_data.csv.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import xarray as xr

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from mld_core import compute_mld_temp_threshold
from ML_baseline.argo_gdac_source import ArgoGDACProfile, extract_argo_gdac_profiles, matching_index_files
from ML_baseline.build_rtofs_time_matched_subset import download_rtofs, model_valid_time
from ML_baseline.features import extract_ml_features
from ML_baseline.rtofs_temporal_audit import check_s3_date


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PROFILE_CSV = BASE_DIR / "argo_gdac_2024_2025_profile_audit.csv"
DEFAULT_TRAINING_CSV = BASE_DIR / "training_data_argo_gdac_rtofs_2024_2025.csv"
DEFAULT_REPORT = BASE_DIR / "ARGO_GDAC_RTOFS_2024_2025_REPORT.md"
DEFAULT_RTOFS_CACHE_DIR = Path("/data/suramya/rtofs_time_matched")
GOM_BBOX = [-98.0, 18.0, -80.0, 31.0]
MAX_OBSERVED_MLD_M = 100.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="20240101")
    parser.add_argument("--end", default="20251231")
    parser.add_argument("--bbox", default="-98,18,-80,31")
    parser.add_argument("--max-profiles", type=int, default=0, help="0 means no cap.")
    parser.add_argument("--max-per-platform", type=int, default=0, help="0 means no cap.")
    parser.add_argument("--profile-csv", type=Path, default=DEFAULT_PROFILE_CSV)
    parser.add_argument("--training-csv", type=Path, default=DEFAULT_TRAINING_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--rtofs-cache-dir", type=Path, default=DEFAULT_RTOFS_CACHE_DIR)
    parser.add_argument("--skip-rtofs-download", action="store_true")
    parser.add_argument("--max-rtofs-dates", type=int, default=0, help="0 uses every RTOFS-eligible date.")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--s3-timeout", type=float, default=10.0)
    parser.add_argument("--leads", default="6,12,18,24")
    return parser.parse_args()


def profile_key(profile: ArgoGDACProfile) -> str:
    return f"{profile.cast_id}|{profile.obs_time}|{profile.lat:.5f}|{profile.lon:.5f}"


def profile_records(profiles: list[ArgoGDACProfile]) -> pd.DataFrame:
    records = []
    for profile in profiles:
        obs_mld = compute_mld_temp_threshold(profile.depth_m, profile.temperature_c)
        obs_time = pd.Timestamp(profile.obs_time)
        records.append(
            {
                "source": profile.source,
                "instrument": profile.instrument,
                "profile_key": profile_key(profile),
                "cast_id": profile.cast_id,
                "cruise_id": profile.cruise_id,
                "platform_id": profile.platform or profile.cruise_id,
                "lat": round(profile.lat, 5),
                "lon": round(profile.lon, 5),
                "obs_time": profile.obs_time,
                "obs_date": obs_time.strftime("%Y%m%d"),
                "obs_year": int(obs_time.year),
                "n_depth_levels": len(profile.depth_m),
                "min_depth_m": round(float(min(profile.depth_m)), 3),
                "max_depth_m": round(float(max(profile.depth_m)), 3),
                "observed_mld": round(obs_mld, 4) if obs_mld is not None else "",
                "temp_mld_ref10": obs_mld is not None,
                "temp_mld_ref10_under100m": obs_mld is not None and obs_mld <= MAX_OBSERVED_MLD_M,
            }
        )
    return pd.DataFrame(records)


def add_rtofs_availability(df: pd.DataFrame, leads: list[int], timeout: float) -> dict[str, str]:
    urls_by_date: dict[str, str] = {}
    for index, obs_date in enumerate(sorted(df["obs_date"].unique()), start=1):
        if index == 1 or index % 50 == 0:
            logger.info("Checking RTOFS S3 availability for date %d/%d", index, df["obs_date"].nunique())
        check = check_s3_date(str(obs_date), leads=leads, timeout=timeout)
        if check.available and check.url:
            urls_by_date[str(obs_date)] = check.url
    df["same_day_rtofs_s3_available"] = df["obs_date"].astype(str).isin(urls_by_date)
    df["rtofs_s3_url"] = df["obs_date"].astype(str).map(urls_by_date).fillna("")
    return urls_by_date


def build_training_rows(
    eligible: pd.DataFrame,
    urls_by_date: dict[str, str],
    cache_dir: Path,
    timeout: float,
) -> tuple[pd.DataFrame, int]:
    rows = []
    skipped_no_features = 0
    for index, (obs_date, group) in enumerate(eligible.groupby("obs_date"), start=1):
        logger.info("Extracting RTOFS features for date %d/%d: %s (%d profiles)", index, eligible["obs_date"].nunique(), obs_date, len(group))
        url = urls_by_date.get(str(obs_date))
        if not url:
            continue
        rtofs_path = download_rtofs(url, cache_dir, timeout)
        ds = xr.open_dataset(rtofs_path)
        valid_time = model_valid_time(ds)
        try:
            for _, row in group.iterrows():
                feat = extract_ml_features(ds, float(row["lat"]), float(row["lon"]))
                if feat is None:
                    skipped_no_features += 1
                    continue
                out = {
                    "rtofs_date": str(obs_date),
                    "wod_source": row["source"],
                    "source_family": "ARGO_GDAC",
                    "instrument": row["instrument"],
                    "cast_id": row["cast_id"],
                    "cruise_id": row["cruise_id"],
                    "platform_id": row["platform_id"],
                    "data_type": "depth_profile",
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "obs_time": row["obs_time"],
                    "n_depth_levels": row["n_depth_levels"],
                    "max_depth_m": row["max_depth_m"],
                    "model_sst": round(feat.model_sst, 4),
                    "sst_gradient": round(feat.sst_gradient, 6),
                    "model_salinity": round(feat.model_salinity, 4),
                    "kinetic_energy": round(feat.kinetic_energy, 6),
                    "model_mld": round(feat.model_mld, 4),
                    "observed_mld": row["observed_mld"],
                    "target_delta_mld": round(float(row["observed_mld"]) - feat.model_mld, 4),
                    "obs_date": str(obs_date),
                    "rtofs_valid_time": valid_time.isoformat() if valid_time is not None else "",
                    "rtofs_source": url,
                    "forecast_lead_hours": int(url.split("_f")[-1].split("_")[0]) if "_f" in url else "",
                }
                if valid_time is not None:
                    out["obs_model_time_delta_hours"] = round(
                        abs((pd.Timestamp(row["obs_time"]) - valid_time).total_seconds()) / 3600.0,
                        3,
                    )
                else:
                    out["obs_model_time_delta_hours"] = ""
                rows.append(out)
        finally:
            ds.close()
    return pd.DataFrame(rows), skipped_no_features


def count_cells(df: pd.DataFrame, degree: float) -> int:
    if df.empty:
        return 0
    lat_cell = (df["lat"].astype(float) // degree) * degree
    lon_cell = (df["lon"].astype(float) // degree) * degree
    return int(pd.DataFrame({"lat": lat_cell, "lon": lon_cell}).drop_duplicates().shape[0])


def top_counts(series: pd.Series, limit: int = 12) -> dict[str, int]:
    return {str(k): int(v) for k, v in series.value_counts().head(limit).items()}


def write_report(
    path: Path,
    index_file_count: int,
    profile_df: pd.DataFrame,
    training_df: pd.DataFrame,
    skipped_no_features: int,
    max_rtofs_dates: int,
) -> None:
    eligible = profile_df[profile_df["temp_mld_ref10_under100m"]]
    rtofs_eligible = eligible[eligible["same_day_rtofs_s3_available"]]
    with path.open("w") as f:
        f.write("# Argo GDAC 2024-2025 Same-Day RTOFS Audit\n\n")
        f.write("## Summary\n")
        f.write(f"- Argo index profile-file matches in GoM/date window: {index_file_count}\n")
        f.write(f"- Argo GDAC profiles extracted after 10m/profile QC: {len(profile_df)}\n")
        f.write(f"- Profiles with 10m temperature-threshold MLD <= {MAX_OBSERVED_MLD_M:.0f}m: {len(eligible)}\n")
        f.write(f"- Eligible profiles with same-day public RTOFS S3 file: {len(rtofs_eligible)}\n")
        f.write(f"- Rows with RTOFS features extracted: {len(training_df)}\n")
        f.write(f"- RTOFS feature extraction skips: {skipped_no_features}\n")
        if max_rtofs_dates:
            f.write(f"- RTOFS feature extraction date cap: top {max_rtofs_dates} dates by platform count, then row count\n")
        if not profile_df.empty:
            f.write(f"- Observation date range: {profile_df['obs_time'].min()} to {profile_df['obs_time'].max()}\n")
            f.write(f"- Platforms in extracted profiles: {profile_df['platform_id'].nunique()}\n")
            f.write(f"- Extracted platform counts: {top_counts(profile_df['platform_id'])}\n")
        if not training_df.empty:
            f.write(f"- Training date range: {training_df['obs_time'].min()} to {training_df['obs_time'].max()}\n")
            f.write(f"- Training platforms: {training_df['platform_id'].nunique()}\n")
            f.write(f"- Training 0.25-degree cells: {count_cells(training_df, 0.25)}\n")
            f.write(f"- Training 0.5-degree cells: {count_cells(training_df, 0.5)}\n")
            f.write(f"- Training 1.0-degree cells: {count_cells(training_df, 1.0)}\n")
            f.write(f"- Training platform counts: {top_counts(training_df['platform_id'])}\n")

        f.write("\n## By Year\n\n")
        f.write("| Year | Extracted | MLD <=100m | Same-day RTOFS eligible | RTOFS feature rows |\n")
        f.write("| ---: | ---: | ---: | ---: | ---: |\n")
        for year in sorted(profile_df["obs_year"].unique()) if not profile_df.empty else []:
            year_profiles = profile_df[profile_df["obs_year"] == year]
            year_eligible = year_profiles[year_profiles["temp_mld_ref10_under100m"]]
            year_rtofs = year_eligible[year_eligible["same_day_rtofs_s3_available"]]
            year_training = training_df[pd.to_datetime(training_df["obs_time"]).dt.year == year] if not training_df.empty else training_df
            f.write(
                f"| {year} | {len(year_profiles)} | {len(year_eligible)} | "
                f"{len(year_rtofs)} | {len(year_training)} |\n"
            )

        f.write("\n## Top Dates For RTOFS-Eligible Profiles\n\n")
        f.write("| Date | Rows | Platforms |\n")
        f.write("| :--- | ---: | :--- |\n")
        if not rtofs_eligible.empty:
            for obs_date, group in rtofs_eligible.groupby("obs_date").size().sort_values(ascending=False).head(30).items():
                date_rows = rtofs_eligible[rtofs_eligible["obs_date"] == obs_date]
                f.write(f"| {obs_date} | {int(group)} | {top_counts(date_rows['platform_id'], limit=8)} |\n")

        f.write("\n## Interpretation\n")
        f.write(
            "- This is a same-day RTOFS residual dataset candidate and should stay separate "
            "from the temporally decoupled main training CSV.\n"
        )
        f.write(
            "- Argo profiles include salinity in the original files, but this first pass uses "
            "the existing temperature-threshold label path for consistency with WOD XBT.\n"
        )
        f.write(
            "- Compare platform/cell coverage against WOD XBT before deciding whether to merge "
            "same-day source families for a combined benchmark.\n"
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    bbox = [float(value.strip()) for value in args.bbox.split(",") if value.strip()]
    leads = [int(value.strip()) for value in args.leads.split(",") if value.strip()]

    index_files = matching_index_files(
        bbox=bbox,
        start_yyyymmdd=args.start,
        end_yyyymmdd=args.end,
        max_profiles=args.max_profiles,
        max_per_platform=args.max_per_platform,
    )
    profiles = extract_argo_gdac_profiles(
        bbox=bbox,
        start_yyyymmdd=args.start,
        end_yyyymmdd=args.end,
        max_profiles=args.max_profiles,
        max_per_platform=args.max_per_platform,
    )
    profile_df = profile_records(profiles)
    urls_by_date = add_rtofs_availability(profile_df, leads=leads, timeout=args.s3_timeout) if not profile_df.empty else {}
    profile_df.to_csv(args.profile_csv, index=False)

    eligible = profile_df[
        profile_df["temp_mld_ref10_under100m"] & profile_df["same_day_rtofs_s3_available"]
    ].copy() if not profile_df.empty else pd.DataFrame()
    if args.max_rtofs_dates and not eligible.empty:
        top_dates = (
            eligible.groupby("obs_date")
            .agg(rows=("source", "size"), platforms=("platform_id", "nunique"))
            .sort_values(["platforms", "rows"], ascending=False)
            .head(args.max_rtofs_dates)
            .index
        )
        eligible = eligible[eligible["obs_date"].isin(top_dates)].copy()
        logger.info("Limited RTOFS feature extraction to %d top dates and %d profiles.", len(top_dates), len(eligible))

    if args.skip_rtofs_download:
        training_df = pd.DataFrame()
        skipped_no_features = 0
    else:
        training_df, skipped_no_features = build_training_rows(eligible, urls_by_date, args.rtofs_cache_dir, args.timeout)
        training_df.to_csv(args.training_csv, index=False)

    write_report(args.report, len(index_files), profile_df, training_df, skipped_no_features, args.max_rtofs_dates)
    logger.info("Wrote %s", args.profile_csv)
    if not args.skip_rtofs_download:
        logger.info("Wrote %s", args.training_csv)
    logger.info("Wrote %s", args.report)
    logger.info("Index profile files: %d", len(index_files))
    logger.info("Extracted Argo profiles: %d", len(profile_df))
    logger.info("Training rows: %d", len(training_df))


if __name__ == "__main__":
    main()
