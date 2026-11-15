"""Terrain horizon masks from a DEM (terrain obstruction).

For each azimuth bin we march outward along the great circle from the observer, sample the DEM
(bilinear) and keep the maximum elevation angle of the terrain, computed exactly on the sphere:

    elev = atan2((R + h_t)·cos θ − (R + h_o), (R + h_t)·sin θ),   θ = d / R

which contains the curvature drop (≈ d²/2R, 2.9 km at 100 km). The observer sits
`observer_height_m` (default 2 m, a lander deck / antenna) above the DEM surface.

DEM access is only through `lunanav.terrain.dem` (P2): `dem_window(center, radius_m)` returning a
south-polar-stereographic grid plus an affine transform (GeoTIFF convention: row 0 = ymax, pixel
centres at +0.5), and `sample_elevation(lat, lon)`. Any object with those two functions can be
passed as `dem=` (tests use a mock DEM).
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

from ._contracts import CONTRACT_VERSION, MOON_RADIUS_M, LatLon, data_mode
from .ephemeris import REPO_ROOT
from .topo import enu_basis

R = float(MOON_RADIUS_M)
PRECOMPUTED_FILE = Path(__file__).with_name("precomputed_horizons.json")


@lru_cache(maxsize=1)
def _precomputed_horizons() -> dict:
    if not PRECOMPUTED_FILE.is_file():
        return {}
    try:
        return json.loads(PRECOMPUTED_FILE.read_text(encoding="utf-8")).get("sites", {})
    except Exception:
        return {}


def lookup_precomputed_horizon(lat_deg: float, lon_deg: float) -> np.ndarray | None:
    """Return precomputed 360-azimuth horizon mask (deg) if (lat_deg, lon_deg) matches a catalog polar site."""
    for entry in _precomputed_horizons().values():
        if abs(entry["lat_deg"] - lat_deg) <= 1e-4 and abs(entry["lon_deg"] - lon_deg) <= 1e-4:
            return np.asarray(entry["horizon_deg"], dtype=np.float32)
    return None


def default_dem():
    """DEM used for horizons, in order of preference:

    1. P2's `lunanav.terrain.dem` module, when it exists;
    2. the real LOLA GeoTIFF from `scripts/astro/fetch_lola_dem.py` (`lola_dem.load_default`,
       file `data/raw/dem/LDEM_80S_80MPP_ADJ.TIF` or `LUNANAV_DEM_PATH`);
    3. None -> callers fall back to the smooth sphere.
    `LUNANAV_DEM=off` disables 2 (the test suite sets it).
    """
    try:
        from lunanav.terrain import dem  # type: ignore[import-not-found]
    except ImportError:
        from .lola_dem import load_default

        return load_default()
    if hasattr(dem, "load_default"):
        return dem.load_default()
    return dem


def cache_dir() -> Path:
    return Path(os.environ.get("LUNANAV_CACHE_DIR", REPO_ROOT / "data" / "cache")) / "horizons"


def _dem_id(dem) -> str:
    for attr in ("DEM_ID", "dem_id", "source_id"):
        v = getattr(dem, attr, None)
        if v is not None:
            return str(v() if callable(v) else v)
    return getattr(dem, "__name__", type(dem).__name__)


def _affine_coeffs(transform):
    if hasattr(transform, "a"):
        return transform.a, transform.b, transform.c, transform.d, transform.e, transform.f
    return tuple(transform)[:6]


def _bilinear(grid: np.ndarray, transform, x: np.ndarray, y: np.ndarray,
              nodata: float | None = -32768.0) -> np.ndarray:
    a, b, c, d, e, f = _affine_coeffs(transform)
    if b or d:
        raise ValueError("rotated DEM transforms are not supported")
    col = (x - c) / a - 0.5
    row = (y - f) / e - 0.5
    h, w = grid.shape
    c0 = np.floor(col).astype(int)
    r0 = np.floor(row).astype(int)
    ok = (c0 >= 0) & (r0 >= 0) & (c0 < w - 1) & (r0 < h - 1)
    c0c, r0c = np.clip(c0, 0, w - 2), np.clip(r0, 0, h - 2)
    fc, fr = col - c0c, row - r0c
    g = grid.astype(float)
    if nodata is not None:
        g = np.where(g == nodata, np.nan, g)
    v = (g[r0c, c0c] * (1 - fc) * (1 - fr) + g[r0c, c0c + 1] * fc * (1 - fr)
         + g[r0c + 1, c0c] * (1 - fc) * fr + g[r0c + 1, c0c + 1] * fc * fr)
    return np.where(ok, v, np.nan)


def _ray_distances_m(res_m: float, max_dist_m: float) -> np.ndarray:
    """Spacing = DEM resolution near the observer, growing to 0.5 % of the distance far away."""
    out, d = [], res_m
    while d <= max_dist_m:
        out.append(d)
        d += max(res_m, 0.005 * d)
    return np.array(out)


def compute_horizon_mask(lat_deg: float, lon_deg: float, dem, n_az: int = 360,
                         max_dist_km: float = 100.0, observer_height_m: float = 2.0) -> np.ndarray:
    """Max terrain elevation angle (deg) for bins centred on az = i·360/n_az. Shape (n_az,)."""
    radius_m = max_dist_km * 1000.0
    grid, transform = dem.dem_window(LatLon(lat_deg=lat_deg, lon_deg=lon_deg), radius_m)
    grid = np.asarray(grid)
    res_m = abs(_affine_coeffs(transform)[0])
    h_obs = float(dem.sample_elevation(lat_deg, lon_deg)) + observer_height_m

    east, north, up = enu_basis(lat_deg, lon_deg)
    az = np.radians(np.arange(n_az) * 360.0 / n_az)
    dist = _ray_distances_m(res_m, radius_m)
    theta = dist / R  # central angle

    # unit vectors of every sample: p·cosθ + (cos az·n + sin az·e)·sinθ   -> (n_az, n_d, 3)
    dirs = np.cos(az)[:, None] * north + np.sin(az)[:, None] * east
    v = (np.cos(theta)[None, :, None] * up[None, None, :]
         + np.sin(theta)[None, :, None] * dirs[:, None, :])
    lat = np.arcsin(np.clip(v[..., 2], -1, 1))
    lon = np.arctan2(v[..., 1], v[..., 0])
    rho = 2 * R * np.tan(np.pi / 4 + lat / 2)
    x, y = rho * np.sin(lon), rho * np.cos(lon)

    h_t = _bilinear(grid, transform, x, y)
    elev = np.degrees(np.arctan2((R + h_t) * np.cos(theta) - (R + h_obs), (R + h_t) * np.sin(theta)))
    mask = np.nanmax(np.where(np.isnan(elev), -90.0, elev), axis=1)
    return mask.astype(np.float32)


def horizon_mask(lat_deg: float, lon_deg: float, n_az: int = 360, max_dist_km: float = 100.0,
                 dem=None, observer_height_m: float = 2.0, use_cache: bool = True) -> np.ndarray:
    """Cached horizon mask. Cache file: data/cache/horizons/<sha1>.npy (README §4 rule 6)."""
    dem = dem if dem is not None else default_dem()
    if dem is None:
        raise RuntimeError("no DEM available: lunanav.terrain.dem is not installed")
    key = (f"{lat_deg:.7f}|{lon_deg:.7f}|{n_az}|{max_dist_km:g}|{observer_height_m:g}|"
           f"{_dem_id(dem)}|{data_mode()}|{CONTRACT_VERSION}")
    path = cache_dir() / (hashlib.sha1(key.encode()).hexdigest()[:20] + ".npy")
    if use_cache and path.exists():
        return np.load(path)
    if (
        n_az == 360
        and abs(max_dist_km - 100.0) < 1e-6
        and abs(observer_height_m - 2.0) < 1e-6
        and _dem_id(dem).startswith("lola:")
    ):
        pre = lookup_precomputed_horizon(lat_deg, lon_deg)
        if pre is not None:
            return pre.copy()
    mask = compute_horizon_mask(lat_deg, lon_deg, dem, n_az, max_dist_km, observer_height_m)
    if use_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp.npy")
        np.save(tmp, mask)
        tmp.replace(path)
    return mask


def horizon_at(mask: np.ndarray, az_deg: np.ndarray) -> np.ndarray:
    """Horizon elevation at arbitrary azimuths, linear interpolation between (circular) bins."""
    n = len(mask)
    pos = np.mod(np.asarray(az_deg, float), 360.0) / (360.0 / n)
    i0 = np.floor(pos).astype(int) % n
    frac = pos - np.floor(pos)
    return mask[i0] * (1 - frac) + mask[(i0 + 1) % n] * frac


__all__ = ["compute_horizon_mask", "default_dem", "horizon_at", "horizon_mask"]
