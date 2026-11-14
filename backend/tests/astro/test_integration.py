import json

import pytest

from lunanav.astro import (
    analyze_earth_visibility,
    analyze_illumination,
    calculate_mission,
)

from .mock_dem import CRATER_FLOOR_LATLON, RIDGE_TOP_LATLON, MockDEM

DEM = MockDEM(res_m=200)
T0, T1 = "2026-11-13T00:00:00Z", "2026-11-20T00:00:00Z"


def test_calculate_mission_ok_and_labelled():
    m = calculate_mission("2027-03-14T12:00:00Z", {"transfer_days": 4})
    json.dumps(m)  # JSON-ready
    assert m["status"] == "ok" and m["result_type"] == "simplified_transfer"
    assert m["departure_utc"] == "2027-03-10T12:00:00Z" and m["transfer_duration_h"] == 96
    assert m["frame"]["name"] == "J2000_ECI" and "J2000.0" in m["frame"]["epoch"]
    assert m["units"]["position"] == "km" and m["units"]["velocity"] == "km/s"
    for key in ("departure_state", "arrival_state", "moon_state_at_arrival"):
        assert m[key]["frame"] == "J2000_ECI" and len(m[key]["vel_km_s"]) == 3
    assert m["trajectory"]["n_samples"] >= 100 and m["trajectory"]["frame"] == "J2000_ECI"
    assert m["interception_window"]["result_type"] == "geometric_estimate"
    assert any("not a validated" in w for w in m["warnings"])
    assert m["mission_plan"]["frame"] == "J2000_ECI"


@pytest.mark.parametrize("arg,params,code", [
    ("not a date", None, "INVALID_DATETIME"),
    ("2200-01-01T00:00:00Z", None, "DATETIME_OUT_OF_RANGE"),
    ("2027-03-14T12:00:00Z", {"transfer_days": 0.1}, "INVALID_PARAMETER"),
    ("2027-03-14T12:00:00Z", {"transfer_days": "x"}, "INVALID_PARAMETER"),
])
def test_calculate_mission_errors_do_not_raise(arg, params, code):
    m = calculate_mission(arg, params)
    assert m["status"] == "error" and m["error"]["code"] == code


def test_unknown_parameter_warns():
    m = calculate_mission("2027-03-14T12:00:00Z", {"propellant": "LOX"})
    assert m["status"] == "ok" and any("propellant" in w for w in m["warnings"])


def test_analyze_illumination_hours_add_up():
    r = analyze_illumination(*RIDGE_TOP_LATLON, T0, T1, terrain_data=DEM)
    assert r["status"] == "ok" and r["method"] == "horizon_mask"
    assert r["illumination_hours"] + r["shadow_hours"] == pytest.approx(168)
    assert r["n_samples"] == 168 and r["sampling_interval_h"] == 1
    assert r["terrain_obstruction_considered"] is True
    crater = analyze_illumination(*CRATER_FLOOR_LATLON, T0, T1, terrain_data=DEM)
    assert crater["illumination_hours"] == 0 and crater["longest_shadow_h"] == 168


def test_analyze_illumination_without_terrain_warns():
    r = analyze_illumination(-89.5, 0, T0, T1)
    assert r["method"] == "smooth_sphere" and r["warnings"]
    r = analyze_illumination(-89.5, 0, T0, T1, terrain_data=False)
    assert r["warnings"] == []


@pytest.mark.parametrize("lat,t0,t1,code", [
    (-95, T0, T1, "INVALID_COORDINATES"),
    (-89, T1, T0, "INVALID_PERIOD"),
    (-89, "bad", T1, "INVALID_DATETIME"),
])
def test_analyze_illumination_errors(lat, t0, t1, code):
    assert analyze_illumination(lat, 0, t0, t1)["error"]["code"] == code


def test_earth_visibility_terrain_status():
    floor = analyze_earth_visibility(*CRATER_FLOOR_LATLON, T0, terrain_data=DEM)
    assert floor["earth_visible"] is False
    assert floor["terrain_obstruction_status"] in ("obstructed_by_terrain", "below_geometric_horizon")
    smooth = analyze_earth_visibility(-89.5, 0, T0)
    assert smooth["terrain_obstruction_status"] == "not_evaluated"
    assert "radio" in smooth["communication_note"]


def test_earth_visibility_interval():
    r = analyze_earth_visibility(-89.5, 0, T0, terrain_data=False, end_datetime=T1)
    assert 0 <= r["interval"]["earth_visibility_pct"] <= 100
    assert r["interval"]["n_samples"] == 168


def test_reference_cases_from_answer_doc():
    m = calculate_mission("2027-03-14T12:00:00Z")
    assert m["earth_moon_distance_km"] == pytest.approx(374_710, abs=20)
    assert m["interception_window"]["start_utc"] == "2027-03-13T15:20:00Z"
    assert m["interception_window"]["end_utc"] == "2027-03-15T08:40:00Z"
    r = analyze_illumination(-90, 0, T0, T1, terrain_data=False)
    assert r["illumination_hours"] == 168 and r["sun_elevation_deg_at_start"] == pytest.approx(1.56, abs=0.01)
    a, b = "2027-03-14T12:00:00Z", "2027-03-21T12:00:00Z"
    r = analyze_illumination(-89.45, -137, a, b, terrain_data=False)
    assert r["illumination_hours"] == 0 and r["shadow_hours"] == 168
    e = analyze_earth_visibility(-89.45, -137, a, terrain_data=False, end_datetime=b)
    assert e["earth_visible"] and e["earth_elevation_deg"] == pytest.approx(5.75, abs=0.01)
    assert e["interval"]["earth_visibility_pct"] == pytest.approx(66.07, abs=0.01)
