"""Integration wrappers for P5 (questionnaire interface).

    from lunanav.astro import calculate_mission, analyze_illumination, analyze_earth_visibility

Thin wrappers over the README §7.8 functions. They return plain JSON-ready dicts and never raise
on bad input: every response has `status` ("ok" | "error"), `warnings` (list of str) and, on
error, `error` = {"code", "message"}. Every vector carries its frame, epoch and units, and every
orbital result carries an honest `result_type` label.

Result-type vocabulary (questionnaire §6):
  * "simplified_transfer"   two-body Lambert arc, Earth gravity only — NOT a validated or
                             mission-feasible trajectory
  * "geometric_estimate"    pure geometry (positions, angles, tolerance windows)
  * "ephemeris_calculation" positions from an ephemeris model
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from .ephemeris import get_ephemeris
from .horizon import default_dem
from .illumination import geometry_series
from .mission import (
    INTERCEPT_TOLERANCE_KM,
    LEO_ALT_KM,
    TRANSFER_ANGLE_DEG,
    plan_mission_detailed,
)
from .timeutil import fmt_utc, time_grid, to_utc

ECI_FRAME = {
    "name": "J2000_ECI",
    "center": "Earth",
    "axes": "ICRF/J2000 mean equator and equinox",
    "epoch": "J2000.0 = 2000-01-01T12:00:00 TT",
}
UNITS = {"position": "km", "velocity": "km/s", "time": "UTC, ISO-8601 ending in Z",
         "angles": "deg", "duration": "h"}
VALID_RANGE = (datetime(1950, 1, 1, tzinfo=timezone.utc), datetime(2100, 1, 1, tzinfo=timezone.utc))
COMMS_NOTE = ("Geometric line of sight to the Earth's centre only. Actual radio communication also "
              "depends on antenna pointing and gain, link budget, ground-station coverage on Earth, "
              "relay satellites and the lander's own terrain mask; it is not modelled here.")


def _error(code: str, message: str, **extra) -> dict:
    return {"status": "error", "error": {"code": code, "message": message}, "warnings": [], **extra}


def _parse_time(value, name: str):
    try:
        t = to_utc(value)
    except (TypeError, ValueError) as exc:
        raise _InputError("INVALID_DATETIME", f"{name}: cannot parse {value!r} ({exc})") from exc
    if not VALID_RANGE[0] <= t <= VALID_RANGE[1]:
        raise _InputError("DATETIME_OUT_OF_RANGE",
                          f"{name}: {fmt_utc(t)} outside supported range 1950–2100")
    return t


def _check_latlon(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError) as exc:
        raise _InputError("INVALID_COORDINATES", "latitude/longitude must be numbers") from exc
    if not -90 <= lat <= 90 or not np.isfinite(lon):
        raise _InputError("INVALID_COORDINATES", f"latitude {lat} outside -90..90")
    lon = ((lon + 180.0) % 360.0) - 180.0
    return lat, lon


class _InputError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _resolve_terrain(terrain_data):
    """terrain_data: None/"auto" -> P2's DEM if installed; False -> smooth sphere; object -> DEM."""
    if terrain_data is False:
        return None, False
    if terrain_data is None or terrain_data == "auto":
        return default_dem(), True
    if not (hasattr(terrain_data, "dem_window") and hasattr(terrain_data, "sample_elevation")):
        raise _InputError("INVALID_TERRAIN",
                          "terrain_data must provide dem_window() and sample_elevation()")
    return terrain_data, True


def _vec(v):
    return [round(float(c), 6) for c in v]


def _source():
    eph = get_ephemeris()
    return {"ephemeris_backend": eph.name, "ephemeris_source": eph.source}


# ---------------------------------------------------------------------------------------------
def calculate_mission(arrival_datetime, parameters: dict | None = None) -> dict:
    """Layer 1. `parameters` (all optional): {"transfer_days": 4.0}.

    Returns departure/arrival times and states, Earth–Moon distance, interception window,
    trajectory samples (J2000 ECI, km), assumptions, status and warnings. `mission_plan` holds
    the README §7.2 `MissionPlan` contract object for the API.
    """
    parameters = dict(parameters or {})
    try:
        arrival = _parse_time(arrival_datetime, "arrival_datetime")
        try:
            transfer_days = float(parameters.pop("transfer_days", 4.0))
        except (TypeError, ValueError) as exc:
            raise _InputError("INVALID_PARAMETER", "transfer_days must be a number") from exc
        if not 0.5 <= transfer_days <= 30:
            raise _InputError("INVALID_PARAMETER", "transfer_days must be between 0.5 and 30")
        warnings = [f"ignored unknown parameter '{k}'" for k in parameters]
        plan, ex = plan_mission_detailed(arrival, transfer_days)
    except _InputError as e:
        return _error(e.code, str(e))
    except ValueError as e:
        return _error("NO_SOLUTION", str(e))

    if get_ephemeris().name == "analytic":
        warnings.append("analytic ephemeris in use (Meeus); install SPICE kernels for DE440 accuracy")
    if "fallback" in ex["interception_rule"]:
        warnings.append("interception window could not be derived; fixed ±6 h used")
    warnings.append("trajectory is a simplified two-body transfer for visualisation and timing; "
                    "it is not a validated or mission-feasible trajectory")

    def state(s):
        return {"t_utc": s["t_utc"], "pos_km": _vec(s["pos_km"]), "vel_km_s": _vec(s["vel_km_s"]),
                "frame": "J2000_ECI"}

    return {
        "status": "ok",
        "result_type": "simplified_transfer",
        "warnings": warnings,
        "frame": ECI_FRAME,
        "units": UNITS,
        "departure_utc": plan.launch_utc,
        "arrival_utc": plan.arrival_utc,
        "transfer_duration_h": plan.transfer_duration_h,
        "earth_moon_distance_km": plan.earth_moon_distance_km,
        "earth_moon_distance_definition": "centre to centre at arrival_utc",
        "interception_window": {
            "start_utc": plan.interception_window.start_utc,
            "end_utc": plan.interception_window.end_utc,
            "result_type": "geometric_estimate",
            "definition": (f"arrival times at which the coasting arc from this same launch is within "
                           f"{INTERCEPT_TOLERANCE_KM:,.0f} km (lunar sphere of influence) of the "
                           "Moon's centre; lunar gravity ignored"),
            "tolerance_km": INTERCEPT_TOLERANCE_KM,
        },
        "departure_state": state(ex["departure_state"]),
        "arrival_state": state(ex["arrival_state"]),
        "moon_state_at_arrival": state(ex["moon_state_at_arrival"]),
        "delta_v_estimates": {
            "tli_delta_v_km_s": round(ex["tli_delta_v_km_s"], 4),
            "c3_km2_s2": round(ex["c3_km2_s2"], 4),
            "arrival_v_inf_km_s": round(ex["arrival_v_inf_km_s"], 4),
            "result_type": "simplified_transfer",
        },
        "trajectory": {"frame": "J2000_ECI", "units": "km", "n_samples": len(plan.trajectory),
                       "samples": [p.model_dump() for p in plan.trajectory]},
        "moon_track": {"frame": "J2000_ECI", "units": "km", "step_h": 1.0,
                       "result_type": "ephemeris_calculation",
                       "samples": [p.model_dump() for p in plan.moon_track]},
        "sun_direction_eci": {"vector": list(plan.sun_direction_eci), "frame": "J2000_ECI",
                              "units": "unit vector Earth→Sun", "t_utc": plan.arrival_utc},
        "assumptions": [
            (f"departure from a circular parking orbit at {LEO_ALT_KM:g} km altitude "
             "in the Moon's orbital plane"),
            "departure epoch = arrival − transfer_days (user-chosen, default 4 d)",
            f"Lambert two-body solution, Earth gravity only, transfer angle {TRANSFER_ANGLE_DEG:g}°",
            "impulsive TLI burn, no finite-burn losses, no mid-course corrections",
            "aim point = Moon centre at arrival; lunar gravity, Sun third-body and J2 ignored",
            "no lunar orbit insertion or descent modelled",
        ],
        "data_sources": _source(),
        "mission_plan": plan.model_dump(mode="json"),
    }


# ---------------------------------------------------------------------------------------------
def analyze_illumination(latitude, longitude, start_datetime, end_datetime, terrain_data=None,
                         step_h: float = 1.0, elevation_m: float | None = None) -> dict:
    """Direct-sunlight analysis at a lunar point over [start, end).

    terrain_data: None/"auto" = P2's DEM if available (else smooth sphere, with a warning);
    False = smooth sphere; or an object with dem_window()/sample_elevation(). Terrain data is
    required for local shadows; without it only the Moon's curvature is accounted for.
    """
    try:
        lat, lon = _check_latlon(latitude, longitude)
        t0 = _parse_time(start_datetime, "start_datetime")
        t1 = _parse_time(end_datetime, "end_datetime")
        if t1 <= t0:
            raise _InputError("INVALID_PERIOD", "end_datetime must be after start_datetime")
        if not 0 < step_h <= 24:
            raise _InputError("INVALID_STEP", "step_h must be in (0, 24]")
        if (t1 - t0) / timedelta(hours=step_h) > 20_000:
            raise _InputError("PERIOD_TOO_LONG", "more than 20 000 samples; increase step_h")
        dem, want_terrain = _resolve_terrain(terrain_data)
        times = time_grid(t0, (t1 - t0).total_seconds() / 3600, step_h)
        if times[-1] >= t1:
            times = times[:-1]
        g = geometry_series(lat, lon, elevation_m, times, use_horizon=dem is not None, dem=dem)
    except _InputError as e:
        return _error(e.code, str(e))

    warnings = []
    if want_terrain and dem is None:
        warnings.append("no terrain data available: smooth-sphere horizon, local shadows ignored")
    lit = g["sun_el"] > g["sun_horizon"]
    n = len(times)
    dark_runs = _runs(~lit)
    period_h = (t1 - t0).total_seconds() / 3600
    return {
        "status": "ok",
        "result_type": "geometric_estimate",
        "warnings": warnings,
        "location": {"lat_deg": lat, "lon_deg": lon, "elevation_m": round(g["elevation_m"], 2),
                     "frame": "MOON_ME (planetocentric, 1737.4 km sphere)"},
        "observation_period": {"start_utc": fmt_utc(t0), "end_utc": fmt_utc(t1),
                               "duration_h": round(period_h, 3)},
        "sampling_interval_h": step_h,
        "n_samples": n,
        "illumination_hours": round(float(lit.sum()) * step_h, 3),
        "shadow_hours": round(float((~lit).sum()) * step_h, 3),
        "illumination_pct": round(float(lit.mean()) * 100, 2),
        "longest_shadow_h": round(max(dark_runs, default=0) * step_h, 3),
        "sunlit_at_start": bool(lit[0]),
        "sun_azimuth_deg_at_start": round(float(g["sun_az"][0]), 3),
        "sun_elevation_deg_at_start": round(float(g["sun_el"][0]), 3),
        "sun_elevation_deg_range": [round(float(g["sun_el"].min()), 3),
                                    round(float(g["sun_el"].max()), 3)],
        "terrain_obstruction_considered": g["method"] == "horizon_mask",
        "method": g["method"],
        "methodology": ("Sun position from the ephemeris, rotated into the lunar ME frame; sunlit "
                        "when the centre of the solar disk is above the local horizon at the Sun's "
                        "azimuth (horizon = DEM horizon mask with lunar curvature, or 0° on a "
                        "smooth sphere). Each sample counts for one sampling interval."),
        "data_sources": {**_source(),
                         "terrain": getattr(dem, "DEM_ID", "lunanav.terrain.dem") if dem else None,
                         "illumination_dataset": None},
        "confidence": "medium" if g["method"] == "horizon_mask" else "low (no local terrain)",
        "limitations": [
            "solar disk treated as a point (0.27° radius ignored: partial sunrise/sunset)",
            "horizon resolution limited by the DEM and 360 azimuth bins, rays to 100 km",
            "no NASA illumination map used; values not yet cross-checked against LOLA products",
            "sampling at step_h can miss shadows shorter than one interval",
        ],
    }


def _runs(mask) -> list[int]:
    out, run = [], 0
    for m in mask:
        if m:
            run += 1
        elif run:
            out.append(run)
            run = 0
    if run:
        out.append(run)
    return out


# ---------------------------------------------------------------------------------------------
def analyze_earth_visibility(latitude, longitude, observation_datetime, terrain_data=None,
                             end_datetime=None, step_h: float = 1.0,
                             elevation_m: float | None = None) -> dict:
    """Geometric Earth visibility at one time; add `end_datetime` for % over an interval."""
    try:
        lat, lon = _check_latlon(latitude, longitude)
        t0 = _parse_time(observation_datetime, "observation_datetime")
        dem, want_terrain = _resolve_terrain(terrain_data)
        times = [t0]
        if end_datetime is not None:
            t1 = _parse_time(end_datetime, "end_datetime")
            if t1 <= t0:
                raise _InputError("INVALID_PERIOD", "end_datetime must be after observation_datetime")
            times = time_grid(t0, (t1 - t0).total_seconds() / 3600, step_h)
            if times[-1] >= t1:
                times = times[:-1]
        g = geometry_series(lat, lon, elevation_m, times, use_horizon=dem is not None, dem=dem)
    except _InputError as e:
        return _error(e.code, str(e))

    warnings = []
    if want_terrain and dem is None:
        warnings.append("no terrain data available: terrain obstruction not evaluated")
    el, hz = g["earth_el"], g["earth_horizon"]
    above_sphere = el > 0
    visible = el > hz
    terrain_eval = g["method"] == "horizon_mask"
    if not terrain_eval:
        obstruction = "not_evaluated"
    elif visible[0]:
        obstruction = "clear"
    elif above_sphere[0]:
        obstruction = "obstructed_by_terrain"
    else:
        obstruction = "below_geometric_horizon"
    out = {
        "status": "ok",
        "result_type": "geometric_estimate",
        "warnings": warnings,
        "location": {"lat_deg": lat, "lon_deg": lon, "elevation_m": round(g["elevation_m"], 2),
                     "frame": "MOON_ME (planetocentric, 1737.4 km sphere)"},
        "observation_utc": fmt_utc(t0),
        "earth_visible": bool(visible[0]),
        "earth_elevation_deg": round(float(el[0]), 3),
        "earth_azimuth_deg": round(float(g["earth_az"][0]), 3),
        "horizon_elevation_deg_at_earth_azimuth": round(float(hz[0]), 3),
        "earth_above_geometric_horizon": bool(above_sphere[0]),
        "terrain_obstruction_status": obstruction,
        "direct_line_of_sight": bool(visible[0]),
        "method": g["method"],
        "communication_note": COMMS_NOTE,
        "data_sources": _source(),
        "limitations": [
            "Earth treated as a point at its centre (apparent radius ~0.95° ignored)",
            "terrain obstruction only with a DEM; 360 azimuth bins, rays to 100 km",
            COMMS_NOTE,
        ],
    }
    if end_datetime is not None:
        out["interval"] = {
            "start_utc": fmt_utc(times[0]), "end_utc": fmt_utc(to_utc(end_datetime)),
            "sampling_interval_h": step_h, "n_samples": len(times),
            "earth_visibility_pct": round(float(visible.mean()) * 100, 2),
            "earth_visible_hours": round(float(visible.sum()) * step_h, 3),
            "earth_elevation_deg_range": [round(float(el.min()), 3), round(float(el.max()), 3)],
        }
    return out
