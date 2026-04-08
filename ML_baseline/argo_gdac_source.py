"""
Direct Argo GDAC profile ingestion.

This bypasses Aquaview metadata and uses the Argo global profile index to find
GoM profile NetCDF files, then extracts temperature/pressure profiles that can
support the project's fixed 10m-reference MLD label.
"""
from __future__ import annotations

import logging
import ssl
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)

ARGO_GDAC_BASE = "https://data-argo.ifremer.fr/dac"
ARGO_INDEX_URL = "https://data-argo.ifremer.fr/ar_index_global_prof.txt"
ARGO_CACHE_DIR = Path("/data/suramya/argo_cache")
INDEX_CACHE_NAME = "ar_index_global_prof.txt"

MIN_DEPTH_LEVELS = 5
MIN_MAX_DEPTH_M = 15.0
MLD_REF_DEPTH_M = 10.0
GOOD_QC_FLAGS = {"1", "2"}

ssl_ctx = ssl._create_unverified_context()


@dataclass(frozen=True)
class ArgoGDACProfile:
    source: str
    instrument: str
    cast_id: str
    cruise_id: str
    platform: str
    lat: float
    lon: float
    obs_time: str
    depth_m: list[float]
    temperature_c: list[float]


def _fetch_bytes(url: str, timeout_seconds: int = 300) -> bytes:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout_seconds, context=ssl_ctx) as resp:
        return resp.read()


def _download_to_cache(url: str, local_path: Path, timeout_seconds: int = 300) -> Path:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if local_path.exists():
        return local_path

    tmp_path = local_path.with_suffix(local_path.suffix + ".tmp")
    tmp_path.write_bytes(_fetch_bytes(url, timeout_seconds=timeout_seconds))
    tmp_path.replace(local_path)
    return local_path


def download_argo_index(index_url: str = ARGO_INDEX_URL) -> Path:
    return _download_to_cache(index_url, ARGO_CACHE_DIR / INDEX_CACHE_NAME, timeout_seconds=300)


def _parse_index_date(value: str) -> str:
    return value.strip()[:8]


def matching_index_files(
    bbox: list[float],
    start_yyyymmdd: str = "20230101",
    end_yyyymmdd: str = "20241231",
    max_profiles: int = 25,
    max_per_platform: int = 5,
    index_url: str = ARGO_INDEX_URL,
) -> list[str]:
    """Return Argo profile file paths from the global index inside bbox/date."""
    west, south, east, north = bbox
    index_path = download_argo_index(index_url)

    header: list[str] | None = None
    matches: list[str] = []
    platform_counts: dict[str, int] = {}
    total_rows = 0
    for raw_line in index_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if header is None:
            header = [v.strip() for v in line.split(",")]
            continue

        values = [v.strip() for v in line.split(",")]
        if len(values) < len(header):
            continue
        item = dict(zip(header, values))
        total_rows += 1
        try:
            lat = float(item.get("latitude", "nan"))
            lon = float(item.get("longitude", "nan"))
        except ValueError:
            continue

        date = _parse_index_date(item.get("date", ""))
        if not (start_yyyymmdd <= date <= end_yyyymmdd):
            continue
        if not (south <= lat <= north and west <= lon <= east):
            continue

        file_name = item.get("file", "")
        if file_name:
            platform_id = file_name.split("/")[1] if "/" in file_name else file_name
            if max_per_platform and platform_counts.get(platform_id, 0) >= max_per_platform:
                continue
            matches.append(file_name)
            platform_counts[platform_id] = platform_counts.get(platform_id, 0) + 1
            if max_profiles and len(matches) >= max_profiles:
                break

    logger.info(
        "Argo GDAC index scan: %d rows scanned, %d matches selected across %d platforms "
        "inside bbox=%s date=%s/%s max_per_platform=%s",
        total_rows,
        len(matches),
        len(platform_counts),
        bbox,
        start_yyyymmdd,
        end_yyyymmdd,
        max_per_platform,
    )
    return matches


def _decode_scalar(value) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="ignore").strip()
    return str(value).strip()


def _qc_mask(qc_values: np.ndarray) -> np.ndarray:
    qc_str = np.array([_decode_scalar(v) for v in qc_values.ravel()]).reshape(qc_values.shape)
    return np.isin(qc_str, list(GOOD_QC_FLAGS))


def _preferred_var(ds: xr.Dataset, raw_name: str, adjusted_name: str) -> tuple[str, str | None]:
    if adjusted_name in ds and np.isfinite(ds[adjusted_name].values).any():
        qc_name = f"{adjusted_name}_QC"
        return adjusted_name, qc_name if qc_name in ds else None
    qc_name = f"{raw_name}_QC"
    return raw_name, qc_name if qc_name in ds else None


def _extract_profiles_from_file(local_path: Path, source_file: str) -> list[ArgoGDACProfile]:
    profiles: list[ArgoGDACProfile] = []
    with xr.open_dataset(local_path, decode_timedelta=False) as ds:
        if "PRES" not in ds or "TEMP" not in ds:
            return profiles

        pres_var, pres_qc_var = _preferred_var(ds, "PRES", "PRES_ADJUSTED")
        temp_var, temp_qc_var = _preferred_var(ds, "TEMP", "TEMP_ADJUSTED")
        pres = ds[pres_var].values
        temp = ds[temp_var].values
        n_prof = int(ds.sizes.get("N_PROF", pres.shape[0] if pres.ndim > 1 else 1))

        if pres.ndim == 1:
            pres = pres.reshape(1, -1)
            temp = temp.reshape(1, -1)

        pres_qc = _qc_mask(ds[pres_qc_var].values) if pres_qc_var else np.ones_like(pres, dtype=bool)
        temp_qc = _qc_mask(ds[temp_qc_var].values) if temp_qc_var else np.ones_like(temp, dtype=bool)

        for idx in range(n_prof):
            depth_arr = np.asarray(pres[idx], dtype=float)
            temp_arr = np.asarray(temp[idx], dtype=float)
            valid = np.isfinite(depth_arr) & np.isfinite(temp_arr) & pres_qc[idx] & temp_qc[idx]
            depth_clean = depth_arr[valid]
            temp_clean = temp_arr[valid]

            if len(depth_clean) < MIN_DEPTH_LEVELS:
                continue
            if float(depth_clean.max()) < MIN_MAX_DEPTH_M:
                continue
            if not (float(depth_clean.min()) <= MLD_REF_DEPTH_M <= float(depth_clean.max())):
                continue

            order = np.argsort(depth_clean)
            depth_clean = depth_clean[order]
            temp_clean = temp_clean[order]

            platform = _decode_scalar(ds["PLATFORM_NUMBER"].values[idx]) if "PLATFORM_NUMBER" in ds else "unknown"
            cycle = _decode_scalar(ds["CYCLE_NUMBER"].values[idx]) if "CYCLE_NUMBER" in ds else str(idx)
            try:
                obs_time = np.datetime_as_string(ds["JULD"].values[idx], unit="s") + "Z"
            except Exception:
                obs_time = _decode_scalar(ds["JULD"].values[idx]) if "JULD" in ds else ""

            profiles.append(
                ArgoGDACProfile(
                    source="ARGO_GDAC",
                    instrument="pfl",
                    cast_id=source_file,
                    cruise_id=platform,
                    platform=platform,
                    lat=float(ds["LATITUDE"].values[idx]),
                    lon=float(ds["LONGITUDE"].values[idx]),
                    obs_time=obs_time,
                    depth_m=depth_clean.tolist(),
                    temperature_c=temp_clean.tolist(),
                )
            )
    return profiles


def extract_argo_gdac_profiles(
    bbox: list[float],
    start_yyyymmdd: str = "20230101",
    end_yyyymmdd: str = "20241231",
    max_profiles: int = 25,
    max_per_platform: int = 5,
    index_url: str = ARGO_INDEX_URL,
) -> list[ArgoGDACProfile]:
    files = matching_index_files(
        bbox=bbox,
        start_yyyymmdd=start_yyyymmdd,
        end_yyyymmdd=end_yyyymmdd,
        max_profiles=max_profiles,
        max_per_platform=max_per_platform,
        index_url=index_url,
    )

    all_profiles: list[ArgoGDACProfile] = []
    skipped_download = 0
    skipped_parse = 0
    for index, source_file in enumerate(files, start=1):
        if index == 1 or index % 250 == 0 or index == len(files):
            logger.info("Argo GDAC fetch/parse progress: %d/%d files", index, len(files))
        local_path = ARGO_CACHE_DIR / source_file
        url = f"{ARGO_GDAC_BASE}/{source_file}"
        try:
            download_argo_file = _download_to_cache(url, local_path, timeout_seconds=120)
            profiles = _extract_profiles_from_file(download_argo_file, source_file)
        except Exception as exc:
            skipped_download += 1
            logger.warning("Argo GDAC profile fetch/parse failed for %s: %s", source_file, exc)
            continue

        if not profiles:
            skipped_parse += 1
        all_profiles.extend(profiles)

    logger.info(
        "Argo GDAC profiles extracted: %d usable from %d selected files "
        "(%d no usable profile, %d fetch/parse failures)",
        len(all_profiles),
        len(files),
        skipped_parse,
        skipped_download,
    )
    return all_profiles
