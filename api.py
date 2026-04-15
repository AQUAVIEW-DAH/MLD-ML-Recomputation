import os
import pickle
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from historical_replay import (
    DEFAULT_REPLAY_DATA_PATH,
    find_nearby_replay_observations,
    get_replay_metadata,
    parse_iso8601,
    get_rtofs_path_for_query_time,
    load_replay_dataframe,
)
from ML_baseline.features import extract_ml_features
from mld_core import DEFAULT_RTOFS_FILE, compute_mld_temp_threshold
from mld_pipeline import get_mld_estimate

APP_MODE = os.getenv("APP_MODE", "historical_replay").strip().lower()
DEFAULT_REPLAY_MODEL_PATH = "ML_baseline/model_historical_replay_2025_jul_aug.pkl"
DEFAULT_LAYER_BBOX = {
    "lat_min": 18.0,
    "lat_max": 31.5,
    "lon_min": -98.5,
    "lon_max": -80.0,
}
DEFAULT_LAYER_STRIDE = 12
MAX_LAYER_POINTS = 450

rtofs_ds = None
replay_df = None
replay_metadata = None
rtofs_cache: dict[str, xr.Dataset] = {}
layer_cache: dict[tuple[str, str, int], dict] = {}
ml_model_cache = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rtofs_ds, replay_df, replay_metadata, rtofs_cache, layer_cache, ml_model_cache
    if APP_MODE == "historical_replay":
        if not os.getenv("ML_MODEL_PATH"):
            os.environ["ML_MODEL_PATH"] = DEFAULT_REPLAY_MODEL_PATH
        replay_df = load_replay_dataframe(DEFAULT_REPLAY_DATA_PATH)
        replay_metadata = get_replay_metadata(replay_df)
        replay_metadata["active_model_path"] = os.getenv("ML_MODEL_PATH")
        print(f"Loaded historical replay metadata from {DEFAULT_REPLAY_DATA_PATH}.")
    else:
        print(f"Loading RTOFS dataset from {DEFAULT_RTOFS_FILE}...")
        try:
            rtofs_ds = xr.open_dataset(DEFAULT_RTOFS_FILE)
            print("Dataset loaded successfully.")
        except Exception as e:
            print(f"Failed to load dataset: {e}")
    yield
    if rtofs_ds is not None:
        rtofs_ds.close()
    for ds in rtofs_cache.values():
        ds.close()
    ml_model_cache = None


app = FastAPI(
    title="MLD MVP API",
    description="API for corrected mixed layer depth estimates in historical replay or legacy mode.",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MLDQueryRequest(BaseModel):
    lat: float
    lon: float
    time: str



def get_replay_dataset(query_time: str) -> xr.Dataset:
    path = str(get_rtofs_path_for_query_time(query_time))
    if path not in rtofs_cache:
        rtofs_cache[path] = xr.open_dataset(Path(path))
    return rtofs_cache[path]



def get_ml_model():
    global ml_model_cache
    if ml_model_cache is not None:
        return ml_model_cache

    ml_model_path = os.getenv("ML_MODEL_PATH", DEFAULT_REPLAY_MODEL_PATH)
    if not os.path.exists(ml_model_path):
        raise FileNotFoundError(f"ML model file not found at {ml_model_path}")

    with open(ml_model_path, "rb") as f:
        ml_model_cache = pickle.load(f)
    return ml_model_cache



def _predict_correction(ds: xr.Dataset, lat: float, lon: float) -> float | None:
    features = extract_ml_features(ds, lat, lon)
    if features is None:
        return None

    model = get_ml_model()
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
    if not np.isfinite(correction):
        return None
    return correction



def _build_model_mld_layer(ds: xr.Dataset, stride: int = DEFAULT_LAYER_STRIDE) -> dict:
    stride = max(1, int(stride))
    layer_time = str(ds["MT"].isel(MT=0).values)
    lats = ds["Latitude"].values
    lons = ds["Longitude"].values
    temp = ds["temperature"].isel(MT=0).values
    depth = ds["Depth"].values
    surf = temp[0]

    points = []
    for y in range(0, lats.shape[0], stride):
        for x in range(0, lats.shape[1], stride):
            lat = float(lats[y, x])
            lon = float(lons[y, x])
            if not np.isfinite(lat) or not np.isfinite(lon):
                continue
            if not (DEFAULT_LAYER_BBOX["lat_min"] <= lat <= DEFAULT_LAYER_BBOX["lat_max"]):
                continue
            if not (DEFAULT_LAYER_BBOX["lon_min"] <= lon <= DEFAULT_LAYER_BBOX["lon_max"]):
                continue
            if not np.isfinite(surf[y, x]):
                continue

            profile = temp[:, y, x]
            mld = compute_mld_temp_threshold(depth, profile)
            if mld is None or not np.isfinite(mld):
                continue

            points.append({
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "value": round(float(mld), 3),
                "y_index": int(y),
                "x_index": int(x),
            })
            if len(points) >= MAX_LAYER_POINTS:
                break
        if len(points) >= MAX_LAYER_POINTS:
            break

    values = [p["value"] for p in points]
    return {
        "layer": "model_mld",
        "time": layer_time,
        "point_count": len(points),
        "stride": stride,
        "bbox": DEFAULT_LAYER_BBOX,
        "value_min": min(values) if values else None,
        "value_max": max(values) if values else None,
        "points": points,
    }



def _build_correction_layer(ds: xr.Dataset, stride: int = DEFAULT_LAYER_STRIDE) -> dict:
    stride = max(1, int(stride))
    layer_time = str(ds["MT"].isel(MT=0).values)
    lats = ds["Latitude"].values
    lons = ds["Longitude"].values
    surf = ds["temperature"].isel(MT=0, Depth=0).values

    points = []
    for y in range(0, lats.shape[0], stride):
        for x in range(0, lats.shape[1], stride):
            lat = float(lats[y, x])
            lon = float(lons[y, x])
            if not np.isfinite(lat) or not np.isfinite(lon):
                continue
            if not (DEFAULT_LAYER_BBOX["lat_min"] <= lat <= DEFAULT_LAYER_BBOX["lat_max"]):
                continue
            if not (DEFAULT_LAYER_BBOX["lon_min"] <= lon <= DEFAULT_LAYER_BBOX["lon_max"]):
                continue
            if not np.isfinite(surf[y, x]):
                continue

            correction = _predict_correction(ds, lat, lon)
            if correction is None:
                continue

            points.append({
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "value": round(float(correction), 3),
                "y_index": int(y),
                "x_index": int(x),
            })
            if len(points) >= MAX_LAYER_POINTS:
                break
        if len(points) >= MAX_LAYER_POINTS:
            break

    values = [p["value"] for p in points]
    return {
        "layer": "correction",
        "time": layer_time,
        "point_count": len(points),
        "stride": stride,
        "bbox": DEFAULT_LAYER_BBOX,
        "value_min": min(values) if values else None,
        "value_max": max(values) if values else None,
        "points": points,
    }


def _build_corrected_mld_layer(ds: xr.Dataset, stride: int = DEFAULT_LAYER_STRIDE) -> dict:
    model_layer = _build_model_mld_layer(ds, stride=stride)
    correction_layer = _build_correction_layer(ds, stride=stride)
    correction_lookup = {
        (point["y_index"], point["x_index"]): point["value"]
        for point in correction_layer["points"]
    }

    points = []
    for point in model_layer["points"]:
        correction = correction_lookup.get((point["y_index"], point["x_index"]))
        if correction is None:
            continue
        points.append({
            "lat": point["lat"],
            "lon": point["lon"],
            "value": round(float(point["value"] + correction), 3),
            "y_index": point["y_index"],
            "x_index": point["x_index"],
        })

    values = [p["value"] for p in points]
    return {
        "layer": "corrected_mld",
        "time": model_layer["time"],
        "point_count": len(points),
        "stride": stride,
        "bbox": DEFAULT_LAYER_BBOX,
        "value_min": min(values) if values else None,
        "value_max": max(values) if values else None,
        "points": points,
    }


def _build_observations_layer(query_time: str) -> dict:
    if replay_df is None:
        return {
            "layer": "observations",
            "time": query_time,
            "point_count": 0,
            "points": [],
        }

    replay_date = parse_iso8601(query_time).date().isoformat()
    day_df = replay_df[replay_df["replay_date"] == replay_date].copy()
    if day_df.empty:
        return {
            "layer": "observations",
            "time": query_time,
            "point_count": 0,
            "points": [],
        }

    points = []
    for _, row in day_df.sort_values(["obs_time_dt", "platform_id"]).iterrows():
        obs_mld = row.get("observed_mld")
        lat = row.get("lat")
        lon = row.get("lon")
        if not np.isfinite(obs_mld) or not np.isfinite(lat) or not np.isfinite(lon):
            continue
        points.append({
            "id": str(row.get("cast_id", row.get("platform_id", ""))),
            "platform_id": str(row.get("platform_id", "")),
            "source": str(row.get("source_family", row.get("wod_source", "replay"))),
            "obs_time": row["obs_time_dt"].isoformat().replace("+00:00", "Z"),
            "lat": round(float(lat), 4),
            "lon": round(float(lon), 4),
            "value": round(float(obs_mld), 3),
        })

    values = [p["value"] for p in points]
    return {
        "layer": "observations",
        "time": query_time,
        "point_count": len(points),
        "value_min": min(values) if values else None,
        "value_max": max(values) if values else None,
        "points": points,
    }


@app.post("/mld")
def query_mld(req: MLDQueryRequest):
    try:
        if APP_MODE == "historical_replay":
            if replay_df is None:
                raise HTTPException(status_code=500, detail="Historical replay dataset not loaded.")
            ds = get_replay_dataset(req.time)
            nearby = find_nearby_replay_observations(replay_df, req.lat, req.lon, req.time)
            res = get_mld_estimate(req.lat, req.lon, req.time, ds, nearby_observations=nearby)
            return asdict(res)

        if rtofs_ds is None:
            raise HTTPException(status_code=500, detail="RTOFS dataset not available on the server.")
        res = get_mld_estimate(req.lat, req.lon, req.time, rtofs_ds)
        return asdict(res)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/map_layer")
def map_layer(
    time: str = Query(...),
    layer: str = Query("model_mld"),
    stride: int = Query(DEFAULT_LAYER_STRIDE, ge=1, le=40),
):
    if APP_MODE != "historical_replay":
        raise HTTPException(status_code=400, detail="Map layers are currently available only in historical replay mode.")
    if layer not in {"model_mld", "correction", "corrected_mld", "observations"}:
        raise HTTPException(status_code=400, detail=f"Unsupported layer '{layer}'.")

    if layer == "observations":
        cache_key = (f"observations:{parse_iso8601(time).date().isoformat()}", layer, stride)
        if cache_key not in layer_cache:
            layer_cache[cache_key] = _build_observations_layer(time)
        return layer_cache[cache_key]

    ds = get_replay_dataset(time)
    cache_key = (str(get_rtofs_path_for_query_time(time)), layer, stride)
    if cache_key not in layer_cache:
        if layer == "model_mld":
            layer_cache[cache_key] = _build_model_mld_layer(ds, stride=stride)
        elif layer == "correction":
            layer_cache[cache_key] = _build_correction_layer(ds, stride=stride)
        elif layer == "corrected_mld":
            layer_cache[cache_key] = _build_corrected_mld_layer(ds, stride=stride)
        else:
            layer_cache[cache_key] = _build_observations_layer(time)
    return layer_cache[cache_key]


@app.get("/metadata")
def metadata():
    if APP_MODE == "historical_replay":
        return replay_metadata or {"mode": APP_MODE}
    return {
        "mode": APP_MODE,
        "default_query_time": None,
        "available_dates": [],
        "active_model_path": os.getenv("ML_MODEL_PATH"),
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "mode": APP_MODE,
        "dataset_loaded": (replay_df is not None) if APP_MODE == "historical_replay" else (rtofs_ds is not None),
        "cached_rtofs_datasets": len(rtofs_cache),
        "cached_layers": len(layer_cache),
        "active_model_path": os.getenv("ML_MODEL_PATH"),
    }
