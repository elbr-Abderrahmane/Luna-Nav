"""Print metadata and status for the repository's configured LOLA DEM."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from lunanav.terrain.dem import default_dem_path, inspect_dem

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dem", type=Path, default=None, help="Optional DEM path override")
    args = parser.parse_args()
    path = args.dem or default_dem_path()
    print(f"Expected DEM: {path}")
    result = inspect_dem(path)
    print(json.dumps(result, indent=2))
    print("General state:", result.get("status", "unknown"))
    return 0 if result.get("exists") else 2

if __name__ == "__main__":
    raise SystemExit(main())
