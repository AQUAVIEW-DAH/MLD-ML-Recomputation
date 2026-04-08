"""
Audit in-situ profile eligibility under several MLD label definitions.

This is an exploratory inventory tool, not a production training-data builder.
It intentionally separates "profile-shaped data exist" from "profile supports
the current 10m temperature-threshold MLD label" and from density-based labels.
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import math
import ssl
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mld_core import compute_mld_temp_threshold
from ML_baseline.argo_gdac_source import ARGO_CACHE_DIR
from ML_baseline.erddap_glider_source import DEFAULT_AUDIT_FILES, load_candidate_datasets
from ML_baseline.wod_source import WOD_CACHE_DIR


logger = logging.getLogger(__name__)

DEFAULT_BBOX = [-98.0, 18.0, -80.0, 31.0]
DEFAULT_OUTPUT_CSV = Path(__file__).with_name("profile_method_fit_audit.csv")
DEFAULT_OUTPUT_REPORT = Path(__file__).with_name("PROFILE_METHOD_FIT_AUDIT.md")
MIN_DEPTH_LEVELS = 5
MIN_MAX_DEPTH_M = 15.0
TEMP_DELTA_C = 0.2
DENSITY_DELTA_KG_M3 = 0.03
ssl_ctx = ssl._create_unverified_context()


@dataclass
class ProfileFitRow:
    provider: str
    source: str
    instrument: str
    cast_id: str
    platform_id: str
    obs_time: str
    lat: float
    lon: float
    n_temp_levels: int
    n_density_levels: int
    min_depth_m: float
    max_depth_m: float
    reaches_5m: bool
    reaches_10m: bool
    reaches_15m: bool
    reaches_20m: bool
    reaches_50m: bool
    reaches_100m: bool
    brackets_10m_temp: bool
    brackets_10m_density: bool
    temp_profile_basic: bool
    temp_mld_ref10: bool
    temp_mld_ref10_under100m: bool
    temp_mld_shallowest_ref: bool
    density_profile_basic: bool
    density_mld_ref10: bool
    density_mld_ref10_under100m: bool
    density_mld_shallowest_ref: bool
    best_standard_label: str
    exploratory_label_available: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bbox", default=",".join(str(v) for v in DEFAULT_BBOX))
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-report", type=Path, default=DEFAULT_OUTPUT_REPORT)
    parser.add_argument("--wod-cache-dir", type=Path, default=WOD_CACHE_DIR)
    parser.add_argument("--argo-cache-dir", type=Path, default=ARGO_CACHE_DIR)
    parser.add_argument("--include-wod", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include-argo-cache", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include-erddap", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--erddap-max-datasets", type=int, default=10)
    return parser.parse_args()


def in_bbox(lat: float, lon: float, bbox: list[float]) -> bool:
    west, south, east, north = bbox
    return south <= lat <= north and west <= lon <= east


def clean_profile(
    depth: np.ndarray,
    temp: np.ndarray | None,
    salt: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    n = len(depth)
    if temp is not None:
        n = min(n, len(temp))
    if salt is not None:
        n = min(n, len(salt))
    depth = np.asarray(depth[:n], dtype=float)
    temp_arr = np.asarray(temp[:n], dtype=float) if temp is not None else None
    salt_arr = np.asarray(salt[:n], dtype=float) if salt is not None else None

    valid = np.isfinite(depth)
    if temp_arr is not None:
        valid &= np.isfinite(temp_arr)
    if salt_arr is not None:
        valid &= np.isfinite(salt_arr)

    depth = depth[valid]
    if temp_arr is not None:
        temp_arr = temp_arr[valid]
    if salt_arr is not None:
        salt_arr = salt_arr[valid]

    if len(depth) == 0:
        return depth, temp_arr, salt_arr

    order = np.argsort(depth)
    depth = depth[order]
    if temp_arr is not None:
        temp_arr = temp_arr[order]
    if salt_arr is not None:
        salt_arr = salt_arr[order]
    return depth, temp_arr, salt_arr


def sigma_t_unesco_1983(salt_psu: np.ndarray, temp_c: np.ndarray) -> np.ndarray:
    """EOS-80 density anomaly at atmospheric pressure.

    This is sufficient for an eligibility audit of density-threshold labels.
    Production density MLD work should prefer TEOS-10/GSW if available.
    """
    s = np.asarray(salt_psu, dtype=float)
    t = np.asarray(temp_c, dtype=float)

    rho_w = (
        999.842594
        + 6.793952e-2 * t
        - 9.095290e-3 * t**2
        + 1.001685e-4 * t**3
        - 1.120083e-6 * t**4
        + 6.536332e-9 * t**5
    )
    a = (
        0.824493
        - 4.0899e-3 * t
        + 7.6438e-5 * t**2
        - 8.2467e-7 * t**3
        + 5.3875e-9 * t**4
    )
    b = -5.72466e-3 + 1.0227e-4 * t - 1.6546e-6 * t**2
    c = 4.8314e-4
    return rho_w + a * s + b * np.power(s, 1.5) + c * s**2 - 1000.0


def compute_threshold_mld(
    depth: np.ndarray,
    values: np.ndarray,
    ref_depth: float | None,
    delta: float,
    use_abs: bool = True,
) -> float | None:
    if len(depth) < MIN_DEPTH_LEVELS:
        return None
    if ref_depth is None:
        ref_depth = float(depth.min())
    if ref_depth < float(depth.min()) or ref_depth > float(depth.max()):
        return None
    ref_value = float(np.interp(ref_depth, depth, values))

    for idx in range(len(depth)):
        if depth[idx] <= ref_depth:
            continue
        diff = values[idx] - ref_value
        if use_abs:
            crossed = abs(diff) >= delta
        else:
            crossed = diff >= delta
        if not crossed:
            continue

        z1, z2 = float(depth[idx - 1]), float(depth[idx])
        v1, v2 = float(values[idx - 1]), float(values[idx])
        d1 = abs(v1 - ref_value) if use_abs else v1 - ref_value
        d2 = abs(v2 - ref_value) if use_abs else v2 - ref_value
        if math.isclose(d1, d2):
            return z2
        return float(z1 + (delta - d1) * (z2 - z1) / (d2 - d1))
    return None


def profile_fit_row(
    provider: str,
    source: str,
    instrument: str,
    cast_id: str,
    platform_id: str,
    obs_time: str,
    lat: float,
    lon: float,
    depth: np.ndarray,
    temp: np.ndarray | None,
    salt: np.ndarray | None,
) -> ProfileFitRow | None:
    depth_t, temp_clean, _ = clean_profile(depth, temp, None)
    depth_d, temp_d, salt_d = clean_profile(depth, temp, salt) if salt is not None else (np.array([]), None, None)

    if temp_clean is None or len(depth_t) == 0:
        return None

    min_depth = float(depth_t.min())
    max_depth = float(depth_t.max())
    temp_basic = len(depth_t) >= MIN_DEPTH_LEVELS and max_depth >= MIN_MAX_DEPTH_M
    brackets_10_temp = temp_basic and min_depth <= 10.0 <= max_depth

    temp_mld_10 = compute_mld_temp_threshold(depth_t, temp_clean, ref_depth=10.0, delta_t=TEMP_DELTA_C)
    temp_mld_shallow = compute_threshold_mld(depth_t, temp_clean, ref_depth=None, delta=TEMP_DELTA_C, use_abs=True)

    density_basic = False
    brackets_10_density = False
    density_mld_10 = None
    density_mld_shallow = None
    n_density = 0
    if temp_d is not None and salt_d is not None and len(depth_d) > 0:
        n_density = len(depth_d)
        density_basic = n_density >= MIN_DEPTH_LEVELS and float(depth_d.max()) >= MIN_MAX_DEPTH_M
        brackets_10_density = density_basic and float(depth_d.min()) <= 10.0 <= float(depth_d.max())
        sigma = sigma_t_unesco_1983(salt_d, temp_d)
        density_mld_10 = compute_threshold_mld(
            depth_d,
            sigma,
            ref_depth=10.0,
            delta=DENSITY_DELTA_KG_M3,
            use_abs=False,
        )
        density_mld_shallow = compute_threshold_mld(
            depth_d,
            sigma,
            ref_depth=None,
            delta=DENSITY_DELTA_KG_M3,
            use_abs=False,
        )

    if temp_mld_10 is not None:
        best_standard = "temperature_threshold_ref10"
    elif density_mld_10 is not None:
        best_standard = "density_threshold_ref10"
    elif temp_basic:
        best_standard = "profile_only_no_standard_mld"
    else:
        best_standard = "no_basic_profile"

    return ProfileFitRow(
        provider=provider,
        source=source,
        instrument=instrument,
        cast_id=str(cast_id),
        platform_id=str(platform_id or "unknown"),
        obs_time=str(obs_time),
        lat=round(float(lat), 5),
        lon=round(float(lon), 5),
        n_temp_levels=int(len(depth_t)),
        n_density_levels=int(n_density),
        min_depth_m=round(min_depth, 3),
        max_depth_m=round(max_depth, 3),
        reaches_5m=bool(max_depth >= 5.0),
        reaches_10m=bool(max_depth >= 10.0),
        reaches_15m=bool(max_depth >= 15.0),
        reaches_20m=bool(max_depth >= 20.0),
        reaches_50m=bool(max_depth >= 50.0),
        reaches_100m=bool(max_depth >= 100.0),
        brackets_10m_temp=bool(brackets_10_temp),
        brackets_10m_density=bool(brackets_10_density),
        temp_profile_basic=bool(temp_basic),
        temp_mld_ref10=bool(temp_mld_10 is not None),
        temp_mld_ref10_under100m=bool(temp_mld_10 is not None and temp_mld_10 <= 100.0),
        temp_mld_shallowest_ref=bool(temp_mld_shallow is not None),
        density_profile_basic=bool(density_basic),
        density_mld_ref10=bool(density_mld_10 is not None),
        density_mld_ref10_under100m=bool(density_mld_10 is not None and density_mld_10 <= 100.0),
        density_mld_shallowest_ref=bool(density_mld_shallow is not None),
        best_standard_label=best_standard,
        exploratory_label_available=bool(temp_mld_shallow is not None or density_mld_shallow is not None),
    )


def _decode(value) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="ignore").strip()
    return str(value).strip()


def _wod_var_slice(ds: xr.Dataset, var: str, idx: int, cum_cache: dict[str, np.ndarray]) -> np.ndarray | None:
    row_var = f"{var}_row_size"
    if var not in ds or row_var not in ds:
        return None
    if row_var not in cum_cache:
        sizes = ds[row_var].values.astype(int)
        cum_cache[row_var] = np.concatenate([[0], np.cumsum(sizes)])
    cum = cum_cache[row_var]
    return ds[var].values[cum[idx] : cum[idx + 1]]


def audit_wod_cache(cache_dir: Path, bbox: list[float]) -> list[ProfileFitRow]:
    rows: list[ProfileFitRow] = []
    for path in sorted(cache_dir.glob("wod_*.nc")):
        parts = path.stem.split("_")
        if len(parts) < 3:
            continue
        instrument = parts[1]
        year = parts[2]
        source = f"WOD_{instrument.upper()}_{year}"
        logger.info("Auditing WOD file %s", path.name)
        with xr.open_dataset(path, decode_timedelta=False) as ds:
            lats = ds["lat"].values
            lons = ds["lon"].values
            cast_ids = ds["wod_unique_cast"].values if "wod_unique_cast" in ds else np.arange(len(lats))
            platforms = ds["Platform"].values if "Platform" in ds else np.full(len(lats), b"")
            cruise_ids = (
                ds["WOD_cruise_identifier"].values
                if "WOD_cruise_identifier" in ds
                else np.full(len(lats), b"")
            )
            times = ds["time"].values if "time" in ds else np.full(len(lats), "")
            cum_cache: dict[str, np.ndarray] = {}

            for idx, (lat, lon) in enumerate(zip(lats, lons)):
                try:
                    lat_f = float(lat)
                    lon_f = float(lon)
                except ValueError:
                    continue
                if not in_bbox(lat_f, lon_f, bbox):
                    continue
                depth = _wod_var_slice(ds, "z", idx, cum_cache)
                temp = _wod_var_slice(ds, "Temperature", idx, cum_cache)
                salt = _wod_var_slice(ds, "Salinity", idx, cum_cache)
                if depth is None or temp is None:
                    continue
                try:
                    obs_time = np.datetime_as_string(times[idx], unit="s") + "Z"
                except Exception:
                    obs_time = _decode(times[idx]) if len(times) > idx else ""
                platform = _decode(platforms[idx]) or _decode(cruise_ids[idx])
                row = profile_fit_row(
                    provider="NOAA_NCEI_WOD_CACHE",
                    source=source,
                    instrument=instrument,
                    cast_id=str(cast_ids[idx]),
                    platform_id=platform,
                    obs_time=obs_time,
                    lat=lat_f,
                    lon=lon_f,
                    depth=depth,
                    temp=temp,
                    salt=salt,
                )
                if row:
                    rows.append(row)
    return rows


def _qc_mask(values: np.ndarray) -> np.ndarray:
    flags = np.array([_decode(v) for v in values.ravel()]).reshape(values.shape)
    return np.isin(flags, ["1", "2"])


def _preferred(ds: xr.Dataset, raw: str, adjusted: str) -> tuple[str, str | None]:
    if adjusted in ds and np.isfinite(ds[adjusted].values).any():
        qc = f"{adjusted}_QC"
        return adjusted, qc if qc in ds else None
    qc = f"{raw}_QC"
    return raw, qc if qc in ds else None


def audit_argo_cache(cache_dir: Path, bbox: list[float]) -> list[ProfileFitRow]:
    rows: list[ProfileFitRow] = []
    for path in sorted(cache_dir.glob("**/*.nc")):
        source_file = str(path.relative_to(cache_dir))
        try:
            ds = xr.open_dataset(path, decode_timedelta=False)
        except Exception as exc:
            logger.warning("Skipping unreadable Argo file %s: %s", path, exc)
            continue
        with ds:
            if "PRES" not in ds or "TEMP" not in ds:
                continue
            pres_var, pres_qc_var = _preferred(ds, "PRES", "PRES_ADJUSTED")
            temp_var, temp_qc_var = _preferred(ds, "TEMP", "TEMP_ADJUSTED")
            psal_var, psal_qc_var = _preferred(ds, "PSAL", "PSAL_ADJUSTED") if "PSAL" in ds else (None, None)
            pres = ds[pres_var].values
            temp = ds[temp_var].values
            psal = ds[psal_var].values if psal_var else None
            if pres.ndim == 1:
                pres = pres.reshape(1, -1)
                temp = temp.reshape(1, -1)
                if psal is not None:
                    psal = psal.reshape(1, -1)
            n_prof = int(ds.sizes.get("N_PROF", pres.shape[0]))
            pres_qc = _qc_mask(ds[pres_qc_var].values) if pres_qc_var else np.ones_like(pres, dtype=bool)
            temp_qc = _qc_mask(ds[temp_qc_var].values) if temp_qc_var else np.ones_like(temp, dtype=bool)
            psal_qc = _qc_mask(ds[psal_qc_var].values) if psal_qc_var and psal is not None else None

            for idx in range(n_prof):
                lat = float(ds["LATITUDE"].values[idx])
                lon = float(ds["LONGITUDE"].values[idx])
                if not in_bbox(lat, lon, bbox):
                    continue
                depth = np.asarray(pres[idx], dtype=float)
                temp_i = np.asarray(temp[idx], dtype=float)
                valid_t = pres_qc[idx] & temp_qc[idx]
                depth_t = depth[valid_t]
                temp_t = temp_i[valid_t]
                salt_t = None
                if psal is not None:
                    salt_i = np.asarray(psal[idx], dtype=float)
                    valid_d = valid_t & (psal_qc[idx] if psal_qc is not None else True)
                    depth_t = depth
                    temp_t = temp_i
                    salt_t = salt_i
                    # clean_profile will apply finite filtering; pre-mask bad QC.
                    depth_t = depth_t[valid_d]
                    temp_t = temp_t[valid_d]
                    salt_t = salt_t[valid_d]
                platform = _decode(ds["PLATFORM_NUMBER"].values[idx]) if "PLATFORM_NUMBER" in ds else "unknown"
                cycle = _decode(ds["CYCLE_NUMBER"].values[idx]) if "CYCLE_NUMBER" in ds else str(idx)
                try:
                    obs_time = np.datetime_as_string(ds["JULD"].values[idx], unit="s") + "Z"
                except Exception:
                    obs_time = ""
                row = profile_fit_row(
                    provider="ARGO_GDAC_CACHE",
                    source="ARGO_GDAC",
                    instrument="pfl",
                    cast_id=f"{source_file}:{cycle}",
                    platform_id=platform,
                    obs_time=obs_time,
                    lat=lat,
                    lon=lon,
                    depth=depth_t,
                    temp=temp_t,
                    salt=salt_t,
                )
                if row:
                    rows.append(row)
    return rows


def _fetch_text(url: str, timeout_seconds: int = 120) -> str:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout_seconds, context=ssl_ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _strip_csvp_header_units(text: str) -> str:
    lines = text.strip().splitlines()
    if not lines:
        return text
    cols = []
    for col in lines[0].split(","):
        col = col.strip()
        if " (" in col:
            col = col[: col.index(" (")]
        cols.append(col)
    return ",".join(cols) + "\n" + "\n".join(lines[1:])


def audit_erddap_candidates(bbox: list[float], max_datasets: int) -> list[ProfileFitRow]:
    rows: list[ProfileFitRow] = []
    candidates = load_candidate_datasets(list(DEFAULT_AUDIT_FILES), max_datasets=max_datasets)
    for candidate in candidates:
        dataset_id = candidate.get("source_key", "")
        tabledap_url = candidate.get("url", "")
        if not dataset_id or not tabledap_url:
            continue
        base = tabledap_url.replace(".html", ".csvp")
        query = (
            "time,latitude,longitude,depth,temperature,salinity,profile_id"
            f"&latitude>={bbox[1]}&latitude<={bbox[3]}"
            f"&longitude>={bbox[0]}&longitude<={bbox[2]}"
            "&depth>=0&depth<=1000"
        )
        url = f"{base}?{urllib.parse.quote(query, safe=',&=><')}"
        try:
            text = _strip_csvp_header_units(_fetch_text(url))
        except Exception as exc:
            logger.warning("ERDDAP salinity query failed for %s: %s", dataset_id, exc)
            query = (
                "time,latitude,longitude,depth,temperature,profile_id"
                f"&latitude>={bbox[1]}&latitude<={bbox[3]}"
                f"&longitude>={bbox[0]}&longitude<={bbox[2]}"
                "&depth>=0&depth<=1000"
            )
            url = f"{base}?{urllib.parse.quote(query, safe=',&=><')}"
            try:
                text = _strip_csvp_header_units(_fetch_text(url))
            except Exception as exc2:
                logger.warning("ERDDAP temperature query failed for %s: %s", dataset_id, exc2)
                continue

        by_profile: dict[str, list[dict[str, str]]] = {}
        for item in csv.DictReader(io.StringIO(text)):
            profile_id = (item.get("profile_id") or "").strip()
            if profile_id:
                by_profile.setdefault(profile_id, []).append(item)

        for profile_id, items in by_profile.items():
            depth: list[float] = []
            temp: list[float] = []
            salt: list[float] = []
            lats: list[float] = []
            lons: list[float] = []
            times: list[str] = []
            has_salt = "salinity" in items[0]
            for item in items:
                try:
                    depth.append(float(item["depth"]))
                    temp.append(float(item["temperature"]))
                    if has_salt:
                        salt.append(float(item["salinity"]))
                    lats.append(float(item["latitude"]))
                    lons.append(float(item["longitude"]))
                    times.append(item.get("time", ""))
                except Exception:
                    continue
            row = profile_fit_row(
                provider="ERDDAP_GLIDER_FETCH",
                source=f"ERDDAP_GLIDER_{dataset_id}",
                instrument="erddap_gld",
                cast_id=f"{dataset_id}:{profile_id}",
                platform_id=dataset_id,
                obs_time=min([t for t in times if t], default=""),
                lat=float(np.nanmean(lats)) if lats else np.nan,
                lon=float(np.nanmean(lons)) if lons else np.nan,
                depth=np.asarray(depth),
                temp=np.asarray(temp),
                salt=np.asarray(salt) if len(salt) == len(depth) else None,
            )
            if row:
                rows.append(row)
    return rows


def write_report(df: pd.DataFrame, output_report: Path, output_csv: Path) -> None:
    output_report.parent.mkdir(parents=True, exist_ok=True)
    bool_cols = [
        "temp_profile_basic",
        "temp_mld_ref10",
        "temp_mld_ref10_under100m",
        "temp_mld_shallowest_ref",
        "density_profile_basic",
        "density_mld_ref10",
        "density_mld_ref10_under100m",
        "density_mld_shallowest_ref",
    ]
    grouped = df.groupby(["provider", "source"], dropna=False).agg(
        profiles=("cast_id", "count"),
        platforms=("platform_id", "nunique"),
        dates=("obs_time", lambda s: pd.to_datetime(s, errors="coerce").dt.date.nunique()),
        median_temp_levels=("n_temp_levels", "median"),
        median_density_levels=("n_density_levels", "median"),
        max_depth_median=("max_depth_m", "median"),
        reaches_10m=("reaches_10m", "sum"),
        brackets_10m_temp=("brackets_10m_temp", "sum"),
        brackets_10m_density=("brackets_10m_density", "sum"),
        **{col: (col, "sum") for col in bool_cols},
    ).reset_index()

    with output_report.open("w", encoding="utf-8") as f:
        f.write("# Profile Method Fit Audit\n\n")
        f.write("**Date:** 2026-04-07\n\n")
        f.write(
            "This report audits profile eligibility under multiple MLD label definitions. "
            "It is an inventory report, not a production model-training result.\n\n"
        )
        f.write("## Method Notes\n\n")
        f.write(
            "- `temp_mld_ref10` matches the current standard 10m, 0.2 C temperature-threshold label.\n"
        )
        f.write(
            "- `density_mld_ref10` uses a standard 10m, 0.03 kg/m^3 density-threshold label and requires salinity.\n"
        )
        f.write(
            "- `*_shallowest_ref` columns are exploratory relaxed labels using the shallowest valid sample as the reference; they are not directly comparable to the current 10m label.\n"
        )
        f.write(
            "- Density is computed with an EOS-80 surface-density approximation for audit purposes; production density MLD should use TEOS-10/GSW if available.\n\n"
        )
        f.write("## Overall Counts\n\n")
        f.write(f"- Profiles audited: {len(df)}\n")
        f.write(f"- Providers: {df['provider'].value_counts().to_dict()}\n")
        for col in bool_cols:
            f.write(f"- {col}: {int(df[col].sum())}\n")
        f.write("\n## Source Summary\n\n")
        f.write(markdown_table(grouped))
        f.write("\n\n")
        f.write(f"Detailed CSV: `{output_csv}`\n")


def markdown_table(df: pd.DataFrame) -> str:
    """Small dependency-free Markdown table formatter."""
    if df.empty:
        return "_No rows._"
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in cols]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    bbox = [float(v) for v in args.bbox.split(",") if v.strip()]

    rows: list[ProfileFitRow] = []
    if args.include_wod:
        rows.extend(audit_wod_cache(args.wod_cache_dir, bbox))
    if args.include_argo_cache:
        rows.extend(audit_argo_cache(args.argo_cache_dir, bbox))
    if args.include_erddap:
        rows.extend(audit_erddap_candidates(bbox, args.erddap_max_datasets))

    df = pd.DataFrame([asdict(row) for row in rows])
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    write_report(df, args.output_report, args.output_csv)
    logger.info("Wrote %d profile rows to %s", len(df), args.output_csv)
    logger.info("Wrote report to %s", args.output_report)


if __name__ == "__main__":
    main()
