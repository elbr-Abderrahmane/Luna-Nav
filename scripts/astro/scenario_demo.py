#!/usr/bin/env python3
"""Compare sites and dates from the command line, and write JSON fixtures for P1/P5.

    python scripts/astro/scenario_demo.py --start 2027-01-10T00:00:00Z
    python scripts/astro/scenario_demo.py --sites im-1 connecting-ridge apollo-11 --start 2027-01-10T00:00:00Z
    python scripts/astro/scenario_demo.py --sites 89.45S,137.3W im-1   (custom site: lat,lon with N/S/E/W)
    python scripts/astro/scenario_demo.py --sweep connecting-ridge --start 2027-01-01T00:00:00Z
    python scripts/astro/scenario_demo.py --list
    python scripts/astro/scenario_demo.py ... --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))


def _deg(v: str) -> float:
    v = v.strip().upper()
    if v and v[-1] in "NSEW":
        return -float(v[:-1]) if v[-1] in "SW" else float(v[:-1])
    return float(v)


def _site_arg(s: str):
    """Catalog id, or custom 'lat,lon' with N/S/E/W suffixes (89.45S,137.3W)."""
    if "," in s:
        lat, lon = s.split(",")
        return {"lat_deg": _deg(lat), "lon_deg": _deg(lon)}
    return s


def _fmt(v, nd=1):
    return "-" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2027-01-10T00:00:00Z")
    ap.add_argument("--sites", nargs="+",
                    default=["connecting-ridge", "artemis-malapert-massif", "im-1", "apollo-11"])
    ap.add_argument("--days", type=float, default=29.530589)
    ap.add_argument("--sweep", help="site id (or lat,lon) for a 12-lunar-day date sweep")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    from lunanav.astro import compare_scenarios, date_sweep, list_sites

    if a.list:
        for s in list_sites():
            print(f"{s['id']:26s} {s['lat_deg']:8.3f} {s['lon_deg']:9.3f}  {s['name']}")
        return 0

    if a.sweep:
        r = date_sweep(_site_arg(a.sweep), a.start, n=12)
    else:
        r = compare_scenarios([{"site": _site_arg(s), "start_utc": a.start} for s in a.sites],
                              window_days=a.days)
    if r["status"] != "ok":
        print(r["error"])
        return 1
    for w in r["warnings"]:
        print("warning:", w)
    print(f"{'scenario':44s} {'sun now':>8s} {'sun %':>6s} {'dark h':>7s} {'earth %':>7s} "
          f"{'gap h':>6s} {'both %':>6s}  next sun event / next Earth event")
    for row in r["rows"]:
        m = row["metrics"]
        print(f"{row['label'][:44]:44s} {row['sun_elevation_deg_at_start']:8.2f} "
              f"{m['sunlight_pct']:6.1f} {m['longest_darkness_h']:7.1f} "
              f"{m['earth_visibility_pct']:7.1f} {m['longest_comms_gap_h']:6.1f} "
              f"{m['power_and_comms_pct']:6.1f}  {row['sun_countdown']['summary']} / "
              f"{row['earth_countdown']['summary']}")
    print("\nbest per metric:")
    for k, b in r["best"].items():
        print(f"  {k:30s} {b['label']} ({_fmt(b['value'])})")
    if a.json:
        a.json.write_text(json.dumps(r, indent=2))
        print("wrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
