from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional
from math import radians, cos, sin, asin, sqrt

import xarray as xr

from mld_core import get_model_mld, compute_mld_temp_threshold
from aquaview_obs import (
    AquaviewClient, 
    search_with_primary_fallback, 
    extract_ioos_profiles,
    extract_gadr_profiles,
    ObservationProfile
)

logger = logging.getLogger(__name__)

def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate great-circle distance between two points on Earth in km."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371.0

@dataclass
class ObservationMLDResult:
    profile: ObservationProfile
    mld_m: float
    distance_km: float

@dataclass
class MLDEstimateResult:
    query_lat: float
    query_lon: float
    query_time: str
    best_estimate_mld: float
    confidence: str  # High, Med, Low
    model_mld: float
    correction_applied: float
    nearby_observations: List[dict[str, Any]]
    window_used: str

def compute_inverse_distance_weighting(obs_results: List[ObservationMLDResult]) -> float:
    """Simple inverse distance weighting for MVP blender."""
    if not obs_results:
        return 0.0
    
    weights = []
    values = []
    
    for obs in obs_results:
        # Avoid division by zero for exactly co-located points
        dist = max(obs.distance_km, 1.0)
        weight = 1.0 / dist
        weights.append(weight)
        values.append(obs.mld_m)
        
    return sum(w * v for w, v in zip(weights, values)) / sum(weights)


def get_mld_estimate(
    lat: float, 
    lon: float, 
    query_time: str, 
    rtofs_ds: xr.Dataset,
    client: Optional[AquaviewClient] = None
) -> MLDEstimateResult:
    """
    Combines Model MLD and Aquaview Observations to produce an outcome.
    For the MVP, this acts as the "Blender" returning a weighted average of nearby obs
    if available, otherwise it falls back to the model.
    """
    if client is None:
        client = AquaviewClient()
        
    # 1. Get Model Value
    model_result = get_model_mld(rtofs_ds, lat, lon)
    base_mld = model_result.mld_m
    if base_mld is None:
        raise ValueError("Could not compute a valid model MLD at this location.")

    # 2. Search for Nearby Observations via Aquaview
    search_res = search_with_primary_fallback(client, lat, lon, query_time)
    
    window_used = search_res.get("window_used", "none")
    features = search_res.get("features", [])
    
    # 3. Extract profiles and compute their individual MLDs
    obs_mld_results: List[ObservationMLDResult] = []
    
    # Needs to match the datetime range of the search window used
    search_body = search_res.get("search_body", {})
    bbox = search_body.get("bbox", [])
    dt_range = search_body.get("datetime", "").split("/")
    start_time, end_time = (dt_range[0], dt_range[1]) if len(dt_range) == 2 else ("", "")
    
    for item in features:
        collection = item.get("collection", "")
        if "ioos" in collection.lower():
            try:
                profiles = extract_ioos_profiles(item, bbox, start_time, end_time)
                for p in profiles:
                    obs_mld = compute_mld_temp_threshold(p.depth_m, p.temperature_c)
                    if obs_mld is not None:
                        dist = haversine(lon, lat, p.lon, p.lat)
                        obs_mld_results.append(
                            ObservationMLDResult(profile=p, mld_m=obs_mld, distance_km=dist)
                        )
            except Exception as e:
                logger.warning(f"Failed to extract profiles from item {item.get('id')}: {e}")
        elif "gadr" in collection.lower():
            try:
                profiles = extract_gadr_profiles(item, bbox, start_time, end_time)
                for p in profiles:
                    obs_mld = compute_mld_temp_threshold(p.depth_m, p.temperature_c)
                    if obs_mld is not None:
                        dist = haversine(lon, lat, p.lon, p.lat)
                        obs_mld_results.append(
                            ObservationMLDResult(profile=p, mld_m=obs_mld, distance_km=dist)
                        )
            except Exception as e:
                logger.warning(f"Failed to extract profiles from GADR {item.get('id')}: {e}")

    # 4. Blend Model and Observations (The 'Intelligence' layer MVP)
    import os
    import pickle
    import numpy as np
    from ML_baseline.features import extract_ml_features
    
    correction = 0.0
    confidence = "Low"
    
    # Check for Machine Learning Engine
    if os.path.exists("ML_baseline/model.pkl"):
        try:
            import pandas as pd
            with open("ML_baseline/model.pkl", "rb") as f:
                model = pickle.load(f)
                
            features = extract_ml_features(rtofs_ds, lat, lon)
            if features is not None:
                # Predict the residual
                X = pd.DataFrame([{
                    'model_sst': features.model_sst, 
                    'sst_gradient': features.sst_gradient, 
                    'model_salinity': features.model_salinity,
                    'kinetic_energy': features.kinetic_energy,
                    'model_mld': features.model_mld
                }])
                correction = float(model.predict(X)[0])
                confidence = "High"
        except Exception as e:
            logger.error(f"Failed to apply ML model: {e}")
            
    # Apply Correction
    best_estimate = base_mld + correction
    
    # Prepare serializable provenance info
    nearby_obs_dicts = [
        {
            "id": res.profile.profile_id,
            "obs_time": res.profile.obs_time,
            "distance_km": round(res.distance_km, 2),
            "mld_m": round(res.mld_m, 2),
            "source": res.profile.source,
        }
        for res in obs_mld_results
    ]

    return MLDEstimateResult(
        query_lat=lat,
        query_lon=lon,
        query_time=query_time,
        best_estimate_mld=round(best_estimate, 2),
        confidence=confidence,
        model_mld=round(base_mld, 2),
        correction_applied=round(correction, 2),
        nearby_observations=nearby_obs_dicts,
        window_used=window_used
    )
