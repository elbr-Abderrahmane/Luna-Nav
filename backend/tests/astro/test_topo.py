from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from lunanav.astro import earth_az_el, sun_az_el
from lunanav.astro.topo import az_el, body_vectors_me, sub_point

T = datetime(2026, 11, 13, tzinfo=UTC)


def test_pole_sun_elevation_never_above_1p6_deg():
    for k in range(0, 366 * 24, 6):
        _, el = sun_az_el(-90.0, 0.0, 0.0, T + timedelta(hours=k))
        assert abs(el) < 1.6


def test_sun_circles_pole_once_per_synodic_month():
    az = [sun_az_el(-90, 0, 0, T + timedelta(hours=h))[0] for h in range(0, 30 * 24, 1)]
    turns = np.sum(np.abs(np.diff(np.unwrap(np.radians(az))))) / (2 * np.pi)
    assert turns == pytest.approx(30 / 29.53, abs=0.03)


def test_pole_azimuth_equals_subsolar_longitude():
    sun_me, _ = body_vectors_me([T])
    _, lon = sub_point(sun_me[0])
    az, _el = sun_az_el(-90, 0, 0, T)
    assert az == pytest.approx(lon % 360, abs=1e-6)


def test_azimuth_convention_cardinal_directions():
    far = 1e9
    # at 85S 0E: +Z (toward north pole) is north, +Y is east
    az, _ = az_el(np.array([0, 0, far]), -85, 0)
    assert az[0] == pytest.approx(0, abs=1e-6)
    az, el = az_el(np.array([0, far, 0]), -85, 0)
    assert az[0] == pytest.approx(90, abs=1e-6) and el[0] == pytest.approx(0, abs=1e-3)


def test_earth_low_on_south_pole_horizon():
    for k in range(0, 60 * 24, 6):
        _, el = earth_az_el(-90, 0, 0, T + timedelta(hours=k))
        assert abs(el) < 8
