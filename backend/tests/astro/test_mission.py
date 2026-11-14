import time
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from lunanav.astro import plan_mission
from lunanav.astro._contracts import MissionPlan
from lunanav.astro.mission import MU_EARTH, kepler_propagate, lambert
from lunanav.astro.timeutil import to_utc

ARRIVAL = "2027-03-14T12:00:00Z"


@pytest.fixture(scope="module")
def plan():
    return plan_mission(ARRIVAL)


def test_valid_model_and_times(plan):
    assert isinstance(plan, MissionPlan)
    MissionPlan.model_validate(plan.model_dump())
    assert plan.arrival_utc == ARRIVAL
    assert plan.launch_utc == "2027-03-10T12:00:00Z"
    assert plan.transfer_duration_h == 96
    assert plan.frame == "J2000_ECI"
    for s in [plan.meta.generated_utc, plan.launch_utc] + [p.t_utc for p in plan.trajectory]:
        assert s.endswith("Z")


def test_moon_track_coverage(plan):
    t = [to_utc(p.t_utc) for p in plan.moon_track]
    assert t[0] == to_utc(plan.launch_utc) - timedelta(days=1)
    assert t[-1] == to_utc(plan.arrival_utc) + timedelta(days=1)
    assert max(np.diff([x.timestamp() for x in t])) <= 3600
    d = np.linalg.norm([p.pos_km for p in plan.moon_track], axis=1)
    assert d.min() > 356_000 and d.max() < 407_000


def test_trajectory_leo_to_moon(plan):
    tr = plan.trajectory
    assert len(tr) >= 100
    assert np.linalg.norm(tr[0].pos_km) == pytest.approx(6371 + 185, abs=1)
    arrival_moon = next(p.pos_km for p in plan.moon_track if p.t_utc == ARRIVAL)
    assert np.allclose(tr[-1].pos_km, arrival_moon, atol=1)
    assert np.linalg.norm(np.array(tr[-2].pos_km) - arrival_moon) < 20_000
    assert tr[0].t_utc == plan.launch_utc and tr[-1].t_utc == plan.arrival_utc


def test_interception_window_contains_arrival(plan):
    w = plan.interception_window
    s, e, a = to_utc(w.start_utc), to_utc(w.end_utc), to_utc(ARRIVAL)
    assert s < a < e
    assert timedelta(hours=6) <= e - s <= timedelta(hours=96)


def test_geometry_and_parameters(plan):
    assert np.linalg.norm(plan.sun_direction_eci) == pytest.approx(1, abs=1e-6)
    assert 356_000 < plan.earth_moon_distance_km < 407_000
    keys = {p.key: p for p in plan.parameters}
    assert all(p.unit for p in plan.parameters)
    assert 2.9 < keys["tli_delta_v_km_s"].value < 3.4  # typical TLI from LEO
    assert abs(keys["subsolar_lat_deg"].value) < 1.6
    assert 0 <= keys["lunar_illumination_pct"].value <= 100


def test_plan_under_one_second():
    t0 = time.perf_counter()
    plan_mission(datetime(2028, 1, 1, tzinfo=UTC), transfer_days=3.0)
    assert time.perf_counter() - t0 < 1.0


def test_lambert_round_trip():
    r1 = np.array([6556.0, 0, 0])
    r2 = np.array([-380_000.0, 50_000, 10_000])
    dth = np.arccos(r1 @ r2 / np.linalg.norm(r1) / np.linalg.norm(r2))
    v1, _ = lambert(r1, r2, 4 * 86400, dth, MU_EARTH)
    r, _ = kepler_propagate(r1, v1, 4 * 86400)
    assert np.linalg.norm(r - r2) < 1.0


@pytest.mark.parametrize("days", [3.0, 4.0, 5.0])
def test_other_transfer_durations(days):
    p = plan_mission(ARRIVAL, transfer_days=days)
    assert p.transfer_duration_h == days * 24
