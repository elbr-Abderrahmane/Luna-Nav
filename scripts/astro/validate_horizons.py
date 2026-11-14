#!/usr/bin/env python3
"""Validate lunanav.astro against NASA/JPL Horizons (needs internet).

For each date it compares:
  * Earth–Moon distance (km): our ephemeris vs Horizons geometric Moon vector (Earth centre,
    J2000 frame, no light-time correction).
  * Sun azimuth and elevation (deg) at lunar sites: our `sun_az_el` vs a Horizons observer table
    for a site on the Moon (body 301, SITE_COORD), airless apparent az/el.

Usage (Windows PowerShell, from the lunanav-team folder, with the .venv active):

    python scripts\\astro\\validate_horizons.py
    python scripts\\astro\\validate_horizons.py --ephemeris spice      # fail loudly if SPICE can't load
    python scripts\\astro\\validate_horizons.py --ephemeris analytic --csv horizons_check_analytic.csv
    python scripts\\astro\\validate_horizons.py --dates 2027-03-14T12:00:00Z 2028-01-01T00:00:00Z

Prints a table with differences and PASS/FAIL per row, writes a CSV (default
data/validation/horizons_check.csv) and exits with code 1 if any row fails.

Tolerances: distance 1 km (SPICE) / 50 km (analytic); Sun azimuth and elevation 0.05 deg
(SPICE) / 0.1 deg (analytic). The small residuals come from light-time and aberration, which
Horizons applies to the apparent az/el and we ignore (~0.006 deg), and from frame details.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
API = "https://ssd.jpl.nasa.gov/api/horizons.api"

DEFAULT_DATES = [
    "2026-11-15T12:00:00Z",
    "2027-03-14T12:00:00Z",
    "2027-08-01T00:00:00Z",
    "2028-01-01T00:00:00Z",
    "2028-06-20T06:00:00Z",
]
# (name, lat_deg, lon_deg east, height_m). The exact pole is avoided because azimuth is
# undefined there; at 89.99 S, 0 E north points along the 0 E meridian, as in our convention.
SITES = [
    ("South pole (89.99S 0E)", -89.99, 0.0, 0.0),
    ("Shackleton far rim (approx.)", -89.32, 129.78, 0.0),
]
TT_MINUS_UTC_S = 69.184


# ---------------------------------------------------------------------------------- Horizons
def horizons_query(params: dict, retries: int = 3) -> str:
    """Call the Horizons API and return the text in its 'result' field."""
    base = {"format": "json", "MAKE_EPHEM": "YES", "OBJ_DATA": "NO", "CSV_FORMAT": "YES"}
    query = {k: (v if str(v).startswith("'") else f"'{v}'") for k, v in {**base, **params}.items()}
    query["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(query)
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                payload = json.loads(r.read().decode("utf-8"))
            if "error" in payload:
                raise RuntimeError(payload["error"])
            return payload["result"]
        except (OSError, ValueError, RuntimeError) as exc:  # network or API error: retry
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Horizons request failed: {last}")


def parse_csv_block(text: str) -> tuple[list[str], list[list[str]]]:
    """Return (header columns, data rows) of a Horizons CSV ephemeris."""
    lines = text.splitlines()
    try:
        soe = next(i for i, ln in enumerate(lines) if ln.strip() == "$$SOE")
        eoe = next(i for i, ln in enumerate(lines) if ln.strip() == "$$EOE")
    except StopIteration as exc:
        raise RuntimeError("no $$SOE/$$EOE block in Horizons output:\n" + text[:2000]) from exc
    header = ""
    for ln in reversed(lines[:soe]):
        if "," in ln and not set(ln.strip()) <= {"*"}:
            header = ln
            break
    cols = [c.strip() for c in header.split(",")]
    rows = [[c.strip() for c in ln.split(",")] for ln in lines[soe + 1 : eoe] if ln.strip()]
    return cols, rows


def _col(cols: list[str], *keys: str) -> int:
    for i, c in enumerate(cols):
        if any(c.startswith(k) for k in keys):
            return i
    raise RuntimeError(f"column {keys} not in Horizons header {cols}")


def _hz_time(t: datetime) -> tuple[str, str]:
    return t.strftime("%Y-%m-%d %H:%M"), (t + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")


def horizons_moon_distance(t: datetime, fetch=horizons_query) -> tuple[float, datetime]:
    """Geometric Earth->Moon distance (km) and the UTC instant Horizons evaluated."""
    start, stop = _hz_time(t)
    text = fetch({
        "COMMAND": "301", "CENTER": "500@399", "EPHEM_TYPE": "VECTORS", "VEC_TABLE": "1",
        "VEC_CORR": "NONE", "REF_PLANE": "FRAME", "REF_SYSTEM": "ICRF", "OUT_UNITS": "KM-S",
        "START_TIME": start, "STOP_TIME": stop, "STEP_SIZE": "1m",
    })
    cols, rows = parse_csv_block(text)
    r = rows[0]
    jd_i = _col(cols, "JD")
    x, y, z = (float(r[_col(cols, k)]) for k in ("X", "Y", "Z"))
    jd = float(r[jd_i])
    scale_tdb = cols[jd_i].upper().startswith("JDTDB")
    unix = (jd - 2440587.5) * 86400.0 - (TT_MINUS_UTC_S if scale_tdb else 0.0)
    return math.sqrt(x * x + y * y + z * z), datetime.fromtimestamp(unix, UTC)


def horizons_sun_az_el(t: datetime, lat: float, lon: float, h_m: float,
                       fetch=horizons_query) -> tuple[float, float]:
    """Apparent (airless) Sun azimuth/elevation (deg) seen from a site on the Moon."""
    start, stop = _hz_time(t)
    text = fetch({
        "COMMAND": "10", "CENTER": "coord@301", "COORD_TYPE": "GEODETIC",
        "SITE_COORD": f"{lon % 360:.6f},{lat:.6f},{h_m / 1000:.4f}",
        "EPHEM_TYPE": "OBSERVER", "QUANTITIES": "4", "ANG_FORMAT": "DEG",
        "APPARENT": "AIRLESS", "START_TIME": start, "STOP_TIME": stop, "STEP_SIZE": "1m",
    })
    cols, rows = parse_csv_block(text)
    r = rows[0]
    return float(r[_col(cols, "Azi")]), float(r[_col(cols, "Elev")])


# ---------------------------------------------------------------------------------- compare
def az_diff(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


def run(dates: list[str], fetch=horizons_query, sites=SITES) -> tuple[list[dict], str]:
    sys.path.insert(0, str(REPO / "backend"))
    from lunanav.astro import get_ephemeris, sun_az_el
    from lunanav.astro.timeutil import to_utc

    eph = get_ephemeris()
    spice = eph.name == "spice"
    tol_km = 1.0 if spice else 50.0
    tol_deg = 0.05 if spice else 0.1
    rows: list[dict] = []
    for d in dates:
        t = to_utc(d).replace(second=0, microsecond=0)
        hz_dist, t_eval = horizons_moon_distance(t, fetch)
        ours = float(sum(c * c for c in eph.moon_eci_km([t_eval])[0]) ** 0.5)
        diff = ours - hz_dist
        rows.append({"date_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "site": "Earth centre",
                     "quantity": "earth_moon_distance_km", "ours": round(ours, 3),
                     "horizons": round(hz_dist, 3), "diff": round(diff, 3),
                     "tolerance": tol_km, "result": "PASS" if abs(diff) <= tol_km else "FAIL"})
        for name, lat, lon, h in sites:
            hz_az, hz_el = horizons_sun_az_el(t, lat, lon, h, fetch)
            our_az, our_el = sun_az_el(lat, lon, h, t)
            for q, o, z, dd in (("sun_azimuth_deg", our_az, hz_az, az_diff(our_az, hz_az)),
                                ("sun_elevation_deg", our_el, hz_el, our_el - hz_el)):
                rows.append({"date_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "site": name,
                             "quantity": q, "ours": round(o, 4), "horizons": round(z, 4),
                             "diff": round(dd, 4), "tolerance": tol_deg,
                             "result": "PASS" if abs(dd) <= tol_deg else "FAIL"})
    return rows, eph.source


def print_table(rows: list[dict]) -> None:
    head = f"{'date (UTC)':<21}{'site':<30}{'quantity':<24}{'ours':>14}{'Horizons':>14}{'diff':>10}  result"
    print(head)
    print("-" * len(head))
    for r in rows:
        print(f"{r['date_utc']:<21}{r['site']:<30}{r['quantity']:<24}{r['ours']:>14}"
              f"{r['horizons']:>14}{r['diff']:>10}  {r['result']}")


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dates", nargs="+", default=DEFAULT_DATES)
    ap.add_argument("--ephemeris", choices=["auto", "analytic", "spice"], default="auto")
    ap.add_argument("--csv", type=Path, default=REPO / "data" / "validation" / "horizons_check.csv")
    a = ap.parse_args(argv)
    os.environ["LUNANAV_EPHEMERIS"] = a.ephemeris

    rows, source = run(a.dates)
    from lunanav.astro import ephemeris as ephm

    print(f"our ephemeris: {source}")
    if ephm.FALLBACK_REASON:
        print(f"SPICE was NOT used: {ephm.FALLBACK_REASON}")
    print()
    print_table(rows)
    write_csv(rows, a.csv)
    n_fail = sum(r["result"] == "FAIL" for r in rows)
    print(f"\n{len(rows) - n_fail}/{len(rows)} rows pass. CSV written to {a.csv}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
