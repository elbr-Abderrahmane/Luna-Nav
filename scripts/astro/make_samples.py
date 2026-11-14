#!/usr/bin/env python3
"""Write sample JSON outputs of the scenario API for P1 (UI) and P5 (endpoints/fixtures).

    python scripts/astro/make_samples.py [--start 2027-01-10T00:00:00Z] [--out mock_data/astro]

Uses the real LOLA DEM when it has been downloaded (fetch_lola_dem.py), else the smooth sphere;
each file says which in `method` / `warnings`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2027-01-10T00:00:00Z")
    ap.add_argument("--out", type=Path, default=REPO / "mock_data" / "astro")
    a = ap.parse_args()

    from lunanav.astro import (
        compare_scenarios,
        date_sweep,
        list_sites,
        site_conditions,
        site_timeline,
    )

    a.out.mkdir(parents=True, exist_ok=True)
    samples = {
        "sites.json": {"status": "ok", "sites": list_sites()},
        "site_conditions_connecting-ridge.json": site_conditions("connecting-ridge", a.start),
        "site_conditions_im-1.json": site_conditions("im-1", a.start),
        "site_timeline_connecting-ridge.json": site_timeline("connecting-ridge", a.start,
                                                             step_h=2.0),
        "compare_four_sites.json": compare_scenarios([
            {"site": "connecting-ridge", "start_utc": a.start},
            {"site": "artemis-malapert-massif", "start_utc": a.start},
            {"site": "im-1", "start_utc": a.start},
            {"site": "apollo-11", "start_utc": a.start},
        ]),
        "date_sweep_connecting-ridge.json": date_sweep("connecting-ridge", a.start, n=12),
    }
    for name, data in samples.items():
        if data.get("status") != "ok":
            print("FAILED", name, data.get("error"))
            return 1
        (a.out / name).write_text(json.dumps(data, indent=1))
        print("wrote", a.out / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
