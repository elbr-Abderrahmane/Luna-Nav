# Agent brief — P3 Astronomy & Physics (LunaNav)

You are the coding agent for **P3, Astronomy & Physics** on LunaNav, a 5-person NASA challenge team building a
lunar South Pole landing-site selection app. Before writing any code, **read `README.md` at the repo root
completely**. It is the source of truth for contracts, conventions and folder ownership. If this brief and the
README disagree, the README wins.

## Your scope
- You own `backend/lunanav/astro/`, `scripts/astro/`, `backend/tests/astro/`, and the astronomy section of `docs/methodology.md`.
- Stack: Python 3.11, numpy, **spiceypy** with NAIF kernels (preferred) or **skyfield** (+ lunar PCK) as fallback, pytest.
- You may import **only** `lunanav.terrain.dem` (read-only DEM access) and `lunanav.schemas` / `lunanav.coords`.

## What to build, per layer
**L1 Mission — `plan_mission(arrival_utc, transfer_days=4.0) -> MissionPlan`**
- Moon position (J2000, Earth-centred, km) from ephemeris; `moon_track` from launch − 1 day to arrival + 1 day at ≤ 1 h step.
- `launch_utc = arrival_utc − transfer_days`. Transfer trajectory: an approximate, visual path from a LEO departure (~185 km) to the Moon's position at arrival (Lambert solve or a smooth patched-conic approximation is fine), ≥ 100 samples.
- `interception_window`: the arrival interval for which the same launch still intercepts within a tolerance; if you simplify, define it explicitly (e.g. ± 6 h) and document it.
- `earth_moon_distance_km` at arrival, `sun_direction_eci` unit vector, extra `parameters` rows (e.g. Moon declination, sub-solar latitude on the Moon, lunar phase/illumination %, C3/Δv estimates if computed). Every row has a `unit`.
- Clearly label in methodology: approximate, for visualisation and timing, not flight dynamics.

**Sun & Earth geometry**
- `sun_az_el(lat, lon, elevation_m, t)` and `earth_az_el(...)` in the topocentric frame of a point in the Moon ME body-fixed frame. Azimuth clockwise from local north (at the pole use the README convention: define north as the direction toward +Z projected, and document how you treat the singular point).
- Kernels: fetched by `scripts/astro/fetch_kernels.py` into `data/raw/kernels/` (planetary ephemeris, leap seconds, lunar orientation PCK + frame kernel for ME). Never commit kernels.

**Terrain obstruction — `horizon_mask(lat, lon, n_az=360, max_dist_km=100)`**
- For each azimuth bin, march along the ray on P2's DEM (`dem_window`) and keep the max elevation angle, including the curvature drop of the Moon (`d²/2R`). Cache masks per point under `data/cache/horizons/`.
- Sunlit if Sun centre elevation > horizon elevation at the Sun's azimuth (optionally model the 0.27° solar radius as partial illumination). Earth visible if Earth centre elevation > horizon.

**Illumination — `illumination_at(...)` and `illumination_area(samples, ...)`**
- Over the window `[arrival_utc, arrival_utc + SURFACE_STAY_DAYS]` with `ANALYSIS_STEP_H` steps, fill every field of `IlluminationSummary` (README §7.1).
- `illumination_area` aggregates over sample points inside a region/zone polygon (P5 passes the samples, e.g. 9–25 points): mean of percentages, max of `longest_shadow_h`, majority for booleans.
- `method = "horizon_mask"` when a DEM horizon was used, `"smooth_sphere"` otherwise (fast path for regions).

## Mock-first plan
- Day 0: everything works with a **simplified analytic model** if kernels are not set up yet (Sun circles the pole horizon with a 29.53-day period, elevation within ±1.54° modulated by season; Earth librating within ±~7° around lon 0). Same function signatures, same outputs, `method = "smooth_sphere"`.
- Then switch to kernels; then add horizons on P2's synthetic DEM (M2); then real DEM (M3).

## Validation (important for credibility)
- Earth–Moon distance stays within ~356 000–407 000 km.
- At the pole, Sun elevation never exceeds ~1.6° on a smooth sphere.
- A point on a high synthetic ridge must show higher illumination than a point in a crater floor.
- If kernels allow, compare the illumination of a known site (e.g. Shackleton rim) against published values in order of magnitude and note it in methodology.

## Conventions (summary, full text README §6–§7)
UTC ISO strings ending in `Z`; units in field names; degrees; longitude east-positive; ECI vectors in km in J2000; Pydantic models from `lunanav.schemas` as return types.

## Definition of done
pytest green, ruff clean, `plan_mission` < 1 s, illumination for one point over 7 days with a cached horizon < 1 s, all outputs valid Pydantic models.

## Contracts
Do not change schemas, endpoints or constants on your own. Write the proposal (field, type, unit, why) and stop so a `contract` PR can go through P5.
