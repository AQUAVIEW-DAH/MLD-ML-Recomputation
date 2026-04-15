from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from math import radians, cos, sin, asin, sqrt
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_REPLAY_DATA_PATH = "artifacts/datasets/training_data_holdout_historical_replay_2025_jul_aug.csv"
DEFAULT_RTOFS_MATCHED_DIR = "/data/suramya/rtofs_time_matched"
DEFAULT_REPLAY_RADIUS_KM = 100.0
DEFAULT_REPLAY_WINDOW_HR = 72


def parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * 6371.0


def _parse_date(value: str) -> str:
    value = str(value).strip()
    fmt = "%Y-%m-%d" if "-" in value else "%Y%m%d"
    return datetime.strptime(value, fmt).date().isoformat()


def load_replay_dataframe(path: str = DEFAULT_REPLAY_DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path).copy()
    df["obs_time_dt"] = pd.to_datetime(df["obs_time"], utc=True)
    raw_dates = df["rtofs_date"].fillna(df["obs_date"])
    df["replay_date"] = raw_dates.map(_parse_date)
    return df


def get_replay_metadata(df: pd.DataFrame) -> dict[str, Any]:
    available_dates = sorted(df["replay_date"].dropna().unique().tolist())
    default_date = available_dates[-1] if available_dates else None
    return {
        "mode": "historical_replay",
        "available_dates": available_dates,
        "available_date_count": len(available_dates),
        "min_date": available_dates[0] if available_dates else None,
        "max_date": available_dates[-1] if available_dates else None,
        "default_query_time": f"{default_date}T12:00:00Z" if default_date else None,
        "support_radius_km": DEFAULT_REPLAY_RADIUS_KM,
        "support_window_hr": DEFAULT_REPLAY_WINDOW_HR,
        "holdout_rows": int(len(df)),
        "holdout_platforms": int(df["platform_id"].nunique()) if "platform_id" in df.columns else 0,
        "source_families": df["source_family"].value_counts().to_dict() if "source_family" in df.columns else {},
    }


def get_rtofs_path_for_query_time(query_time: str, base_dir: str = DEFAULT_RTOFS_MATCHED_DIR) -> Path:
    dt = parse_iso8601(query_time)
    ymd = dt.strftime("%Y%m%d")
    path = Path(base_dir) / f"rtofs.{ymd}" / "rtofs_glo_3dz_f006_6hrly_hvr_US_east.nc"
    if not path.exists():
        raise FileNotFoundError(f"No replay RTOFS file available for {dt.date()} at {path}")
    return path


def find_nearby_replay_observations(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    query_time: str,
    radius_km: float = DEFAULT_REPLAY_RADIUS_KM,
    time_window_hr: int = DEFAULT_REPLAY_WINDOW_HR,
    limit: int = 25,
) -> list[dict[str, Any]]:
    query_dt = parse_iso8601(query_time)
    start = query_dt - timedelta(hours=time_window_hr)
    end = query_dt + timedelta(hours=time_window_hr)

    window_df = df[(df["obs_time_dt"] >= start) & (df["obs_time_dt"] <= end)].copy()
    if window_df.empty:
        return []

    window_df["distance_km"] = window_df.apply(
        lambda row: haversine_km(lon, lat, float(row["lon"]), float(row["lat"])), axis=1
    )
    nearby = window_df[window_df["distance_km"] <= radius_km].copy()
    if nearby.empty:
        return []

    nearby["time_delta_hr"] = (nearby["obs_time_dt"] - query_dt).abs().dt.total_seconds() / 3600.0
    nearby = nearby.sort_values(["distance_km", "time_delta_hr", "obs_time_dt"]).head(limit)

    return [
        {
            "id": str(row.get("cast_id", row.get("platform_id", f"obs-{idx}"))),
            "platform_id": str(row.get("platform_id", "")),
            "obs_time": row["obs_time_dt"].isoformat().replace("+00:00", "Z"),
            "distance_km": round(float(row["distance_km"]), 2),
            "mld_m": round(float(row["observed_mld"]), 2),
            "source": str(row.get("source_family", row.get("wod_source", "replay"))),
            "lat": round(float(row["lat"]), 4),
            "lon": round(float(row["lon"]), 4),
        }
        for idx, (_, row) in enumerate(nearby.iterrows(), start=1)
    ]
