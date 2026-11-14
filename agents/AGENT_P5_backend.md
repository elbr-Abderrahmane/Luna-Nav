# Agent brief — P5 Backend & Integration (LunaNav)

You are the coding agent for **P5, Backend & Integration** on LunaNav, a 5-person NASA challenge team building a
lunar South Pole landing-site selection app. Before writing any code, **read `README.md` at the repo root
completely**. It is the source of truth for contracts, conventions and folder ownership. If this brief and the
README disagree, the README wins.

## Your scope
- You own: repo setup, `backend/lunanav/schemas/`, `backend/lunanav/api/`, `backend/lunanav/report/`,
  `backend/lunanav/config.py`, `mock_data/` (structure and validity), `contracts/` (openapi, CHANGELOG),
  `scripts/precompute.py`, `backend/tests/integration/`, `docker-compose.yml`, CI, deployment.
- Stack: Python 3.11, FastAPI, Pydantic v2, uvicorn, pytest + httpx, ruff, Jinja2 + WeasyPrint for PDF (reportlab as fallback if system libs are a problem), Docker, GitHub Actions.
- You are the **integrator and contract keeper**. You may fix imports/wiring in other modules; you do not rewrite their science.

## M0 — before kickoff (your critical path, everyone depends on it)
1. Create the repo with the exact structure in README §5, `.gitignore` (data/, kernels, node_modules, caches), branch protection on `main`.
2. Write **all Pydantic models** in `lunanav/schemas/` exactly as README §7 (names, fields, units, enums, `Meta` on every response). Use `Literal` for enums, `conlist(min_length=3, max_length=3)` for `zone_ids`, a validator that UTC strings end in `Z`.
3. `config.py`: constants of README §6.6 + env (`LUNANAV_DATA_MODE`, data/kernel paths, `LUNANAV_LLM_ENABLED`, CORS origins).
4. FastAPI app under `/api/v1` with all endpoints of README §7.7 working in **`fixtures` mode** (serve and filter `mock_data/` JSON; `evaluate/zones` can return the stored example, re-ranked for the requested ids).
5. Write the fixtures (README §9: 6 regions, 6–8 zones in 2 regions, 10 points in 2 zones, varied and plausible, one failing a hard limit). Ask P2/P3/P4 to review their parts.
6. Export `contracts/openapi.json` (`scripts/export_openapi.py`), start `contracts/CHANGELOG.md` at 0.1.0.
7. CI: ruff, pytest, **fixture validation** (every fixture parses into its model), **OpenAPI drift check** (exported spec == committed file), frontend typecheck/test/build.
8. `docker-compose.yml`: backend on :8000, frontend on :5173, `data/` mounted.

## M1–M2 — integration
- `api/services/pipeline.py` composes the modules (README §7.8):
  - regions = `terrain.list_regions` + `terrain.region_terrain` + `astro.illumination_area(samples)` + `decision.preliminary_suitability`
  - zones = `terrain.identify_zones` + `astro.illumination_area` per zone
  - evaluate/zones = load the 3 zones → `decision.evaluate(level="zone")` + `decision.explain`
  - points = `terrain.identify_points` + `astro.illumination_at` per point → `decision.evaluate(level="point")`
- Sample points for area illumination: a grid of 9–25 points inside the polygon (shapely), deterministic.
- `synthetic` and `real` modes go through the pipeline; `fixtures` mode bypasses it. Mode reported in `meta.data_mode` and `/health`.
- Disk cache under `data/cache/` keyed by `(object_id, arrival date, data_mode, CONTRACT_VERSION)`. `scripts/precompute.py` warms it for all regions/zones for a given arrival date.
- Error shape `{error:{code,message,details}}`; 422 for wrong zone count, 404 for unknown ids, 503 with a clear message if data files are missing.
- Integration tests: every endpoint returns a valid model in each mode; L1 → L4 end-to-end happy path; contract test that `meta.contract_version == CONTRACT_VERSION`.

## Report (L4)
`POST /report` builds an HTML from a Jinja2 template and renders a PDF: title page (mission + arrival), interception info, selected region, the 3 zones table + score chart (matplotlib PNG) + explanation, recommended zone, **optimal coordinates in big type**, point parameters, screenshots from the frontend, data sources & methodology (`docs/methodology.md` + `meta.sources`), generation time and data mode.

## Deployment & coordination
- Deploy backend (container on Render/Railway/Fly or similar) and frontend (static host) by M4; keep a fallback: the frontend in fixtures mode as a static build that works offline for the demo.
- Run the `contract` PR process (README §10): every change updates model + openapi + fixtures + CHANGELOG + version together, with affected owners approving.
- Keep `docs/decisions.md` and the milestone table up to date; post a short status in team chat at each milestone.

## Definition of done
`docker compose up` gives a working app; CI green; all endpoints documented in `/docs` (Swagger); fixtures valid; demo path L1 → L4 → PDF works in fixtures mode at any time.

## Contracts
You implement contract changes but you do not decide them alone: get agreement from the affected owners first.
