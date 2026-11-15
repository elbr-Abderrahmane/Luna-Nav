# LunaNav — P2: Terrain & Coordinates

P2 owns `backend/lunanav/coords.py`, `backend/lunanav/terrain/` and
`scripts/terrain/`. This package follows the team README supplied on 14 Nov 2026.
It deliberately does not create API endpoints, a site catalog, astronomy functions,
frontend components, verdict logic, or a second data directory.

## Integration status and important limitation

The official team README was available during preparation. The repository itself was
not supplied: in particular, `backend/lunanav/astro/lola_dem.py`, the current P3
tests, and the merged dependency files could not be inspected. Therefore this package
implements a self-contained Rasterio reader with a narrow public API, but **must be
compared with and, where possible, adapted to P3's existing `astro/lola_dem.py` before
merging**. Do not deploy two independent DEM readers. The integration checklist lists
the exact review required.

## Responsibilities

- Moon planetocentric coordinate normalization and south-polar stereographic transforms.
- DEM path discovery, metadata inspection, raster bounds and NoData-aware reads.
- Distinguish nominal 80–90°S coverage from actual raster coverage.
- Point elevation sampling and JSON-ready local heightmap extraction.
- Optional local slope, elevation roughness (standard deviation), and basic statistics.

P2 does not compute Sun/Earth positions, horizon profiles, sunrise/sunset, timelines,
scenario comparisons, site verdicts, landing safety, or MCDA scores. Those remain
outside this package.

## Files

```text
backend/lunanav/coords.py
backend/lunanav/terrain/{__init__.py,dem.py,heightmap.py,terrain_metrics.py}
backend/tests/terrain/{__init__.py,conftest.py,test_coords.py,test_dem.py,
                      test_heightmap.py,test_terrain_metrics.py}
scripts/terrain/{inspect_dem.py,test_site_coverage.py}
```

Copy these paths into the existing repository; do not copy a `data/` directory.
The real DEM stays at the repository path
`data/raw/dem/LDEM_80S_80MPP_ADJ.TIF` and must remain git-ignored.

## Coordinate convention

- Body: Moon; reference radius `MOON_RADIUS_M = 1_737_400`.
- Frame: Moon Mean-Earth / Polar-axis (ME), body-fixed.
- Latitude: planetocentric degrees, range −90° to +90°.
- Longitude: east-positive degrees, normalized to [−180°, +180°).
- Projection: exact south polar stereographic definition from the team README:

```text
+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs
```

Forward equations (angles in radians):
`rho = 2 R tan(pi/4 + phi/2)`, `x_m = rho sin(lambda)`,
`y_m = rho cos(lambda)`.
Inverse: `rho = sqrt(x_m² + y_m²)`, `phi = 2 atan(rho/(2R)) - pi/2`,
`lambda = atan2(x_m, y_m)`.

At the exact south pole, projected x/y are (0, 0); longitude is undefined and the
inverse returns 0° by convention. This convention is documented and tested.

## DEM location and inspection

Default path resolution is relative to the repository root inferred from the module:
`data/raw/dem/LDEM_80S_80MPP_ADJ.TIF`. You can override it with the `dem_path`
argument or `LUNANAV_DEM_PATH`. The fetch script already owned by P3 remains the
download mechanism:

```powershell
cd backend
py ..\scripts\astro\fetch_lola_dem.py
```

The P2 package never downloads or bundles the 181 MB raster. Rasterio opens the raster
read-only and reports driver, dimensions, band count, CRS, transform, resolution,
bounds, dtype, and NoData. A CRS or transform that does not match the stated lunar
projection must be investigated; do not silently reproject or assume it is correct.

## Coverage and sampling

The nominal latitude envelope is 80°S through 90°S. A site north of 80°S is
`outside_nominal_coverage`; P2 never extrapolates it. For a site within the nominal
envelope, the projected coordinate is checked against the actual raster bounds and
pixel indices. A missing DEM is reported as `dem_unavailable`, not as an invented
elevation. `is_covered` is true only when the raster exists, the point is within
nominal and actual coverage, and the selected pixel is valid (not NoData).

`sample_elevation` returns a JSON-ready dictionary. Missing, out-of-bounds, and
NoData cases have `elevation_m: null` and an explanatory `status`.

## Heightmaps

`extract_heightmap` extracts a square window around the projected site. The requested
radius is in metres. Window clipping at raster edges is explicit; NoData values are
represented as JSON `null` (not NaN). Returned data includes rows, columns, pixel
resolution, bounds, center pixel, and nested altitude values. The function does not
interpolate missing pixels or imply that the heightmap is a landing-safety assessment.

## Optional terrain metrics

- Slope: Horn-style 3×3 finite differences, in degrees; output is null where the
  3×3 neighborhood contains invalid/NoData samples.
- Roughness: standard deviation of valid elevations in a local window, in metres.
- Summary: valid count, min/max/mean/std in metres.

These are local descriptive metrics only. They are optional UI enhancements, not a
site ranking or landing-zone detector.

## P3 integration

The team README explicitly allows `astro` to import `terrain.dem` read-only for
horizons, and says P2 may adopt or wrap `astro/lola_dem.py`. Before merging:

1. Inspect P3's public functions, coordinate transform, NoData policy, and horizon
   profile implementation.
2. Prefer re-exporting/adapting P3's existing reader over retaining a second reader.
3. Keep P3's existing function signatures and return contracts unchanged.
4. Confirm that P3 uses the same ME body-fixed frame, radius, east-positive longitude,
   and projection.
5. Confirm how P3 treats invalid horizon rays and edge-of-raster behavior.
6. Run both P3's astronomy tests and P2's terrain tests against the real DEM.

No P3 module was included with the supplied README, so this archive does not claim
that this review or cross-module validation has already happened.

## Dependencies and commands

Use the main project's existing environment; no independent dependency manifest is
added. The team README lists Python 3.11+, NumPy, Rasterio and Pytest.

From repository root:

```powershell
py -m pip install numpy rasterio pytest
py -m pytest backend/tests/terrain -q
py scripts/terrain/inspect_dem.py
py scripts/terrain/test_site_coverage.py -85 0
```

The team's normal setup remains authoritative:

```powershell
cd backend
py -m pip install -r requirements.txt -r lunanav\astro\requirements-astro.txt
py ..\scripts\astro\fetch_lola_dem.py
```

## Scientific limitations

- This product DEM nominally covers only 80–90°S, not the entire Moon.
- Sites north of 80°S must use P3's documented `smooth_sphere` fallback; P2 only
  reports coverage and does not select or implement the astronomy method.
- Raster CRS, transform, pixel registration, and NoData metadata must be checked
  against the actual downloaded product.
- Elevation accuracy and local detail are limited by the DEM's nominal 80 m/pixel
  resolution and its source data.
- Heightmaps and local metrics are not a full landing hazard or safety analysis.
- Horizon profiles and all astronomical events remain P3 responsibilities.
- Passing synthetic unit tests verifies code behavior against fixtures, not scientific
  validity of the real LOLA product or the whole LunaNav model.
