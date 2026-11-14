# LunaNav: Team README

> Our entry for the NASA Space Apps Challenge 2026 **"Lunar Landing Site Navigator"** (Nov 14–15).
> This file is the **single source of truth** for what we build, who owns what, how the code is laid
> out and the data contracts every module must respect. Every agent brief in `agents/` points back
> here. If something here conflicts with an agent brief, **this README wins**.

**Deadline: Sat Nov 15, 23:59 local.** Submission = a **recorded video, max 90 seconds**, explaining the
project (no live judging). Everything we build should be visible and understandable inside that video.

---

## 1. What we are building

The challenge asks for a tool that helps mission planners and the public understand **when and
where** a lunar landing site has sunlight (power) and a line of sight to Earth (communications):
time remaining before sunset or Earthset, how long the sunlight and Earth visibility windows last,
solar elevation for power, and a way to **compare sites and dates**.

LunaNav answers one question: **"If we land here, on this date, will we have power and comms, and for how long?"**

### The app flow

| # | Screen | What the user does / sees | Backend call (P3 function) |
|---|---|---|---|
| **1** | **Scenario builder** | Build **2–4 scenario cards**. Each card = a **site** (pick from the 26-site catalog, or type lat/lon) + a **landing date** (+ optional mission duration, default one lunar day). | `GET /sites` |
| **2** | **Site view** | For one card: the **terrain horizon** around the site with the **Sun and Earth** drawn on it, current Sun elevation, power (W/m² on a vertical panel), and live **countdowns to sunset / Earthset** (or sunrise / Earthrise). | `site_conditions` |
| **3** | **Timeline** | A slider over **one lunar day (29.5 days)** from the landing date. Three bars: **sunlight**, **Earth visible**, **both** (power + comms). Dragging the slider moves the Sun and Earth on the horizon view. | `site_timeline` |
| **4** | **Compare** | The cards **side by side**: `sunlight_pct`, `longest_darkness_h`, `earth_visibility_pct`, `longest_comms_gap_h`, `power_and_comms_pct`, the best card per metric highlighted, and a **verdict** per card: **viable / marginal / not viable** with the reasons. | `compare_scenarios` + verdict (P4) |
| **5** | **Date sweep** | For one site: the **next 12 lunar days** as a small chart/table ("what if the launch slips?"). Click a row to add it as a new scenario card. | `date_sweep` |
| *opt.* | Explainers / export | Short public explainers ("why does the Sun skim the horizon at the pole?", "what is libration?") and an export of the comparison (CSV / JSON / printable page). | – |

There is **no trajectory layer, no region → zone → point drill-down and no PDF mission report** any more.
Those belonged to the pre-challenge plan and are dropped (see §12).

### Official challenge resources we use or link

- **NASA PGDA LOLA south-pole DEM** (Barker et al. 2023), 80 m/px, used for terrain horizons. Also the PGDA average-illumination maps, used to validate us.
- **JPL Horizons**, used to validate our Sun/Earth ephemeris.
- **NAIF SPICE kernels (DE440)**, our high-accuracy ephemeris backend.
- **LROC QuickMap** and **Moon Trek**: link out from the site view so a user can look at the real site.
- **CSA Moon page**: context for the public explainers.

---

## 2. Team & ownership

| ID | Role | Stack | Owns (folders) | Agent brief |
|---|---|---|---|---|
| **P1** | Frontend & Visualization | React / TypeScript | `frontend/` | `agents/AGENT_P1_frontend.md` |
| **P2** | Terrain & Coordinates | Python / GIS | `backend/lunanav/terrain/`, `backend/lunanav/coords.py`, `scripts/terrain/` | `agents/AGENT_P2_terrain.md` |
| **P3** | Astronomy & Physics (**wrida**) | Python / scientific computing | `backend/lunanav/astro/`, `scripts/astro/`, `mock_data/astro/` | `agents/AGENT_P3_astro.md` |
| **P4** | Verdict, Explanations & Content | Python / product | `backend/lunanav/decision/`, `docs/explainers/`, `docs/methodology.md` (verdict part) | `agents/AGENT_P4_decision.md` |
| **P5** | Backend, Integration & Video | FastAPI / QA / DevOps | `backend/app/`, `backend/tests/` (non-astro), deployment, demo video | `agents/AGENT_P5_backend.md` |

Fill in names: P1 ______ · P2 ______ · P3 wrida · P4 ______ · P5 ______

### 2.1 Who does what, per screen

| | **1 Scenario builder** | **2 Site view** | **3 Timeline** | **4 Compare** | **5 Date sweep** |
|---|---|---|---|---|---|
| **P1** | Card list (2–4), site picker with search + category filter, lat/lon input with validation, date picker | Horizon panorama (azimuth 0–360 × elevation) with Sun/Earth disks, gauges, countdown timers, QuickMap / Moon Trek links | Slider + three bars (sunlight / Earth / both), animates the horizon view | Side-by-side table, best-per-metric highlight, verdict badges + reasons | Chart of 12 rows, "add as card" button |
| **P2** | Coordinate checks (inside DEM coverage? south of 80°S?) | Optional local terrain: slope and roughness at the site, small heightmap for a 3D inset | – | Optional extra column: slope at site | – |
| **P3** | 26-site catalog | `site_conditions`: Sun/Earth az/el, horizon height, power, countdowns, windows, metrics | `site_timeline`: time series + horizon profile | `compare_scenarios` metrics + `best` | `date_sweep` |
| **P4** | – | One-sentence plain-language summary of the card | – | **Verdict rule** (viable / marginal / not viable) + reasons, short comparison explanation | One-line "best date" explanation |
| **P5** | `/sites` endpoint | `/scenarios/conditions` | `/scenarios/timeline` | `/scenarios/compare` (adds P4 verdicts) | `/scenarios/date-sweep` |

P5 also does caching, deployment, the screen recording and the 90-second video edit (with everyone).
Everyone: unit tests for their own module, keep `mock_data/` fixtures valid for their outputs.

---

## 3. Architecture

```
                      ┌──────────────────────────────────────────┐
                      │ frontend/  (P1)  React + TS              │
                      │ scenario cards · horizon view · charts   │
                      └──────────────────┬───────────────────────┘
                                         │ HTTP JSON  /api/*
                      ┌──────────────────▼───────────────────────┐
                      │ backend/app  (P5)  FastAPI               │
                      │ routes → services → adapters → modules   │
                      └───┬──────────────────┬───────────────┬───┘
                          │ Python calls     │               │
            ┌─────────────▼───┐   ┌──────────▼───────┐   ┌───▼────────────────┐
            │ terrain/ (P2)   │◄──┤ astro/ (P3)      │   │ decision/ (P4)     │
            │ DEM access,     │   │ ephemeris,       │   │ verdict rule,      │
            │ slope, coords   │   │ horizons, scen-  │   │ explanations       │
            └────────┬────────┘   │ arios, sites     │   └────────────────────┘
                     │            └──────────────────┘   (pure: metrics in →
                     ▼                                     verdict out)
          data/raw/dem/LDEM_80S_80MPP_ADJ.TIF (real LOLA, git-ignored)
```

Rules:

1. **The API is the only thing the frontend talks to.** The frontend never computes science. It only formats, animates and interpolates what the API sends.
2. **Modules talk through plain Python functions** that return JSON-ready dicts (§6). No module calls another over HTTP.
3. **Allowed imports:** `app` → everything · `astro` → `terrain.dem` (read-only, for horizons; falls back to `astro/lola_dem.py` when P2's module is absent) · `decision` → nothing but the metric dicts it is given · `terrain` → `coords`.
4. **`decision/` is pure**: metrics in, verdict + reasons out. It never reads the DEM or computes illumination.
5. **No silent fallbacks.** If the DEM does not cover a site, astro uses the smooth-sphere horizon and says so in `method` and `warnings`. The UI must show that warning on the card.
6. **Cache** results on disk keyed by `(site id or rounded lat/lon, start_utc, window_days, step_h, method)`. A full lunar day with a DEM horizon takes about a second; a 12-row sweep is about 12×.

---

## 4. Repository structure

What exists now is marked ✔. The rest is to be created by its owner.

```
Luna-Nav/
├── README.md                          ✔ this file
├── agents/                            ✔ AGENT_P1_frontend.md … AGENT_P5_backend.md
├── docs/
│   ├── methodology.md                 ✔ data sources + methods (P3 astronomy part done)
│   ├── validation_lola_illumination.csv ✔ our numbers vs NASA PGDA illumination maps
│   ├── explainers/                    ← P4: short public explainer texts (markdown)
│   └── decisions.md                   ← one line per decision: date, decision, who
├── mock_data/
│   └── astro/                         ✔ real outputs of the P3 functions (P1/P5 build on these)
│       ├── sites.json                 ✔ the 26-site catalog as served by /sites
│       ├── site_conditions_connecting-ridge.json   ✔ screen 2
│       ├── site_conditions_im-1.json  ✔ screen 2 (second example)
│       ├── site_timeline_connecting-ridge.json     ✔ screen 3
│       ├── compare_four_sites.json    ✔ screen 4
│       └── date_sweep_connecting-ridge.json        ✔ screen 5
├── data/                              ← git-ignored: LOLA DEM, PGDA maps, SPICE kernels
│   └── raw/dem/ · raw/illumination/ · kernels/
├── frontend/                          ← P1
│   └── src/
│       ├── screens/                   ← ScenarioBuilder, SiteView, Timeline, Compare, DateSweep
│       ├── components/                ← ScenarioCard, HorizonView, Countdown, WindowBars, VerdictBadge
│       ├── api/                       ← client.ts, types.ts, fixtures (= mock_data/astro)
│       └── state/scenarioStore.ts     ← §7
├── backend/
│   ├── requirements.txt               ✔ P5 (FastAPI); merge astro deps from astro/requirements-astro.txt
│   ├── app/                           ✔ P5 FastAPI app (main.py, api/, services/, integrations/, models/)
│   ├── lunanav/
│   │   ├── astro/                     ✔ P3 (see astro/README.md)
│   │   ├── terrain/                   ← P2 (dem.py may simply adopt astro/lola_dem.py)
│   │   ├── coords.py                  ← P2
│   │   └── decision/                  ← P4 (verdict.py, explain.py)
│   └── tests/
│       ├── astro/                     ✔ 71 tests (69 pass + 2 skip when the DEM / PGDA files are absent)
│       └── …                          ✔ P5 API tests
└── scripts/
    ├── astro/                         ✔ fetch_kernels.py, fetch_lola_dem.py, validate_horizons.py,
    │                                    validate_lola_illumination.py, scenario_demo.py, make_samples.py
    └── terrain/                       ← P2
```

**Tooling:** Python 3.11+, FastAPI, Pydantic v2, numpy, rasterio (DEM), spiceypy (optional), pytest.
Frontend: Node 20, Vite, React 18, TypeScript; any chart lib (recharts suggested). Plain SVG/canvas is
enough for the horizon view; three.js is optional.

**Setup (Windows, as used by P3):**
```powershell
cd backend
py -m pip install -r requirements.txt -r lunanav\astro\requirements-astro.txt
py ..\scripts\astro\fetch_lola_dem.py          # 181 MB real DEM → data\raw\dem\
py ..\scripts\astro\fetch_kernels.py           # optional SPICE kernels
py -m pytest tests\astro -q
py ..\scripts\astro\scenario_demo.py           # prints the 4-site comparison
```

---

## 5. Conventions (non-negotiable)

### 5.1 Units are in the field name
Every numeric field ends with its unit.

| Suffix | Meaning | Suffix | Meaning |
|---|---|---|---|
| `_m` | metres | `_km` | kilometres |
| `_deg` | degrees | `_pct` | percent, 0–100 |
| `_h` | hours | `_w_m2` | W per m² |
| `_kwh_m2` | kWh per m² | `_utc` | ISO-8601 UTC string ending in `Z`, e.g. `2027-01-10T00:00:00Z` |

Human-readable durations come pre-formatted in `*_text` fields (`"3 d 4 h 12 min"`). The frontend shows
those instead of formatting hours itself.

### 5.2 Lunar coordinates
- **Body:** Moon, sphere of radius `MOON_RADIUS_M = 1_737_400` (LOLA reference).
- **Frame:** Moon Mean-Earth / Polar-axis (ME) body-fixed frame (the frame LOLA products use).
- **Lat/lon:** planetocentric, **degrees**; latitude −90…90 (south pole = −90); longitude **east-positive, −180…180**. Inputs outside that range are normalized (`sites.normalize_latlon`).
- **Elevation:** `elevation_m` = metres above the 1737.4 km sphere (can be negative). If the user gives none, it is sampled from the DEM.
- Always explicit `lat_deg`, `lon_deg` fields, never anonymous pairs (GeoJSON, if used, is `[lon, lat]`).
- **DEM projection:** south polar stereographic on the sphere, exactly what the PGDA LOLA files use:
  `+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs`
  - forward: `ρ = 2R·tan(π/4 + φ/2)`, `x_m = ρ·sin λ`, `y_m = ρ·cos λ`
  - inverse: `ρ = √(x²+y²)`, `φ = 2·atan(ρ/2R) − π/2`, `λ = atan2(x, y)`
- **DEM coverage:** 80–90°S. Sites north of 80°S (Apollo, most CLPS, Chang'e…) use the **smooth-sphere** horizon and carry a warning. That is correct behaviour, not a bug.
- **Azimuth:** degrees clockwise from local north (0–360), north = toward the lunar north pole along the local meridian. **Elevation angle:** degrees above the local horizontal plane.

### 5.3 Time
- Each scenario card has its own **landing date** = `start_utc`.
- **Analysis window** = `[start_utc, start_utc + window_days]`, default **one lunar day**, `window_days = 29.530589` (synodic month).
- Sampling: `step_h = 0.5` for `site_conditions`, `1.0` for timeline / compare / sweep. Events (sunrise, sunset, earthrise, earthset) are refined by bisection to ≤ 30 s.
- Valid date range is limited by the ephemeris (analytic model ~1900–2100; SPICE DE440 longer). Out-of-range dates come back as an error, never as a crash.

### 5.4 Definitions (so everyone says the same thing in the video)
- **Sunlit** = centre of the solar disk above the local terrain horizon at the Sun's azimuth. `disk_visible_fraction` tells how much of the disk is up (at the poles the Sun skims the horizon for days).
- **Earth visible** = centre of the Earth disk above the local horizon. This is **geometric line of sight only**, not a radio link budget (see `COMMS_NOTE` in the output).
- **Power** = geometry only: irradiance at the Moon's distance from the Sun (1361 W/m² at 1 AU) × visible disk fraction × cos(Sun elevation) for a vertical panel facing the Sun. No efficiency, temperature or dust.
- **Power + comms** = times when both are true.

### 5.5 IDs
- Site ids are the catalog's kebab-case ids (`connecting-ridge`, `im-1`, `malapert-massif`…). A user-typed coordinate gets `id: null`, `category: "custom"`, `coord_quality: "user_input"`.
- Scenario card ids are frontend-only (`card-1`…). The API identifies a scenario by its `label` (auto: `"<site name> @ <YYYY-MM-DD>"`; numbered if two cards collide).

### 5.6 Shared constants
`MOON_RADIUS_M = 1737400` · `SYNODIC_MONTH_D = 29.530589` · `SOLAR_CONSTANT_W_M2 = 1361` ·
`AU_KM = 149597870.7` · `EARTH_RADIUS_KM = 6371` · `SUN_RADIUS_KM = 695700` · `REFINE_TOL_S = 30` ·
`MAX_SAMPLES = 20000` · `MIN_CARDS = 2`, `MAX_CARDS = 4` (UI; the API accepts 1–12) ·
`SWEEP_N = 12`, `SWEEP_EVERY_D = 29.530589` (API accepts n = 1–36) · DEM `LDEM_80S_80MPP_ADJ.TIF`, horizon
360 azimuth bins, rays to 100 km. Astro constants live in `astro/scenarios.py`; the frontend mirrors the UI ones in
`frontend/src/lib/constants.ts`.

---

## 6. Data contracts

The **P3 functions in `backend/lunanav/astro/scenarios.py` and their real outputs in
`mock_data/astro/` are the source of truth** for the science shapes. P5's Pydantic models in
`backend/app/models/` must accept them unchanged; P1 types them from the same files. If a field
is unclear, open the JSON in `mock_data/astro/`: it is a real run, not a hand-written guess.

### 6.1 Common envelope (every P3 result)

```ts
type UTC = string;                         // "2027-01-10T00:00:00Z"

interface Envelope {
  status: "ok" | "error";
  result_type: "ephemeris_calculation";
  warnings: string[];                      // show them on the card
  data_sources: { ephemeris_backend: string; ephemeris_source: string };   // analytic (Meeus) or SPICE DE440
  limitations: string[];                   // methodology caveats, for the explainer / export
}
interface ErrorResult {                    // functions never raise on bad input
  status: "error";
  error: { code: string; message: string };// UNKNOWN_SITE, INVALID_COORDINATES, INVALID_WINDOW, INVALID_SCENARIOS, …
}

type SiteInput = string                     // catalog id, e.g. "im-1"
               | { lat_deg: number; lon_deg: number; name?: string; elevation_m?: number };

interface Site {
  id: string | null; name: string; category: string;   // apollo | artemis | clps | international | south_pole_candidate | reference | custom
  mission: string | null; agency: string | null;
  coord_quality: "landed" | "approximate" | "exact" | "user_input";
  lat_deg: number; lon_deg: number; elevation_m: number;
}
```

### 6.2 Screen 1: sites

```ts
// GET /api/sites?category=artemis      → { status, sites: Site[] }   (26 sites, see mock_data/astro/sites.json)
// GET /api/sites/{id}                  → { status, site: Site }
```
Python: `list_sites(category=None)`, `get_site(site_id)`, `resolve_site(site)`.

### 6.3 Screen 2: site conditions

```ts
// POST /api/scenarios/conditions  { site: SiteInput, start_utc: UTC, window_days?: number }
// Python: site_conditions(site, start_datetime, window_days=29.530589, step_h=0.5, terrain_data=None)
interface BodyNow {
  azimuth_deg: number; elevation_deg: number;
  horizon_elevation_deg: number;           // terrain horizon height at that azimuth
  margin_above_horizon_deg: number;        // elevation − horizon; > 0 = up
  visible: boolean; disk_visible_fraction: number;      // 0..1
  apparent_radius_deg: number; distance_km: number;
}
interface Countdown {
  next_event: "sunset" | "sunrise" | "earthset" | "earthrise";
  next_event_utc: UTC | null; time_remaining_h: number | null; time_remaining_text: string | null;
  beyond_window: boolean;                  // true = no change during the whole window
  summary: string;                         // "Earthrise in 21 h 37 min" / "Sun stays up for the whole 29.5-day window"
}
interface Window {                         // one continuous interval
  start_utc: UTC; end_utc: UTC; duration_h: number; duration_text: string; starts_in_h: number;
  open_at_window_start: boolean; open_at_window_end: boolean;   // clipped by the analysis window
}
interface Metrics {
  sunlight_pct: number; sunlight_hours: number; longest_darkness_h: number;
  earth_visibility_pct: number; earth_visible_hours: number; longest_comms_gap_h: number;
  power_and_comms_pct: number;
  sun_elevation_deg_max: number; sun_elevation_deg_min: number; sun_elevation_deg_mean_when_lit: number | null;
  earth_elevation_deg_max: number; earth_elevation_deg_min: number;
  mean_vertical_panel_factor: number; mean_horizontal_panel_factor: number;
  vertical_panel_energy_kwh_m2: number; n_sunsets: number; n_earthsets: number;
  libration_lat_range_deg: [number, number]; libration_lon_range_deg: [number, number];
}
interface SiteConditions extends Envelope {
  site: Site;
  method: "horizon_mask" | "smooth_sphere";
  window: { start_utc: UTC; end_utc: UTC; duration_h: number; duration_days: number;
            sampling_interval_h: number; n_samples: number };
  now: { t_utc: UTC; sun: BodyNow; earth: BodyNow;
         power: { irradiance_w_m2: number; vertical_panel_factor: number;
                  horizontal_panel_factor: number; vertical_panel_w_m2: number };
         libration: { sub_earth_lat_deg: number; sub_earth_lon_deg: number };
         sub_solar: { lat_deg: number; lon_deg: number } };
  countdown: { sun: Countdown; earth: Countdown };
  next_events: { event: string; t_utc: UTC; in_h: number; in_text: string }[];
  windows: { sunlit: Window[]; earth_visible: Window[]; power_and_comms: Window[] };
  metrics: Metrics;
}
```
"Now" means **the landing moment** (`start_utc`). For a live countdown in the UI, P1 subtracts the time
moved on the slider from `time_remaining_h`, or reads the next event from `next_events`.

### 6.4 Screen 3: timeline

```ts
// POST /api/scenarios/timeline  { site: SiteInput, start_utc: UTC, days?: number, step_h?: number }
// Python: site_timeline(site, start_datetime, days=29.530589, step_h=1.0, terrain_data=None)
interface SiteTimeline extends SiteConditions {
  series: {                                // parallel arrays, one entry per sample
    t_utc: UTC[]; hours_from_start: number[];
    sun_azimuth_deg: number[]; sun_elevation_deg: number[]; sun_horizon_deg: number[];
    sun_disk_visible_fraction: number[];
    earth_azimuth_deg: number[]; earth_elevation_deg: number[]; earth_horizon_deg: number[];
    earth_visible: boolean[]; irradiance_w_m2: number[];
  };
  horizon_profile: { azimuth_deg: number[]; elevation_deg: number[]; method: string };  // 360 bins: draw this as the skyline
}
```
The three bars come from `windows.sunlit`, `windows.earth_visible`, `windows.power_and_comms` (use
`starts_in_h` / `duration_h` against the 708.7 h window). ~709 samples per card is small enough to send whole.

### 6.5 Screen 4: compare + verdict

```ts
// POST /api/scenarios/compare  { scenarios: { site: SiteInput; start_utc: UTC; label?: string; window_days?: number }[] }   // 2–4 from the UI
// Python: compare_scenarios(scenarios, window_days=29.530589, step_h=1.0, terrain_data=None)
interface CompareRow {
  label: string; site: Site; start_utc: UTC; method: string; warnings: string[];
  sunlit_at_start: boolean; sun_elevation_deg_at_start: number;
  earth_visible_at_start: boolean; earth_elevation_deg_at_start: number;
  sun_countdown: Countdown; earth_countdown: Countdown;
  metrics: Metrics; windows: SiteConditions["windows"];
  verdict: Verdict;                        // added by P5 from P4's rule (not in the P3 output)
}
interface Compare extends Envelope {
  n_scenarios: number; rows: CompareRow[];
  best: Record<CompareKey, { label: string; value: number;
                             direction: "higher_is_better" | "lower_is_better" }>;
}
type CompareKey = "sunlight_pct" | "longest_darkness_h" | "earth_visibility_pct" | "longest_comms_gap_h"
                | "power_and_comms_pct" | "vertical_panel_energy_kwh_m2" | "sun_elevation_deg_max";

interface Verdict {                        // P4: backend/lunanav/decision/verdict.py
  level: "viable" | "marginal" | "not_viable";
  reasons: string[];                       // ["Longest night 354 h > 72 h limit", …]
  summary: string;                         // one plain-language sentence for the card
  thresholds: Record<string, number>;      // the numbers actually used, shown in the UI tooltip
}
```

**Default verdict rule** (P4 owns and may tune it; whatever is used must be shown in the UI):

| Level | Condition |
|---|---|
| **not viable** | `longest_darkness_h > 100` **or** `sunlight_pct < 30` **or** `earth_visibility_pct < 20` |
| **viable** | `sunlight_pct ≥ 60` **and** `longest_darkness_h ≤ 50` **and** `earth_visibility_pct ≥ 50` **and** `longest_comms_gap_h ≤ 72` |
| **marginal** | everything else |

Python: `verdict(metrics: dict, thresholds: dict | None = None) -> Verdict`. Pure function, metrics in, verdict out.
The numbers describe a **solar-powered lander with ~4 days of battery and direct-to-Earth comms**, stated in the UI as our
assumption, not a NASA rule. Metrics are computed over the card's window, so a shorter mission duration can change the verdict.
On `compare_four_sites.json` (full lunar day from 2027-01-10) this gives: Connecting Ridge **marginal** (100 % sun, but a
347 h comms gap → needs a relay), Malapert / IM-1 / Apollo 11 **not viable** (nights of 247–274 h).

### 6.6 Screen 5: date sweep

```ts
// POST /api/scenarios/date-sweep  { site: SiteInput, first_start_utc: UTC, n?: number, every_days?: number }
// Python: date_sweep(site, first_start_datetime, n=12, every_days=29.530589, window_days=None, step_h=1.0, terrain_data=None)
interface DateSweep extends Envelope {
  site: Site; every_days: number; window_days: number;
  rows: (Omit<CompareRow, "windows" | "verdict"> & { sub_solar_lat_deg: number; verdict?: Verdict })[];   // label = "YYYY-MM-DD"
  best: Compare["best"];
}
```
"Add as card" = new card with the same site and `start_utc = row.start_utc`.

### 6.7 Endpoint summary (`/api`, P5's existing prefix)

| Method | Path | Returns | Producer |
|---|---|---|---|
| GET | `/health` | `{status, ...}` | P5 |
| GET | `/api/sites`, `/api/sites/{id}` | §6.2 | P3 |
| POST | `/api/scenarios/conditions` | `SiteConditions` | P3 |
| POST | `/api/scenarios/timeline` | `SiteTimeline` | P3 |
| POST | `/api/scenarios/compare` | `Compare` (+ verdicts) | P3 + P4 |
| POST | `/api/scenarios/date-sweep` | `DateSweep` (+ verdicts) | P3 + P4 |
| GET | `/api/explainers` | `{id, title, markdown}[]` (optional) | P4 |
| POST | `/api/export` | CSV / JSON of a `Compare` (optional) | P5 |

Errors: P3 results with `status: "error"` become HTTP 422 with `{ "error": { code, message } }`.
The old `/api/mission`, `/regions`, `/zones`, `/points`, `/reports` routes in `backend/app/api/` are
retired: P5 removes them (or leaves them unregistered) once the new routes work.

---

## 7. Frontend state (P1, everyone should know it)

```ts
interface ScenarioCard {
  id: string;                     // "card-1"
  site: SiteInput;                // catalog id or {lat_deg, lon_deg, name?}
  startUtc: string;
  windowDays?: number;            // mission duration, default 29.530589
  label?: string;
}
interface ScenarioState {
  cards: ScenarioCard[];          // 2..4
  activeCardId: string | null;    // the card shown in site view / timeline
  sliderHours: number;            // 0 .. 708.7, position on the timeline
  sweepSiteId: string | null;     // site of the open date sweep
}
```
- Results are fetched per card and cached by `(site, startUtc)` (TanStack Query or a simple map).
- Changing a card's site or date only refetches that card and the comparison.
- State in `sessionStorage` (and optionally the URL) so a refresh or a shared link keeps the cards.

---

## 8. Mock data & working order

Nobody waits for anybody:

- **P1** builds every screen against the files in `mock_data/astro/` from day 0. They are real outputs, so switching to the live API changes nothing in the shapes. Add a fake `verdict` to the compare fixture until P4's rule is in.
- **P5** wires the routes to the P3 functions directly (they are fast and already real); `mock_data/astro/` serves as the API test fixtures.
- **P4** writes `verdict()` against the `metrics` objects in `compare_four_sites.json` and `date_sweep_connecting-ridge.json`.
- **P2** adopts or wraps `astro/lola_dem.py` as `lunanav.terrain.dem` and adds slope at site / heightmap if time allows.
- Regenerate fixtures after any astro change: `py scripts\astro\make_samples.py`.

A good demo set (in the fixtures): **Connecting Ridge** (near-permanent sunlight, Earth only part-time),
**Malapert Massif** (Earth always up, less Sun), **IM-1 Odysseus** (a real landing that ran out of power),
**Apollo 11** (equatorial contrast: a two-week night).

---

## 9. Validation (say this in the video)

| Check | Result | How |
|---|---|---|
| Sun/Earth positions vs **JPL Horizons** | **25/25 pass** (≤ 2.8 km, ≤ 0.012° with the analytic model; SPICE DE440 closer) | `scripts/astro/validate_horizons.py` |
| Our sunlight % vs **NASA PGDA** average-illumination maps (LOLA, Mazarico et al.) | **~1 percentage point median difference** | `scripts/astro/validate_lola_illumination.py`, results in `docs/validation_lola_illumination.csv` |
| Unit tests | **71 tests**: 69 pass + 2 skip when the DEM / PGDA files are not downloaded | `py -m pytest backend/tests/astro -q` |

Methodology and limitations: `docs/methodology.md` and `backend/lunanav/astro/README.md`.

---

## 10. Collaboration rules

- **Branches:** `main` is always demo-able. Work on `p1/<topic>`, `p2/<topic>`… Small PRs or small direct pushes, pull before you push (`git pull --rebase origin main`).
- **Don't edit another person's folder.** Ping them instead. Exception: P5 may fix imports and wiring.
- **Contract changes** (anything in §5–§6): say it in the team chat first, update this README, the fixtures and the function in the same commit.
- **Agents:** each of us gives their `agents/AGENT_Px_*.md` to their coding agent and tells it to read this README first. Agents must not change contracts on their own; they propose the change and stop.
- **Large files stay out of git** (`data/`, kernels, `.TIF`). Use the fetch scripts.

---

## 11. Milestones (Nov 14–15)

| # | Milestone | Done when | Owner |
|---|---|---|---|
| **M0** | Science ready | P3 scenario functions, 26-site catalog, real LOLA horizons, validation, fixtures ✔ | P3 ✔ |
| **M1** | Walking skeleton on fixtures | All 5 screens click through on `mock_data/astro/` | P1 |
| **M2** | Live API | `/api/sites` + 4 `/api/scenarios/*` routes call the P3 functions; verdicts attached | P5 + P4 |
| **M3** | Frontend on live API | Cards built from any site/date, real horizon with Sun & Earth, slider animation | P1 + P5 |
| **M4** | Polish | Verdict reasons, explainers, export, QuickMap/Moon Trek links, warnings visible | P1, P4 |
| **M5** | Freeze & video | Feature freeze **Nov 15 ~18:00**; record the screens; cut the **90-second** video; submit before **23:59** | everyone, P5 leads |

**90-second video outline (suggestion):** 0–10 s problem (power + comms decide a landing) · 10–30 s build
two cards and open the site view (horizon, Sun, Earth, countdowns) · 30–50 s drag the timeline · 50–70 s compare
4 sites with verdicts · 70–80 s date sweep, add a better date · 80–90 s validated against JPL Horizons and NASA LOLA maps.

---

## 12. What changed from the pre-challenge plan

The pre-challenge plan (date → region → 3 zones → point → PDF report, plus an L1 Earth–Moon trajectory
layer) is **dropped**. The official challenge is about sunlight and Earth visibility over time at a site,
and comparing sites and dates, which the scenario flow above covers directly.

- `astro/mission.py`, `plan_mission`, `calculate_mission` and the trajectory tests still exist but are **not used by the app**.
- The `illumination_at`, `analyze_illumination`, `analyze_earth_visibility` wrappers remain available for P5's old adapters; new code should use the four scenario functions.
- Regions, zones, candidate points, MCDA scoring and the PDF report are out of scope. P4's job is now the verdict rule and the explanations; P2's job is DEM access, coordinates and optional local terrain.
