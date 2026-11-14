#!/usr/bin/env python3
"""Quick look at the astro module, and a way to regenerate the L1 fixture.

    python scripts/astro/astro_demo.py --arrival 2027-03-14T12:00:00Z
    python scripts/astro/astro_demo.py --arrival 2027-03-14T12:00:00Z --mission-json out.json

`--mission-json` writes a MissionPlan JSON that P5 can drop into mock_data/mission_plan.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

SITES = {  # placeholder coordinates, smooth-sphere only (no DEM yet)
    "South pole": (-90.0, 0.0),
    "Shackleton rim (approx.)": (-89.9, 0.0),
    "Connecting ridge (approx.)": (-89.45, -137.0),
    "Malapert massif (approx.)": (-86.0, 0.0),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arrival", default="2027-03-14T12:00:00Z")
    ap.add_argument("--transfer-days", type=float, default=4.0)
    ap.add_argument("--mission-json", type=Path)
    a = ap.parse_args()
    from lunanav.astro import get_ephemeris, illumination_at, plan_mission

    plan = plan_mission(a.arrival, a.transfer_days)
    print(f"ephemeris: {get_ephemeris().source}")
    print(f"launch {plan.launch_utc}  arrival {plan.arrival_utc}  "
          f"window {plan.interception_window.start_utc} → {plan.interception_window.end_utc}")
    print(f"Earth–Moon distance {plan.earth_moon_distance_km:,.0f} km")
    for p in plan.parameters:
        print(f"  {p.label:<55} {p.value} {p.unit}")
    print("\nsmooth-sphere illumination over the 7-day stay:")
    for name, (lat, lon) in SITES.items():
        s = illumination_at(lat, lon, 0.0, plan.arrival_utc, use_horizon=False)
        print(f"  {name:<28} sun {s.illumination_pct:5.1f} %  earth {s.earth_visibility_pct:5.1f} %"
              f"  sun el@arrival {s.sun_elevation_deg_at_arrival:+.2f}°")
    if a.mission_json:
        a.mission_json.write_text(json.dumps(plan.model_dump(mode="json"), indent=1))
        print(f"\nwrote {a.mission_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
