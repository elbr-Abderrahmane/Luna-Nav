from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from lunanav.astro.ephemeris import (
    AU_KM,
    AnalyticEphemeris,
    find_kernels,
    moon_ecliptic_of_date,
    sun_ecliptic_of_date,
)
from lunanav.astro.topo import body_vectors_me, sub_point

YEAR = [datetime(2027, 1, 1, tzinfo=UTC) + timedelta(hours=6 * k) for k in range(4 * 366)]


def test_meeus_moon_example_47a():
    lon, lat, dist = moon_ecliptic_of_date(np.array([2448724.5]))
    assert lon[0] == pytest.approx(133.162655, abs=2e-6)
    assert lat[0] == pytest.approx(-3.229126, abs=2e-6)
    assert dist[0] == pytest.approx(368409.7, abs=0.1)


def test_meeus_sun_example_25a():
    lon, _, dist = sun_ecliptic_of_date(np.array([2448908.5]))
    assert lon[0] == pytest.approx(199.90988, abs=1e-4)
    assert dist[0] / AU_KM == pytest.approx(0.99766, abs=1e-5)


def test_earth_moon_distance_range_over_a_year():
    d = np.linalg.norm(AnalyticEphemeris().moon_eci_km(YEAR), axis=1)
    assert d.min() > 356_000 and d.max() < 407_000
    assert d.max() - d.min() > 40_000  # perigee/apogee actually show up


def test_sun_distance_and_direction_sane():
    s = AnalyticEphemeris().sun_eci_km(YEAR)
    au = np.linalg.norm(s, axis=1) / AU_KM
    assert au.min() > 0.98 and au.max() < 1.02
    dec = np.degrees(np.arcsin(s[:, 2] / np.linalg.norm(s, axis=1)))
    assert dec.max() == pytest.approx(23.44, abs=0.05) and dec.min() == pytest.approx(-23.44, abs=0.05)


def test_subsolar_latitude_bounded_and_librations():
    sun_me, earth_me = body_vectors_me(YEAR)
    ss = np.array([sub_point(v) for v in sun_me])
    se = np.array([sub_point(v) for v in earth_me])
    assert np.abs(ss[:, 0]).max() < 1.6  # lunar obliquity to the ecliptic is 1.54 deg
    assert np.abs(se[:, 0]).max() < 7.5  # libration in latitude ~6.7 deg
    assert np.abs(se[:, 1]).max() < 8.5  # libration in longitude ~7.9 deg


def test_full_moon_faces_sun():
    # Full Moon 2024-01-25 17:54 UTC: near side lit, sub-solar longitude ~ 0
    sun_me, _ = body_vectors_me([datetime(2024, 1, 25, 17, 54, tzinfo=UTC)])
    assert abs(sub_point(sun_me[0])[1]) < 10


@pytest.mark.skipif(not find_kernels()[1], reason="SPICE kernels not fetched")
def test_spice_matches_analytic():
    from lunanav.astro.ephemeris import SpiceEphemeris

    t = YEAR[::60]
    sp, an = SpiceEphemeris(), AnalyticEphemeris()
    assert np.linalg.norm(sp.moon_eci_km(t) - an.moon_eci_km(t), axis=1).max() < 50
    a, _b = body_vectors_me(t)  # current backend (analytic here)
    rot = sp.j2000_to_moon_me(t)
    s = np.einsum("nij,nj->ni", rot, sp.sun_eci_km(t) - sp.moon_eci_km(t))
    cosang = np.sum(s * a, 1) / np.linalg.norm(s, axis=1) / np.linalg.norm(a, axis=1)
    assert np.degrees(np.arccos(np.clip(cosang, -1, 1))).max() < 0.05


def test_auto_falls_back_with_a_reason(tmp_path, monkeypatch):
    import lunanav.astro.ephemeris as ephm

    monkeypatch.setenv("LUNANAV_EPHEMERIS", "auto")
    monkeypatch.setattr(ephm, "kernel_dir_candidates", lambda: [tmp_path])
    ephm.get_ephemeris.cache_clear()
    with pytest.warns(RuntimeWarning, match="SPICE not used"):
        eph = ephm.get_ephemeris()
    assert eph.name == "analytic"
    assert "missing" in ephm.FALLBACK_REASON and str(tmp_path.resolve()) in ephm.FALLBACK_REASON


def test_forced_spice_raises_clearly(tmp_path, monkeypatch):
    import lunanav.astro.ephemeris as ephm

    monkeypatch.setenv("LUNANAV_EPHEMERIS", "spice")
    monkeypatch.setattr(ephm, "kernel_dir_candidates", lambda: [tmp_path])
    ephm.get_ephemeris.cache_clear()
    with pytest.raises(FileNotFoundError, match="fetch_kernels"):
        ephm.get_ephemeris()


def test_kernel_discovery_is_independent_of_cwd(tmp_path, monkeypatch):
    import lunanav.astro.ephemeris as ephm

    kdir = tmp_path / "kernels"
    kdir.mkdir()
    for name in ("naif0012.tls", "de440s.bsp", "moon_pa_de440_200625.bpc",
                 "moon_de440_220930.tf", "moon_de440_250416.tf"):
        (kdir / name).write_text("x")
    monkeypatch.setenv("LUNANAV_KERNEL_DIR", str(kdir))
    monkeypatch.chdir(tmp_path)
    d, files, _ = ephm.find_kernels()
    assert d == kdir.resolve()
    assert [f.name for f in files] == ["naif0012.tls", "de440s.bsp", "moon_pa_de440_200625.bpc",
                                       "moon_de440_250416.tf"]
    monkeypatch.chdir(kdir)  # any other working directory finds the same set
    assert ephm.find_kernels()[0] == kdir.resolve()
