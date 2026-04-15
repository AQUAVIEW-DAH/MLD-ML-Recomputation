from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Any, List, Optional
from math import radians, cos, sin, asin, sqrt

import xarray as xr

from mld_core import get_model_mld, compute_mld_temp_threshold
from aquaview_obs import (
    AquaviewClient,
    search_with_primary_fallback,
    extract_erddap_profiles,
    extract_gadr_profiles,
    ObservationProfile,
)

logger = logging.getLogger(__name__)
DEFAULT_ML_MODEL_PATH = "artifacts/models/model.pkl"


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
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
    confidence: str
    model_mld: float
    correction_applied: float
    nearby_observations: List[dict[str, Any]]
    window_used: str


def confidence_from_support(model_loaded: bool, nearby_count: int) -> str:
    if not model_loaded:
        return "Low"
    if nearby_count >= 3:
        return "High"
    if nearby_count >= 1:
        return "Medium"
    return "Low"



def get_mld_estimate(
    lat: float,
    lon: float,
    query_time: str,
    rtofs_ds: xr.Dataset,
    client: Optional[AquaviewClient] = None,
    nearby_observations: Optional[List[dict[str, Any]]] = None,
) -> MLDEstimateResult:
    if client is None:
        client = AquaviewClient()

    model_result = get_model_mld(rtofs_ds, lat, lon)
    base_mld = model_result.mld_m
    if base_mld is None:
        raise ValueError("Could not compute a valid model MLD at this location.")

    obs_mld_results: List[ObservationMLDResult] = []
    window_used = "none"
    nearby_obs_dicts: List[dict[str, Any]] = []

    if nearby_observations is not None:
        window_used = "historical_replay_local"
        nearby_obs_dicts = nearby_observations
    else:
        try:
            search_res = search_with_primary_fallback(client, lat, lon, query_time)
            window_used = search_res.get("window_used", "none")
            features = search_res.get("features", [])

            search_body = search_res.get("search_body", {})
            bbox = search_body.get("bbox", [])
            dt_range = search_body.get("datetime", "").split("/")
            start_time, end_time = (dt_range[0], dt_range[1]) if len(dt_range) == 2 else ("", "")

            for item in features:
                collection = item.get("collection", "")
                if "ioos" in collection.lower():
                    try:
                        profiles = extract_erddap_profiles(item, bbox, start_time, end_time)
                        for p in profiles:
                            obs_mld = compute_mld_temp_threshold(p.depth_m, p.temperature_c)
                            if obs_mld is not None:
                                dist = haversine(lon, lat, p.lon, p.lat)
                                obs_mld_results.append(
                                    ObservationMLDResult(profile=p, mld_m=obs_mld, distance_km=dist)
                                )
                    except Exception as e:
                        logger.warning("Failed to extract profiles from item %s: %s", item.get("id"), e)
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
                        logger.warning("Failed to extract profiles from GADR %s: %s", item.get("id"), e)
        except Exception as e:
            logger.warning("Aquaview observation lookup failed; continuing model-only: %s", e)
            window_used = "lookup_failed"

        nearby_obs_dicts = [
            {
                "id": res.profile.profile_id,
                "platform_id": res.profile.platform_id,
                "obs_time": res.profile.obs_time,
                "distance_km": round(res.distance_km, 2),
                "mld_m": round(res.mld_m, 2),
                "source": res.profile.source,
                "lat": round(res.profile.lat, 4),
                "lon": round(res.profile.lon, 4),
            }
            for res in obs_mld_results
        ]

    import pickle
    import pandas as pd
    from ml.features import extract_ml_features

    correction = 0.0
    ml_model_loaded = False
    ml_model_path = os.getenv("ML_MODEL_PATH", DEFAULT_ML_MODEL_PATH)

    if os.path.exists(ml_model_path):
        try:
            with open(ml_model_path, "rb") as f:
                model = pickle.load(f)

            features = extract_ml_features(rtofs_ds, lat, lon)
            if features is not None:
                X = pd.DataFrame([
                    {
                        "model_sst": features.model_sst,
                        "sst_gradient": features.sst_gradient,
                        "model_salinity": features.model_salinity,
                        "kinetic_energy": features.kinetic_energy,
                        "model_mld": features.model_mld,
                    }
                ])
                correction = float(model.predict(X)[0])
                ml_model_loaded = True
        except Exception as e:
            logger.error("Failed to apply ML model from %s: %s", ml_model_path, e)

    best_estimate = base_mld + correction
    confidence = confidence_from_support(ml_model_loaded, len(nearby_obs_dicts))

    return MLDEstimateResult(
        query_lat=lat,
        query_lon=lon,
        query_time=query_time,
        best_estimate_mld=round(best_estimate, 2),
        confidence=confidence,
        model_mld=round(base_mld, 2),
        correction_applied=round(correction, 2),
        nearby_observations=nearby_obs_dicts,
        window_used=window_used,
    )
