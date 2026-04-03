from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from aquaview_obs import (
    PRIMARY_RADIUS_KM,
    PRIMARY_WINDOW_HR,
    build_bbox,
    isoformat_z,
    parse_iso8601,
)
from mld_core import get_model_mld, open_rtofs_dataset
from mld_observations import compute_observed_mlds


def build_debug_payload(
    lat: float,
    lon: float,
    query_time: str,
    observation_profiles: list,
) -> dict[str, Any]:
    ds = open_rtofs_dataset()
    try:
        model_result = get_model_mld(ds, lat, lon)
    finally:
        ds.close()

    observed = compute_observed_mlds(observation_profiles)
    return {
        "query": {"lat": lat, "lon": lon, "time": query_time},
        "model": model_result.to_dict(),
        "observations": {
            "count": len(observed),
            "profiles": observed,
            "support_window_km": PRIMARY_RADIUS_KM,
            "support_window_hr": PRIMARY_WINDOW_HR,
        },
    }


def build_primary_window_payload(lat: float, lon: float, query_time: str) -> dict[str, Any]:
    query_dt = parse_iso8601(query_time)
    return {
        "bbox": build_bbox(lat, lon, PRIMARY_RADIUS_KM),
        "datetime": (
            f"{isoformat_z(query_dt - timedelta(hours=PRIMARY_WINDOW_HR))}/"
            f"{isoformat_z(query_dt + timedelta(hours=PRIMARY_WINDOW_HR))}"
        ),
    }


if __name__ == "__main__":
    payload = build_primary_window_payload(28.5, -88.2, "2026-04-01T06:00:00Z")
    print(json.dumps(payload, indent=2))
