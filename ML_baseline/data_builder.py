import sys; import os; sys.path.insert(0, os.path.abspath(".."))
import time
import pandas as pd
import xarray as xr
import logging
from typing import List, Dict

from mld_core import DEFAULT_RTOFS_FILE, compute_mld_temp_threshold
from aquaview_obs import AquaviewClient, build_stac_search_body, extract_ioos_profiles, extract_gadr_profiles
from features import extract_ml_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gulf of Mexico coordinates covering massive array
GOM_BBOX = [-100.0, 15.0, -50.0, 50.0]
GOM_CENTER_LAT = 25.0
GOM_CENTER_LON = -90.0

def build_dataset():
    logger.info("Initializing Dataset Builder...")
    
    logger.info("Loading RTOFS Model Subset...")
    rtofs_ds = xr.open_dataset(DEFAULT_RTOFS_FILE)
    
    model_time = str(rtofs_ds["MT"].isel(MT=0).values)
    # Give a wide 5 day window to gather massive historic anomaly context around the model slice!
    start_time = "2026-03-29T00:00:00Z"
    end_time = "2026-04-03T23:59:59Z"
    
    client = AquaviewClient()
    
    # We use a broad STAC query over the Gulf bounding box
    body = {
        "collections": ["GADR", "IOOS"],
        "bbox": GOM_BBOX,
        "datetime": f"{start_time}/{end_time}",
        "limit": 100
    }
    
    logger.info(f"Querying Aquaview catalog across {start_time}/{end_time}...")
    res = client.search(body)
    features = res.get("features", [])
    logger.info(f"Found {len(features)} STAC items intersecting window via STAC.")
    
    dataset_rows = []
    
    count_profiles = 0
    
    for item in features:
        collection = item.get("collection", "").lower()
        extracted = []
        
        try:
            if "ioos" in collection:
                extracted = extract_ioos_profiles(item, GOM_BBOX, "", "")
            elif "gadr" in collection:
                extracted = extract_gadr_profiles(item, GOM_BBOX, "", "")
        except Exception as e:
            logger.warning(f"Parse failure on {item.get('id')}: {e}")
            continue
            
        for profile in extracted:
            obs_mld = compute_mld_temp_threshold(profile.depth_m, profile.temperature_c)
            if obs_mld is None:
                continue
                
            # Extract ML Features for this specific local coordinate
            # If coordinates are entirely offshore or NaN on RTOFS, this handles it
            feat = extract_ml_features(rtofs_ds, profile.lat, profile.lon)
            if feat is None:
                continue
                
            dataset_rows.append({
                "source": profile.source,
                "lat": round(profile.lat, 4),
                "lon": round(profile.lon, 4),
                "obs_time": profile.obs_time,
                "model_sst": round(feat.model_sst, 4),
                "sst_gradient": round(feat.sst_gradient, 6),
                "model_mld": round(feat.model_mld, 4),
                "observed_mld": round(obs_mld, 4),
                "target_delta_mld": round(obs_mld - feat.model_mld, 4)
            })
            count_profiles += 1
            
    logger.info(f"Extracted a final training dataset of {count_profiles} physical data points.")
    
    df = pd.DataFrame(dataset_rows)
    df.to_csv("training_data.csv", index=False)
    logger.info("Saved strictly engineered tabular data to: training_data.csv")

if __name__ == "__main__":
    build_dataset()
