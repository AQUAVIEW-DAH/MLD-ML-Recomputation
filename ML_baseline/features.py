import numpy as np
import xarray as xr
from dataclasses import dataclass
from typing import Optional, Dict

from mld_core import find_nearest_valid_point, compute_mld_temp_threshold

@dataclass
class MLFeatures:
    model_mld: float
    model_sst: float
    sst_gradient: float

def compute_local_sst_gradient(ds: xr.Dataset, i: int, j: int) -> float:
    """
    Computes a simple centered-difference magnitude for the Sea Surface Temperature
    at grid index (i, j) to serve as a proxy for Frontogenesis.
    """
    surf_temp = ds["temperature"].isel(MT=0, Depth=0).values
    
    max_y, max_x = surf_temp.shape
    
    # Safe bounds checking for finite differences
    y_min = max(0, i - 1)
    y_max = min(max_y - 1, i + 1)
    
    x_min = max(0, j - 1)
    x_max = min(max_x - 1, j + 1)
    
    dy = surf_temp[y_max, j] - surf_temp[y_min, j]
    dx = surf_temp[i, x_max] - surf_temp[i, x_min]
    
    # Handle NaNs near land masks gracefully
    if np.isnan(dy): dy = 0.0
    if np.isnan(dx): dx = 0.0
    
    return float(np.sqrt(dx**2 + dy**2))

def extract_ml_features(ds: xr.Dataset, lat: float, lon: float) -> Optional[MLFeatures]:
    """
    Extracts the feature vector required for the ML model at a given Lat/Lon.
    """
    try:
        i, j = find_nearest_valid_point(ds, lat, lon)
    except ValueError:
        return None
        
    # Extract profile for MLD
    profile = ds["temperature"].isel(MT=0, Y=i, X=j).values
    depth = ds["Depth"].values
    
    model_mld = compute_mld_temp_threshold(depth, profile)
    if model_mld is None:
        return None
        
    # Extract SST (Surface Temp)
    model_sst = profile[0]
    if np.isnan(model_sst):
        return None
        
    # Compute the Gradient (Front Proxy)
    sst_grad = compute_local_sst_gradient(ds, i, j)
    
    return MLFeatures(
        model_mld=float(model_mld),
        model_sst=float(model_sst),
        sst_gradient=sst_grad
    )
