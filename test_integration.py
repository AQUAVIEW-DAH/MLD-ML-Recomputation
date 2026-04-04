import sys
import json
import xarray as xr
from dataclasses import asdict
from mld_pipeline import get_mld_estimate
from mld_core import DEFAULT_RTOFS_FILE

def test_pipeline():
    print("Loading local RTOFS model data...")
    ds = xr.open_dataset(DEFAULT_RTOFS_FILE)
    
    # Extract the first available time from the model dataset 
    # to ensure our time query aligns with the model's validity
    model_time = str(ds["MT"].isel(MT=0).values)
    print(f"Model time slice found: {model_time}")
    
    # Coordinates for Gulf of Mexico
    test_lat = 28.5
    test_lon = -88.2
    
    print(f"Querying MLD Estimate for lat={test_lat}, lon={test_lon}, time={model_time}...")
    try:
        res = get_mld_estimate(test_lat, test_lon, model_time, ds)
        print("\n=== SUCESS! PIPELINE RESULT ===")
        print(json.dumps(asdict(res), indent=2))
    except Exception as e:
        print(f"\nPipeline failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
