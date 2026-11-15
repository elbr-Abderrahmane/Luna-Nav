"""Check a user-supplied lunar coordinate against nominal and actual DEM coverage."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from lunanav.terrain.dem import site_coverage

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lat_deg", type=float)
    parser.add_argument("lon_deg", type=float)
    parser.add_argument("--dem", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = site_coverage(args.lat_deg, args.lon_deg, args.dem)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
