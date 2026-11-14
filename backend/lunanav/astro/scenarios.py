"""Site / date scenarios: countdowns, lunar-day windows, comparison, date sweeps, power metrics.

Built for the official challenge objectives ("time remaining before sunset or Earthset",
"duration of sunlight and Earth visibility windows", "compare sites and dates", "solar
elevation for power"). Everything returns JSON-ready dicts and never raises on bad input
(same `status` / `warnings` / `error` convention as `integration.py`).

    from lunanav.astro import site_conditions, site_timeline, compare_scenarios, date_sweep

Definitions
  * Sun "up" / sunlit  = centre of the solar disk above the local horizon at the Sun's azimuth.
    `disk_visible_fraction` gives the part of the disk above the horizon (0..1), because at the
    poles the Sun skims the horizon for days.
  * Earth "up" / visible = centre of the Earth disk above the local horizon (geometric line of
    sight only, see COMMS_NOTE).
  * Horizon = DEM horizon mask (terrain + lunar curvature) when a DEM covers the site, else the
    0 deg plane of the smooth sphere (`method` says which).
  * Event times (sunrise/sunset/earthrise/earthset) are found on the sampling grid and refined
    by bisection to <= 30 s. Events shorter than one sampling step can be missed.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from .horizon import horizon_at, horizon_mask
from .integration import (
    COMMS_NOTE,
    _check_latlon,
    _error,
    _InputError,
    _parse_time,
    _resolve_terrain,
    _source,
)
from .sites import resolve_site
from .timeutil import fmt_utc
from .topo import az_el, body_vectors_me, sub_point, surface_point_km

SYNODIC_MONTH_D = 29.530589            # mean lunar day (new moon to new moon)
AU_KM = 149_597_870.7
SOLAR_CONSTANT_W_M2 = 1361.0           # at 1 AU
SUN_RADIUS_KM = 695_700.0
EARTH_RADIUS_KM = 6_371.0
MAX_SAMPLES = 20_000
REFINE_TOL_S = 30.0

EVENT_NAMES = {"sun": ("sunrise", "sunset"), "earth": ("earthrise", "earthset")}


# ---------------------------------------------------------------------------------------------
# geometry helpers
def disk_visible_fraction(margin_deg, radius_deg):
    """Fraction of a disk of angular radius r whose centre is `margin` above a straight horizon."""
    d = np.clip(np.asarray(margin_deg, float) / radius_deg, -1.0, 1.0)
    return 1.0 - (np.arccos(d) - d * np.sqrt(1.0 - d * d)) / np.pi


def fmt_duration(hours: float | None) -> str | None:
    """'3 d 4 h 12 min' style text for the UI."""
    if hours is None:
        return None
    m = round(hours * 60)
    d, m = divmod(m, 1440)
    h, m = divmod(m, 60)
    parts = ([f"{d} d"] if d else []) + ([f"{h} h"] if h or d else []) + [f"{m} min"]
    return " ".join(parts)


class SiteModel:
    """One observer on the Moon: horizon mask (or smooth sphere) + vectorised Sun/Earth state."""

    def __init__(self, lat_deg: float, lon_deg: float, elevation_m: float | None = None,
                 dem=None, n_az: int = 360, max_dist_km: float = 100.0):
        self.lat, self.lon = lat_deg, lon_deg
        self.warnings: list[str] = []
        self.mask = None
        if dem is not None:
            try:
                elev_dem = float(dem.sample_elevation(lat_deg, lon_deg))
                if not np.isfinite(elev_dem) or elev_dem <= -30000:
                    raise ValueError("site outside DEM coverage")
                mask = np.asarray(horizon_mask(lat_deg, lon_deg, n_az=n_az,
                                               max_dist_km=max_dist_km, dem=dem), float)
                if np.all(mask <= -89.0):
                    raise ValueError("no DEM samples around the site")
                # bins whose whole ray left the DEM: fall back to the geometric horizon (0 deg)
                self.mask = np.where(mask <= -89.0, 0.0, mask)
                if np.any(mask <= -89.0):
                    self.warnings.append("DEM does not cover every azimuth: missing bins use "
                                         "the smooth-sphere horizon")
                if elevation_m is None:
                    elevation_m = elev_dem
            except Exception as exc:  # noqa: BLE001 - any DEM problem -> smooth sphere
                self.mask = None
                self.warnings.append(f"terrain horizon unavailable here ({exc}): smooth-sphere "
                                     "horizon, local shadows ignored")
        self.elevation_m = float(elevation_m) if elevation_m is not None else 0.0
        self.method = "horizon_mask" if self.mask is not None else "smooth_sphere"
        self._p = surface_point_km(lat_deg, lon_deg, self.elevation_m)

    def horizon(self, az_deg) -> np.ndarray:
        az = np.asarray(az_deg, float)
        return horizon_at(self.mask, az) if self.mask is not None else np.zeros_like(az)

    def horizon_profile(self, n: int = 360) -> dict:
        az = np.arange(n) * 360.0 / n
        return {"azimuth_deg": [round(float(a), 3) for a in az],
                "elevation_deg": [round(float(e), 3) for e in self.horizon(az)],
                "method": self.method}

    def state(self, times: list[datetime]) -> dict:
        sun_me, earth_me = body_vectors_me(times)
        s_az, s_el = az_el(sun_me, self.lat, self.lon, self.elevation_m)
        e_az, e_el = az_el(earth_me, self.lat, self.lon, self.elevation_m)
        s_dist = np.linalg.norm(sun_me - self._p, axis=1)
        e_dist = np.linalg.norm(earth_me - self._p, axis=1)
        s_r = np.degrees(np.arcsin(SUN_RADIUS_KM / s_dist))
        e_r = np.degrees(np.arcsin(EARTH_RADIUS_KM / e_dist))
        s_m = s_el - self.horizon(s_az)
        e_m = e_el - self.horizon(e_az)
        s_frac = disk_visible_fraction(s_m, s_r)
        irr = SOLAR_CONSTANT_W_M2 * (AU_KM / s_dist) ** 2
        return {
            "sun_az": s_az, "sun_el": s_el, "sun_margin": s_m, "sun_up": s_m > 0,
            "sun_frac": s_frac, "sun_radius": s_r, "sun_dist": s_dist,
            "earth_az": e_az, "earth_el": e_el, "earth_margin": e_m, "earth_up": e_m > 0,
            "earth_frac": disk_visible_fraction(e_m, e_r), "earth_radius": e_r,
            "earth_dist": e_dist, "earth_me": earth_me, "sun_me": sun_me,
            "irradiance": irr * s_frac,
            "pf_vertical": s_frac * np.cos(np.radians(np.clip(s_el, 0, 90))),
            "pf_horizontal": s_frac * np.sin(np.radians(np.clip(s_el, 0, 90))),
        }


def _grid(t0: datetime, t1: datetime, step_h: float) -> list[datetime]:
    n = int(np.floor((t1 - t0) / timedelta(hours=step_h) + 1e-9))
    times = [t0 + timedelta(hours=k * step_h) for k in range(n + 1)]
    if times[-1] < t1:
        times.append(t1)
    return times


def _refine(site: SiteModel, body: str, lo: list[datetime], hi: list[datetime],
            up_lo: np.ndarray) -> list[datetime]:
    """Bisection on all crossings at once; returns crossing times (<= REFINE_TOL_S)."""
    lo, hi = list(lo), list(hi)
    key = f"{body}_up"
    while lo and max((h - l).total_seconds() for l, h in zip(lo, hi)) > REFINE_TOL_S:
        mid = [l + (h - l) / 2 for l, h in zip(lo, hi)]
        up_mid = site.state(mid)[key]
        for i in range(len(mid)):
            if up_mid[i] == up_lo[i]:
                lo[i] = mid[i]
            else:
                hi[i] = mid[i]
    return [l + (h - l) / 2 for l, h in zip(lo, hi)]


def _events_and_windows(site: SiteModel, body: str, times, up: np.ndarray, t0, t1):
    """Refined events and visibility intervals [(start, end, clipped_start, clipped_end)]."""
    idx = np.nonzero(up[1:] != up[:-1])[0]
    rise_name, set_name = EVENT_NAMES[body]
    cross = _refine(site, body, [times[i] for i in idx], [times[i + 1] for i in idx],
                    up[idx]) if len(idx) else []
    events = [{"event": set_name if up[i] else rise_name, "t": t} for i, t in zip(idx, cross)]
    windows, start = [], (t0 if up[0] else None)
    for ev in events:
        if ev["event"] == rise_name:
            start = ev["t"]
        elif start is not None:
            windows.append((start, ev["t"], start == t0 and up[0], False))
            start = None
    if start is not None:
        windows.append((start, t1, start == t0 and bool(up[0]), True))
    return events, windows


def _intersect(a, b):
    out = []
    for s1, e1, cs1, ce1 in a:
        for s2, e2, cs2, ce2 in b:
            s, e = max(s1, s2), min(e1, e2)
            if e > s:
                out.append((s, e, (cs1 and s == s1) or (cs2 and s == s2),
                            (ce1 and e == e1) or (ce2 and e == e2)))
    return sorted(out)


def _hours(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 3600.0


def _win_json(w, t_ref):
    s, e, cs, ce = w
    return {"start_utc": fmt_utc(s), "end_utc": fmt_utc(e), "duration_h": round(_hours(s, e), 3),
            "duration_text": fmt_duration(_hours(s, e)),
            "starts_in_h": round(_hours(t_ref, s), 3),
            "open_at_window_start": bool(cs), "open_at_window_end": bool(ce)}


def _longest_gap_h(windows, t0, t1) -> float:
    edges, cur = [], t0
    for s, e, *_ in windows:
        edges.append(_hours(cur, s))
        cur = e
    edges.append(_hours(cur, t1))
    return max(edges)


def _total_h(windows) -> float:
    return sum(_hours(s, e) for s, e, *_ in windows)


def _countdown(body, up0, events, t0, window_h):
    rise_name, set_name = EVENT_NAMES[body]
    want = set_name if up0 else rise_name
    nxt = next((e for e in events if e["event"] == want), None)
    label = "Sun" if body == "sun" else "Earth"
    if nxt is None:
        state = "up" if up0 else "down"
        return {"next_event": want, "next_event_utc": None, "time_remaining_h": None,
                "time_remaining_text": None, "beyond_window": True,
                "summary": f"{label} stays {state} for the whole {window_h / 24:.1f}-day window"}
    h = _hours(t0, nxt["t"])
    return {"next_event": want, "next_event_utc": fmt_utc(nxt["t"]),
            "time_remaining_h": round(h, 3), "time_remaining_text": fmt_duration(h),
            "beyond_window": False, "summary": f"{want.capitalize()} in {fmt_duration(h)}"}


# ---------------------------------------------------------------------------------------------
# core analysis (raises _InputError / ValueError; wrappers below catch)
def _analyze(site_info: dict, t0: datetime, window_days: float, step_h: float, dem,
             include_series: bool = False) -> dict:
    if not 0 < window_days <= 400:
        raise _InputError("INVALID_WINDOW", "window_days must be in (0, 400]")
    if not 0 < step_h <= 24:
        raise _InputError("INVALID_STEP", "step_h must be in (0, 24]")
    t1 = t0 + timedelta(days=window_days)
    if (t1 - t0) / timedelta(hours=step_h) > MAX_SAMPLES:
        raise _InputError("PERIOD_TOO_LONG", f"more than {MAX_SAMPLES} samples; increase step_h")
    site = SiteModel(site_info["lat_deg"], site_info["lon_deg"], site_info.get("elevation_m"),
                     dem=dem)
    times = _grid(t0, t1, step_h)
    st = site.state(times)
    window_h = _hours(t0, t1)

    sun_ev, sun_w = _events_and_windows(site, "sun", times, st["sun_up"], t0, t1)
    earth_ev, earth_w = _events_and_windows(site, "earth", times, st["earth_up"], t0, t1)
    both_w = _intersect(sun_w, earth_w)

    sub_e_lat, sub_e_lon = sub_point(st["earth_me"][0])
    sub_s_lat, sub_s_lon = sub_point(st["sun_me"][0])
    sub_e = np.array([sub_point(v) for v in st["earth_me"]])

    # time-weighted means (trapezoid over the possibly uneven last step)
    dt = np.diff([(t - t0).total_seconds() / 3600 for t in times])
    def tmean(a):
        a = np.asarray(a, float)
        return float(np.sum((a[1:] + a[:-1]) / 2 * dt) / window_h)

    def body_now(prefix):
        return {"azimuth_deg": round(float(st[f"{prefix}_az"][0]), 3),
                "elevation_deg": round(float(st[f"{prefix}_el"][0]), 3),
                "horizon_elevation_deg": round(float(st[f"{prefix}_el"][0]
                                                     - st[f"{prefix}_margin"][0]), 3),
                "margin_above_horizon_deg": round(float(st[f"{prefix}_margin"][0]), 3),
                "visible": bool(st[f"{prefix}_up"][0]),
                "disk_visible_fraction": round(float(st[f"{prefix}_frac"][0]), 3),
                "apparent_radius_deg": round(float(st[f"{prefix}_radius"][0]), 4),
                "distance_km": round(float(st[f"{prefix}_dist"][0]), 1)}

    sun_el = st["sun_el"]
    events = sorted(
        [{"event": e["event"], "t_utc": fmt_utc(e["t"]), "in_h": round(_hours(t0, e["t"]), 3),
          "in_text": fmt_duration(_hours(t0, e["t"]))} for e in sun_ev + earth_ev],
        key=lambda e: e["in_h"])

    out = {
        "site": {k: site_info.get(k) for k in ("id", "name", "category", "mission", "agency",
                                                "coord_quality")}
        | {"lat_deg": site.lat, "lon_deg": site.lon, "elevation_m": round(site.elevation_m, 2)},
        "method": site.method,
        "warnings": list(site.warnings),
        "window": {"start_utc": fmt_utc(t0), "end_utc": fmt_utc(t1),
                   "duration_h": round(window_h, 3), "duration_days": round(window_days, 4),
                   "sampling_interval_h": step_h, "n_samples": len(times)},
        "now": {
            "t_utc": fmt_utc(t0),
            "sun": body_now("sun"),
            "earth": body_now("earth"),
            "power": {
                "irradiance_w_m2": round(float(st["irradiance"][0]), 1),
                "vertical_panel_factor": round(float(st["pf_vertical"][0]), 4),
                "horizontal_panel_factor": round(float(st["pf_horizontal"][0]), 4),
                "vertical_panel_w_m2": round(float(st["irradiance"][0] * np.cos(
                    np.radians(max(sun_el[0], 0.0)))), 1),
            },
            "libration": {"sub_earth_lat_deg": round(sub_e_lat, 3),
                          "sub_earth_lon_deg": round(sub_e_lon, 3)},
            "sub_solar": {"lat_deg": round(sub_s_lat, 3), "lon_deg": round(sub_s_lon, 3)},
        },
        "countdown": {"sun": _countdown("sun", bool(st["sun_up"][0]), sun_ev, t0, window_h),
                      "earth": _countdown("earth", bool(st["earth_up"][0]), earth_ev, t0,
                                          window_h)},
        "next_events": events,
        "windows": {"sunlit": [_win_json(w, t0) for w in sun_w],
                    "earth_visible": [_win_json(w, t0) for w in earth_w],
                    "power_and_comms": [_win_json(w, t0) for w in both_w]},
        "metrics": {
            "sunlight_pct": round(100 * _total_h(sun_w) / window_h, 2),
            "sunlight_hours": round(_total_h(sun_w), 3),
            "longest_darkness_h": round(_longest_gap_h(sun_w, t0, t1), 3),
            "earth_visibility_pct": round(100 * _total_h(earth_w) / window_h, 2),
            "earth_visible_hours": round(_total_h(earth_w), 3),
            "longest_comms_gap_h": round(_longest_gap_h(earth_w, t0, t1), 3),
            "power_and_comms_pct": round(100 * _total_h(both_w) / window_h, 2),
            "sun_elevation_deg_max": round(float(sun_el.max()), 3),
            "sun_elevation_deg_min": round(float(sun_el.min()), 3),
            "sun_elevation_deg_mean_when_lit": (round(float(sun_el[st["sun_up"]].mean()), 3)
                                                if st["sun_up"].any() else None),
            "earth_elevation_deg_max": round(float(st["earth_el"].max()), 3),
            "earth_elevation_deg_min": round(float(st["earth_el"].min()), 3),
            "mean_vertical_panel_factor": round(tmean(st["pf_vertical"]), 4),
            "mean_horizontal_panel_factor": round(tmean(st["pf_horizontal"]), 4),
            "vertical_panel_energy_kwh_m2": round(
                tmean(st["irradiance"] * np.cos(np.radians(np.clip(sun_el, 0, 90))))
                * window_h / 1000, 3),
            "n_sunsets": sum(e["event"] == "sunset" for e in sun_ev),
            "n_earthsets": sum(e["event"] == "earthset" for e in earth_ev),
            "libration_lat_range_deg": [round(float(sub_e[:, 0].min()), 3),
                                        round(float(sub_e[:, 0].max()), 3)],
            "libration_lon_range_deg": [round(float(sub_e[:, 1].min()), 3),
                                        round(float(sub_e[:, 1].max()), 3)],
        },
    }
    if include_series:
        out["series"] = {
            "t_utc": [fmt_utc(t) for t in times],
            "hours_from_start": [round(_hours(t0, t), 4) for t in times],
            "sun_azimuth_deg": np.round(st["sun_az"], 3).tolist(),
            "sun_elevation_deg": np.round(sun_el, 3).tolist(),
            "sun_horizon_deg": np.round(sun_el - st["sun_margin"], 3).tolist(),
            "sun_disk_visible_fraction": np.round(st["sun_frac"], 3).tolist(),
            "earth_azimuth_deg": np.round(st["earth_az"], 3).tolist(),
            "earth_elevation_deg": np.round(st["earth_el"], 3).tolist(),
            "earth_horizon_deg": np.round(st["earth_el"] - st["earth_margin"], 3).tolist(),
            "earth_visible": st["earth_up"].tolist(),
            "irradiance_w_m2": np.round(st["irradiance"], 1).tolist(),
        }
        out["horizon_profile"] = site.horizon_profile()
    return out


LIMITATIONS = [
    "Sun/Earth positions from the ephemeris backend (analytic Meeus model or SPICE DE440)",
    "sunlit / visible = disk centre above the horizon; disk_visible_fraction gives partial disks",
    "horizon from the DEM (360 azimuth bins, rays to 100 km) only where a DEM covers the site",
    "events shorter than one sampling interval can be missed",
    "power factors are geometry only: no panel efficiency, temperature or dust",
    COMMS_NOTE,
]


def _site_and_dem(site, terrain_data):
    try:
        info = resolve_site(site)
    except KeyError as exc:
        raise _InputError("UNKNOWN_SITE", str(exc).strip("'\"")) from exc
    except ValueError as exc:
        raise _InputError("INVALID_COORDINATES", str(exc)) from exc
    _check_latlon(info["lat_deg"], info["lon_deg"])
    dem, want = _resolve_terrain(terrain_data)
    return info, dem, want


def _wrap(info, dem, want, res):
    warnings = res.pop("warnings")
    if want and dem is None:
        warnings.insert(0, "no terrain data available: smooth-sphere horizon, local shadows "
                           "ignored")
    return {"status": "ok", "result_type": "ephemeris_calculation", "warnings": warnings,
            **res, "data_sources": _source(), "limitations": LIMITATIONS}


# ---------------------------------------------------------------------------------------------
# public API
def site_conditions(site, start_datetime, window_days: float = SYNODIC_MONTH_D,
                    step_h: float = 0.5, terrain_data=None) -> dict:
    """Everything for one scenario (site + date): current Sun/Earth, countdowns, windows, metrics.

    site: catalog id ("im-1"), {"lat_deg", "lon_deg"[, "name", "elevation_m"]} or (lat, lon).
    terrain_data: None/"auto" (P2 DEM if installed), False (smooth sphere), or a DEM object.
    """
    try:
        info, dem, want = _site_and_dem(site, terrain_data)
        t0 = _parse_time(start_datetime, "start_datetime")
        res = _analyze(info, t0, float(window_days), float(step_h), dem)
    except _InputError as e:
        return _error(e.code, str(e))
    return _wrap(info, dem, want, res)


def site_timeline(site, start_datetime, days: float = SYNODIC_MONTH_D, step_h: float = 1.0,
                  terrain_data=None) -> dict:
    """`site_conditions` + time series and horizon profile, for animations and sky plots."""
    try:
        info, dem, want = _site_and_dem(site, terrain_data)
        t0 = _parse_time(start_datetime, "start_datetime")
        res = _analyze(info, t0, float(days), float(step_h), dem, include_series=True)
    except _InputError as e:
        return _error(e.code, str(e))
    return _wrap(info, dem, want, res)


COMPARE_KEYS = {  # metric -> True if higher is better
    "sunlight_pct": True, "longest_darkness_h": False, "earth_visibility_pct": True,
    "longest_comms_gap_h": False, "power_and_comms_pct": True,
    "vertical_panel_energy_kwh_m2": True, "sun_elevation_deg_max": True,
}


def _row(label, res):
    cd = res["countdown"]
    return {
        "label": label, "site": res["site"], "start_utc": res["window"]["start_utc"],
        "method": res["method"], "warnings": res["warnings"],
        "sunlit_at_start": res["now"]["sun"]["visible"],
        "sun_elevation_deg_at_start": res["now"]["sun"]["elevation_deg"],
        "earth_visible_at_start": res["now"]["earth"]["visible"],
        "earth_elevation_deg_at_start": res["now"]["earth"]["elevation_deg"],
        "sun_countdown": cd["sun"], "earth_countdown": cd["earth"],
        "metrics": res["metrics"],
        "windows": res["windows"],
    }


def _best(rows):
    best = {}
    for key, higher in COMPARE_KEYS.items():
        vals = [(r["metrics"][key], r["label"]) for r in rows]
        v = max(vals) if higher else min(vals)
        best[key] = {"label": v[1], "value": v[0],
                     "direction": "higher_is_better" if higher else "lower_is_better"}
    return best


def compare_scenarios(scenarios: list[dict], window_days: float = SYNODIC_MONTH_D,
                      step_h: float = 1.0, terrain_data=None) -> dict:
    """Side-by-side comparison of 1..12 (site, date) scenarios.

    scenarios: [{"site": <id | {lat_deg, lon_deg} | (lat, lon)>, "start_utc": ..., "label"?,
                 "window_days"?}, ...]. One row per scenario + the best scenario per metric.
    """
    try:
        if not isinstance(scenarios, (list, tuple)) or not 1 <= len(scenarios) <= 12:
            raise _InputError("INVALID_SCENARIOS", "give 1 to 12 scenarios")
        rows, warnings = [], []
        for i, sc in enumerate(scenarios):
            if not isinstance(sc, dict) or "site" not in sc or "start_utc" not in sc:
                raise _InputError("INVALID_SCENARIOS",
                                  f"scenario {i}: needs 'site' and 'start_utc'")
            info, dem, want = _site_and_dem(sc["site"], terrain_data)
            t0 = _parse_time(sc["start_utc"], f"scenarios[{i}].start_utc")
            res = _analyze(info, t0, float(sc.get("window_days", window_days)), float(step_h),
                           dem)
            label = sc.get("label") or f"{info['name']} @ {fmt_utc(t0)[:10]}"
            if want and dem is None and not warnings:
                warnings.append("no terrain data available: smooth-sphere horizon, local "
                                "shadows ignored")
            rows.append(_row(label, res))
    except _InputError as e:
        return _error(e.code, str(e))
    if len({r["label"] for r in rows}) < len(rows):
        for i, r in enumerate(rows):
            r["label"] = f"{i + 1}. {r['label']}"
    return {"status": "ok", "result_type": "ephemeris_calculation", "warnings": warnings,
            "n_scenarios": len(rows), "rows": rows, "best": _best(rows),
            "data_sources": _source(), "limitations": LIMITATIONS}


def date_sweep(site, first_start_datetime, n: int = 12, every_days: float = SYNODIC_MONTH_D,
               window_days: float | None = None, step_h: float = 1.0, terrain_data=None) -> dict:
    """Same site, n start dates spaced `every_days` apart ("what if the launch slips?").

    Default: one row per lunar day (synodic month) for a year, each analysed over the following
    lunar day. Shows the seasonal change at the poles (sub-solar latitude moves +-1.54 deg).
    """
    try:
        info, dem, want = _site_and_dem(site, terrain_data)
        t_first = _parse_time(first_start_datetime, "first_start_datetime")
        n = int(n)
        if not 1 <= n <= 36:
            raise _InputError("INVALID_PARAMETER", "n must be 1..36")
        if not 0 < float(every_days) <= 400:
            raise _InputError("INVALID_PARAMETER", "every_days must be in (0, 400]")
        wd = float(window_days) if window_days is not None else float(every_days)
        rows = []
        for k in range(n):
            t0 = t_first + timedelta(days=k * float(every_days))
            res = _analyze(info, t0, wd, float(step_h), dem)
            row = _row(fmt_utc(t0)[:10], res)
            row["sub_solar_lat_deg"] = res["now"]["sub_solar"]["lat_deg"]
            row.pop("windows")
            rows.append(row)
    except _InputError as e:
        return _error(e.code, str(e))
    warnings = (["no terrain data available: smooth-sphere horizon, local shadows ignored"]
                if want and dem is None else [])
    return {"status": "ok", "result_type": "ephemeris_calculation", "warnings": warnings,
            "site": rows[0]["site"], "every_days": float(every_days), "window_days": wd,
            "rows": rows, "best": _best(rows), "data_sources": _source(),
            "limitations": LIMITATIONS}


__all__ = ["SYNODIC_MONTH_D", "SiteModel", "compare_scenarios", "date_sweep",
           "disk_visible_fraction", "fmt_duration", "site_conditions", "site_timeline"]
