# P2 integration checklist

## Repository and ownership
- [ ] Work on a `p2/...` branch; pull/rebase before integration.
- [ ] Copy only the listed P2 files into the existing repository.
- [ ] Do not create `data/`, API routes, frontend files, site catalogues, astronomy
      functions, decision logic, or a second backend.
- [ ] Confirm `data/raw/dem/` is already git-ignored.

## Mandatory P3 reader review (not completed: P3 source was not supplied)
- [ ] Read `backend/lunanav/astro/lola_dem.py` in full.
- [ ] Record its public functions and current callers.
- [ ] Compare coordinate projection and Moon radius with `coords.py`.
- [ ] Compare raster opening, NoData masking, bounds checks and pixel indexing.
- [ ] Compare horizon ray sampling and edge-of-raster behavior.
- [ ] Reuse/adapt the P3 reader where possible; avoid two independent readers.
- [ ] Preserve every existing P3 signature and return contract.
- [ ] Ask P3 to approve any necessary interface changes before editing contracts.

## DEM and scientific checks
- [ ] Download the real file using `py scripts/astro/fetch_lola_dem.py`.
- [ ] Confirm the exact filename and path:
      `data/raw/dem/LDEM_80S_80MPP_ADJ.TIF`.
- [ ] Run `py scripts/terrain/inspect_dem.py`.
- [ ] Confirm CRS, transform, resolution, dimensions, bounds, dtype and NoData against
      the actual NASA PGDA product metadata.
- [ ] Test a known point against the raster's actual coverage.
- [ ] Confirm sites north of 80°S are reported uncovered (no extrapolation).
- [ ] Confirm missing DEM and NoData are reported as missing, never fabricated.
- [ ] Confirm longitude is east-positive and normalized to [−180°, 180°).

## Tests and integration
- [ ] Run `py -m pytest backend/tests/terrain -q`.
- [ ] Run `py -m pytest backend/tests/astro -q`.
- [ ] Run P3 tests that require the real DEM after downloading it.
- [ ] Confirm P3's horizon outputs are unchanged after integration.
- [ ] Confirm P5 can serialize all P2 result dictionaries as JSON.
- [ ] Confirm P1 receives `null` for unavailable values and handles it.
- [ ] Confirm optional slope/roughness are not treated as landing-safety scores.

## Review and merge
- [ ] P3 validates the reader integration.
- [ ] P5 validates imports, paths and test discovery.
- [ ] P1 confirms the optional heightmap shape is usable.
- [ ] P2 documents any changed interface in the team README before merge.
- [ ] Keep the DEM TIFF out of the ZIP and Git.
