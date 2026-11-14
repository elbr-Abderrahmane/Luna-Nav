import json
from datetime import timedelta

import numpy as np
import pytest

from lunanav.astro import (
    compare_scenarios,
    date_sweep,
    get_site,
    list_sites,
    resolve_site,
    site_conditions,
    site_timeline,
)
from lunanav.astro.scenarios import SiteModel, disk_visible_fraction, fmt_duration
from lunanav.astro.sites import CATEGORIES
from lunanav.astro.timeutil import to_utc

from .mock_dem import CRATER_FLOOR_LATLON, RIDGE_TOP_LATLON, MockDEM

T0 = "2027-01-10T00:00:00Z"   # southern summer at the pole (sub-solar latitude < 0)
DEM = MockDEM(res_m=200)


# ---- sites ------------------------------------------------------------------------------------
def test_catalog_is_valid():
    sites = list_sites()
    ids = [s["id"] for s in sites]
    assert len(ids) == len(set(ids)) >= 20
    for s in sites:
        assert -90 <= s["lat_deg"] <= 90 and -180 <= s["lon_deg"] <= 180
        assert s["category"] in CATEGORIES
        assert s["coord_quality"] in ("landed", "approximate", "exact")
    cats = {s["category"] for s in sites}
    assert {"apollo", "clps", "artemis", "international"} <= cats
    assert get_site("apollo-11")["lat_deg"] == pytest.approx(0.674)


def test_resolve_custom_and_errors():
    s = resolve_site({"lat_deg": -89.5, "lon_deg": 190, "name": "Mine"})
    assert s["lon_deg"] == pytest.approx(-170) and s["name"] == "Mine"
    assert s["category"] == "custom"
    assert resolve_site((-10, 20))["lat_deg"] == -10
    with pytest.raises(KeyError):
        resolve_site("nope")
    with pytest.raises(ValueError):
        resolve_site({"lat_deg": -91, "lon_deg": 0})


# ---- helpers ----------------------------------------------------------------------------------
def test_disk_fraction_and_duration_text():
    assert disk_visible_fraction(0.0, 0.27) == pytest.approx(0.5)
    assert disk_visible_fraction(1.0, 0.27) == 1.0
    assert disk_visible_fraction(-1.0, 0.27) == 0.0
    assert 0.5 < disk_visible_fraction(0.1, 0.27) < 1
    assert fmt_duration(76.2) == "3 d 4 h 12 min"
    assert fmt_duration(0.5) == "30 min"


# ---- single scenario ----------------------------------------------------------------------------
def test_site_conditions_json_and_consistency():
    r = site_conditions("apollo-11", T0)
    json.dumps(r)
    assert r["status"] == "ok" and r["method"] == "smooth_sphere"
    m, w = r["metrics"], r["windows"]
    # equatorial near side: ~half a lunar day of sunlight, Earth always up
    assert 45 < m["sunlight_pct"] < 55
    assert m["earth_visibility_pct"] == 100 and m["longest_comms_gap_h"] == 0
    assert m["power_and_comms_pct"] == pytest.approx(m["sunlight_pct"], abs=0.01)
    assert sum(x["duration_h"] for x in w["sunlit"]) == pytest.approx(m["sunlight_hours"], abs=0.01)
    assert m["n_sunsets"] == 1
    # sun stays well above the horizon at noon at the equator
    assert m["sun_elevation_deg_max"] > 80


def test_countdown_matches_refined_event():
    r = site_conditions("apollo-11", T0)
    cd = r["countdown"]["sun"]
    assert cd["time_remaining_h"] is not None and not cd["beyond_window"]
    t = to_utc(cd["next_event_utc"])
    site = SiteModel(0.674, 23.473)
    st = site.state([t - timedelta(minutes=2), t + timedelta(minutes=2)])
    assert st["sun_up"][0] != st["sun_up"][1]
    assert r["next_events"][0]["in_h"] <= cd["time_remaining_h"]


def test_far_side_never_sees_earth():
    r = site_conditions("change-4", T0)
    assert r["metrics"]["earth_visibility_pct"] == 0
    assert r["countdown"]["earth"]["beyond_window"]
    assert r["windows"]["power_and_comms"] == []


def test_pole_sun_skims_horizon():
    r = site_conditions("south-pole", T0)
    assert r["metrics"]["sun_elevation_deg_max"] < 1.6
    lib = r["metrics"]["libration_lat_range_deg"]
    assert lib[0] < -5 and lib[1] > 5          # Earth bobs up and down at the pole
    assert 0 < r["metrics"]["earth_visibility_pct"] < 100


def test_terrain_ridge_beats_crater():
    ridge = site_conditions({"lat_deg": RIDGE_TOP_LATLON[0], "lon_deg": RIDGE_TOP_LATLON[1]},
                            T0, terrain_data=DEM)
    crater = site_conditions({"lat_deg": CRATER_FLOOR_LATLON[0],
                              "lon_deg": CRATER_FLOOR_LATLON[1]}, T0, terrain_data=DEM)
    assert ridge["method"] == crater["method"] == "horizon_mask"
    assert ridge["metrics"]["sunlight_pct"] > crater["metrics"]["sunlight_pct"]
    assert crater["metrics"]["sunlight_pct"] == 0


def test_dem_failure_falls_back_with_warning():
    class Broken(MockDEM):
        def sample_elevation(self, lat_deg, lon_deg):
            raise ValueError("outside DEM")

    r = site_conditions("apollo-11", T0, terrain_data=Broken())
    assert r["status"] == "ok" and r["method"] == "smooth_sphere"
    assert any("terrain horizon unavailable" in w for w in r["warnings"])


@pytest.mark.parametrize("site,start,kw,code", [
    ("nope", T0, {}, "UNKNOWN_SITE"),
    ({"lat_deg": 99, "lon_deg": 0}, T0, {}, "INVALID_COORDINATES"),
    ("im-1", "garbage", {}, "INVALID_DATETIME"),
    ("im-1", T0, {"window_days": 0}, "INVALID_WINDOW"),
    ("im-1", T0, {"step_h": 0}, "INVALID_STEP"),
])
def test_errors_do_not_raise(site, start, kw, code):
    r = site_conditions(site, start, **kw)
    assert r["status"] == "error" and r["error"]["code"] == code


# ---- timeline, comparison, sweep ------------------------------------------------------------------
def test_timeline_series_shapes():
    r = site_timeline("connecting-ridge", T0, days=2, step_h=1)
    s = r["series"]
    assert len(s["t_utc"]) == 49 == len(s["sun_elevation_deg"]) == len(s["earth_visible"])
    assert len(r["horizon_profile"]["azimuth_deg"]) == 360


def test_compare_scenarios_best_per_metric():
    r = compare_scenarios([
        {"site": "apollo-11", "start_utc": T0},
        {"site": "change-4", "start_utc": T0},
        {"site": {"lat_deg": -89.45, "lon_deg": -137.3}, "start_utc": T0, "label": "ridge"},
    ])
    json.dumps(r)
    assert r["status"] == "ok" and r["n_scenarios"] == 3
    assert r["best"]["earth_visibility_pct"]["value"] == 100
    assert r["best"]["longest_comms_gap_h"]["label"].startswith("Apollo 11")
    assert compare_scenarios([])["error"]["code"] == "INVALID_SCENARIOS"
    assert compare_scenarios([{"site": "im-1"}])["error"]["code"] == "INVALID_SCENARIOS"


def test_date_sweep_shows_polar_seasons():
    r = date_sweep("connecting-ridge", "2027-01-01T00:00:00Z", n=12)
    assert r["status"] == "ok" and len(r["rows"]) == 12
    sun = np.array([row["metrics"]["sunlight_pct"] for row in r["rows"]])
    sub = np.array([row["sub_solar_lat_deg"] for row in r["rows"]])
    assert sun.max() - sun.min() > 30            # seasons matter at the pole
    # more sunlight when the sub-solar point is south (southern summer)
    assert sun[sub < -0.5].mean() > sun[sub > 0.5].mean()
