"""Analytic mock DEM shaped like P2's real one (south polar stereographic, GeoTIFF row order).

Exposes the same two functions as `lunanav.terrain.dem` (README §7.8):
`dem_window(center, radius_m) -> (grid float32, Affine)` and `sample_elevation(lat, lon)`.
Features (placeholders, not real sites):
  * CRATER: bowl, radius 8 km, floor 2500 m below datum, 400 m raised rim, centred 89.0°S 45°E
  * RIDGE: 1500 m high, 4 km wide, 40 km long Gaussian ridge, crest through 88.5°S 60°W
  * gentle ±40 m undulations everywhere else
"""

from __future__ import annotations

import math

import numpy as np
from affine import Affine

R = 1_737_400.0
NODATA = -32768.0


def stereo(lat_deg, lon_deg):
    phi, lam = np.radians(lat_deg), np.radians(lon_deg)
    rho = 2 * R * np.tan(np.pi / 4 + phi / 2)
    return rho * np.sin(lam), rho * np.cos(lam)


CRATER_LATLON = (-89.0, 45.0)
CRATER_FLOOR_LATLON = CRATER_LATLON
RIDGE_TOP_LATLON = (-88.5, -60.0)
_CX, _CY = stereo(*CRATER_LATLON)
_RX, _RY = stereo(*RIDGE_TOP_LATLON)
_RIDGE_DIR = np.array([math.cos(0.4), math.sin(0.4)])  # arbitrary strike


def height(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    h = 40 * np.sin(x / 7000.0) * np.cos(y / 9000.0)
    # crater: parabolic bowl + rim
    r = np.hypot(x - _CX, y - _CY) / 8000.0
    bowl = np.where(r < 1, -2500 * (1 - r**2), 0.0)
    rim = 400 * np.exp(-((r - 1) / 0.25) ** 2)
    h = h + bowl + rim
    # ridge: gaussian across strike, tapered along strike
    dx, dy = x - _RX, y - _RY
    along = dx * _RIDGE_DIR[0] + dy * _RIDGE_DIR[1]
    across = -dx * _RIDGE_DIR[1] + dy * _RIDGE_DIR[0]
    h = h + 1500 * np.exp(-(across / 2000.0) ** 2) * np.exp(-(along / 20000.0) ** 4)
    return h


class MockDEM:
    def __init__(self, res_m: float = 200.0, flat: bool = False):
        self.res_m = res_m
        self.flat = flat
        self.DEM_ID = f"mock-{'flat' if flat else 'features'}-{res_m:g}m"

    def _h(self, x, y):
        return np.zeros(np.broadcast(x, y).shape) if self.flat else height(x, y)

    def dem_window(self, center, radius_m):
        cx, cy = stereo(center.lat_deg, center.lon_deg)
        res = self.res_m
        xmin = math.floor((cx - radius_m) / res) * res - res
        ymax = math.ceil((cy + radius_m) / res) * res + res
        n = math.ceil(2 * radius_m / res) + 3
        xs = xmin + (np.arange(n) + 0.5) * res
        ys = ymax - (np.arange(n) + 0.5) * res
        grid = self._h(xs[None, :], ys[:, None]).astype(np.float32)
        return grid, Affine(res, 0.0, xmin, 0.0, -res, ymax)

    def sample_elevation(self, lat_deg, lon_deg):
        return float(self._h(*stereo(lat_deg, lon_deg)))
