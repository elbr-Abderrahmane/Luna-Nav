import time
from datetime import UTC, datetime

import numpy as np
import pytest

from lunanav.astro import horizon_mask, illumination_area, illumination_at
from lunanav.astro._contracts import IlluminationSummary, LatLon
from lunanav.astro.horizon import cache_dir, horizon_at

from .mock_dem import CRATER_FLOOR_LATLON, RIDGE_TOP_LATLON, MockDEM

ARRIVAL = datetime(2026, 11, 13, tzinfo=UTC)  # pole Sun elevation ~ +1.5 deg
ARRIVAL_LOW = datetime(2027, 3, 14, 12, tzinfo=UTC)  # pole Sun elevation ~ -0.8 deg
DEM = MockDEM(res_m=200)


def test_flat_dem_horizon_is_the_curvature_dip():
    mask = horizon_mask(-88.0, 30.0, dem=MockDEM(res_m=200, flat=True), max_dist_km=50)
    dip = -np.degrees(np.arccos(1737400 / (1737400 + 2.0)))  # 2 m observer height
    assert mask.shape == (360,)
    assert np.all(mask < 0) and np.all(mask > dip - 0.01)


def test_works_at_the_exact_pole():
    mask = horizon_mask(-90.0, 0.0, dem=DEM, max_dist_km=60)
    assert np.isfinite(mask).all()
    assert mask.max() > mask.min()  # crater at 1 deg away (30 km) shows up in one direction


def test_crater_floor_is_enclosed():
    mask = horizon_mask(*CRATER_FLOOR_LATLON, dem=DEM)
    assert mask.min() > 5.0  # 2.9 km of rim relief within 8 km


def test_ridge_beats_crater_floor():
    for arrival in (ARRIVAL, ARRIVAL_LOW):
        ridge = illumination_at(*RIDGE_TOP_LATLON, None, arrival, dem=DEM)
        crater = illumination_at(*CRATER_FLOOR_LATLON, None, arrival, dem=DEM)
        assert ridge.method == crater.method == "horizon_mask"
        assert ridge.illumination_pct > crater.illumination_pct
        assert crater.illumination_pct == 0 and crater.longest_shadow_h == 7 * 24
        assert crater.earth_visibility_pct == 0
    ridge = illumination_at(*RIDGE_TOP_LATLON, None, ARRIVAL, dem=DEM)
    assert ridge.illumination_pct > 80


def test_summary_fields_and_window():
    s = illumination_at(-89.5, 10.0, 0.0, ARRIVAL, use_horizon=False)
    assert isinstance(s, IlluminationSummary)
    assert s.method == "smooth_sphere"
    assert s.window_start_utc == "2026-11-13T00:00:00Z"
    assert s.window_end_utc == "2026-11-20T00:00:00Z"
    assert 0 <= s.illumination_pct <= 100 and 0 <= s.earth_visibility_pct <= 100
    assert 0 <= s.longest_shadow_h <= 168
    assert s.sunlit_at_arrival == (s.sun_elevation_deg_at_arrival > 0)


def test_falls_back_to_smooth_sphere_without_dem():
    s = illumination_at(-89.5, 10.0, 0.0, ARRIVAL)  # lunanav.terrain.dem absent
    assert s.method == "smooth_sphere"


def test_horizon_cache_written_and_reused():
    t0 = time.perf_counter()
    a = horizon_mask(*RIDGE_TOP_LATLON, dem=DEM)
    cold = time.perf_counter() - t0
    files = list(cache_dir().glob("*.npy"))
    assert len(files) == 1
    t0 = time.perf_counter()
    b = horizon_mask(*RIDGE_TOP_LATLON, dem=DEM)
    assert time.perf_counter() - t0 < cold
    np.testing.assert_array_equal(a, b)


def test_point_illumination_with_cached_horizon_under_1s():
    illumination_at(*RIDGE_TOP_LATLON, None, ARRIVAL, dem=DEM)
    t0 = time.perf_counter()
    illumination_at(*RIDGE_TOP_LATLON, None, ARRIVAL, dem=DEM)
    assert time.perf_counter() - t0 < 1.0


def test_horizon_interpolation_wraps():
    m = np.zeros(360, np.float32)
    m[359], m[0] = 2.0, 4.0
    assert horizon_at(m, np.array([359.5]))[0] == pytest.approx(3.0)


def test_area_aggregation_rules():
    pts = [LatLon(lat_deg=lat, lon_deg=lon) for lat, lon in
           [RIDGE_TOP_LATLON, CRATER_FLOOR_LATLON, (-88.6, -60.5)]]
    area = illumination_area(pts, ARRIVAL, dem=DEM)
    each = [illumination_at(p.lat_deg, p.lon_deg, None, ARRIVAL, dem=DEM) for p in pts]
    assert area.illumination_pct == pytest.approx(np.mean([e.illumination_pct for e in each]), abs=0.01)
    assert area.longest_shadow_h == max(e.longest_shadow_h for e in each)
    assert area.sunlit_at_arrival == (sum(e.sunlit_at_arrival for e in each) >= 2)
    assert area.method == "horizon_mask"
    fast = illumination_area(pts, ARRIVAL, use_horizon=False)
    assert fast.method == "smooth_sphere"
