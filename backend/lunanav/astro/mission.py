"""Layer 1: Earth–Moon transfer and interception window.

APPROXIMATE, FOR VISUALISATION AND TIMING, NOT FLIGHT DYNAMICS.

* Moon positions come from the ephemeris backend (J2000, Earth-centred, km).
* Transfer: Earth two-body Lambert arc (universal variables) from a circular 185 km LEO to the
  Moon's centre at arrival, with a fixed 170 deg transfer angle in the Moon's orbital plane
  (a near-Hohmann geometry; exactly 180 deg is singular for Lambert). Lunar gravity is ignored.
* Interception window: keep the same launch (same departure state), coast the arc past and before
  the nominal arrival, and report the interval during which the spacecraft is within
  INTERCEPT_TOLERANCE_KM of the Moon's centre. The default tolerance is the Moon's sphere of
  influence (66 100 km), i.e. "arrival times at which this launch still reaches the Moon's SOI".
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np

from ._contracts import CONTRACT_VERSION, EARTH_RADIUS_KM, Meta, MissionPlan, data_mode
from .ephemeris import get_ephemeris
from .timeutil import fmt_utc, time_grid, to_utc
from .topo import body_vectors_me, sub_point

MU_EARTH = 398_600.4418  # km^3/s^2
MOON_SOI_KM = 66_100.0
LEO_ALT_KM = 185.0
TRANSFER_ANGLE_DEG = 170.0
INTERCEPT_TOLERANCE_KM = MOON_SOI_KM
TRAJECTORY_SAMPLES = 150


# ---- universal-variable two-body tools (Curtis, Orbital Mechanics for Eng. Students, ch. 3/5) --
def _stumpff(z: float) -> tuple[float, float]:
    if z > 1e-8:
        s = math.sqrt(z)
        return (s - math.sin(s)) / s**3, (1 - math.cos(s)) / z
    if z < -1e-8:
        s = math.sqrt(-z)
        return (math.sinh(s) - s) / s**3, (math.cosh(s) - 1) / (-z)
    return 1 / 6, 1 / 2


def lambert(r1: np.ndarray, r2: np.ndarray, tof_s: float, dtheta_rad: float, mu: float = MU_EARTH):
    """Velocities (v1, v2) for the arc r1 -> r2 in tof_s with transfer angle dtheta (< 2π)."""
    n1, n2 = np.linalg.norm(r1), np.linalg.norm(r2)
    A = math.sin(dtheta_rad) * math.sqrt(n1 * n2 / (1 - math.cos(dtheta_rad)))

    def y(z):
        S, C = _stumpff(z)
        return n1 + n2 + A * (z * S - 1) / math.sqrt(C)

    def F(z):
        S, C = _stumpff(z)
        yz = y(z)
        return (yz / C) ** 1.5 * S + A * math.sqrt(yz) - math.sqrt(mu) * tof_s

    # bracket the root on z (y(z) must be positive), then bisect: robust and fast enough
    lo = -4 * math.pi**2
    while y(lo) < 0:
        lo += 0.1
    hi = 4 * math.pi**2 - 1e-6
    if F(lo) > 0 or F(hi) < 0:
        raise ValueError("Lambert: no single-revolution solution for this geometry")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if F(mid) > 0:
            hi = mid
        else:
            lo = mid
    z = 0.5 * (lo + hi)
    yz = y(z)
    f = 1 - yz / n1
    g = A * math.sqrt(yz / mu)
    gdot = 1 - yz / n2
    v1 = (r2 - f * r1) / g
    v2 = (gdot * r2 - r1) / g
    return v1, v2


def kepler_propagate(r0: np.ndarray, v0: np.ndarray, dt_s: float, mu: float = MU_EARTH):
    """Universal-variable propagation of (r0, v0) by dt_s (may be negative)."""
    n0 = np.linalg.norm(r0)
    vr0 = float(r0 @ v0) / n0
    alpha = 2 / n0 - float(v0 @ v0) / mu
    sq = math.sqrt(mu)
    chi = sq * abs(alpha) * dt_s  # Curtis' initial guess
    for _ in range(100):
        z = alpha * chi**2
        S, C = _stumpff(z)
        Fx = (n0 * vr0 / sq * chi**2 * C + (1 - alpha * n0) * chi**3 * S + n0 * chi - sq * dt_s)
        dF = n0 * vr0 / sq * chi * (1 - alpha * chi**2 * S) + (1 - alpha * n0) * chi**2 * C + n0
        step = Fx / dF
        chi -= step
        if abs(step) < 1e-9:
            break
    z = alpha * chi**2
    S, C = _stumpff(z)
    f = 1 - chi**2 / n0 * C
    g = dt_s - chi**3 / sq * S
    r = f * r0 + g * v0
    nr = np.linalg.norm(r)
    fdot = sq / (nr * n0) * (alpha * chi**3 * S - chi)
    gdot = 1 - chi**2 / nr * C
    return r, fdot * r0 + gdot * v0


# ---- mission plan -------------------------------------------------------------------------
def _unit(v):
    return v / np.linalg.norm(v)


def _row(key, label, value, unit):
    return {"key": key, "label": label, "value": value, "unit": unit}


def _transfer(arrival: datetime, transfer_s: float):
    eph = get_ephemeris()
    m_prev, m_arr, m_next = eph.moon_eci_km([arrival - timedelta(hours=1), arrival,
                                             arrival + timedelta(hours=1)])
    v_moon = (m_next - m_prev) / 7200.0
    u = _unit(m_arr)
    h_hat = _unit(np.cross(m_arr, v_moon))
    w = np.cross(h_hat, u)  # in-plane, along the Moon's motion
    ang = math.radians(TRANSFER_ANGLE_DEG)
    r_leo = EARTH_RADIUS_KM + LEO_ALT_KM
    r1 = r_leo * (math.cos(-ang) * u + math.sin(-ang) * w)
    v1, v2 = lambert(r1, m_arr, transfer_s, ang)
    return r1, v1, v2, m_arr, v_moon, h_hat


def _interception_window(launch, arrival, r1, v1, search_h=48.0, step_min=10.0):
    eph = get_ephemeris()
    offsets = np.arange(-search_h * 60, search_h * 60 + step_min, step_min)  # minutes
    times = [arrival + timedelta(minutes=float(m)) for m in offsets]
    moon = eph.moon_eci_km(times)
    t0 = (arrival - launch).total_seconds()
    sc = np.array([kepler_propagate(r1, v1, t0 + m * 60)[0] for m in offsets])
    inside = np.linalg.norm(sc - moon, axis=1) <= INTERCEPT_TOLERANCE_KM
    i0 = len(offsets) // 2
    if not inside[i0]:
        return arrival - timedelta(hours=6), arrival + timedelta(hours=6), "fixed ±6 h (fallback)"
    lo = i0
    while lo > 0 and inside[lo - 1]:
        lo -= 1
    hi = i0
    while hi < len(offsets) - 1 and inside[hi + 1]:
        hi += 1
    return times[lo], times[hi], f"within {INTERCEPT_TOLERANCE_KM:,.0f} km of Moon (SOI)"


def plan_mission(arrival_utc: datetime | str, transfer_days: float = 4.0) -> MissionPlan:
    return plan_mission_detailed(arrival_utc, transfer_days)[0]


def plan_mission_detailed(arrival_utc: datetime | str, transfer_days: float = 4.0):
    """(MissionPlan, extras) where extras holds the departure/arrival state vectors."""
    if not 0.5 <= transfer_days <= 30:
        raise ValueError(f"transfer_days must be between 0.5 and 30, got {transfer_days}")
    arrival = to_utc(arrival_utc).replace(microsecond=0)
    transfer_s = transfer_days * 86400.0
    launch = arrival - timedelta(seconds=transfer_s)
    eph = get_ephemeris()

    # Moon track: launch − 1 d … arrival + 1 d, 1 h step (+ exact endpoint)
    track_t = time_grid(launch - timedelta(days=1), transfer_days * 24 + 48, 1.0)
    moon_track = eph.moon_eci_km(track_t)

    r1, v1, v2, m_arr, v_moon, h_hat = _transfer(arrival, transfer_s)
    s = np.linspace(0, 1, TRAJECTORY_SAMPLES) ** 2  # dense near Earth where the arc bends most
    traj = [(launch + timedelta(seconds=float(x * transfer_s)),
             kepler_propagate(r1, v1, float(x * transfer_s))[0]) for x in s]
    traj[-1] = (arrival, m_arr)

    win_start, win_end, win_rule = _interception_window(launch, arrival, r1, v1)

    # geometry at arrival
    sun = eph.sun_eci_km([arrival])[0]
    sun_dir = _unit(sun)
    sun_me, earth_me = body_vectors_me([arrival])
    ss_lat, ss_lon = sub_point(sun_me[0])
    se_lat, se_lon = sub_point(earth_me[0])
    # phase: angle Sun–Moon–Earth; illuminated fraction k = (1 + cos i) / 2
    sm, em = sun - m_arr, -m_arr
    phase_i = math.degrees(math.acos(float(_unit(sm) @ _unit(em))))
    illum_frac = (1 + math.cos(math.radians(phase_i))) / 2
    elong = math.degrees(math.atan2(float(np.cross(sun_dir, _unit(m_arr)) @ np.array([0, 0, 1.0])),
                                    float(sun_dir @ _unit(m_arr))))
    phase_name = _phase_name(illum_frac, elong)
    dist = float(np.linalg.norm(m_arr))
    dec = math.degrees(math.asin(m_arr[2] / dist))
    ra = math.degrees(math.atan2(m_arr[1], m_arr[0])) % 360
    r_leo = float(np.linalg.norm(r1))
    v_circ = math.sqrt(MU_EARTH / r_leo) * _unit(np.cross(np.cross(r1, v1), r1))
    dv_tli = float(np.linalg.norm(v1 - v_circ))
    c3 = float(v1 @ v1) - 2 * MU_EARTH / r_leo
    v_inf_arr = float(np.linalg.norm(v2 - v_moon))
    incl = math.degrees(math.acos(h_hat[2]))
    win_h = (win_end - win_start).total_seconds() / 3600

    params = [
        _row("earth_moon_distance_launch_km", "Earth–Moon distance at launch",
             round(float(np.linalg.norm(eph.moon_eci_km([launch])[0])), 1), "km"),
        _row("moon_ra_deg", "Moon right ascension (J2000)", round(ra, 3), "deg"),
        _row("moon_dec_deg", "Moon declination (J2000)", round(dec, 3), "deg"),
        _row("subsolar_lat_deg", "Sub-solar latitude on the Moon", round(ss_lat, 3), "deg"),
        _row("subsolar_lon_deg", "Sub-solar longitude on the Moon", round(ss_lon, 3), "deg"),
        _row("subearth_lat_deg", "Sub-Earth latitude (libration)", round(se_lat, 3), "deg"),
        _row("subearth_lon_deg", "Sub-Earth longitude (libration)", round(se_lon, 3), "deg"),
        _row("south_pole_sun_elevation_deg", "Sun elevation at the south pole (smooth sphere)",
             round(-ss_lat, 3), "deg"),
        _row("lunar_phase_angle_deg", "Lunar phase angle (Sun–Moon–Earth)", round(phase_i, 2), "deg"),
        _row("lunar_illumination_pct", "Illuminated fraction of the disk seen from Earth",
             round(illum_frac * 100, 1), "%"),
        _row("lunar_phase", "Lunar phase", phase_name, "text"),
        _row("leo_altitude_km", "Departure orbit altitude (circular)", LEO_ALT_KM, "km"),
        _row("transfer_plane_inclination_deg", "Transfer plane inclination to Earth equator",
             round(incl, 2), "deg"),
        _row("transfer_angle_deg", "Transfer angle (Lambert)", TRANSFER_ANGLE_DEG, "deg"),
        _row("tli_delta_v_km_s", "Trans-lunar injection Δv (approx.)", round(dv_tli, 3), "km/s"),
        _row("c3_km2_s2", "Launch energy C3", round(c3, 3), "km2/s2"),
        _row("arrival_v_inf_km_s", "Arrival speed relative to the Moon (no lunar gravity)",
             round(v_inf_arr, 3), "km/s"),
        _row("interception_window_h", "Interception window length", round(win_h, 2), "h"),
        _row("interception_rule", "Interception window definition", win_rule, "text"),
        _row("ephemeris_model", "Ephemeris model", eph.name, "text"),
    ]

    extras = {
        "departure_state": {"t_utc": fmt_utc(launch), "pos_km": r1, "vel_km_s": v1},
        "arrival_state": {"t_utc": fmt_utc(arrival), "pos_km": m_arr, "vel_km_s": v2},
        "moon_state_at_arrival": {"t_utc": fmt_utc(arrival), "pos_km": m_arr, "vel_km_s": v_moon},
        "interception_rule": win_rule,
        "tli_delta_v_km_s": dv_tli, "c3_km2_s2": c3, "arrival_v_inf_km_s": v_inf_arr,
    }
    plan = MissionPlan(
        meta=Meta(contract_version=CONTRACT_VERSION, data_mode=data_mode(),
                  generated_utc=fmt_utc(datetime.now(timezone.utc)),
                  sources=[eph.source,
                           "Approximate two-body Lambert transfer (visualisation, not flight dynamics)"]),
        arrival_utc=fmt_utc(arrival),
        launch_utc=fmt_utc(launch),
        transfer_duration_h=round(transfer_s / 3600, 3),
        interception_window={"start_utc": fmt_utc(win_start), "end_utc": fmt_utc(win_end)},
        earth_moon_distance_km=round(dist, 1),
        frame="J2000_ECI",
        moon_track=[{"t_utc": fmt_utc(t), "pos_km": tuple(round(float(c), 3) for c in p)}
                    for t, p in zip(track_t, moon_track, strict=True)],
        trajectory=[{"t_utc": fmt_utc(t), "pos_km": tuple(round(float(c), 3) for c in p)}
                    for t, p in traj],
        sun_direction_eci=tuple(round(float(c), 9) for c in sun_dir),
        parameters=params,
    )
    return plan, extras


def _phase_name(k: float, elong_deg: float) -> str:
    waxing = elong_deg > 0
    if k < 0.03:
        return "New Moon"
    if k > 0.97:
        return "Full Moon"
    if 0.47 <= k <= 0.53:
        return "First Quarter" if waxing else "Last Quarter"
    if k < 0.5:
        return "Waxing Crescent" if waxing else "Waning Crescent"
    return "Waxing Gibbous" if waxing else "Waning Gibbous"
