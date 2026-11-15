"""Real LOLA south-pole DEM reader with the same interface as P2's `lunanav.terrain.dem`.

Default file: NASA PGDA "A New View of the Lunar South Pole from LOLA" (Barker et al. 2023),
`LDEM_80S_80MPP_ADJ.TIF`: 80 m/px, 80-90 deg S, 7600 x 7600 float32, heights in metres relative
to the 1737.4 km sphere, NaN = no data. Its projection is exactly README section 6.2:
    +proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m
Download with `python scripts/astro/fetch_lola_dem.py` (into data/raw/dem/). Any other PGDA
LDEM_*MPP_ADJ.TIF (40 m, 20 m, 10 m) works too: set LUNANAV_DEM_PATH.

Interface (README section 7.8, used by horizon.py):
    dem_window(center: LatLon, radius_m) -> (grid float32 with -32768 nodata, Affine)
    sample_elevation(lat_deg, lon_deg) -> float (NaN outside coverage)
P2 can adopt this file as `lunanav.terrain.dem` unchanged, or keep their own; astro prefers
P2's module when it exists.
"""

from __future__ import annotations

import math
import os
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np

from .ephemeris import REPO_ROOT

_DEM_LOCK = threading.RLock()

R = 1_737_400.0
NODATA = -32768.0
DEFAULT_FILE = "LDEM_80S_80MPP_ADJ.TIF"
DEFAULT_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/" + DEFAULT_FILE


def default_path() -> Path:
    p = os.environ.get("LUNANAV_DEM_PATH")
    return Path(p) if p else REPO_ROOT / "data" / "raw" / "dem" / DEFAULT_FILE


def stereo(lat_deg, lon_deg):
    phi, lam = np.radians(lat_deg), np.radians(lon_deg)
    rho = 2 * R * np.tan(np.pi / 4 + phi / 2)
    return rho * np.sin(lam), rho * np.cos(lam)


class LolaDEM:
    """Windowed, read-only access to a south-polar-stereographic LOLA GeoTIFF (rasterio)."""

    def __init__(self, path: str | os.PathLike):
        import rasterio  # optional dependency, only needed for real terrain

        self.path = Path(path)
        self._ds = rasterio.open(self.path)
        crs = self._ds.crs.to_proj4() if self._ds.crs else ""
        if "+proj=stere" not in crs or "+lat_0=-90" not in crs:
            raise ValueError(f"{self.path.name}: expected south polar stereographic, got {crs!r}")
        t = self._ds.transform
        self.res_m = float(t.a)
        self.transform = t
        self.DEM_ID = f"lola:{self.path.name}"
        self._nodata = self._ds.nodata

    # -- helpers ---------------------------------------------------------------------------------
    def _clean(self, a: np.ndarray) -> np.ndarray:
        a = a.astype(np.float32)
        bad = ~np.isfinite(a)
        if self._nodata is not None and np.isfinite(self._nodata):
            bad |= a == self._nodata
        a[bad] = NODATA
        return a

    def dem_window(self, center, radius_m: float):
        from rasterio.windows import Window

        cx, cy = stereo(center.lat_deg, center.lon_deg)
        t = self.transform
        col0 = math.floor((cx - radius_m - t.c) / t.a) - 1
        row0 = math.floor((cy + radius_m - t.f) / t.e) - 1
        n = math.ceil(2 * radius_m / self.res_m) + 3
        win = Window(col0, row0, n, n)
        with _DEM_LOCK:
            grid = self._ds.read(1, window=win, boundless=True, fill_value=np.nan)
            w_transform = self._ds.window_transform(win)
        return self._clean(grid), w_transform

    def sample_elevation(self, lat_deg: float, lon_deg: float) -> float:
        """Bilinear height (m) at a point; NaN outside coverage or next to no-data."""
        from rasterio.windows import Window

        x, y = stereo(lat_deg, lon_deg)
        t = self.transform
        col = (float(x) - t.c) / t.a - 0.5
        row = (float(y) - t.f) / t.e - 0.5
        c0, r0 = math.floor(col), math.floor(row)
        with _DEM_LOCK:
            raw = self._ds.read(1, window=Window(c0, r0, 2, 2), boundless=True, fill_value=np.nan)
        q = self._clean(raw).astype(float)
        if np.any(q == NODATA):
            return float("nan")
        fc, fr = col - c0, row - r0
        return float(q[0, 0] * (1 - fc) * (1 - fr) + q[0, 1] * fc * (1 - fr)
                     + q[1, 0] * (1 - fc) * fr + q[1, 1] * fc * fr)


@lru_cache(maxsize=4)
def _open(path: str) -> LolaDEM:
    return LolaDEM(path)


def load_default():
    """The LOLA DEM if the file exists, rasterio is installed and LUNANAV_DEM != "off"."""
    if os.environ.get("LUNANAV_DEM", "").lower() in ("off", "0", "false", "none"):
        return None
    p = default_path()
    if not p.exists():
        return None
    try:
        return _open(str(p))
    except ImportError:
        return None


__all__ = ["DEFAULT_URL", "LolaDEM", "default_path", "load_default"]
