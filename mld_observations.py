from __future__ import annotations

from typing import Any

from aquaview_obs import ObservationProfile
from mld_core import compute_mld_temp_threshold


def compute_observed_mlds(profiles: list[ObservationProfile]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for profile in profiles:
        mld = compute_mld_temp_threshold(profile.depth_m, profile.temperature_c)
        results.append(
            {
                "source": profile.source,
                "platform_id": profile.platform_id,
                "profile_id": profile.profile_id,
                "obs_time": profile.obs_time,
                "lat": profile.lat,
                "lon": profile.lon,
                "mld_m": mld,
                "metadata": profile.metadata,
            }
        )
    return results
