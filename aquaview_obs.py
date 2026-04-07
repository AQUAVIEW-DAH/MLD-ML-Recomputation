from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import cos, radians
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import csv
import io
import json
import logging
import numpy as np
import ssl
import time as _time

logger = logging.getLogger(__name__)

# Create unverified SSL context to avoid CERTIFICATE_VERIFY_FAILED in local run
ssl_context = ssl._create_unverified_context()


DEFAULT_AQUAVIEW_SEARCH_URL = (
    "https://aquaview-sfeos-1025757962819.us-east1.run.app/search"
)

PRIMARY_RADIUS_KM = 50.0
PRIMARY_WINDOW_HR = 48
FALLBACK_RADIUS_KM = 100.0
FALLBACK_WINDOW_HR = 72
PROFILE_COLLECTIONS = ("GADR", "IOOS")

# --- Retry / Timeout defaults ---
DEFAULT_TIMEOUT = 120           # seconds (up from 30)
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 5          # seconds
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class SearchWindow:
    radius_km: float
    time_window_hr: int
    bbox: list[float]
    datetime_range: str


@dataclass(frozen=True)
class ObservationProfile:
    source: str
    collection: str
    institution: str
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
            "collection": self.collection,
            "institution": self.institution,
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


# ------------------------------------------------------------------
#  Robust HTTP fetch with retry + exponential backoff
# ------------------------------------------------------------------
def fetch_text(
    url: str,
    api_token: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> str:
    """Fetch a URL with retry logic for transient failures."""
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    request = Request(url, headers=headers)

    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            with urlopen(request, timeout=timeout_seconds, context=ssl_context) as response:
                return response.read().decode("utf-8")
        except HTTPError as e:
            last_err = e
            if e.code in RETRYABLE_HTTP_CODES:
                wait = RETRY_BACKOFF_BASE * (2 ** attempt)
                logger.warning(
                    "HTTP %d from %s (attempt %d/%d), retrying in %ds…",
                    e.code, url[:80], attempt + 1, max_retries, wait,
                )
                _time.sleep(wait)
                continue
            raise  # non-retryable HTTP error (400, 404, etc.)
        except (TimeoutError, ssl.SSLError, URLError, ConnectionResetError, OSError) as e:
            last_err = e
            wait = RETRY_BACKOFF_BASE * (2 ** attempt)
            logger.warning(
                "%s on %s (attempt %d/%d), retrying in %ds…",
                type(e).__name__, url[:80], attempt + 1, max_retries, wait,
            )
            _time.sleep(wait)
            continue

    # All retries exhausted
    raise last_err  # type: ignore[misc]


def fetch_bytes(
    url: str,
    timeout_seconds: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> bytes:
    """Fetch raw bytes (e.g. NetCDF) with retry logic."""
    request = Request(url)
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            with urlopen(request, timeout=timeout_seconds, context=ssl_context) as response:
                return response.read()
        except (HTTPError, TimeoutError, ssl.SSLError, URLError,
                ConnectionResetError, OSError) as e:
            last_err = e
            wait = RETRY_BACKOFF_BASE * (2 ** attempt)
            logger.warning(
                "%s fetching %s (attempt %d/%d), retrying in %ds…",
                type(e).__name__, url[:80], attempt + 1, max_retries, wait,
            )
            _time.sleep(wait)
            continue
    raise last_err  # type: ignore[misc]


# ------------------------------------------------------------------
#  Aquaview STAC search client
# ------------------------------------------------------------------
class AquaviewClient:
    def __init__(
        self,
        search_url: str = DEFAULT_AQUAVIEW_SEARCH_URL,
        api_token: str | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT,
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
        with urlopen(request, timeout=self.timeout_seconds, context=ssl_context) as response:
            return json.loads(response.read().decode("utf-8"))


# ------------------------------------------------------------------
#  STAC item filtering
# ------------------------------------------------------------------
def is_usable_profile_item(item: dict[str, Any]) -> bool:
    """Check if a STAC item is a vertical ocean profile with temp + depth."""
    properties = item.get("properties", {})
    cdm_type = properties.get("aquaview:cdm_data_type", "")
    if cdm_type not in {"Profile", "TrajectoryProfile"}:
        return False

    raw_variables = properties.get("aquaview:variables", [])
    if isinstance(raw_variables, str):
        raw_variables = [raw_variables]
    variables = {str(variable).strip("-").lower() for variable in raw_variables}

    has_temp = "temperature" in variables or "temp" in variables or any("temp" in v for v in variables)
    has_depth = "depth" in variables or "pressure" in variables or "pres" in variables or any("pres" in v for v in variables)
    return has_temp and has_depth


def is_usable_sst_station(item: dict[str, Any]) -> bool:
    """Check if a STAC item is a TimeSeries station with sea_water_temperature."""
    properties = item.get("properties", {})
    cdm_type = properties.get("aquaview:cdm_data_type", "")
    if cdm_type != "TimeSeries":
        return False

    raw_variables = properties.get("aquaview:variables", [])
    if isinstance(raw_variables, str):
        raw_variables = [raw_variables]
    variables = {str(v).lower() for v in raw_variables}

    return "sea_water_temperature" in variables


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


# ------------------------------------------------------------------
#  Asset helpers
# ------------------------------------------------------------------
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


def build_erddap_csvp_url(
    item: dict[str, Any],
    bbox: list[float],
    start_time: str,
    end_time: str,
    variables: str = "time,latitude,longitude,depth,temperature,profile_id",
) -> str:
    """Build an ERDDAP tabledap CSVP URL with server-side spatial/temporal filtering."""
    base_url = get_asset_href(item, ("csvp",))
    if not base_url:
        raise ValueError(f"IOOS item {item.get('id')} is missing a csvp asset")

    query = (
        f"{variables}"
        f"&time>={start_time}"
        f"&time<={end_time}"
        f"&latitude>={bbox[1]}"
        f"&latitude<={bbox[3]}"
        f"&longitude>={bbox[0]}"
        f"&longitude<={bbox[2]}"
    )
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


# Keep old name for backward compat
build_ioos_csvp_url = build_erddap_csvp_url


def build_secoora_sst_url(
    item: dict[str, Any],
    start_time: str,
    end_time: str,
) -> str:
    """Build an ERDDAP CSVP URL for SECOORA stations with sea_water_temperature."""
    base_url = get_asset_href(item, ("csvp",))
    if not base_url:
        raise ValueError(f"SECOORA item {item.get('id')} is missing a csvp asset")

    query = (
        "time,latitude,longitude,sea_water_temperature"
        f"&time>={start_time}"
        f"&time<={end_time}"
    )
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


# ------------------------------------------------------------------
#  Parsing helpers
# ------------------------------------------------------------------
def _safe_float(value: str | None) -> float | None:
    if value in (None, "", "NaN", "nan"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_ioos_csvp(text: str, platform_id: str, collection: str = "", institution: str = "") -> list[ObservationProfile]:
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
                source="ERDDAP" if not collection else collection,
                collection=collection,
                institution=institution,
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


def parse_secoora_sst_csv(
    text: str,
    platform_id: str,
    collection: str = "SECOORA",
    institution: str = "",
) -> list[ObservationProfile]:
    """
    Parse SECOORA TimeSeries CSV into a single-depth "surface" profile.
    Returns one ObservationProfile per station with depth=[0.0] and the
    mean observed SST.  This provides surface-only validation points.
    """
    # The header line from csvp looks like:
    #   time (UTC),latitude (degrees_north),longitude (degrees_east),sea_water_temperature (degree_Celsius)
    # We need to normalise the column names.
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return []

    # Normalise csvp header (strip units in parens)
    header = lines[0]
    clean_cols = []
    for col in header.split(","):
        col = col.strip()
        if " (" in col:
            col = col[:col.index(" (")]
        clean_cols.append(col)

    clean_csv = ",".join(clean_cols) + "\n" + "\n".join(lines[1:])
    reader = csv.DictReader(io.StringIO(clean_csv))

    temps: list[float] = []
    lats: list[float] = []
    lons: list[float] = []
    times: list[str] = []
    for row in reader:
        t = _safe_float(row.get("sea_water_temperature"))
        lat = _safe_float(row.get("latitude"))
        lon = _safe_float(row.get("longitude"))
        time_val = row.get("time", "")
        if t is not None:
            temps.append(t)
        if lat is not None:
            lats.append(lat)
        if lon is not None:
            lons.append(lon)
        if time_val:
            times.append(time_val)

    if not temps:
        return []

    return [
        ObservationProfile(
            source="SECOORA",
            collection=collection,
            institution=institution,
            platform_id=platform_id,
            profile_id=f"{platform_id}_sst",
            obs_time=min(times) if times else "",
            lat=float(np.mean(lats)) if lats else np.nan,
            lon=float(np.mean(lons)) if lons else np.nan,
            depth_m=[0.0],
            temperature_c=[float(np.mean(temps))],
            metadata={"sst_obs_count": len(temps), "surface_only": True},
        )
    ]


# ------------------------------------------------------------------
#  Profile extraction — ERDDAP (IOOS, SECOORA profile)
# ------------------------------------------------------------------
def extract_erddap_profiles(
    item: dict[str, Any],
    bbox: list[float],
    start_time: str,
    end_time: str,
    api_token: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT,
) -> list[ObservationProfile]:
    url = build_erddap_csvp_url(item, bbox, start_time, end_time)
    text = fetch_text(url, api_token=api_token, timeout_seconds=timeout_seconds)
    collection = item.get("collection", "Unknown")
    institution = item.get("properties", {}).get("aquaview:institution", "")
    return parse_ioos_csvp(text, platform_id=str(item.get("id", "")), collection=collection, institution=institution)


def extract_secoora_sst(
    item: dict[str, Any],
    start_time: str,
    end_time: str,
    timeout_seconds: int = DEFAULT_TIMEOUT,
) -> list[ObservationProfile]:
    """Extract surface SST from a SECOORA TimeSeries station."""
    url = build_secoora_sst_url(item, start_time, end_time)
    text = fetch_text(url, timeout_seconds=timeout_seconds)
    institution = item.get("properties", {}).get("aquaview:institution", "")
    return parse_secoora_sst_csv(
        text,
        platform_id=str(item.get("id", "")),
        collection=item.get("collection", "SECOORA"),
        institution=institution,
    )


# ------------------------------------------------------------------
#  Profile extraction — GADR (Argo NetCDF)
# ------------------------------------------------------------------
def extract_gadr_profiles(
    item: dict[str, Any],
    bbox: list[float],
    start_time: str,
    end_time: str,
) -> list[ObservationProfile]:
    import tempfile
    import os
    import xarray as xr

    collection = item.get("collection", "GADR")
    institution = item.get("properties", {}).get("aquaview:institution", "")

    href = get_asset_href(item, ("gdac_prof", "gadr_prof"))
    if not href:
        raise ValueError(f"No valid nc asset for {item.get('id')}")

    logger.info("Downloading GADR file: %s", href[:90])
    content = fetch_bytes(href, timeout_seconds=DEFAULT_TIMEOUT)

    fd, path = tempfile.mkstemp(suffix='.nc')
    with os.fdopen(fd, 'wb') as f:
        f.write(content)

    profiles = []
    try:
        ds = xr.open_dataset(path)
        if "N_PROF" not in ds.dims:
            return profiles

        # FIX: use ds.sizes instead of ds.dims to avoid FutureWarning
        n_prof = ds.sizes.get("N_PROF", 0)
        start_dt = np.datetime64(start_time.replace("Z", "")) if start_time else np.datetime64('1900-01-01')
        end_dt = np.datetime64(end_time.replace("Z", "")) if end_time else np.datetime64('2100-01-01')

        for i in range(n_prof):
            lat_val = float(ds["LATITUDE"].isel(N_PROF=i).values)
            lon_val = float(ds["LONGITUDE"].isel(N_PROF=i).values)

            # Filter spatial limits (generous bbox mapping)
            if not (bbox[1] <= lat_val <= bbox[3] and bbox[0] <= lon_val <= bbox[2]):
                continue

            raw_time = ds["JULD"].isel(N_PROF=i).values
            if np.isnat(raw_time):
                continue

            time_val = np.datetime64(raw_time)
            if not (start_dt <= time_val <= end_dt):
                continue

            str_time = str(time_val)

            pres_arr = ds["PRES"].isel(N_PROF=i).values
            temp_arr = ds["TEMP"].isel(N_PROF=i).values

            valid = np.isfinite(pres_arr) & np.isfinite(temp_arr)
            pres_clean = pres_arr[valid].tolist()
            temp_clean = temp_arr[valid].tolist()

            if len(pres_clean) > 0:
                profiles.append(ObservationProfile(
                    source="GADR",
                    collection=collection,
                    institution=institution,
                    platform_id=str(item.get("id", "")),
                    profile_id=f"{item.get('id', '')}_{i}",
                    obs_time=str_time,
                    lat=lat_val,
                    lon=lon_val,
                    depth_m=pres_clean,
                    temperature_c=temp_clean,
                    metadata={}
                ))

        logger.info(
            "GADR %s: %d/%d profiles inside GoM bbox",
            item.get("id", "?"), len(profiles), n_prof,
        )
    finally:
        if 'ds' in locals():
            ds.close()
        os.remove(path)

    return profiles


# ------------------------------------------------------------------
#  Persistence
# ------------------------------------------------------------------
def load_search_results(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_search_results(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
