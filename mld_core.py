from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr


DEFAULT_RTOFS_FILE = Path("rtofs_glo_3dz_f054_6hrly_hvr_US_east.nc")


@dataclass(frozen=True)
class ModelMLDResult:
    query_lat: float
    query_lon: float
    grid_lat: float
    grid_lon: float
    time: str
    mld_m: float | None
    y_index: int
    x_index: int
    source: str = "RTOFS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_lat": self.query_lat,
            "query_lon": self.query_lon,
            "grid_lat": self.grid_lat,
            "grid_lon": self.grid_lon,
            "time": self.time,
            "mld_m": self.mld_m,
            "y_index": self.y_index,
            "x_index": self.x_index,
            "source": self.source,
        }


def open_rtofs_dataset(path: str | Path = DEFAULT_RTOFS_FILE) -> xr.Dataset:
    return xr.open_dataset(Path(path))


def find_nearest_valid_point(ds: xr.Dataset, lat: float, lon: float) -> tuple[int, int]:
    lats = ds["Latitude"].values
    lons = ds["Longitude"].values
    surf = ds["temperature"].isel(MT=0, Depth=0).values

    valid = np.isfinite(surf) & np.isfinite(lats) & np.isfinite(lons)
    if not np.any(valid):
        raise ValueError("No valid ocean points found in dataset")

    dist2 = (lats - lat) ** 2 + (lons - lon) ** 2
    dist2[~valid] = np.inf

    i, j = np.unravel_index(np.argmin(dist2), dist2.shape)
    return int(i), int(j)


def compute_mld_temp_threshold(
    depth: np.ndarray | list[float],
    temp: np.ndarray | list[float],
    ref_depth: float = 10.0,
    delta_t: float = 0.2,
) -> float | None:
    depth_arr = np.asarray(depth, dtype=float)
    temp_arr = np.asarray(temp, dtype=float)

    mask = np.isfinite(depth_arr) & np.isfinite(temp_arr)
    depth_arr = depth_arr[mask]
    temp_arr = temp_arr[mask]

    if len(depth_arr) == 0:
        return None

    order = np.argsort(depth_arr)
    depth_arr = depth_arr[order]
    temp_arr = temp_arr[order]

    if ref_depth < depth_arr.min() or ref_depth > depth_arr.max():
        return None

    tref = np.interp(ref_depth, depth_arr, temp_arr)
    target = tref - delta_t

    for idx in range(len(depth_arr)):
        if depth_arr[idx] <= ref_depth:
            continue
        if temp_arr[idx] <= target:
            z1, z2 = depth_arr[idx - 1], depth_arr[idx]
            t1, t2 = temp_arr[idx - 1], temp_arr[idx]
            if np.isclose(t1, t2):
                return float(z2)
            return float(z1 + (target - t1) * (z2 - z1) / (t2 - t1))

    return None


def get_model_mld(ds: xr.Dataset, lat: float, lon: float) -> ModelMLDResult:
    i, j = find_nearest_valid_point(ds, lat, lon)
    profile = ds["temperature"].isel(MT=0, Y=i, X=j).values
    depth = ds["Depth"].values
    mld = compute_mld_temp_threshold(depth, profile)

    return ModelMLDResult(
        query_lat=float(lat),
        query_lon=float(lon),
        grid_lat=float(ds["Latitude"].isel(Y=i, X=j).item()),
        grid_lon=float(ds["Longitude"].isel(Y=i, X=j).item()),
        time=str(ds["MT"].isel(MT=0).values),
        mld_m=mld,
        y_index=i,
        x_index=j,
    )
