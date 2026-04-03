import xarray as xr
import numpy as np

ds = xr.open_dataset("rtofs_glo_3dz_f054_6hrly_hvr_US_east.nc")
print(ds)

print(ds["temperature"])
print(ds["salinity"])
print(ds["u"])
print(ds["v"])

print(ds["temperature"].attrs)
print(ds["salinity"].attrs)


#compute mld based on lat long
def find_nearest_valid_point(ds, lat, lon):
    lats = ds["Latitude"].values
    lons = ds["Longitude"].values
    surf = ds["temperature"].isel(MT=0, Depth=0).values

    valid = np.isfinite(surf) & np.isfinite(lats) & np.isfinite(lons)
    if not np.any(valid):
        raise ValueError("No valid ocean points found in dataset")

    # simple squared-distance in lat/lon space
    dist2 = (lats - lat)**2 + (lons - lon)**2
    dist2[~valid] = np.inf

    i, j = np.unravel_index(np.argmin(dist2), dist2.shape)
    return i, j

def compute_mld_temp_threshold(depth, temp, ref_depth=10.0, delta_t=0.2):
    depth = np.asarray(depth, dtype=float)
    temp = np.asarray(temp, dtype=float)

    mask = np.isfinite(depth) & np.isfinite(temp)
    depth = depth[mask]
    temp = temp[mask]

    if len(depth) == 0:
        return None

    order = np.argsort(depth)
    depth = depth[order]
    temp = temp[order]

    if ref_depth < depth.min() or ref_depth > depth.max():
        return None

    tref = np.interp(ref_depth, depth, temp)
    target = tref - delta_t

    for k in range(len(depth)):
        if depth[k] <= ref_depth:
            continue
        if temp[k] <= target:
            z1, z2 = depth[k-1], depth[k]
            t1, t2 = temp[k-1], temp[k]
            if np.isclose(t1, t2):
                return float(z2)
            return float(z1 + (target - t1) * (z2 - z1) / (t2 - t1))

    return None

def get_model_mld(ds, lat, lon):
    i, j = find_nearest_valid_point(ds, lat, lon)
    profile = ds["temperature"].isel(MT=0, Y=i, X=j).values
    depth = ds["Depth"].values

    mld = compute_mld_temp_threshold(depth, profile)

    return {
        "query_lat": lat,
        "query_lon": lon,
        "grid_lat": float(ds["Latitude"].isel(Y=i, X=j).item()),
        "grid_lon": float(ds["Longitude"].isel(Y=i, X=j).item()),
        "time": str(ds["MT"].isel(MT=0).values),
        "mld_m": mld,
        "y_index": int(i),
        "x_index": int(j),
    }

result = get_model_mld(ds, 28.5, -88.2)
print(result)