# LunaNav — Team README

> Lunar South Pole landing-site selection app for the NASA challenge (14th–15th).
> This file is the **single source of truth** for who owns what, how the code is laid out, and the
> data contracts every module must respect. Every agent brief in `docs/agents/` points back here.
> If something here conflicts with an agent brief, **this README wins**.

---

## 1. What we are building

A web app that walks a user from a mission date down to one recommended landing coordinate:

**Mission Configuration → Lunar South Pole Exploration → Regional Selection → Landing-Zone Identification → Selection of Three Candidates → Comparative Evaluation → Recommended Landing Zone → Optimal Landing-Point Identification → Final Mission Report**

The real challenge datasets are **not available yet**. We therefore build everything **mock-first**:
every module works end to end on fake data that has *exactly* the same shape (and, for terrain, the
same file format) as the real data will have. When the datasets arrive, we swap the data source,
not the code.

---

## 2. The four layers

| Layer | What the user sees | Output passed to the next layer |
|---|---|---|
| **L1 Mission Configuration & Earth–Moon Interception** | 3D Earth + orbiting Moon, date picker for arrival, transfer trajectory, collapsible mission info panel, Confirm button | `arrival_utc`, interception window, trajectory, mission parameters (`MissionPlan`) |
| **L2 South Pole Regional Exploration** | Earth fades out, camera flies to the lunar South Pole, predefined regions drawn as highlighted boundaries, hover + click info cards, select one region | `selected_region_id` + region data (`Region`) |
| **L3 Landing-Zone Identification & Evaluation** | Zoom into region, landing-zone polygons, hover + click info cards, user picks **exactly 3**, app scores/ranks them, comparison summary, winner highlighted | 3 scored candidates, ranking, `recommended_zone_id` (`ZoneEvaluation`) |
| **L4 Optimal Landing-Point Identification** | Zoom into winning zone, candidate point markers, click for details, optimal point highlighted, **Generate Report** (PDF) | final coordinates, point evaluation, PDF report (`PointsResult`, report) |

Global features: starfield background, smooth camera transitions, floating info cards, collapsible panels,
back-navigation **without losing selections**, consistent coordinate systems.

---

## 3. Team & ownership

| ID | Role | Stack | Owns (folders) | Agent brief |
|---|---|---|---|---|
| **P1** | Frontend & Visualization | React / TypeScript, three.js | `frontend/` | `docs/agents/AGENT_P1_frontend.md` |
| **P2** | Geospatial & Terrain | Python / GIS | `backend/lunanav/terrain/`, `backend/lunanav/coords.py`, `scripts/terrain/` | `docs/agents/AGENT_P2_terrain.md` |
| **P3** | Astronomy & Physics | Python / scientific computing | `backend/lunanav/astro/`, `scripts/astro/` | `docs/agents/AGENT_P3_astro.md` |
| **P4** | Decision Engine & AI | Python / algorithms | `backend/lunanav/decision/`, `docs/methodology.md` (scoring part) | `docs/agents/AGENT_P4_decision.md` |
| **P5** | Backend & Integration | FastAPI / QA / DevOps | `backend/lunanav/api/`, `backend/lunanav/schemas/`, `backend/lunanav/report/`, `mock_data/`, `contracts/`, CI, deployment | `docs/agents/AGENT_P5_backend.md` |

Fill in names: P1 ______ · P2 ______ · P3 ______ · P4 ______ · P5 ______

### 3.1 Who does what, per layer

| | **L1 Mission** | **L2 Regions** | **L3 Zones (pick 3)** | **L4 Points + Report** |
|---|---|---|---|---|
| **P1 Frontend** | Earth–Moon 3D scene, date picker, trajectory line, collapsible mission panel, Confirm | Camera fly-to pole, region boundary overlays, hover/click info cards, region select | Zone polygons on terrain mesh, info cards, exactly-3 selection UI, comparison charts (radar + bars), winner highlight, explanation panel | Point markers, point info card, optimal point highlight, terrain inspection, Generate Report button |
| **P2 Terrain** | — | Region polygons, region terrain stats (elevation, slope, roughness, surface), heightmaps for the 3D mesh | **Zone identification** (polygons from slope/roughness masks), zone terrain metrics, crater/boulder density | **Candidate point generation**, local slope/roughness, distance to craters/hazards |
| **P3 Astro** | **Moon ephemeris, transfer trajectory, interception window, launch time, Earth–Moon distance, orbital params** | Region illumination & Earth visibility at arrival | Zone illumination %, longest shadow, Earth visibility / comms | Point-level illumination & Earth visibility using horizon masks (terrain obstruction) |
| **P4 Decision** | — | Preliminary suitability score/label for regions | **Weighted scoring / MCDA, hard constraints, ranking of the 3, comparison explanation** | **Point ranking, optimal point, final explanation**, methodology text for the report |
| **P5 Backend** | `/mission/plan` endpoint | `/regions` endpoints | `/zones`, `/evaluate/zones` endpoints | `/points` endpoint, **PDF report generation**, deployment, demo build |

Everyone: unit tests for their own module, keep `mock_data/` fixtures valid for their outputs.

---

## 4. Shared architecture

```
                      ┌───────────────────────────────────────────┐
                      │ frontend/  (P1)  React + TS + three.js    │
                      │ zustand mission store · TanStack Query    │
                      └──────────────────┬────────────────────────┘
                                         │ HTTP JSON  /api/v1/*
                                         │ (types generated from OpenAPI)
                      ┌──────────────────▼────────────────────────┐
                      │ backend/lunanav/api  (P5)  FastAPI        │
                      │ routes → services/pipeline.py → modules   │
                      │ DATA_MODE = fixtures | synthetic | real   │
                      └───┬───────────────┬───────────────┬───────┘
                          │ Python calls  │               │
            ┌─────────────▼───┐   ┌───────▼────────┐  ┌───▼───────────────┐
            │ terrain/ (P2)   │◄──┤ astro/ (P3)    │  │ decision/ (P4)    │
            │ DEM, slope,     │   │ ephemeris,     │  │ normalize, weight,│
            │ zones, points   │   │ sun/earth,     │  │ rank, explain     │
            └────────┬────────┘   │ horizon masks  │  └───────────────────┘
                     │            └────────────────┘   (pure: metrics in →
                     ▼                                   scores out)
          data/ GeoTIFF (synthetic now, LOLA later)
```

Rules of the architecture:

1. **The API is the only thing the frontend talks to.** The frontend never computes science; it only converts coordinates for display.
2. **Modules talk through plain Python functions with Pydantic models** from `lunanav.schemas` (signatures in §7). No module calls another over HTTP.
3. **Allowed imports:** `api` → everything · `astro` → `terrain.dem` (read-only DEM access for horizon masks) · `decision` → `schemas` only · `terrain` → `coords`, `schemas`. Nothing else crosses folders.
4. **`decision/` is pure**: it receives metrics and returns scores. It never reads files or computes terrain/illumination.
5. **Three data modes** controlled by env `LUNANAV_DATA_MODE`:
   - `fixtures` – the API returns hand-written JSON from `mock_data/`. Available on day 0 so P1 is never blocked.
   - `synthetic` – the real pipeline runs on a **synthetic DEM GeoTIFF** generated by P2 (same projection, format and resolution as LOLA). Proves the science code works.
   - `real` – same pipeline on the challenge datasets.
6. **Expensive results are cached** on disk under `data/cache/` keyed by `(object_id, arrival_utc date, data_mode, contract_version)`.

---

## 5. Repository structure

```
lunanav/
├── README.md                     ← this file
├── docs/
│   ├── agents/                   ← AGENT_P1_frontend.md … AGENT_P5_backend.md
│   ├── methodology.md            ← data sources + methods (P2, P3, P4 write; goes into the PDF)
│   └── decisions.md              ← short log of decisions (date, decision, who)
├── contracts/                    ← P5 owns; changes only via "contract" PR (§10)
│   ├── openapi.json              ← exported from FastAPI, committed
│   ├── coord_test_vectors.json   ← lat/lon ↔ polar-stereo ↔ 3D test points (P2 creates)
│   └── CHANGELOG.md              ← every contract change, with version bump
├── mock_data/                    ← fixtures, valid against the schemas (CI checks it)
│   ├── mission_plan.json
│   ├── criteria.json
│   ├── regions.geojson
│   ├── zones/REG-01.geojson …
│   ├── evaluations/zones_example.json
│   ├── points/REG-01-Z01.json …
│   └── heightmaps/REG-01.json …
├── data/                         ← gitignored (except data/README.md)
│   ├── raw/                      ← downloaded datasets (LOLA GeoTIFFs, kernels…)
│   ├── synthetic/                ← synthetic DEM GeoTIFFs (P2 script output)
│   ├── processed/                ← derived rasters: slope, roughness, hazard masks
│   └── cache/
├── frontend/                     ← P1
│   ├── package.json
│   └── src/
│       ├── app/                  ← App shell, routing between layers, starfield
│       ├── scenes/               ← EarthMoonScene.tsx, MoonScene.tsx, CameraRig.tsx
│       ├── layers/               ← L1Mission/, L2Regions/, L3Zones/, L4Points/
│       ├── components/           ← InfoCard, CollapsiblePanel, ComparisonChart, …
│       ├── api/                  ← client.ts, types.gen.ts (generated), fixtures.ts
│       ├── state/missionStore.ts ← zustand store (§8)
│       └── lib/coords.ts         ← TS port of coords.py, tested with coord_test_vectors.json
├── backend/
│   ├── pyproject.toml
│   ├── lunanav/
│   │   ├── schemas/              ← Pydantic models = SOURCE OF TRUTH for all contracts (P5)
│   │   ├── coords.py             ← projections & conversions (P2)
│   │   ├── config.py             ← constants (§6), env vars (P5)
│   │   ├── terrain/              ← P2
│   │   ├── astro/                ← P3
│   │   ├── decision/             ← P4
│   │   ├── report/               ← PDF generation (P5)
│   │   └── api/                  ← FastAPI app, routes, services/pipeline.py (P5)
│   └── tests/
│       ├── terrain/ astro/ decision/   ← owners' unit tests
│       └── integration/          ← P5: contract + end-to-end tests
├── scripts/
│   ├── terrain/make_synthetic_dem.py, preprocess_dem.py   (P2)
│   ├── astro/fetch_kernels.py                             (P3)
│   └── precompute.py                                      (P5, calls everyone)
├── docker-compose.yml
└── .github/workflows/ci.yml      ← lint + tests + fixture validation + openapi drift check
```

**Tooling:** Python 3.11, `uv` (or pip) · FastAPI, Pydantic v2, numpy, scipy, rasterio, pyproj, shapely · pytest, ruff.
Node 20 · Vite, React 18, TypeScript (strict), three, @react-three/fiber, @react-three/drei, zustand, @tanstack/react-query, recharts, openapi-typescript · vitest.

---

## 6. Conventions (non-negotiable)

### 6.1 Units are in the field name
Every numeric field ends with its unit. No exceptions, no unit-less numbers except IDs, ranks and 0–1 normalized scores.

| Suffix | Meaning | Suffix | Meaning |
|---|---|---|---|
| `_m` | metres | `_km` | kilometres |
| `_deg` | degrees | `_pct` | percent, 0–100 |
| `_h` | hours | `_km2` | square km |
| `_per_km2` | count per km² | `_utc` | ISO-8601 UTC string, always ending in `Z`, e.g. `2027-03-14T12:00:00Z` |

`score` = 0–100 (higher is better). `normalized` = 0–1 (1 = best). `rank` = 1 is best.

### 6.2 Lunar coordinates
- **Body:** Moon, sphere of radius `MOON_RADIUS_M = 1_737_400` (LOLA reference).
- **Frame:** Moon Mean-Earth / Polar-axis (ME) body-fixed frame (the frame LOLA products use).
- **Lat/lon:** planetocentric, **degrees**; latitude −90…90 (south pole = −90); longitude **east-positive, −180…180**.
- **Elevation:** `elevation_m` = metres above the 1737.4 km sphere (can be negative).
- **GeoJSON order is `[lon_deg, lat_deg]`** (standard GeoJSON). Everywhere else we write explicit `lat_deg`, `lon_deg` fields — never anonymous pairs.
- **Map projection for rasters:** south polar stereographic on the sphere:
  `+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs`
  - forward: `ρ = 2R·tan(π/4 + φ/2)`, `x_m = ρ·sin λ`, `y_m = ρ·cos λ`
  - inverse: `ρ = √(x²+y²)`, `φ = 2·atan(ρ/2R) − π/2`, `λ = atan2(x, y)`
  - If a LOLA product ships with a different projection, P2 reprojects it into this one in preprocessing.
- **Azimuth:** degrees clockwise from local north (0–360). **Elevation angle:** degrees above the local horizontal plane.

### 6.3 3D scene conventions (frontend, also used by P3 when sending vectors)
- **L1 scene (Earth-centred):** frame J2000 Earth-centred inertial; API sends `pos_km`. Display scale `1 unit = 1000 km`. Bodies may be visually enlarged (`BODY_VISUAL_SCALE`), but **positions are always true scale**.
- **L2–L4 scene (Moon-centred):** Moon at origin, `1 unit = 1 km`, ME frame.
- **Axis mapping (both scenes), three.js is Y-up:** `three.x = X`, `three.y = Z`, `three.z = −Y` where (X, Y, Z) is the physical frame (Z = north pole / celestial north).
- Surface point → 3D: `r = (MOON_RADIUS_M + elevation_m · VERTICAL_EXAGGERATION) / 1000`,
  `X = r cosφ cosλ`, `Y = r cosφ sinλ`, `Z = r sinφ`, then apply the axis mapping.
- `VERTICAL_EXAGGERATION` is a frontend-only display setting (default 3). Never send exaggerated values from the backend.
- `contracts/coord_test_vectors.json` holds ~10 points with lat/lon/elevation → x_m/y_m → three.js xyz. Both `coords.py` and `coords.ts` must pass them.

### 6.4 Time
- The **mission time** is `arrival_utc` chosen in L1. Every L2–L4 request carries it as a query/body parameter.
- **Analysis window** for illumination & Earth visibility = `[arrival_utc, arrival_utc + SURFACE_STAY_DAYS]`, default `SURFACE_STAY_DAYS = 7`, time step `ANALYSIS_STEP_H = 1`.

### 6.5 IDs
Stable, human-readable strings, hierarchical:
- region `REG-01` · zone `REG-01-Z03` · point `REG-01-Z03-P07`
- criterion ids are snake_case (`slope_mean`, `illumination`, …), defined in `criteria.json`.

### 6.6 Shared constants (`backend/lunanav/config.py`, mirrored in `frontend/src/lib/constants.ts`)
`MOON_RADIUS_M=1737400` · `EARTH_RADIUS_KM=6371` · `SURFACE_STAY_DAYS=7` · `ANALYSIS_STEP_H=1` · `ZONES_TO_COMPARE=3` · `CONTRACT_VERSION="0.1.0"` · `SOUTH_POLE_MAX_LAT_DEG=-80` (study area is south of 80°S).

---

## 7. Data contracts

The **Pydantic models in `backend/lunanav/schemas/` are the source of truth**. FastAPI exports them to
`contracts/openapi.json`; the frontend generates `src/api/types.gen.ts` from it (`npm run gen:api`).
The shapes below are written in TypeScript notation for readability; the Pydantic models must match them exactly.

### 7.1 Common pieces

```ts
type UTC = string;                         // "2027-03-14T12:00:00Z"

interface Meta {                           // present on EVERY response, field name "meta"
  contract_version: string;                // "0.1.0"
  data_mode: "fixtures" | "synthetic" | "real";
  generated_utc: UTC;
  sources: string[];                       // e.g. ["LOLA LDEM 20 m/px (synthetic stand-in)"]
}

interface LatLon { lat_deg: number; lon_deg: number; }

interface TerrainSummary {                 // P2 produces (region & zone level)
  elevation_mean_m: number;
  elevation_min_m: number;
  elevation_max_m: number;
  slope_mean_deg: number;
  slope_max_deg: number;
  slope_p95_deg: number;
  roughness_rms_m: number;                 // RMS of detrended heights over ROUGHNESS_BASELINE_M (default 25 m)
  crater_density_per_km2: number;          // craters ≥ CRATER_MIN_DIAMETER_M (default 10 m)
  boulder_density_per_km2: number | null;  // null = no data
  safe_area_pct: number;                   // % of cells passing the slope+roughness masks
  surface_description: string;             // short text, e.g. "Ridge crest, gentle slopes, few small craters"
}

interface IlluminationSummary {            // P3 produces (any level)
  window_start_utc: UTC;
  window_end_utc: UTC;
  illumination_pct: number;                // % of window with Sun (disk centre) above local horizon
  longest_shadow_h: number;                // longest continuous dark period in window
  sunlit_at_arrival: boolean;
  sun_azimuth_deg_at_arrival: number;
  sun_elevation_deg_at_arrival: number;
  earth_visibility_pct: number;            // % of window with Earth above local horizon
  earth_visible_at_arrival: boolean;
  earth_azimuth_deg_at_arrival: number;
  earth_elevation_deg_at_arrival: number;
  method: "horizon_mask" | "smooth_sphere" | "fixture";
}

interface PreliminarySuitability {         // P4 produces (region level)
  score: number;                           // 0–100
  label: "high" | "medium" | "low";
  notes: string[];
}

interface Explanation {                    // P4 produces
  summary: string;                         // 2–4 sentences, why the winner wins
  bullets: string[];
  per_candidate: Record<string, { strengths: string[]; weaknesses: string[] }>;
  generated_by: "template" | "llm";
}
```

### 7.2 Layer 1 — Mission

```ts
// POST /api/v1/mission/plan
interface MissionPlanRequest {
  arrival_utc: UTC;
  transfer_days?: number;                  // default 4.0
}

interface TimedPosition { t_utc: UTC; pos_km: [number, number, number]; }   // J2000 Earth-centred

interface MissionPlan {
  meta: Meta;
  arrival_utc: UTC;
  launch_utc: UTC;
  transfer_duration_h: number;
  interception_window: { start_utc: UTC; end_utc: UTC };
  earth_moon_distance_km: number;          // centre to centre at arrival
  frame: "J2000_ECI";
  moon_track: TimedPosition[];             // Moon from launch−1 day to arrival+1 day, ≤ 1 h step
  trajectory: TimedPosition[];             // spacecraft from launch to arrival, ≥ 100 samples
  sun_direction_eci: [number, number, number];  // unit vector Earth→Sun at arrival (for scene lighting)
  parameters: { key: string; label: string; value: number | string; unit: string }[];  // extra rows for info panel
}
```
The trajectory is an **approximate, visual** transfer (patched-conic / Lambert-style), not a flight-dynamics product. That is stated in the methodology.

### 7.3 Layer 2 — Regions

```ts
// GET /api/v1/regions?arrival_utc=...
type RegionCollection = { meta: Meta } & GeoJSON.FeatureCollection<GeoJSON.Polygon, RegionProperties>;

interface RegionProperties {
  id: string;                              // "REG-01"
  name: string;                            // "Connecting Ridge"
  center: LatLon;
  area_km2: number;
  terrain: TerrainSummary;
  illumination: IlluminationSummary | null;   // null only if arrival_utc omitted
  suitability: PreliminarySuitability;
}

// GET /api/v1/regions/{region_id}?arrival_utc=...
// → { meta, region: GeoJSON.Feature<Polygon, RegionProperties> }

// GET /api/v1/terrain/heightmap?area_id=REG-01&max_size=256
interface Heightmap {
  meta: Meta;
  area_id: string;
  crs: "moon_south_polar_stereo";          // projection in §6.2
  bbox_m: { xmin: number; ymin: number; xmax: number; ymax: number };
  width: number; height: number;           // ≤ max_size
  resolution_m: number;
  elevation_min_m: number; elevation_max_m: number;
  encoding: "float32_base64";              // row-major, row 0 = ymax (GeoTIFF order), little-endian
  nodata_value: number;                    // -32768
  data: string;
}
```

### 7.4 Layer 3 — Zones and evaluation

```ts
// GET /api/v1/regions/{region_id}/zones?arrival_utc=...
type ZoneCollection = { meta: Meta } & GeoJSON.FeatureCollection<GeoJSON.Polygon, ZoneProperties>;

interface ZoneProperties {
  id: string;                              // "REG-01-Z03"
  region_id: string;
  name: string;                            // "Zone 3"
  center: LatLon;
  area_km2: number;
  terrain: TerrainSummary;
  illumination: IlluminationSummary;
}

// GET /api/v1/criteria
interface Criterion {
  id: string;                              // "slope_mean"
  label: string;                           // "Average slope"
  source_field: string;                    // dotted path into the candidate, e.g. "terrain.slope_mean_deg"
  unit: string;                            // "deg"
  direction: "lower_is_better" | "higher_is_better";
  levels: ("zone" | "point")[];
  default_weight: { zone?: number; point?: number };   // weights per level sum to 1
  normalization: { type: "linear"; best: number; worst: number };   // clipped to [0,1]
  hard_limit: { op: "<=" | ">="; value: number } | null;            // violates → not eligible
}
// → { meta, criteria: Criterion[] }

// POST /api/v1/evaluate/zones
interface ZoneEvaluationRequest {
  arrival_utc: UTC;
  region_id: string;
  zone_ids: [string, string, string];      // exactly 3, else HTTP 422
  weights?: Record<string, number>;        // optional override; renormalized to sum 1
  method?: "weighted_sum" | "topsis";      // default "weighted_sum"
}

interface CriterionScore {
  criterion_id: string;
  raw_value: number | null;
  unit: string;
  normalized: number;                      // 0–1, 1 = best
  weight: number;
  contribution: number;                    // weight × normalized × 100
  passes_hard_limit: boolean;
}

interface CandidateScore {
  id: string;
  rank: number;                            // 1 = best; ineligible candidates ranked after eligible ones
  score: number;                           // 0–100
  eligible: boolean;
  disqualifiers: string[];                 // "slope_max 16.2 deg > limit 15 deg"
  criteria: CriterionScore[];
}

interface Evaluation {                     // same shape for zones and points
  meta: Meta;
  level: "zone" | "point";
  method: "weighted_sum" | "topsis";
  weights_used: Record<string, number>;
  candidates: CandidateScore[];            // sorted by rank
  recommended_id: string | null;           // null if nothing eligible
  sensitivity: { stable: boolean; winner_share_pct: number; notes: string };
       // winner_share_pct = % of random weight perturbations (±20%) where the winner stays #1
  explanation: Explanation;
}
// POST /evaluate/zones → Evaluation (level = "zone")
```

### 7.5 Layer 4 — Points

```ts
// GET /api/v1/zones/{zone_id}/points?arrival_utc=...&n=10
interface PointProperties {
  id: string;                              // "REG-01-Z03-P07"
  zone_id: string;
  lat_deg: number; lon_deg: number;
  x_m: number; y_m: number;                // polar stereo
  elevation_m: number;
  terrain_local: {
    slope_deg: number;                     // over LANDER_FOOTPRINT_M (default 20 m)
    roughness_rms_m: number;
    distance_to_nearest_crater_m: number;
    distance_to_nearest_hazard_m: number;
    nearest_hazard_type: "crater" | "steep_slope" | "boulder" | "shadow" | "other";
  };
  illumination: IlluminationSummary;       // method should be "horizon_mask" in synthetic/real modes
}

interface PointsResult {
  meta: Meta;
  zone_id: string;
  points: GeoJSON.FeatureCollection<GeoJSON.Point, PointProperties>;
  evaluation: Evaluation;                  // level = "point"; recommended_id = optimal point
}
```

### 7.6 Report

```ts
// POST /api/v1/report   → application/pdf
interface ReportRequest {
  mission: MissionPlan;
  region: RegionProperties;
  zones: ZoneProperties[];                 // the 3 compared
  zone_evaluation: Evaluation;
  points: PointsResult;
  screenshots?: { label: string; png_base64: string }[];   // canvas captures from the frontend
}
```
The report contains: mission configuration & dates, interception info, selected region, the 3 zones and their comparison, recommended zone, optimal coordinates, detailed parameters, and **data sources & methodology** (from `docs/methodology.md` + `meta.sources`).

### 7.7 Endpoint summary (`/api/v1`)

| Method | Path | Returns | Producer modules |
|---|---|---|---|
| GET | `/health` | `{status, data_mode, contract_version}` | P5 |
| POST | `/mission/plan` | `MissionPlan` | P3 |
| GET | `/criteria` | `{meta, criteria}` | P4 |
| GET | `/regions` | `RegionCollection` | P2 + P3 + P4 |
| GET | `/regions/{id}` | `{meta, region}` | P2 + P3 + P4 |
| GET | `/terrain/heightmap` | `Heightmap` | P2 |
| GET | `/regions/{id}/zones` | `ZoneCollection` | P2 + P3 |
| POST | `/evaluate/zones` | `Evaluation` | P4 |
| GET | `/zones/{id}/points` | `PointsResult` | P2 + P3 + P4 |
| POST | `/report` | PDF | P5 |
| GET | `/meta/methodology` | `{markdown, sources}` | P5 (from docs) |

Errors: `{ "error": { "code": "ZONE_COUNT", "message": "...", "details": {} } }` with HTTP 4xx/5xx.

### 7.8 Python module interfaces (in-process)

```python
# terrain (P2) — lunanav/terrain/__init__.py
def list_regions() -> list[RegionGeometry]                     # id, name, polygon (lon/lat), center, area
def region_terrain(region_id: str) -> TerrainSummary
def identify_zones(region_id: str, max_zones: int = 8) -> list[ZoneGeometryWithTerrain]
def identify_points(zone_id: str, n: int = 10) -> list[PointGeometryWithTerrain]
def get_heightmap(area_id: str, max_size: int = 256) -> Heightmap
# terrain.dem — read-only DEM access (used by P3 for horizons)
def sample_elevation(lat_deg: float, lon_deg: float) -> float
def dem_window(center: LatLon, radius_m: float) -> tuple[np.ndarray, Affine]   # polar-stereo grid

# astro (P3) — lunanav/astro/__init__.py
def plan_mission(arrival_utc: datetime, transfer_days: float = 4.0) -> MissionPlan
def sun_az_el(lat_deg, lon_deg, elevation_m, t_utc) -> tuple[float, float]
def earth_az_el(lat_deg, lon_deg, elevation_m, t_utc) -> tuple[float, float]
def horizon_mask(lat_deg, lon_deg, n_az: int = 360, max_dist_km: float = 100) -> np.ndarray  # elev angle per az bin
def illumination_at(lat_deg, lon_deg, elevation_m, arrival_utc, use_horizon: bool = True) -> IlluminationSummary
def illumination_area(samples: list[LatLon], arrival_utc) -> IlluminationSummary   # aggregate over sample points

# decision (P4) — lunanav/decision/__init__.py   (pure functions, no I/O except reading criteria config)
def get_criteria() -> list[Criterion]
def preliminary_suitability(terrain: TerrainSummary, illum: IlluminationSummary | None) -> PreliminarySuitability
def evaluate(candidates: list[Candidate], level: Literal["zone","point"],
             weights: dict[str, float] | None = None, method: str = "weighted_sum") -> Evaluation
def explain(evaluation: Evaluation, candidates: list[Candidate]) -> Explanation
```
`Candidate` = `{id, terrain | terrain_local, illumination}`; P4 reads values through `Criterion.source_field`.

---

## 8. Frontend state & navigation (P1, everyone should know it)

```ts
interface MissionState {
  layer: 1 | 2 | 3 | 4;
  arrivalUtc: string | null;
  missionPlan: MissionPlan | null;          // confirmed in L1
  selectedRegionId: string | null;          // L2
  zoneSelection: string[];                  // L3, max 3, order of clicking
  zoneEvaluation: Evaluation | null;        // L3
  pointsResult: PointsResult | null;        // L4
  selectedPointId: string | null;           // L4
}
```
- Going **back** never clears anything.
- Changing an **upstream input** clears only what depends on it: new `arrivalUtc` → clears `missionPlan`, `zoneEvaluation`, `pointsResult` (keeps region + zone selection, re-fetches). New region → clears zone selection and everything after.
- State persisted to `sessionStorage` so a refresh does not lose progress.

---

## 9. Mock-data plan

The point: **nobody waits for anybody, and nobody waits for the datasets.**

| Stage | When | What exists | Who |
|---|---|---|---|
| **Fixtures** | Prep (before kickoff) | Hand-written JSON in `mock_data/` for every endpoint, validated by the Pydantic models. 6 regions, 6–8 zones in each of 2 regions, 10 points in 2 zones. API runs in `fixtures` mode. | P5 writes, owners review their parts |
| **Synthetic** | Prep → Day 1 morning | `scripts/terrain/make_synthetic_dem.py` builds a south-polar stereographic GeoTIFF (e.g. 20 m/px, ~300×300 km around the pole) from fractal noise + crater bowls + ridges. Whole pipeline (slope → zones → points → illumination with horizons → scoring) runs on it. | P2 builds DEM; P3, P4 run on it; P5 wires `synthetic` mode |
| **Real** | As soon as datasets are released | Replace the GeoTIFF path / kernel paths in config, rerun `scripts/precompute.py`. | P2 + P3 lead, P5 verifies |

Mock content guidance:
- Region names can follow well-known south-pole sites (e.g. Shackleton rim, Connecting Ridge, de Gerlache rim, Malapert massif, Nobile rim, Haworth) but **coordinates in fixtures are placeholders** until checked against real data. Mark them `"sources": ["placeholder"]`.
- Fixtures must be **plausible and varied** so the UI and scoring show real differences: slopes 2–20°, illumination 20–90 %, Earth visibility 0–100 %, at least one zone that fails a hard limit, one zone pair with close scores.
- Likely real datasets (to be confirmed by the challenge): LOLA south-polar DEMs (GeoTIFF, 5–20 m/px), LOLA-derived slope/roughness maps, illumination/average-sunlight maps, LROC imagery, NAIF SPICE kernels for ephemerides. Whatever arrives, it gets converted into our projection/units in preprocessing, not in the business logic.

---

## 10. Collaboration rules

- **Branches:** `main` is always demo-able. Work on `p1/<topic>`, `p2/<topic>`… Small PRs, merge often.
- **Reviews:** P5 reviews everything that touches `api/`, `schemas/`, `contracts/`, `mock_data/`. Owners review changes in their folder.
- **Contract changes** (anything in §6–§7): open a PR labelled `contract` that updates **together** the Pydantic model, `contracts/openapi.json`, the fixtures, `contracts/CHANGELOG.md` and bumps `CONTRACT_VERSION`. Every affected owner approves. Adding an optional field = minor bump; renaming/removing = needs team agreement in chat first.
- **Don't edit another person's folder.** Open an issue or ping them. Exception: P5 may fix imports/wiring.
- **CI must stay green:** ruff, pytest, fixture validation, OpenAPI drift check (`openapi.json` matches the code), frontend typecheck + vitest + build.
- **Agents:** each of us pastes their `docs/agents/AGENT_Px_*.md` into their coding agent and tells it to read this README first. Agents must not change contracts on their own; they propose the change and stop.
- **Decisions** go into `docs/decisions.md` in one line: date, decision, who.

---

## 11. Milestones

| # | Milestone | Done when | Owner of the check |
|---|---|---|---|
| **M0** | Skeleton & contracts frozen v0.1 (prep, before kickoff) | Repo exists with the structure above; Pydantic schemas + fixtures merged; API serves fixtures; frontend shows L1 with fixture data; coord test vectors exist | P5 |
| **M1** | Walking skeleton, all 4 layers on fixtures | A user can click through L1 → L4 and download a (rough) PDF, all on fixtures | P1 + P5 |
| **M2** | Science on synthetic data | `synthetic` mode: real slope/zone/point generation (P2), real ephemeris + illumination with horizons (P3), real scoring + template explanations (P4) | P2, P3, P4 |
| **M3** | Real data in | Challenge datasets preprocessed into our projection; precompute run; numbers sanity-checked against known sites | P2 + P3, P5 verifies |
| **M4** | Polish | Camera transitions, charts, explanation texts (optional LLM), full PDF, deployed URL | P1, P4, P5 |
| **M5** | Freeze & demo | Feature freeze ~3 h before submission; demo script rehearsed; README + methodology final; video/screenshots | everyone |

Suggested timing for the challenge days: **Day 1** morning M2 → afternoon M3 → evening start M4. **Day 2** M4 → freeze → M5.

---

## 12. Open questions (resolve when the challenge statement / data is out)

1. Which datasets and resolutions are provided, and over what area? (drives DEM resolution and caching)
2. Does the challenge specify landing criteria/thresholds (max slope, min illumination, comms)? If yes, they replace our defaults in `criteria.json`.
3. Predefined regions: use the challenge's list if given, else our 6.
4. Is boulder data available? If not, `boulder_density_per_km2 = null` and its weight is redistributed.
5. Deployment target and demo format (live URL vs video).
