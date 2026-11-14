# `lunanav.astro` — Astronomy & Physics (P3)

Sun and Earth geometry, illumination and Earth visibility (with terrain horizons), and the
Layer 1 Earth–Moon transfer. Public API is exactly README §7.8.

## Run it

```bash
cd backend
pip install -r lunanav/astro/requirements-astro.txt
python -m pytest tests/astro -q            # 73 tests, ~5 s (1 SPICE test skipped until kernels exist)
ruff check lunanav/astro tests/astro
python ../scripts/astro/astro_demo.py --arrival 2027-03-14T12:00:00Z   # human-readable summary
python ../scripts/astro/astro_demo.py --mission-json /tmp/mission_plan.json  # fixture for P5
python ../scripts/astro/fetch_kernels.py   # optional: SPICE kernels into data/raw/kernels/
python ../scripts/astro/validate_horizons.py  # compare with JPL Horizons (internet), CSV in data/validation/
```

```python
from lunanav.astro import plan_mission, illumination_at, illumination_area, sun_az_el, horizon_mask
plan = plan_mission("2027-03-14T12:00:00Z")              # MissionPlan, < 0.2 s
s = illumination_at(-89.45, -137.0, None, plan.arrival_utc)  # IlluminationSummary
```

## P5 integration (questionnaire interface)

```python
from lunanav.astro import calculate_mission, analyze_illumination, analyze_earth_visibility
```

`integration.py` wraps the functions below and returns JSON-ready dicts with `status`,
`warnings`, `error`, `frame` (with epoch), `units` and an honest `result_type`
(`simplified_transfer` / `geometric_estimate` / `ephemeris_calculation`). They never raise on bad
input. Full answers to P5's questionnaire are in the team's Claude Doc
"LunaNav P3 Astronomy — Integration Questionnaire Answers".

## Scenario tools for the official challenge (`scenarios.py`, `sites.py`)

```python
from lunanav.astro import site_conditions, site_timeline, compare_scenarios, date_sweep, list_sites
r = site_conditions("im-1", "2027-01-10T00:00:00Z")        # or {"lat_deg": -89.45, "lon_deg": -137.3}
r["countdown"]["sun"]["summary"]       # "Sunrise in 4 d 17 h 44 min"
r["windows"]["power_and_comms"]        # [{start_utc, end_utc, duration_h, ...}, ...]
compare_scenarios([{"site": "apollo-11", "start_utc": t}, {"site": "change-4", "start_utc": t}])
date_sweep("connecting-ridge", "2027-01-01T00:00:00Z", n=12)  # one row per lunar day
```

| Function | Gives |
|---|---|
| `site_conditions(site, start, window_days=29.53, step_h=0.5, terrain_data=None)` | `now` (Sun/Earth az/el, horizon, margin, visible disk fraction, irradiance, panel factors, libration), `countdown` (next sunset/sunrise and Earthset/Earthrise with time remaining), `next_events`, `windows` (sunlit, earth_visible, power_and_comms), `metrics` |
| `site_timeline(...)` | the same + `series` (for animation / sky plots) + `horizon_profile` (360 az bins) |
| `compare_scenarios([{site, start_utc, label?, window_days?}, ...])` | one row per scenario + `best` per metric |
| `date_sweep(site, first_start, n=12, every_days=29.53)` | one row per start date + `best` |
| `list_sites(category=None)`, `get_site(id)`, `resolve_site(site)` | curated catalog (26 sites: Apollo, CLPS, Artemis III regions, Chang'e, Chandrayaan-3, SLIM, Luna 9, polar references) and custom coordinates |

Same conventions as `integration.py`: JSON-ready dicts, `status`/`warnings`/`error`, never raise.
Sites outside DEM coverage automatically use the smooth sphere with a warning.
CLI: `python scripts/astro/scenario_demo.py --list | --sites ... | --sweep <site>`.

## Real LOLA terrain (`lola_dem.py`)

```bash
pip install rasterio
python ../scripts/astro/fetch_lola_dem.py --with-illumination   # 181 MB DEM + 59 MB NASA maps
python ../scripts/astro/validate_lola_illumination.py            # vs NASA maps, ~15 s
python ../scripts/astro/make_samples.py                          # JSON samples in mock_data/astro/
```

Once `data/raw/dem/LDEM_80S_80MPP_ADJ.TIF` exists, every horizon (old functions and scenario tools)
uses it automatically (`method = "horizon_mask"`). P2's `lunanav.terrain.dem` wins if present;
`LUNANAV_DEM_PATH` picks another file; `LUNANAV_DEM=off` disables it (the tests do). Sites outside
80–90°S fall back to the smooth sphere with a warning. Against NASA's average illumination maps:
median difference ~1 percentage point at 36 points (details in `docs/methodology.md`).

## Files

| File | What |
|---|---|
| `ephemeris.py` | Backends. `AnalyticEphemeris` (default, no files): Meeus ch. 47 Moon / ch. 25 Sun, precessed to J2000, IAU 2009 lunar orientation. `SpiceEphemeris`: DE440 + `MOON_ME` via spiceypy. `LUNANAV_EPHEMERIS=auto\|analytic\|spice` (auto = SPICE if `data/raw/kernels/lunanav.tm` exists). |
| `topo.py` | `sun_az_el`, `earth_az_el`, ENU basis, sub-solar / sub-Earth points. |
| `horizon.py` | `horizon_mask` (ray march on `lunanav.terrain.dem`, spherical curvature, cached in `data/cache/horizons/`). |
| `illumination.py` | `illumination_at`, `illumination_area` → `IlluminationSummary`. |
| `scenarios.py` | Countdowns, lunar-day windows, comparison, date sweep, power metrics. |
| `lola_dem.py` | Real LOLA GeoTIFF reader, same interface as P2's `terrain.dem`. |
| `sites.py`, `sites.json` | Curated site catalog + custom coordinates. |
| `mission.py` | `plan_mission` → `MissionPlan` (Lambert transfer, SOI-based interception window, info-panel parameters). |
| `_contracts.py` | Imports `lunanav.schemas` / `config` / `coords` when they exist; until then, exact copies of README §6–§7 so this module runs today. **Delete the fallbacks once P5/P2 land theirs.** |
| `tests/astro/mock_dem.py` | Analytic mock DEM with the same interface and grid convention as P2's `dem_window`, with a crater and a ridge. |

## Behaviour other people rely on

* **SPICE discovery:** kernels are found in `LUNANAV_KERNEL_DIR`, else `<repo>/data/raw/kernels`
  (resolved from the package location, so any working directory works), and loaded file by file.
  If `auto` cannot load them it uses the analytic model, issues a `RuntimeWarning` and stores the
  reason in `lunanav.astro.ephemeris.FALLBACK_REASON`. `LUNANAV_EPHEMERIS=spice` raises instead.

* **No DEM yet → smooth sphere.** `illumination_at(..., use_horizon=True)` uses
  `lunanav.terrain.dem` if importable, else falls back to `method="smooth_sphere"`. As soon as P2's
  module exists, horizons switch on with no code change. You can also pass `dem=` explicitly.
* **`illumination_area(samples, arrival_utc, use_horizon=True, dem=None)`**: extra keyword
  `use_horizon` (pure Python, not an API contract change). P5: pass `use_horizon=False` for the
  six L2 regions (fast path), keep the default for zones and points.
* `elevation_m=None` means "read it from the DEM" (0 m without DEM).
* **Window sampling:** `[arrival, arrival + 7 d)` at 1 h → 168 samples, each standing for its
  hour. So a fully dark week gives `longest_shadow_h = 168` and `window_end_utc = arrival + 7 d`.
* **Sunlit** = Sun disk centre above the horizon at the Sun's azimuth (horizon interpolated
  between the 360 bins). Same for Earth.
* Horizon observer height: 2 m above the DEM surface (lander deck). Rays to 100 km.
* Text-valued `parameters` rows use `unit: "text"`.
* Pole convention: at exactly ±90° the azimuth origin is the meridian of the `lon_deg` you pass
  (default 0 → +y of the polar-stereo map is azimuth 0).

## Validation (all in tests)

| Check | Result |
|---|---|
| Meeus worked examples 47.a (Moon) and 25.a (Sun) | match to 1e-6 deg / 0.1 km |
| Earth–Moon distance over 2027 | 356–407 Mm, both extremes reached |
| Sun elevation at the pole, one year, smooth sphere | always < 1.6° |
| Sun azimuth at the pole | one turn per 29.53 d |
| Libration (sub-Earth point) | lat < 7.5°, lon < 8.5° |
| Full Moon 2024-01-25 | sub-solar longitude ≈ 0° |
| Mock ridge crest vs crater floor | ridge 100 % / 42 %, crater 0 % (two seasons) |
| TLI Δv from 185 km LEO | ≈ 3.19 km/s (textbook ~3.1–3.2) |
| `plan_mission` / cached point illumination | ~0.15 s / ~5 ms |

Not yet done: SPICE cross-check (kernel host blocked from the build sandbox; the test runs
automatically once `fetch_kernels.py` has been run), and comparing Shackleton-rim illumination
with published values (needs the real DEM, M3).
