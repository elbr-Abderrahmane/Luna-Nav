# LunaNav — Methodology

<!-- P2 (terrain), P3 (astronomy) and P4 (scoring) each own one section. Edit only yours. -->

## Terrain (P2)

*Module: `backend/lunanav/coords.py` and `backend/lunanav/terrain/`.*

**Coordinates and projection.** Planetocentric latitude (`[-90°, +90°]`) and east-positive longitude (`[-180°, +180°)`) are defined in the Moon Mean-Earth / Polar-axis (ME) body-fixed frame on the LOLA reference sphere (`R = 1 737 400 m`). South-polar stereographic coordinates (`+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +R=1737400 +units=m +no_defs`) use the spherical equations `ρ = 2R·tan(π/4 + φ/2)`, `x = ρ·sin λ`, `y = ρ·cos λ`.

**DEM access and coverage.** `DEMReader` and `LolaDEM` open NASA PGDA's `LDEM_80S_80MPP_ADJ.TIF` read-only via Rasterio. Nominal coverage is `80°S–90°S`; sites north of `80°S` are reported as `outside_nominal_coverage` without extrapolation, while missing files (`dem_unavailable`), out-of-bounds points (`outside_raster_bounds`) and masked pixels (`nodata`) return explicit `null` elevations rather than fabricated values.

**Local heightmaps and terrain metrics.** `extract_heightmap` extracts clipped square elevation windows around a site with JSON-safe `null` values for NoData. Optional descriptive metrics (`local_slope` via a 3×3 Horn finite-difference kernel, `local_roughness` as elevation standard deviation, and `terrain_summary`) provide local context without acting as a landing-safety certification.

## Astronomy & illumination (P3)

**Ephemerides.** Positions of the Moon and the Sun relative to the Earth (J2000, km) come from
NASA/JPL NAIF SPICE kernels (DE440) when available. Otherwise, and in the current build, an
analytic model is used: Meeus, *Astronomical Algorithms* (2nd ed.), ch. 47 for the Moon (truncated
ELP-2000/82, ~10″ in longitude, ~10 km in distance) and ch. 25 for the Sun (~0.01°), precessed to
J2000. The Moon's orientation uses the IAU WGCCRE 2009 model (Archinal et al., 2011), which
approximates the Mean-Earth/Polar-axis (ME) frame used by LOLA. Light-time and aberration are
ignored (< 0.01° at the Moon). Both models agree with the published worked examples.

**Local Sun and Earth direction.** For a surface point (planetocentric lat/lon, elevation above the
1737.4 km sphere) we compute the direction to the Sun and the Earth in the local east-north-up
frame. Azimuth is measured clockwise from local north; elevation above the local horizontal plane.
At the pole the azimuth origin is the requested meridian.

**Terrain obstruction.** For each point we build a horizon mask: 360 azimuth bins, rays out to
100 km on the DEM, sample spacing equal to the DEM resolution near the point and growing to 0.5 %
of the distance further away. The elevation angle of each terrain sample is computed on the sphere,
so the Moon's curvature (≈ d²/2R, 2.9 km at 100 km) is included. The observer is 2 m above the
surface. Masks are cached per point.

**Illumination and Earth visibility.** Over the surface-stay window (arrival + 7 days, 1-hour
steps) a point is sunlit when the centre of the Sun's disk is above the horizon mask at the Sun's
azimuth; the Earth is visible when its centre is above the mask at its azimuth. We report the % of
the window sunlit and Earth-visible, the longest continuous dark period, and the geometry at
arrival. Without a DEM ("smooth sphere"), the horizon is the 0° plane. Regions and zones aggregate
9–25 sample points (mean of percentages, worst-case shadow, majority for yes/no). Partial
illumination of the 0.27°-radius solar disk is not modelled.

**Mission trajectory (Layer 1).** The transfer is **approximate, for visualisation and timing, not
flight dynamics**. Launch time = arrival − transfer duration (default 4 days). The arc is a
two-body (Earth only) Lambert solution from a circular 185 km parking orbit to the Moon's centre at
arrival, with a 170° transfer angle in the Moon's orbital plane; lunar gravity and perturbations
are ignored. The interception window is the interval of arrival times for which the same launch
brings the spacecraft within the Moon's sphere of influence (66 100 km). Reported Δv and C3 are
estimates from this model.

**Validation.** Earth–Moon distance stays within 356 000–407 000 km over a year; the Sun never rises
more than 1.6° above the horizon at the pole on a smooth sphere; the Sun circles the pole once per
synodic month; libration stays within ±7.5° (lat) / ±8.5° (lon); on a synthetic DEM, a ridge crest
is illuminated far more than a crater floor (which stays permanently shadowed); TLI Δv ≈ 3.2 km/s.
Against NASA/JPL Horizons (5 dates, 2026-11-15 to 2028-06-20; geometric Earth–Moon distance and
Sun azimuth/elevation at 89.99°S 0°E and an approximate Shackleton far-rim point;
`scripts/astro/validate_horizons.py`, run 2026-11-13), all 25 comparisons agree: with the SPICE
DE440 kernels the largest differences are 0.0 km in distance, 0.0001° in elevation and 0.0057° in
azimuth; with the analytic fallback they are 2.8 km, 0.0023° and 0.0121°. The residual azimuth
offset is light-time and aberration, which Horizons includes in apparent az/el and we ignore.
Comparison of a known site (Shackleton rim) against published illumination values is pending real
data.

**Scenarios, countdowns and windows (`astro/scenarios.py`).** A scenario is a site (from the
curated catalog `astro/sites.json` or custom coordinates) plus a start time. Over a window
(default one synodic month, 29.53 d, sampled every 0.5–1 h) we compute Sun and Earth az/el, the
horizon elevation at their azimuths, and whether each disk centre is above it. Every change of
state is refined by bisection to within 30 s; that gives sunrise, sunset, Earthrise and Earthset
times and the "time remaining" countdowns. Sunlit windows, Earth-visible windows and their overlap
("power and comms") are reported with durations, together with the longest darkness and the longest
comms gap. Power metrics are geometric only: irradiance 1361 W/m² × (1 AU / d)² × the visible
fraction of the solar disk (circle segment above a straight horizon, solar radius ≈ 0.27°), times
cos(elevation) for a Sun-facing vertical panel or sin(elevation) for a horizontal one. A date sweep
repeats the analysis for start dates one lunar day apart, which shows the polar seasons (sub-solar
latitude ±1.54°). Where no DEM covers a site (for example Apollo sites outside the polar DEM) the
horizon is the smooth sphere, and the output says so. Catalog coordinates marked "approximate" are
region centres and should be checked against their sources. LROC QuickMap (south polar projection,
Earth shadow layer) is the visual reference we use to cross-check lit and shadowed areas.

**Real terrain (LOLA) and validation against NASA.** Horizons use NASA's LOLA south-pole DEM
`LDEM_80S_80MPP_ADJ.TIF` (PGDA product 90, Barker et al. 2023; 80 m/px, 80–90°S, same polar
stereographic projection as README §6.2), read by `astro/lola_dem.py` and downloaded by
`scripts/astro/fetch_lola_dem.py`. P2's `lunanav.terrain.dem` takes precedence when it exists.
We compared long-term average Sun visibility (mean visible fraction of the solar disk) and Earth
visibility (any part of the disk) over 2 years at 3 h steps with NASA's published maps
(PGDA product 69, Mazarico et al. 2011, `AVGVISIB_85S_060M_201608[_EARTH].TIF`, 3×3-pixel median
because the map has isolated zero pixels) at 36 points (6 named sites, 30 random points 85.5–89.9°S;
`scripts/astro/validate_lola_illumination.py`, results in `docs/validation_lola_illumination.csv`).
Sun: median |difference| 0.9 percentage points, correlation 0.973. Earth: median 1.2 pp, correlation
0.988. Shackleton's floor is 0 % for both, as published. The largest differences are on sharp crests
(connecting ridge 79 % vs 56 %, de Gerlache rim 69 % vs 50 %): there the 80 m DEM smooths nearby
relief, our observer stands 2 m above the surface, and the 60 m reference pixels vary by tens of
percent across a few hundred metres. A finer DEM (`--res 40` or `20`) should narrow this.

## Verdict, ranking and explanations (P4)

*Module: `backend/lunanav/decision/`. Pure functions: metrics in, decision out. No astronomy and no terrain access: P4 only interprets metrics computed by P3.*

### Verdict rule

Inputs (from `metrics`): `sunlight_pct`, `longest_darkness_h`, `earth_visibility_pct`, `longest_comms_gap_h`. Evaluation order: validate inputs, then `not_viable`, then `viable`, else `marginal`.

| Level | Condition |
|---|---|
| not_viable | longest_darkness_h > 100, or sunlight_pct < 30, or earth_visibility_pct < 20 |
| viable | sunlight_pct >= 60 and longest_darkness_h <= 50 and earth_visibility_pct >= 50 and longest_comms_gap_h <= 72 |
| marginal | all other cases |

Thresholds live in `DEFAULT_THRESHOLDS` and can be overridden; the thresholds actually used are returned with each verdict. They model a solar lander with ~4 days of battery and direct-to-Earth comms: **team assumptions, not NASA rules**. Missing, `None`, negative, non-finite or out-of-range inputs raise a controlled `DecisionInputError`; they are never read as favorable.

### Optional multi-criteria ranking (`ranking.py`)

Criteria: sunlight_pct (max), longest_darkness_h (min), earth_visibility_pct (max), longest_comms_gap_h (min), power_and_comms_pct (max), vertical_panel_energy_kwh_m2 (max).

- **Normalization**: min-max to [0, 1] (0 = worst, 1 = best; "min" criteria are inverted). A criterion equal for all scenarios gets 1.0.
- **WSM**: score = sum(weight x normalized value).
- **TOPSIS**: vector normalization, weighting, distances to the ideal and anti-ideal solutions, closeness C = d- / (d+ + d-).
- **Weight profiles** (assumptions): *science* favors productive time (sunlight, power + comms, energy); *engineering* favors worst cases (longest night, longest comms gap). Custom weights are accepted and normalized to sum 1.
- **Sensitivity**: each weight x(1-25 %) and x(1+25 %), 200 random weightings (fixed seed), and science vs engineering. Stable = winner never changes and wins >= 80 % of random weightings; moderate >= 50 %; else sensitive.

A ranking is relative: the top scenario can still be `not_viable`.

### Limits

Geometry only; no radio link budget, terrain hazards or thermal model. Min-max results depend on which scenarios are compared. Weights and thresholds are team choices and should be tuned with the team.
