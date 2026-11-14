# Agent brief — P4 Decision Engine & AI (LunaNav)

You are the coding agent for **P4, Decision Engine & AI** on LunaNav, a 5-person NASA challenge team building a
lunar South Pole landing-site selection app. Before writing any code, **read `README.md` at the repo root
completely**. It is the source of truth for contracts, conventions and folder ownership. If this brief and the
README disagree, the README wins.

## Your scope
- You own `backend/lunanav/decision/`, `backend/tests/decision/`, `mock_data/criteria.json` (content), and the
  scoring section of `docs/methodology.md`.
- Stack: Python 3.11, numpy, pytest. Optional LLM client for explanations (behind a flag).
- **Your module is pure**: metrics in → scores out. No file I/O except reading the criteria config, no terrain or astronomy computations, imports only `lunanav.schemas`.

## Functions to provide (README §7.8)
```python
get_criteria() -> list[Criterion]
preliminary_suitability(terrain, illum | None) -> PreliminarySuitability      # L2
evaluate(candidates, level, weights=None, method="weighted_sum") -> Evaluation # L3 (3 zones) and L4 (n points)
explain(evaluation, candidates) -> Explanation
```

## Default criteria (put them in `criteria.json`; they are placeholders until the challenge states its own)
| id | source_field | dir | zone w | point w | normalization best → worst | hard limit |
|---|---|---|---|---|---|---|
| slope_mean | terrain.slope_mean_deg | lower | 0.20 | — | 2 → 15 | — |
| slope_max | terrain.slope_max_deg | lower | 0.10 | — | 5 → 25 | zone: ≤ 15 |
| slope_local | terrain_local.slope_deg | lower | — | 0.25 | 0 → 10 | point: ≤ 8 |
| roughness | terrain.roughness_rms_m / terrain_local.roughness_rms_m | lower | 0.15 | 0.15 | 0.1 → 1.0 | — |
| crater_density | terrain.crater_density_per_km2 | lower | 0.10 | — | 5 → 100 | — |
| boulder_density | terrain.boulder_density_per_km2 | lower | 0.05 | — | 0 → 50 | — |
| hazard_distance | terrain_local.distance_to_nearest_hazard_m | higher | — | 0.15 | 200 → 20 | point: ≥ 30 |
| illumination | illumination.illumination_pct | higher | 0.20 | 0.20 | 90 → 20 | ≥ 30 |
| longest_shadow | illumination.longest_shadow_h | lower | 0.05 | 0.10 | 0 → 72 | — |
| earth_visibility | illumination.earth_visibility_pct | higher | 0.15 | 0.15 | 100 → 0 | ≥ 10 |

Split `roughness` into two ids if one id per source_field is simpler. Weights per level must sum to 1.

## Algorithm
1. **Extract** raw values through `source_field`. Missing value (`null`, e.g. no boulder data) → drop that criterion for **all** candidates and renormalize weights; mention it in the explanation.
2. **Hard limits** → `eligible`, `passes_hard_limit`, human-readable `disqualifiers` ("slope_max 16.2 deg > limit 15 deg").
3. **Normalize** each criterion linearly between `best` and `worst`, clipped to [0, 1]. Use the **absolute** best/worst from config, not min/max of the 3 candidates, so scores are comparable across runs.
4. **Aggregate**: `weighted_sum` → `score = 100 × Σ w·n`. Also implement **TOPSIS** as `method="topsis"` (closeness × 100) so we can show we considered MCDA properly.
5. **Rank**: eligible first by score desc, then ineligible by score desc; ties broken by illumination, then slope. `recommended_id` = top eligible, or `null`.
6. **Sensitivity**: 500 random perturbations of the weights (each ×U(0.8, 1.2), renormalized, fixed seed); `winner_share_pct` = % where the winner stays #1; `stable = winner_share_pct ≥ 80`.
7. **Weights override** from the request: unknown ids → error; renormalize to sum 1.

`preliminary_suitability` for regions: same normalization with zone weights on region-level metrics, label `high ≥ 70`, `medium ≥ 45`, else `low`; `notes` = 1–3 short phrases.

## Explanations ("AI explanations")
- **Template first (required):** deterministic text built from the numbers: the winner, its margin over #2, the 2–3 criteria with the largest contribution gap, any disqualifiers, the sensitivity result. Per candidate: top 2 strengths and weaknesses. `generated_by = "template"`.
- **LLM (optional, M4):** if `LUNANAV_LLM_ENABLED=true` and an API key is set, send the `Evaluation` JSON and ask for a rewrite of the same facts in clearer prose. Rules: never introduce numbers not in the input, check that every number in the output exists in the input (else fall back to the template), timeout 10 s, model name from env. `generated_by = "llm"`.

## Mock-first plan
Your code needs no datasets: build and test on `mock_data/` fixtures and on small hand-made candidate lists from day 0. Write unit tests for: normalization edges, weights summing to 1, an ineligible candidate never ranked above an eligible one, null criterion handling, determinism (same input → same output), TOPSIS vs weighted sum agree on a dominated case, explanation mentions the winner and contains only input numbers.

## Conventions (summary, full text README §6–§7)
`score` 0–100, `normalized` 0–1 with 1 = best, `rank` 1 = best, `contribution = weight × normalized × 100`. Return Pydantic models from `lunanav.schemas`.

## Definition of done
pytest green, ruff clean, `evaluate` on 3 zones < 50 ms (excluding sensitivity < 300 ms), methodology section written (criteria table, formulas, why these weights, limitations).

## Contracts
Changing criteria values in `criteria.json` is yours. Changing the **shape** of `Criterion`, `Evaluation`, `Explanation` is a contract change: write the proposal and stop so a `contract` PR can go through P5.
