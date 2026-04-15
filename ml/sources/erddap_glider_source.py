"""
Direct ERDDAP glider source ingestion.

This bypasses Aquaview and reads candidate ERDDAP tabledap datasets discovered
by `source_audit.py`.  Each ERDDAP profile is grouped by dataset/profile_id and
returned with the same profile-shaped fields used by the WOD data builder.
"""
from __future__ import annotations

import csv
import io
import logging
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ml.paths import AUDITS_DIR

logger = logging.getLogger(__name__)

DEFAULT_AUDIT_FILES = [
    AUDITS_DIR / "source_audit_erddap_secoora.csv",
    AUDITS_DIR / "source_audit_erddap_ioos_gliders.csv",
]
MIN_DEPTH_LEVELS = 5
MIN_MAX_DEPTH_M = 15.0
MLD_REF_DEPTH_M = 10.0
DEFAULT_MAX_DATASETS = 5

ssl_ctx = ssl._create_unverified_context()


@dataclass(frozen=True)
class ERDDAPGliderProfile:
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


def _fetch_text(url: str, timeout_seconds: int = 120) -> str:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout_seconds, context=ssl_ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _strip_csvp_header_units(text: str) -> str:
    lines = text.strip().splitlines()
    if not lines:
        return text

    clean_cols = []
    for col in lines[0].split(","):
        col = col.strip()
        if " (" in col:
            col = col[: col.index(" (")]
        clean_cols.append(col)
    return ",".join(clean_cols) + "\n" + "\n".join(lines[1:])


def _dataset_csvp_url(
    tabledap_url: str,
    bbox: list[float],
    depth_max_m: float,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    base = tabledap_url.replace(".html", ".csvp")
    query = (
        "time,latitude,longitude,depth,temperature,profile_id"
        f"&latitude>={bbox[1]}"
        f"&latitude<={bbox[3]}"
        f"&longitude>={bbox[0]}"
        f"&longitude<={bbox[2]}"
        "&depth>=0"
        f"&depth<={depth_max_m}"
    )
    if start_time:
        query += f"&time>={start_time}"
    if end_time:
        query += f"&time<={end_time}"
    return f"{base}?{urllib.parse.quote(query, safe=',&=><')}"


def load_candidate_datasets(
    audit_files: list[Path] | None = None,
    max_datasets: int = DEFAULT_MAX_DATASETS,
) -> list[dict[str, str]]:
    if audit_files is None:
        audit_files = DEFAULT_AUDIT_FILES

    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for audit_file in audit_files:
        if not audit_file.exists():
            logger.warning("ERDDAP audit file not found: %s", audit_file)
            continue

        with audit_file.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("status") != "profile_candidate":
                    continue
                key = (row.get("provider", ""), row.get("source_key", ""))
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(row)
                if max_datasets and len(candidates) >= max_datasets:
                    return candidates
    return candidates


def parse_erddap_glider_csvp(
    text: str,
    dataset_id: str,
) -> list[ERDDAPGliderProfile]:
    clean_csv = _strip_csvp_header_units(text)
    rows_by_profile: dict[str, list[dict[str, str]]] = {}
    for row in csv.DictReader(io.StringIO(clean_csv)):
        profile_id = (row.get("profile_id") or "").strip()
        if not profile_id:
            continue
        rows_by_profile.setdefault(profile_id, []).append(row)

    profiles: list[ERDDAPGliderProfile] = []
    skipped_sparse = 0
    skipped_shallow = 0
    skipped_no_ref_depth = 0
    for profile_id, rows in rows_by_profile.items():
        depth_temp: dict[float, list[float]] = {}
        lats: list[float] = []
        lons: list[float] = []
        times: list[str] = []

        for row in rows:
            try:
                depth = float(row.get("depth", "nan"))
                temp = float(row.get("temperature", "nan"))
            except ValueError:
                continue
            if not np.isfinite(depth) or not np.isfinite(temp):
                continue
            depth_temp.setdefault(depth, []).append(temp)

            try:
                lat = float(row.get("latitude", "nan"))
                lon = float(row.get("longitude", "nan"))
            except ValueError:
                lat = np.nan
                lon = np.nan
            if np.isfinite(lat):
                lats.append(lat)
            if np.isfinite(lon):
                lons.append(lon)
            time_val = row.get("time", "")
            if time_val:
                times.append(time_val)

        if len(depth_temp) < MIN_DEPTH_LEVELS:
            skipped_sparse += 1
            continue

        depth_arr = np.array(sorted(depth_temp.keys()), dtype=float)
        temp_arr = np.array([float(np.mean(depth_temp[depth])) for depth in depth_arr], dtype=float)
        if float(depth_arr.max()) < MIN_MAX_DEPTH_M:
            skipped_shallow += 1
            continue

        # The project MLD definition uses a 10m temperature reference. Some
        # ERDDAP glider profiles only start below 10m, so they cannot produce a
        # comparable observed MLD label even if they are otherwise profile-like.
        if not (float(depth_arr.min()) <= MLD_REF_DEPTH_M <= float(depth_arr.max())):
            skipped_no_ref_depth += 1
            continue

        profiles.append(
            ERDDAPGliderProfile(
                source=f"ERDDAP_GLIDER_{dataset_id}",
                instrument="erddap_gld",
                cast_id=f"{dataset_id}:{profile_id}",
                cruise_id=dataset_id,
                platform=dataset_id,
                lat=float(np.mean(lats)) if lats else np.nan,
                lon=float(np.mean(lons)) if lons else np.nan,
                obs_time=min(times) if times else "",
                depth_m=depth_arr.tolist(),
                temperature_c=temp_arr.tolist(),
            )
        )
    logger.info(
        "ERDDAP %s profile QC: %d groups, %d usable, skipped %d sparse, "
        "%d shallow, %d missing %.1fm reference depth",
        dataset_id,
        len(rows_by_profile),
        len(profiles),
        skipped_sparse,
        skipped_shallow,
        skipped_no_ref_depth,
        MLD_REF_DEPTH_M,
    )
    return profiles


def extract_erddap_glider_profiles(
    bbox: list[float],
    audit_files: list[Path] | None = None,
    max_datasets: int = DEFAULT_MAX_DATASETS,
    depth_max_m: float = 1000.0,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[ERDDAPGliderProfile]:
    candidates = load_candidate_datasets(audit_files=audit_files, max_datasets=max_datasets)
    logger.info("ERDDAP glider candidates selected: %d", len(candidates))

    all_profiles: list[ERDDAPGliderProfile] = []
    for candidate in candidates:
        dataset_id = candidate.get("source_key", "")
        tabledap_url = candidate.get("url", "")
        if not dataset_id or not tabledap_url:
            continue

        url = _dataset_csvp_url(
            tabledap_url,
            bbox=bbox,
            depth_max_m=depth_max_m,
            start_time=start_time,
            end_time=end_time,
        )
        try:
            text = _fetch_text(url)
        except Exception as exc:
            logger.warning("ERDDAP glider fetch failed for %s: %s", dataset_id, exc)
            continue

        profiles = parse_erddap_glider_csvp(text, dataset_id=dataset_id)
        all_profiles.extend(profiles)
        logger.info("ERDDAP %s: extracted %d usable profiles", dataset_id, len(profiles))

    logger.info("Total ERDDAP glider profiles extracted: %d", len(all_profiles))
    return all_profiles
