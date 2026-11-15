# Decisions log

Date | Decision | Owner
--- | --- | ---
2026-11-14 | Verdict rule = README default thresholds (not_viable checked first) | P4
2026-11-14 | Verdict thresholds stay team assumptions (solar lander, ~4 d battery, direct-to-Earth), shown in UI | P4
2026-11-14 | Missing/invalid metrics raise DecisionInputError, never read as favorable | P4
2026-11-14 | Optional ranking (WSM + TOPSIS, min-max normalization, science/engineering weights, sensitivity) lives in decision/ranking.py; pending team confirmation | P4
2026-11-14 | Time to sunset at landing not used as a criterion (not in `metrics`; would need a contract change) | P4
