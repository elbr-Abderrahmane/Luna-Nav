# LUNA NAV — Backend & Integration Foundation

Modular Python + FastAPI backend foundation for **LUNA NAV** (NASA Lunar Landing Site Navigator).

Built for **Person 5 (Backend & Integration)** to run independently with validated `MOCK` / `SIMULATED` datasets and clean adapter boundaries while awaiting final technical specifications from:
- **Person 1**: Frontend & 3D Visualization
- **Person 2**: Terrain Analysis & GIS
- **Person 3**: Astronomy & Orbital Mechanics
- **Person 4**: Decision Engine & Optimization

---

## 1. Project Structure

```text
backend/
├── app/
│   ├── main.py                      # FastAPI application factory, CORS, /health, router registration
│   ├── api/                         # Provisional REST API route handlers (Layers 1–4)
│   │   ├── mission.py               # POST /api/mission/configure, GET /api/mission/{mission_id}
│   │   ├── regions.py               # GET /api/regions, GET /api/regions/{region_id}
│   │   ├── zones.py                 # GET /api/regions/{region_id}/zones, POST /api/zones/compare
│   │   ├── points.py                # GET /api/zones/{zone_id}/points, POST /api/points/evaluate
│   │   └── reports.py               # POST /api/reports/generate, GET /api/reports/{report_id}
│   ├── models/                      # Strict Pydantic v2 validation schemas
│   │   ├── common.py                # Measurement (with UNAVAILABLE support), GeoJSON, SimulationBanner
│   │   ├── mission.py               # Layer 1 mission & trajectory models
│   │   ├── region.py                # Layer 2 South Pole region models
│   │   ├── zone.py                  # Layer 3 landing-zone polygon & 3-zone comparison models
│   │   ├── point.py                 # Layer 4 candidate touchdown point & evaluation models
│   │   └── report.py                # Layer 4 PDF report request & metadata models
│   ├── services/                    # Business orchestration layer (independent of scientific formulas)
│   │   ├── mission_service.py       # Mission Service
│   │   ├── region_service.py        # Region Service
│   │   ├── terrain_service.py       # Terrain Service
│   │   ├── astronomy_service.py     # Astronomy Service
│   │   ├── decision_service.py      # Decision Service
│   │   └── report_service.py        # Report Service (ReportLab PDF template generator)
│   ├── integrations/                # Adapter boundaries for teammates' modules
│   │   ├── frontend_adapter.py      # Person 1 presentation adapter
│   │   ├── terrain_adapter.py       # Person 2 GIS & Terrain adapter interface + MockTerrainAdapter
│   │   ├── astronomy_adapter.py     # Person 3 Astronomy adapter interface + MockAstronomyAdapter
│   │   └── decision_adapter.py      # Person 4 Decision Engine adapter interface + MockDecisionAdapter
│   ├── mock_data/                   # Structural JSON & GeoJSON mock fixtures
│   │   ├── regions.json             # 3 Lunar South Pole regions (MOCK)
│   │   ├── zones.json               # Candidate landing-zone polygons (MOCK)
│   │   └── points.json              # Candidate landing points (MOCK)
│   └── core/
│       ├── config.py                # Environment settings & structured Python logging
│       └── exceptions.py            # Domain exceptions & unified JSON error handlers
├── tests/                           # Automated pytest suite
│   ├── conftest.py
│   ├── test_health_and_mission.py
│   ├── test_regions_and_zones.py
│   ├── test_points_and_reports.py
│   └── test_validation_and_adapters.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 2. Installation

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

*(If running in an environment where packages are already installed globally/user-level, you can run `uvicorn` and `pytest` directly.)*

---

## 3. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment variables:
- `LUNA_ENV`: `development` (default) or `production`
- `LUNA_LOG_LEVEL`: `INFO`, `DEBUG`, `WARNING`, `ERROR`
- `LUNA_CORS_ORIGINS`: Comma-separated list of allowed frontend origins for Person 1
- `USE_MOCK_TERRAIN`: `true` (uses `MockTerrainAdapter`) or `false` (`RealTerrainAdapterStub`)
- `USE_MOCK_ASTRONOMY`: `true` (uses `MockAstronomyAdapter`) or `false` (`RealAstronomyAdapterStub`)
- `USE_MOCK_DECISION`: `true` (uses `MockDecisionAdapter`) or `false` (`RealDecisionAdapterStub`)

---

## 4. Running the Backend

From the `backend/` directory:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 5. Swagger & ReDoc Documentation

Once the server is running, inspect and test all endpoints interactively:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 6. Provisional API Endpoints

| Layer | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| System | `GET` | `/health` | Health status and active adapter mode (`MOCK` vs `REAL_STUB`) |
| Layer 1 | `POST` | `/api/mission/configure` | Configure mission arrival date & compute simulated interception |
| Layer 1 | `GET` | `/api/mission/{mission_id}` | Retrieve configured mission by ID (includes `msn-default-mock`) |
| Layer 2 | `GET` | `/api/regions` | List Lunar South Pole exploration regions and GeoJSON boundaries |
| Layer 2 | `GET` | `/api/regions/{region_id}` | Get specific South Pole region details |
| Layer 3 | `GET` | `/api/regions/{region_id}/zones` | List candidate landing-zone polygons inside a region |
| Layer 3 | `POST` | `/api/zones/compare` | Compare & rank **exactly 3** distinct landing zones in a region |
| Layer 4 | `GET` | `/api/zones/{zone_id}/points` | List candidate landing-point markers inside a zone |
| Layer 4 | `POST` | `/api/points/evaluate` | Evaluate candidate landing points (or custom coordinates) |
| Layer 4 | `POST` | `/api/reports/generate` | Generate a provisional mission PDF report |
| Layer 4 | `GET` | `/api/reports/{report_id}` | Get report JSON metadata (or download PDF via `?format=pdf`) |

---

## 7. Testing

Run the automated test suite from the `backend/` directory:

```bash
pytest -v
```

---

## 8. Mock-Data Limitations & Missing-Data Policy

1. **All current data is `MOCK` / `SIMULATED`**: Every API response includes a `simulation_banner` (`is_simulated: true`) and every generated PDF report displays a prominent `MOCK / SIMULATED DATA ONLY` header. No numbers in `app/mock_data/` represent validated NASA LRO/LOLA observations.
2. **Missing scientific data is never treated as zero**: When a parameter is unmeasured (for example, `boulder_density` in `zone-shackleton-beta`, `nearest_obstacle_distance` in `pt-shackleton-a2`, or `solar_sub_longitude` in `MockAstronomyAdapter`), it is represented as:
   ```json
   {
     "value": null,
     "unit": "boulders/km^2",
     "status": "UNAVAILABLE",
     "note": "UNAVAILABLE: High-resolution boulder count not available..."
   }
   ```
   Pydantic validation actively rejects any attempt to pair `status: "UNAVAILABLE"` with a numeric value like `0.0`.

---

## 9. How to Replace Mock Adapters with Real Scientific Modules

When Persons 2, 3, and 4 deliver their technical specification READMEs and Python packages:

1. **Person 2 (Terrain Analysis & GIS)**:
   - Open `app/integrations/terrain_adapter.py`.
   - Implement the methods on `RealTerrainAdapterStub` (or rename to `RealTerrainAdapter`) by calling Person 2's functions and mapping their output into `RegionModel`, `LandingZoneModel`, and `LandingPointModel`.
   - Set `USE_MOCK_TERRAIN=false` in `.env`.
2. **Person 3 (Astronomy & Orbital Mechanics)**:
   - Open `app/integrations/astronomy_adapter.py`.
   - Wire Person 3's ephemeris/trajectory, solar illumination, and Earth visibility functions inside `RealAstronomyAdapterStub`.
   - Set `USE_MOCK_ASTRONOMY=false` in `.env`.
3. **Person 4 (Decision Engine & Optimization)**:
   - Open `app/integrations/decision_adapter.py`.
   - Wire Person 4's multi-criteria ranking functions inside `RealDecisionAdapterStub.evaluate_three_zones` and `evaluate_landing_points`.
   - Set `USE_MOCK_DECISION=false` in `.env`.
4. **Person 1 (Frontend & 3D Visualization)**:
   - Open `app/integrations/frontend_adapter.py` and `app/models/` if any response envelope fields or 3D coordinate frames need adjustment.
