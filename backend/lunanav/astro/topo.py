"""Topocentric Sun/Earth directions for a point on the Moon (ME body-fixed frame).

Local frame (README §6.2): azimuth clockwise from local north, 0–360 deg; elevation above the
local horizontal plane of the sphere (not of the terrain facet).

Pole convention: at the exact pole "north" is degenerate. We use the continuous limit of the ENU
basis for the longitude you pass: north = (cos lon, sin lon, 0), i.e. the direction from the pole
along meridian `lon` toward the equator (= toward +Z along that meridian). With the default
lon = 0 this is the +y axis of the south-polar-stereographic map, so map "up" = azimuth 0.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np

from ._contracts import MOON_RADIUS_M
from .ephemeris import get_ephemeris
from .timeutil import to_utc


def enu_basis(lat_deg: float, lon_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """East, north, up unit vectors in the ME frame. Well defined at the poles (see module doc)."""
    phi, lam = np.radians(lat_deg), np.radians(lon_deg)
    east = np.array([-np.sin(lam), np.cos(lam), 0.0])
    north = np.array([-np.sin(phi) * np.cos(lam), -np.sin(phi) * np.sin(lam), np.cos(phi)])
    up = np.array([np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)])
    return east, north, up


def surface_point_km(lat_deg: float, lon_deg: float, elevation_m: float = 0.0) -> np.ndarray:
    r = (MOON_RADIUS_M + elevation_m) / 1000.0
    return r * enu_basis(lat_deg, lon_deg)[2]


def body_vectors_me(times: list[datetime]) -> tuple[np.ndarray, np.ndarray]:
    """Sun and Earth positions relative to the Moon centre, ME frame, km. Shapes (n, 3)."""
    eph = get_ephemeris()
    moon = eph.moon_eci_km(times)
    sun = eph.sun_eci_km(times)
    rot = eph.j2000_to_moon_me(times)
    sun_me = np.einsum("nij,nj->ni", rot, sun - moon)
    earth_me = np.einsum("nij,nj->ni", rot, -moon)
    return sun_me, earth_me


def az_el(target_me_km: np.ndarray, lat_deg: float, lon_deg: float, elevation_m: float = 0.0):
    """Azimuth/elevation (deg) of target(s) given in ME km relative to the Moon centre."""
    east, north, up = enu_basis(lat_deg, lon_deg)
    rel = np.atleast_2d(target_me_km) - surface_point_km(lat_deg, lon_deg, elevation_m)
    e, n, u = rel @ east, rel @ north, rel @ up
    az = np.mod(np.degrees(np.arctan2(e, n)), 360.0)
    el = np.degrees(np.arctan2(u, np.hypot(e, n)))
    return az, el


def sun_earth_series(lat_deg, lon_deg, elevation_m, times):
    """(sun_az, sun_el, earth_az, earth_el) arrays over `times`."""
    sun_me, earth_me = body_vectors_me([to_utc(t) for t in times])
    s_az, s_el = az_el(sun_me, lat_deg, lon_deg, elevation_m)
    e_az, e_el = az_el(earth_me, lat_deg, lon_deg, elevation_m)
    return s_az, s_el, e_az, e_el


def sun_az_el(lat_deg, lon_deg, elevation_m, t_utc) -> tuple[float, float]:
    sun_me, _ = body_vectors_me([to_utc(t_utc)])
    az, el = az_el(sun_me, lat_deg, lon_deg, elevation_m)
    return float(az[0]), float(el[0])


def earth_az_el(lat_deg, lon_deg, elevation_m, t_utc) -> tuple[float, float]:
    _, earth_me = body_vectors_me([to_utc(t_utc)])
    az, el = az_el(earth_me, lat_deg, lon_deg, elevation_m)
    return float(az[0]), float(el[0])


def sub_point(target_me_km: np.ndarray) -> tuple[float, float]:
    """Planetocentric (lat_deg, lon_deg) of the sub-target point for one ME vector."""
    v = np.asarray(target_me_km, float).reshape(3)
    lat = np.degrees(np.arcsin(v[2] / np.linalg.norm(v)))
    lon = np.degrees(np.arctan2(v[1], v[0]))
    return float(lat), float(lon)
