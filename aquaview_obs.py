from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import cos, radians
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen

import csv
import io
import json
import numpy as np


DEFAULT_AQUAVIEW_SEARCH_URL = (
    "https://aquaview-sfeos-1025757962819.us-east1.run.app/search"
)

PRIMARY_RADIUS_KM = 50.0
PRIMARY_WINDOW_HR = 48
FALLBACK_RADIUS_KM = 100.0
FALLBACK_WINDOW_HR = 72
PROFILE_COLLECTIONS = ("GADR", "IOOS")


@dataclass(frozen=True)
class SearchWindow:
    radius_km: float
    time_window_hr: int
    bbox: list[float]
    datetime_range: str


@dataclass(frozen=True)
class ObservationProfile:
    source: str
    platform_id: str
    profile_id: str
    obs_time: str
    lat: float
    lon: float
    depth_m: list[float]
    temperature_c: list[float]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "platform_id": self.platform_id,
            "profile_id": self.profile_id,
            "obs_time": self.obs_time,
            "lat": self.lat,
            "lon": self.lon,
            "depth_m": self.depth_m,
            "temperature_c": self.temperature_c,
            "metadata": self.metadata,
        }


def parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_bbox(lat: float, lon: float, radius_km: float) -> list[float]:
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(cos(radians(lat)), 1e-6))
    return [
        round(lon - lon_delta, 2),
        round(lat - lat_delta, 2),
        round(lon + lon_delta, 2),
        round(lat + lat_delta, 2),
    ]


def make_search_window(lat: float, lon: float, query_time: str, radius_km: float, time_window_hr: int) -> SearchWindow:
    dt = parse_iso8601(query_time)
    start = dt - timedelta(hours=time_window_hr)
    end = dt + timedelta(hours=time_window_hr)
    return SearchWindow(
        radius_km=radius_km,
        time_window_hr=time_window_hr,
        bbox=build_bbox(lat, lon, radius_km),
        datetime_range=f"{isoformat_z(start)}/{isoformat_z(end)}",
    )


def build_stac_search_body(
    lat: float,
    lon: float,
    query_time: str,
    radius_km: float,
    time_window_hr: int,
    limit: int = 20,
    collections: Iterable[str] = PROFILE_COLLECTIONS,
) -> dict[str, Any]:
    window = make_search_window(lat, lon, query_time, radius_km, time_window_hr)
    return {
        "collections": list(collections),
        "bbox": window.bbox,
        "datetime": window.datetime_range,
        "limit": limit,
    }


class AquaviewClient:
    def __init__(
        self,
        search_url: str = DEFAULT_AQUAVIEW_SEARCH_URL,
        api_token: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.search_url = search_url
        self.api_token = api_token
        self.timeout_seconds = timeout_seconds

    def search(self, body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        request = Request(self.search_url, data=data, headers=headers, method="POST")
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


def is_usable_profile_item(item: dict[str, Any]) -> bool:
    properties = item.get("properties", {})
    cdm_type = properties.get("aquaview:cdm_data_type", "")
    if cdm_type not in {"Profile", "TrajectoryProfile"}:
        return False

    raw_variables = properties.get("aquaview:variables", [])
    if isinstance(raw_variables, str):
        raw_variables = [raw_variables]
    variables = {str(variable).strip("-").lower() for variable in raw_variables}

    has_temp = "temperature" in variables or "temp" in variables
    has_depth = "depth" in variables or "pressure" in variables or "pres" in variables
    return has_temp and has_depth


def search_nearby_obs_items(
    client: AquaviewClient,
    lat: float,
    lon: float,
    query_time: str,
    radius_km: float,
    time_window_hr: int,
    limit: int = 20,
) -> dict[str, Any]:
    body = build_stac_search_body(lat, lon, query_time, radius_km, time_window_hr, limit=limit)
    response = client.search(body)
    features = response.get("features", [])
    usable = [item for item in features if is_usable_profile_item(item)]
    return {"search_body": body, "features": usable, "raw_count": len(features), "usable_count": len(usable)}


def search_with_primary_fallback(
    client: AquaviewClient,
    lat: float,
    lon: float,
    query_time: str,
    primary_min_count: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    primary = search_nearby_obs_items(
        client,
        lat,
        lon,
        query_time,
        radius_km=PRIMARY_RADIUS_KM,
        time_window_hr=PRIMARY_WINDOW_HR,
        limit=limit,
    )
    if primary["usable_count"] >= primary_min_count:
        return {"window_used": "primary", **primary}

    fallback = search_nearby_obs_items(
        client,
        lat,
        lon,
        query_time,
        radius_km=FALLBACK_RADIUS_KM,
        time_window_hr=FALLBACK_WINDOW_HR,
        limit=limit,
    )
    return {"window_used": "fallback", "primary": primary, **fallback}


def get_asset_href(item: dict[str, Any], preferred_keys: Iterable[str]) -> str | None:
    assets = item.get("assets", {})
    for key in preferred_keys:
        asset = assets.get(key)
        if asset and asset.get("href"):
            return str(asset["href"])
    for asset in assets.values():
        href = asset.get("href")
        if href:
            return str(href)
    return None


def build_ioos_csvp_url(item: dict[str, Any], bbox: list[float], start_time: str, end_time: str) -> str:
    base_url = get_asset_href(item, ("csvp",))
    if not base_url:
        raise ValueError(f"IOOS item {item.get('id')} is missing a csvp asset")

    query = (
        "time,latitude,longitude,depth,temperature,profile_id"
        f"&time>={start_time}"
        f"&time<={end_time}"
        f"&latitude>={bbox[1]}"
        f"&latitude<={bbox[3]}"
        f"&longitude>={bbox[0]}"
        f"&longitude<={bbox[2]}"
    )
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


def fetch_text(url: str, api_token: str | None = None, timeout_seconds: int = 30) -> str:
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8")


def _safe_float(value: str | None) -> float | None:
    if value in (None, "", "NaN", "nan"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_ioos_csvp(text: str, platform_id: str) -> list[ObservationProfile]:
    reader = csv.DictReader(io.StringIO(text))
    rows_by_profile: dict[str, list[dict[str, str]]] = {}
    for row in reader:
        profile_id = row.get("profile_id") or row.get("profile") or row.get("time")
        if not profile_id:
            continue
        rows_by_profile.setdefault(str(profile_id), []).append(row)

    profiles: list[ObservationProfile] = []
    for profile_id, rows in rows_by_profile.items():
        depth_temp_pairs: list[tuple[float, float]] = []
        latitudes: list[float] = []
        longitudes: list[float] = []
        times: list[str] = []
        for row in rows:
            depth = _safe_float(row.get("depth"))
            temp = _safe_float(row.get("temperature"))
            lat = _safe_float(row.get("latitude"))
            lon = _safe_float(row.get("longitude"))
            time_value = row.get("time")
            if depth is not None and temp is not None:
                depth_temp_pairs.append((depth, temp))
            if lat is not None:
                latitudes.append(lat)
            if lon is not None:
                longitudes.append(lon)
            if time_value:
                times.append(time_value)

        if not depth_temp_pairs:
            continue

        depth_temp_pairs.sort(key=lambda pair: pair[0])
        profiles.append(
            ObservationProfile(
                source="IOOS",
                platform_id=platform_id,
                profile_id=profile_id,
                obs_time=min(times) if times else "",
                lat=float(np.mean(latitudes)) if latitudes else np.nan,
                lon=float(np.mean(longitudes)) if longitudes else np.nan,
                depth_m=[pair[0] for pair in depth_temp_pairs],
                temperature_c=[pair[1] for pair in depth_temp_pairs],
                metadata={"row_count": len(rows)},
            )
        )
    return profiles


def extract_ioos_profiles(
    item: dict[str, Any],
    bbox: list[float],
    start_time: str,
    end_time: str,
    api_token: str | None = None,
    timeout_seconds: int = 30,
) -> list[ObservationProfile]:
    url = build_ioos_csvp_url(item, bbox, start_time, end_time)
    text = fetch_text(url, api_token=api_token, timeout_seconds=timeout_seconds)
    return parse_ioos_csvp(text, platform_id=str(item.get("id", "")))


def extract_gadr_profiles(
    item: dict[str, Any],
    lat: float,
    lon: float,
    start_time: str,
    end_time: str,
) -> list[ObservationProfile]:
    raise NotImplementedError(
        "GADR profile extraction is not implemented yet. The current MVP path should start with IOOS."
    )


def load_search_results(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_search_results(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
