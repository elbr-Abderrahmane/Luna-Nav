# LunaNav — Architecture & Engineering Decisions

2026-11-14 | Pivot from 4-layer (trajectory -> region -> zone -> point) to 5-screen Scenario Flow (sites, conditions, timeline, compare, date-sweep) | Team
2026-11-14 | Verdict rule = README default thresholds (not_viable checked first) | P4
2026-11-14 | Verdict thresholds stay team assumptions (solar lander, ~4 d battery, direct-to-Earth), shown in UI | P4
2026-11-14 | Missing/invalid metrics raise DecisionInputError, never read as favorable | P4
2026-11-14 | Optional ranking (WSM + TOPSIS, min-max normalization, science/engineering weights, sensitivity) lives in decision/ranking.py; pending team confirmation | P4
2026-11-14 | Time to sunset at landing not used as a criterion (not in `metrics`; would need a contract change) | P4
2026-11-15 | Unified P2 (`lunanav.terrain.dem`) and P3 (`lunanav.astro.lola_dem`) DEM access so `horizon.py` uses `load_default()` while preserving P2's JSON-ready terrain helpers | P2 + P3 + P5
2026-11-15 | Integrated P1 (`frontend/`), P2 (`terrain/`, `coords.py`), P3 (`astro/`), P4 (`decision/`, `docs/explainers/`) and P5 (`backend/app/`) under `/api/*` | P5
