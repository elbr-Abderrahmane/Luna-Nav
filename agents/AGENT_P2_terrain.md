# Agent brief — P2 Geospatial & Terrain (LunaNav)

You are the coding agent for **P2, Geospatial & Terrain** on LunaNav, a 5-person NASA challenge team building a
lunar South Pole landing-site selection app. Before writing any code, **read `README.md` at the repo root
completely**. It is the source of truth for contracts, conventions and folder ownership. If this brief and the
README disagree, the README wins.

## Your scope
- You own `backend/lunanav/terrain/`, `backend/lunanav/coords.py`, `scripts/terrain/`, `backend/tests/terrain/`,
  `contracts/coord_test_vectors.json`, and the terrain section of `docs/methodology.md`.
- Stack: Python 3.11, numpy, scipy, rasterio, pyproj, shapely, (scikit-image optional), pytest.
- You produce terrain facts. You do **not** score (P4) or compute illumination (P3).

## The real data is not here yet: build on a synthetic DEM
`scripts/terrain/make_synthetic_dem.py` writes `data/synthetic/south_pole_dem.tif`:
- Projection exactly as README §6.2 (`+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m`), float32 metres, nodata −32768.
- ~300 × 300 km centred on the pole, 20 m/px (keep a CLI flag for resolution; a 40 m/px version for fast tests).
- Content: fractal (fBm) background, a few large craters (bowl + raised rim), many small craters (power-law sizes, so crater density is measurable), a couple of ridges/massifs, elevation range roughly −5 000…+5 000 m.
- Fixed random seed → reproducible.
Everything downstream reads the DEM path from config, so the switch to real LOLA data is only a config change plus `preprocess_dem.py` (reproject/resample into our projection, clip, fill nodata).

## What to build, per layer
**Coordinates (`coords.py`)** — forward/inverse polar stereo (pyproj), lat/lon/elev → body-fixed XYZ, XYZ → three.js axes (README §6.3), polygon conversion lon/lat ↔ x/y. Create `contracts/coord_test_vectors.json` (~10 points incl. the pole, 80°S, lon ±180, negative elevation) and test against it. P1 ports the same functions to TS and uses the same vectors.

**Derived rasters (`preprocess`)** — cache to `data/processed/`:
- slope (deg) from the DEM using projected pixel size (Horn method),
- roughness_rms_m: RMS of detrended heights in a `ROUGHNESS_BASELINE_M = 25 m` window,
- safe mask: slope ≤ `SAFE_SLOPE_DEG` (default 10) and roughness ≤ `SAFE_ROUGHNESS_M` (default 0.5 on real data; tune on synthetic),
- crater map: simple detection (or for synthetic, the generator's own catalog), craters ≥ `CRATER_MIN_DIAMETER_M` = 10 m; on real data use a provided catalog if there is one.

**L2 Regions** — `list_regions()` returns 6 predefined regions (polygons in lon/lat, closed rings, counter-clockwise exterior). Until the challenge gives a list, use placeholder sites near the pole spaced apart, each ~15–40 km across. `region_terrain(region_id) -> TerrainSummary` (every field in README §7.1). `get_heightmap(area_id, max_size)` → resampled window around a region or zone, `float32_base64`, row 0 = ymax.

**L3 Zones** — `identify_zones(region_id, max_zones=8)`: connected components of the safe mask inside the region, minimum area `MIN_ZONE_AREA_KM2` (default 0.5), simplified polygons (shapely `simplify`, keep ≤ 64 vertices), sorted by safe area. Each zone gets a full `TerrainSummary`. IDs `REG-01-Z01…`, stable for the same input.

**L4 Points** — `identify_points(zone_id, n=10)`: candidate cells inside the zone maximising distance to hazards and minimising local slope over `LANDER_FOOTPRINT_M = 20 m`, with a minimum spacing between points (e.g. 200 m). For each: lat/lon, x_m/y_m, elevation_m, `terrain_local` (slope, roughness, distance to nearest crater, distance to nearest hazard + type). Use a distance transform on the hazard mask.

**DEM access for P3** — `terrain.dem.sample_elevation(lat, lon)` and `dem_window(center, radius_m)` (returns array + affine transform). Read-only, fast (memory-map or cache the dataset handle). P3 uses it for horizon masks; keep the signature stable.

## Conventions (summary, full text README §6–§7)
Units in field names; degrees; longitude east-positive −180…180; GeoJSON `[lon, lat]`; elevation in metres relative to 1 737 400 m sphere; use the Pydantic models in `lunanav.schemas`, never raw dicts in public functions.

## Order of work
1. `coords.py` + test vectors. 2. Synthetic DEM. 3. Slope/roughness/safe mask + tests on analytic surfaces (a tilted plane must give the exact slope). 4. Regions + heightmaps. 5. Zones. 6. Points. 7. `preprocess_dem.py` ready for real LOLA (M3). 8. Methodology text.

## Definition of done
pytest green, ruff clean, functions return valid Pydantic models, the whole region → zones → points chain for one region runs in < 30 s on the 40 m/px synthetic DEM (results cached), numbers are physically plausible.

## Contracts
Do not change schemas, endpoint shapes or constants on your own. If you need a change, write the proposal (field, type, unit, why) and stop so a `contract` PR can go through P5.
