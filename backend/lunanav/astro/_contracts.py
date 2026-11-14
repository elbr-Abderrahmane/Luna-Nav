"""Shared contracts used by astro, imported from the owners' modules when they exist.

`lunanav.schemas` (P5), `lunanav.config` (P5) and `lunanav.coords` (P2) are not written yet.
Until they are, this file provides copies that follow README §6–§7 to the letter, so astro runs and
is tested today. As soon as the real modules land, the `try` imports pick them up and the
fallbacks below are dead code (delete them then). Do not extend these fallbacks: contract changes
go through P5 (README §10).
"""

from __future__ import annotations

import math
import os
from typing import Literal

from pydantic import BaseModel

# ---- constants (README §6.6) ----------------------------------------------------------------
try:
    from lunanav.config import (  # type: ignore[import-not-found]
        ANALYSIS_STEP_H,
        CONTRACT_VERSION,
        MOON_RADIUS_M,
        SURFACE_STAY_DAYS,
    )
except ImportError:
    MOON_RADIUS_M = 1_737_400
    SURFACE_STAY_DAYS = 7
    ANALYSIS_STEP_H = 1
    CONTRACT_VERSION = "0.1.0"

EARTH_RADIUS_KM = 6371.0
DataMode = Literal["fixtures", "synthetic", "real"]


def data_mode() -> str:
    mode = os.environ.get("LUNANAV_DATA_MODE", "synthetic")
    return mode if mode in ("fixtures", "synthetic", "real") else "synthetic"


# ---- schemas (README §7.1, §7.2) ------------------------------------------------------------
try:
    from lunanav.schemas import (  # type: ignore[import-not-found]
        IlluminationSummary,
        LatLon,
        Meta,
        MissionPlan,
    )
except ImportError:

    class Meta(BaseModel):
        contract_version: str
        data_mode: DataMode
        generated_utc: str
        sources: list[str]

    class LatLon(BaseModel):
        lat_deg: float
        lon_deg: float

    class IlluminationSummary(BaseModel):
        window_start_utc: str
        window_end_utc: str
        illumination_pct: float
        longest_shadow_h: float
        sunlit_at_arrival: bool
        sun_azimuth_deg_at_arrival: float
        sun_elevation_deg_at_arrival: float
        earth_visibility_pct: float
        earth_visible_at_arrival: bool
        earth_azimuth_deg_at_arrival: float
        earth_elevation_deg_at_arrival: float
        method: Literal["horizon_mask", "smooth_sphere", "fixture"]

    class TimedPosition(BaseModel):
        t_utc: str
        pos_km: tuple[float, float, float]

    class InterceptionWindow(BaseModel):
        start_utc: str
        end_utc: str

    class MissionParameter(BaseModel):
        key: str
        label: str
        value: float | str
        unit: str

    class MissionPlan(BaseModel):
        meta: Meta
        arrival_utc: str
        launch_utc: str
        transfer_duration_h: float
        interception_window: InterceptionWindow
        earth_moon_distance_km: float
        frame: Literal["J2000_ECI"]
        moon_track: list[TimedPosition]
        trajectory: list[TimedPosition]
        sun_direction_eci: tuple[float, float, float]
        parameters: list[MissionParameter]


# ---- coordinates (README §6.2) --------------------------------------------------------------
try:
    from lunanav.coords import latlon_to_stereo  # type: ignore[import-not-found]
except ImportError:

    def latlon_to_stereo(lat_deg: float, lon_deg: float) -> tuple[float, float]:
        """South polar stereographic on the 1737.4 km sphere -> (x_m, y_m)."""
        phi, lam = math.radians(lat_deg), math.radians(lon_deg)
        rho = 2 * MOON_RADIUS_M * math.tan(math.pi / 4 + phi / 2)
        return rho * math.sin(lam), rho * math.cos(lam)
