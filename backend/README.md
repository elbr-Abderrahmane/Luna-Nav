# LunaNav Backend — Unified FastAPI & Scientific Engine (P2 + P3 + P4 + P5)

This directory contains the unified Python backend for **LunaNav** (NASA Space Apps 2026 "Lunar Landing Site Navigator"), integrating all scientific and engineering modules into a single FastAPI application (`app.main:app`).

---

## Architecture & Module Ownership

```text
backend/
├── app/                        # P5 — FastAPI Application & Service Layer
│   ├── main.py                 # FastAPI entrypoint, CORS, startup ephemeris/DEM checks
│   ├── api/                    # REST API routers
│   │   ├── sites.py            # GET /api/sites, GET /api/sites/{id}
│   │   ├── scenarios.py        # POST /api/scenarios/{conditions,timeline,compare,date-sweep,rank}
│   │   ├── terrain.py          # GET /api/terrain/{inspect,coverage,elevation,heightmap,metrics}
│   │   ├── explainers.py       # GET /api/explainers, GET /api/explainers/{id}
│   │   ├── export.py           # POST /api/export (CSV & JSON)
│   │   ├── health.py           # GET /health, GET /api/health
│   │   ├── mission.py          # Legacy /api/mission/plan
│   │   ├── regions.py          # Legacy /api/regions
│   │   ├── zones.py            # Legacy /api/zones
│   │   ├── points.py           # Legacy /api/points
│   │   └── reports.py          # Legacy /api/reports (PDF generation)
│   ├── core/
│   │   ├── config.py           # Environment & path configuration
│   │   ├── cache.py            # Deterministic SHA-256 disk cache (data/cache/scenarios/)
│   │   └── logging_config.py   # Structured logging
│   ├── models/
│   │   └── scenarios.py        # Pydantic v2 schemas for the 5-screen scenario flow
│   └── services/
│       ├── scenario_service.py # Orchestrates P3 -> P4 -> P2 + disk caching + CSV/JSON export
│       └── explainer_service.py# Serves P4's markdown explainers (docs/explainers/*.md)
├── lunanav/                    # Scientific Core Package
│   ├── coords.py               # P2 — Lunar coordinate transforms & south-pole stereographic projection
│   ├── terrain/                # P2 — LOLA DEM reader, heightmap clipping, Horn slope & roughness
│   ├── astro/                  # P3 — SPICE/analytic ephemeris, topocentric geometry, horizon mask, scenarios
│   └── decision/               # P4 — Rule-based viability verdict, WSM/TOPSIS ranking, sensitivity & explainers
└── tests/                      # 174-test unified pytest suite
    ├── astro/                  # P3 astronomy & ephemeris unit tests
    ├── terrain/                # P2 coordinates, DEM, heightmap & slope unit tests
    ├── decision/               # P4 verdict, ranking & explanation unit tests
    ├── test_scenarios_api.py   # P5 full-stack scenario API integration tests
    └── test_*.py               # P5 legacy API & adapter tests
```

---

## Quick Start

### 1. Install Dependencies
```bash
python3 -m pip install -r backend/requirements.txt
```

### 2. Optional: Fetch NASA NAIF SPICE Kernels
Without kernels, `lunanav.astro` automatically falls back to its built-in analytic ephemeris and labels outputs accordingly. To use exact JPL DE440s + `MOON_ME` SPICE ephemerides:
```bash
PYTHONPATH=backend python3 scripts/astro/fetch_kernels.py
```

### 3. Start the API Server
```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 4. Run the Full Test Suite (174 Tests)
```bash
cd backend
python3 -m pytest -v
```

---

## REST API Endpoints Summary

| Method | Endpoint | Screen / Module | Description |
|---|---|---|---|
| `GET` | `/api/health` | System (P5) | Service health, ephemeris backend, and DEM status |
| `GET` | `/api/sites` | Screen 1 (P3) | List the 26 curated lunar landing sites (optional `?category=`) |
| `GET` | `/api/sites/{id}` | Screen 1 (P3) | Get a single catalog site by ID |
| `POST` | `/api/scenarios/conditions` | Screen 2 (P3+P4+P2) | Instantaneous geometry, countdowns, windows, metrics, P4 verdict & P2 terrain |
| `POST` | `/api/scenarios/timeline` | Screen 3 (P3+P4) | Full lunar-day time series + 360-azimuth skyline profile + P4 verdict |
| `POST` | `/api/scenarios/compare` | Screen 4 (P3+P4) | Side-by-side comparison of 1–12 scenarios + P4 verdicts, explanation & ranking |
| `POST` | `/api/scenarios/date-sweep` | Screen 5 (P3+P4) | 12-lunar-day seasonal sweep for a site + P4 verdicts & seasonal summary |
| `POST` | `/api/scenarios/rank` | Decision (P4) | Multi-criteria WSM + TOPSIS ranking and Monte-Carlo weight sensitivity |
| `GET` | `/api/terrain/inspect` | Terrain (P2) | LOLA south-pole DEM raster metadata & availability |
| `GET` | `/api/terrain/coverage` | Terrain (P2) | Nominal (`80°S–90°S`) and raster coverage check for `(lat_deg, lon_deg)` |
| `GET` | `/api/terrain/elevation` | Terrain (P2) | Sample elevation in metres above the 1737.4 km reference sphere |
| `GET` | `/api/terrain/heightmap` | Terrain (P2) | Clipped local square DEM heightmap (`null` for NoData) |
| `GET` | `/api/terrain/metrics` | Terrain (P2) | Local 3x3 Horn slope (`deg`), roughness (`m`), and elevation stats |
| `GET` | `/api/explainers` | Explainers (P4) | List all 5 public educational explainers |
| `GET` | `/api/explainers/{id}` | Explainers (P4) | Retrieve a single explainer (`sunlight`, `earth_visibility`, `lunar_day`, `lunar_libration`, `verdicts`) |
| `POST` | `/api/export` | Export (P5) | Export a scenario comparison as downloadable CSV or JSON |
