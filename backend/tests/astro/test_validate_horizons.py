"""Offline test of scripts/astro/validate_horizons.py with mocked Horizons responses.

The mock answers in Horizons' own CSV layout. Vector times come back as JDTDB (as Horizons
does by default), so the script's TDB->UTC handling is exercised.
"""

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

from lunanav.astro import get_ephemeris, sun_az_el

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "astro" / "validate_horizons.py"
spec = importlib.util.spec_from_file_location("validate_horizons", SCRIPT)
vh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh)


def _wrap(header, row):
    return ("API VERSION: 1.2\n*******\nTarget body name: mock\n" + header + "\n"
            "**************************************************\n$$SOE\n" + row + "\n$$EOE\n")


def make_fake(offset_km=0.0, offset_deg=0.0):
    calls = []

    def fake(params):
        calls.append(params)
        start = datetime.strptime(params["START_TIME"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
        if params["EPHEM_TYPE"] == "VECTORS":
            # Horizons reads START_TIME as TDB for vectors: the true UTC instant is 69.184 s earlier
            t_utc = start - timedelta(seconds=69.184)
            x, y, z = get_ephemeris().moon_eci_km([t_utc])[0]
            k = 1 + offset_km / np.linalg.norm([x, y, z])
            jd = start.timestamp() / 86400 + 2440587.5
            return _wrap("            JDTDB,            Calendar Date (TDB),                      X,"
                         "                      Y,                      Z,",
                         f"{jd:.9f}, A.D. mock, {x * k:.15E}, {y * k:.15E}, {z * k:.15E},")
        lon, lat, h_km = (float(v) for v in params["SITE_COORD"].split(","))
        az, el = sun_az_el(lat, lon, h_km * 1000, start)
        return _wrap(" Date__(UT)__HR:MN, , , Azimuth_(a-app), Elevation_(a-app),",
                     f" {start:%Y-%b-%d %H:%M}, , , {az + offset_deg:.6f}, {el + offset_deg:.6f},")

    return fake, calls


def test_all_rows_pass_when_horizons_agrees():
    fake, calls = make_fake()
    rows, _ = vh.run(["2027-03-14T12:00:00Z", "2028-01-01T00:00:00Z"], fetch=fake)
    assert len(rows) == 2 * (1 + 2 * len(vh.SITES))
    assert all(r["result"] == "PASS" for r in rows), rows
    dist = [r for r in rows if r["quantity"] == "earth_moon_distance_km"]
    assert all(abs(r["diff"]) < 0.01 for r in dist)  # TDB/UTC handled exactly
    assert any(c.get("CENTER") == "coord@301" for c in calls)
    assert all(c["START_TIME"].count(":") == 1 for c in calls)


def test_rows_fail_when_off():
    fake, _ = make_fake(offset_km=500, offset_deg=1.0)
    rows, _ = vh.run(["2027-03-14T12:00:00Z"], fetch=fake)
    assert all(r["result"] == "FAIL" for r in rows)


def test_azimuth_difference_wraps():
    assert abs(vh.az_diff(359.9, 0.1) + 0.2) < 1e-9
    assert abs(vh.az_diff(0.1, 359.9) - 0.2) < 1e-9


def test_csv_written(tmp_path):
    fake, _ = make_fake()
    rows, _ = vh.run(["2027-03-14T12:00:00Z"], fetch=fake)
    out = tmp_path / "check.csv"
    vh.write_csv(rows, out)
    lines = out.read_text().splitlines()
    assert lines[0].startswith("date_utc,site,quantity,ours,horizons,diff,tolerance,result")
    assert len(lines) == len(rows) + 1
