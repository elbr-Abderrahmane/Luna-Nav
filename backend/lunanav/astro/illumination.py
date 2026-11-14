"""Illumination and Earth visibility over the surface-stay window (README §6.4, §7.1)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

import numpy as np

from ._contracts import ANALYSIS_STEP_H, SURFACE_STAY_DAYS, IlluminationSummary, LatLon
from .horizon import default_dem, horizon_at, horizon_mask
from .timeutil import fmt_utc, time_grid, to_utc
from .topo import sun_earth_series


def _longest_run_h(dark: np.ndarray, step_h: float) -> float:
    best = run = 0
    for d in dark:
        run = run + 1 if d else 0
        best = max(best, run)
    return best * step_h


def _summary(times, window_end, s_az, s_el, e_az, e_el, sun_hz, earth_hz, method) -> IlluminationSummary:
    lit = s_el > sun_hz
    vis = e_el > earth_hz
    return IlluminationSummary(
        window_start_utc=fmt_utc(times[0]),
        window_end_utc=fmt_utc(window_end),
        illumination_pct=round(float(lit.mean() * 100), 2),
        longest_shadow_h=float(_longest_run_h(~lit, ANALYSIS_STEP_H)),
        sunlit_at_arrival=bool(lit[0]),
        sun_azimuth_deg_at_arrival=round(float(s_az[0]), 3),
        sun_elevation_deg_at_arrival=round(float(s_el[0]), 3),
        earth_visibility_pct=round(float(vis.mean() * 100), 2),
        earth_visible_at_arrival=bool(vis[0]),
        earth_azimuth_deg_at_arrival=round(float(e_az[0]), 3),
        earth_elevation_deg_at_arrival=round(float(e_el[0]), 3),
        method=method,
    )


def _window(arrival_utc):
    """Sample k stands for the interval [t_k, t_k + step); window_end is excluded.

    7 days at 1 h -> 168 samples, so `longest_shadow_h` is at most 168 and percentages are of
    the window length.
    """
    grid = time_grid(to_utc(arrival_utc), SURFACE_STAY_DAYS * 24.0, ANALYSIS_STEP_H)
    return grid[:-1], grid[-1]


def illumination_at(lat_deg: float, lon_deg: float, elevation_m: float | None,
                    arrival_utc: datetime | str, use_horizon: bool = True, dem=None,
                    n_az: int = 360, max_dist_km: float = 100.0) -> IlluminationSummary:
    """Point illumination. Sunlit = Sun disk centre above the local horizon at the Sun azimuth.

    `use_horizon=True` uses the DEM horizon mask when a DEM is available (method "horizon_mask");
    otherwise, or without a DEM, the horizon is the 0 deg plane of the sphere ("smooth_sphere").
    `elevation_m=None` reads the elevation from the DEM (0 if there is none).
    """
    times, window_end = _window(arrival_utc)
    g = geometry_series(lat_deg, lon_deg, elevation_m, times, use_horizon, dem, n_az, max_dist_km)
    return _summary(times, window_end, g["sun_az"], g["sun_el"], g["earth_az"], g["earth_el"],
                    g["sun_horizon"], g["earth_horizon"], g["method"])


def geometry_series(lat_deg, lon_deg, elevation_m, times, use_horizon=True, dem=None,
                    n_az: int = 360, max_dist_km: float = 100.0) -> dict:
    """Sun/Earth az/el and the horizon elevation at their azimuths, for every time in `times`.

    Returns arrays sun_az, sun_el, earth_az, earth_el, sun_horizon, earth_horizon (deg), plus
    method ("horizon_mask" | "smooth_sphere") and elevation_m actually used.
    """
    dem = dem if dem is not None else (default_dem() if use_horizon else None)
    if elevation_m is None:
        elevation_m = float(dem.sample_elevation(lat_deg, lon_deg)) if dem is not None else 0.0
    s_az, s_el, e_az, e_el = sun_earth_series(lat_deg, lon_deg, elevation_m, times)
    if use_horizon and dem is not None:
        mask = horizon_mask(lat_deg, lon_deg, n_az=n_az, max_dist_km=max_dist_km, dem=dem)
        s_hz, e_hz, method = horizon_at(mask, s_az), horizon_at(mask, e_az), "horizon_mask"
    else:
        s_hz, e_hz, method = np.zeros_like(s_el), np.zeros_like(e_el), "smooth_sphere"
    return {"sun_az": s_az, "sun_el": s_el, "earth_az": e_az, "earth_el": e_el,
            "sun_horizon": s_hz, "earth_horizon": e_hz, "method": method,
            "elevation_m": elevation_m}


def _circular_mean_deg(a: Iterable[float]) -> float:
    r = np.radians(np.asarray(list(a), float))
    return float(np.mod(np.degrees(np.arctan2(np.sin(r).mean(), np.cos(r).mean())), 360.0))


def aggregate(summaries: list[IlluminationSummary]) -> IlluminationSummary:
    """Area summary: mean of %, max of longest shadow, majority for booleans, mean geometry."""
    if not summaries:
        raise ValueError("no samples")
    S = summaries

    def mean(f):
        return round(float(np.mean([getattr(s, f) for s in S])), 3)

    def majority(f):
        return sum(bool(getattr(s, f)) for s in S) * 2 > len(S)

    methods = {s.method for s in S}
    return IlluminationSummary(
        window_start_utc=S[0].window_start_utc,
        window_end_utc=S[0].window_end_utc,
        illumination_pct=round(mean("illumination_pct"), 2),
        longest_shadow_h=max(s.longest_shadow_h for s in S),
        sunlit_at_arrival=majority("sunlit_at_arrival"),
        sun_azimuth_deg_at_arrival=round(_circular_mean_deg(s.sun_azimuth_deg_at_arrival for s in S), 3),
        sun_elevation_deg_at_arrival=mean("sun_elevation_deg_at_arrival"),
        earth_visibility_pct=round(mean("earth_visibility_pct"), 2),
        earth_visible_at_arrival=majority("earth_visible_at_arrival"),
        earth_azimuth_deg_at_arrival=round(
            _circular_mean_deg(s.earth_azimuth_deg_at_arrival for s in S), 3),
        earth_elevation_deg_at_arrival=mean("earth_elevation_deg_at_arrival"),
        method="horizon_mask" if methods == {"horizon_mask"} else "smooth_sphere",
    )


def illumination_area(samples: list[LatLon], arrival_utc: datetime | str,
                      use_horizon: bool = True, dem=None) -> IlluminationSummary:
    """Aggregate over sample points of a region/zone (P5 passes e.g. 9–25 points).

    Pass `use_horizon=False` for the fast smooth-sphere path (e.g. the six L2 regions).
    """
    return aggregate([
        illumination_at(p.lat_deg, p.lon_deg, None, arrival_utc, use_horizon=use_horizon, dem=dem)
        for p in samples
    ])
