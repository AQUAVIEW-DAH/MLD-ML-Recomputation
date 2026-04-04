from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import xarray as xr
from dataclasses import asdict
from contextlib import asynccontextmanager

from mld_pipeline import get_mld_estimate
from mld_core import DEFAULT_RTOFS_FILE

# Global variable to hold our loaded RTOFS dataset
rtofs_ds = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rtofs_ds
    print(f"Loading RTOFS dataset from {DEFAULT_RTOFS_FILE}...")
    try:
        # Load dataset lazily or fully, depends precisely on xr behavior, but keeps the handle open
        rtofs_ds = xr.open_dataset(DEFAULT_RTOFS_FILE)
        print("Dataset loaded successfully.")
    except Exception as e:
        print(f"Failed to load dataset: {e}")
    yield
    if rtofs_ds is not None:
        rtofs_ds.close()

app = FastAPI(
    title="MLD MVP API",
    description="API for Mixed Layer Depth best estimates using RTOFS and Aquaview Observations",
    version="0.1.0",
    lifespan=lifespan
)

class MLDQueryRequest(BaseModel):
    lat: float
    lon: float
    time: str

@app.post("/mld")
def query_mld(req: MLDQueryRequest):
    if rtofs_ds is None:
        raise HTTPException(status_code=500, detail="RTOFS dataset not available on the server.")
    
    try:
        # Pass the pre-loaded dataset to save I/O time per request
        res = get_mld_estimate(req.lat, req.lon, req.time, rtofs_ds)
        # Using asdict since the result is a standard Python dataclass
        return asdict(res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "dataset_loaded": rtofs_ds is not None
    }
