from __future__ import annotations
import logging
from aquaview_obs import AquaviewClient, search_with_primary_fallback, extract_ioos_profiles

def main():
    client = AquaviewClient()
    query_time = "2026-04-01T06:00:00Z"
    lat = 28.5
    lon = -88.2

    print(f"Searching Aquaview around lat={lat}, lon={lon}, time={query_time}")
    res = search_with_primary_fallback(client, lat, lon, query_time)
    print(f"Found {res.get('usable_count', 0)} usable items using window: {res.get('window_used')}")
    
    features = res.get("features", [])
    search_body = res.get("search_body", {})
    bbox = search_body.get("bbox", [])
    dt_range = search_body.get("datetime", "2026-03-30T06:00:00Z/2026-04-03T06:00:00Z").split("/")
    
    start_dt = dt_range[0] if len(dt_range) > 0 else ""
    end_dt = dt_range[1] if len(dt_range) > 1 else ""

    for item in features:
        print(f"\nItem: {item.get('id')}")
        collection = item.get("collection", "")
        print(f"Collection: {collection}")
        if "ioos" in collection.lower():
            try:
                profiles = extract_ioos_profiles(item, bbox, start_dt, end_dt)
                print(f"  Success! Extracted {len(profiles)} profiles.")
                for p in profiles:
                    print(f"    Profile id={p.profile_id}, MLD arrays length={len(p.depth_m)}")
            except Exception as e:
                print(f"  Failed to extract: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
