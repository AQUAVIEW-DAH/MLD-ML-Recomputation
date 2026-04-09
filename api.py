import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

import xarray as xr
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from historical_replay import (
    DEFAULT_REPLAY_DATA_PATH,
    find_nearby_replay_observations,
    get_replay_metadata,
    get_rtofs_path_for_query_time,
    load_replay_dataframe,
)
from mld_core import DEFAULT_RTOFS_FILE
from mld_pipeline import get_mld_estimate

APP_MODE = os.getenv("APP_MODE", "historical_replay").strip().lower()
DEFAULT_REPLAY_MODEL_PATH = "ML_baseline/model_historical_replay_2025_jul_aug.pkl"

rtofs_ds = None
replay_df = None
replay_metadata = None
rtofs_cache: dict[str, xr.Dataset] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rtofs_ds, replay_df, replay_metadata, rtofs_cache
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


app = FastAPI(
    title="MLD MVP API",
    description="API for corrected mixed layer depth estimates in historical replay or legacy mode.",
    version="0.2.0",
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
        "active_model_path": os.getenv("ML_MODEL_PATH"),
    }
