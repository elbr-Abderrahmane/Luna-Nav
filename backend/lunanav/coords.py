"""Lunar coordinate normalization and south-polar stereographic transforms."""

from __future__ import annotations

import math

MOON_RADIUS_M = 1_737_400.0
PROJ4_SOUTH_POLAR = (
    "+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 "
    "+x_0=0 +y_0=0 +R=1737400 +units=m +no_defs"
)


def normalize_latlon(lat_deg: float, lon_deg: float) -> tuple[float, float]:
    """Validate latitude and normalize east-positive longitude to [-180, 180)."""
    lat = float(lat_deg)
    lon = float(lon_deg)
    if not math.isfinite(lat) or not math.isfinite(lon):
        raise ValueError("Latitude and longitude must be finite numbers.")
    if not -90.0 <= lat <= 90.0:
        raise ValueError("Latitude must be between -90 and +90 degrees.")
    normalized_lon = (lon + 180.0) % 360.0 - 180.0
    # Longitude has no geographic meaning at either pole; retain normalized input.
    return lat, normalized_lon


def latlon_to_xy(lat_deg: float, lon_deg: float) -> tuple[float, float]:
    """Convert planetocentric lunar latitude/longitude to projected metres."""
    lat, lon = normalize_latlon(lat_deg, lon_deg)
    if lat == -90.0:
        return 0.0, 0.0
    phi = math.radians(lat)
    lam = math.radians(lon)
    rho = 2.0 * MOON_RADIUS_M * math.tan(math.pi / 4.0 + phi / 2.0)
    return rho * math.sin(lam), rho * math.cos(lam)


def xy_to_latlon(x_m: float, y_m: float) -> tuple[float, float]:
    """Convert projected metres to lunar planetocentric latitude/longitude."""
    x = float(x_m)
    y = float(y_m)
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("Projected coordinates must be finite numbers.")
    rho = math.hypot(x, y)
    if rho == 0.0:
        return -90.0, 0.0  # longitude is undefined at the south pole
    phi = 2.0 * math.atan(rho / (2.0 * MOON_RADIUS_M)) - math.pi / 2.0
    lam = math.atan2(x, y)
    return math.degrees(phi), (math.degrees(lam) + 180.0) % 360.0 - 180.0


def is_nominal_dem_latitude(lat_deg: float) -> bool:
    """Return whether latitude lies in the nominal 80–90°S DEM envelope."""
    lat, _ = normalize_latlon(lat_deg, 0.0)
    return -90.0 <= lat <= -80.0
