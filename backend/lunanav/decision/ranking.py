"""LunaNav - P4 : classement multicritère (WSM + TOPSIS) et analyse de sensibilité.

COUCHE OPTIONNELLE, construite au-dessus du verdict. Module pur : il ne lit que
les `metrics` fournis par P3 et ne calcule aucune astronomie.

Important : un classement est RELATIF (A meilleur que B). Il ne dit pas si le
site est utilisable : c'est le rôle du verdict. Un scénario peut être 1er du
classement et quand même `not_viable`.
"""
from __future__ import annotations

import math
import random
from typing import Any

from .verdict import DecisionInputError, verdict

# ---------------------------------------------------------------------------
# 1. Critères : nom, unité, sens d'optimisation
# ---------------------------------------------------------------------------
CRITERIA: dict[str, dict[str, str]] = {
    "sunlight_pct": {"label": "Sunlight", "unit": "%", "direction": "max"},
    "longest_darkness_h": {"label": "Longest night", "unit": "h", "direction": "min"},
    "earth_visibility_pct": {"label": "Earth visibility", "unit": "%", "direction": "max"},
    "longest_comms_gap_h": {"label": "Longest comms gap", "unit": "h", "direction": "min"},
    "power_and_comms_pct": {"label": "Power + comms together", "unit": "%", "direction": "max"},
    "vertical_panel_energy_kwh_m2": {"label": "Vertical panel energy", "unit": "kWh/m2", "direction": "max"},
}
_PERCENT = {"sunlight_pct", "earth_visibility_pct", "power_and_comms_pct"}

# ---------------------------------------------------------------------------
# 2. Profils de pondération (hypothèses d'équipe, somme = 1)
# ---------------------------------------------------------------------------
# science     : veut un maximum de temps productif (soleil, énergie, soleil+Terre ensemble)
# engineering : veut limiter les pires cas (nuit la plus longue, coupure radio la plus longue)
WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "science": {
        "sunlight_pct": 0.25, "longest_darkness_h": 0.10,
        "earth_visibility_pct": 0.15, "longest_comms_gap_h": 0.10,
        "power_and_comms_pct": 0.25, "vertical_panel_energy_kwh_m2": 0.15,
    },
    "engineering": {
        "sunlight_pct": 0.15, "longest_darkness_h": 0.25,
        "earth_visibility_pct": 0.10, "longest_comms_gap_h": 0.25,
        "power_and_comms_pct": 0.15, "vertical_panel_energy_kwh_m2": 0.10,
    },
}
METHODS = ("wsm", "topsis", "both")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _prepare_rows(rows: Any) -> tuple[list[str], list[dict], list[str]]:
    """Renvoie (labels, matrice de valeurs par critère, niveaux de verdict)."""
    if not isinstance(rows, list) or len(rows) < 2:
        raise DecisionInputError("ranking needs a list of at least 2 scenarios")
    labels: list[str] = []
    values: list[dict] = []
    levels: list[str] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("metrics"), dict):
            raise DecisionInputError(f"row {i} must be a dict with a 'metrics' dict")
        label = row.get("label") or f"scenario-{i + 1}"
        if label in labels:
            raise DecisionInputError(f"duplicate scenario label: {label!r}")
        metrics = row["metrics"]
        vals = {}
        for key in CRITERIA:
            v = metrics.get(key)
            if v is None or not _is_number(v) or v < 0 or (key in _PERCENT and v > 100):
                raise DecisionInputError(f"{label}: metric {key} is missing or invalid ({v!r})")
            vals[key] = float(v)
        v_level = (row.get("verdict") or {}).get("level") or verdict(metrics)["level"]
        labels.append(label)
        values.append(vals)
        levels.append(v_level)
    return labels, values, levels


def resolve_weights(profile: str = "engineering", weights: dict | None = None) -> dict[str, float]:
    """Poids personnalisés (prioritaires) ou profil, normalisés pour que la somme = 1."""
    if weights is None:
        if profile not in WEIGHT_PROFILES:
            raise DecisionInputError(f"unknown profile {profile!r} (use {sorted(WEIGHT_PROFILES)})")
        w = dict(WEIGHT_PROFILES[profile])
    else:
        unknown = set(weights) - set(CRITERIA)
        if unknown:
            raise DecisionInputError(f"unknown criteria in weights: {sorted(unknown)}")
        w = {k: float(weights.get(k, 0.0)) for k in CRITERIA}
        if any(not _is_number(x) or x < 0 for x in w.values()) or sum(w.values()) <= 0:
            raise DecisionInputError("weights must be numbers >= 0 with a positive sum")
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


# ---------------------------------------------------------------------------
# 3. Normalisation (min-max) : ramène chaque critère entre 0 (pire) et 1 (meilleur)
# ---------------------------------------------------------------------------
def normalize_minmax(values: list[dict]) -> list[dict]:
    """Benefit (max) : (x-min)/(max-min). Cost (min) : (max-x)/(max-min).
    Si tous les scénarios ont la même valeur, le critère ne départage personne : 1.0."""
    out = [dict() for _ in values]
    for key, spec in CRITERIA.items():
        col = [v[key] for v in values]
        lo, hi = min(col), max(col)
        for i, x in enumerate(col):
            if hi == lo:
                out[i][key] = 1.0
            elif spec["direction"] == "max":
                out[i][key] = (x - lo) / (hi - lo)
            else:
                out[i][key] = (hi - x) / (hi - lo)
    return out


# ---------------------------------------------------------------------------
# 4. WSM : somme pondérée
# ---------------------------------------------------------------------------
def wsm_scores(values: list[dict], weights: dict[str, float]) -> list[float]:
    norm = normalize_minmax(values)
    return [sum(weights[k] * n[k] for k in CRITERIA) for n in norm]


# ---------------------------------------------------------------------------
# 5. TOPSIS : proximité à la solution idéale
# ---------------------------------------------------------------------------
def topsis_scores(values: list[dict], weights: dict[str, float]) -> list[float]:
    n = len(values)
    # (a) normalisation vectorielle puis pondération
    weighted = [dict() for _ in range(n)]
    for key in CRITERIA:
        norm = math.sqrt(sum(v[key] ** 2 for v in values))
        for i in range(n):
            weighted[i][key] = (values[i][key] / norm * weights[key]) if norm else 0.0
    # (b) solution idéale (meilleure) et anti-idéale (pire) par critère
    ideal, anti = {}, {}
    for key, spec in CRITERIA.items():
        col = [w[key] for w in weighted]
        ideal[key] = max(col) if spec["direction"] == "max" else min(col)
        anti[key] = min(col) if spec["direction"] == "max" else max(col)
    # (c) distances et coefficient de proximité C = d- / (d+ + d-)
    scores = []
    for w in weighted:
        d_plus = math.sqrt(sum((w[k] - ideal[k]) ** 2 for k in CRITERIA))
        d_minus = math.sqrt(sum((w[k] - anti[k]) ** 2 for k in CRITERIA))
        denom = d_plus + d_minus
        scores.append(d_minus / denom if denom else 0.5)  # 0.5 = scénarios identiques
    return scores


def _ranks(scores: list[float]) -> list[int]:
    """Rang 1 = meilleur ; égalités partagent le rang (1, 2, 2, 4)."""
    order = sorted(scores, reverse=True)
    return [1 + sum(1 for o in order if o > s + 1e-9) for s in scores]


# ---------------------------------------------------------------------------
# 6. Classement de 2 à N scénarios
# ---------------------------------------------------------------------------
def rank_scenarios(rows: list[dict], profile: str = "engineering",
                   weights: dict | None = None, method: str = "both") -> dict:
    """Classe 2 à N scénarios. `rows` = lignes de compare_scenarios (label + metrics)."""
    if method not in METHODS:
        raise DecisionInputError(f"unknown method {method!r} (use {METHODS})")
    labels, values, levels = _prepare_rows(rows)
    w = resolve_weights(profile, weights)
    norm = normalize_minmax(values)
    wsm = wsm_scores(values, w) if method in ("wsm", "both") else None
    top = topsis_scores(values, w) if method in ("topsis", "both") else None
    wsm_r = _ranks(wsm) if wsm else None
    top_r = _ranks(top) if top else None

    out_rows = []
    for i, label in enumerate(labels):
        item = {"label": label, "verdict_level": levels[i],
                "normalized": {k: round(v, 4) for k, v in norm[i].items()}}
        if wsm:
            item.update(wsm_score=round(wsm[i], 4), wsm_rank=wsm_r[i])
        if top:
            item.update(topsis_score=round(top[i], 4), topsis_rank=top_r[i])
        out_rows.append(item)
    primary = "topsis_rank" if top else "wsm_rank"
    out_rows.sort(key=lambda r: r[primary])
    return {
        "method": method,
        "profile": "custom" if weights is not None else profile,
        "weights": {k: round(v, 4) for k, v in w.items()},
        "criteria": {k: dict(v) for k, v in CRITERIA.items()},
        "normalization": "min-max (WSM) / vector (TOPSIS)",
        "ranking": out_rows,
        "note": ("The ranking is relative. Check each scenario's verdict: the top-ranked "
                 "scenario can still be not_viable."),
    }


# ---------------------------------------------------------------------------
# 7. Analyse de sensibilité
# ---------------------------------------------------------------------------
def _order(rows, w, method) -> list[str]:
    _, values, _ = _prepare_rows(rows)
    s = topsis_scores(values, w) if method == "topsis" else wsm_scores(values, w)
    labels = [r.get("label") or f"scenario-{i + 1}" for i, r in enumerate(rows)]
    return [lab for _, lab in sorted(zip(s, labels), key=lambda p: -p[0])]


def sensitivity_analysis(rows: list[dict], profile: str = "engineering",
                         method: str = "topsis", delta: float = 0.25,
                         n_random: int = 200, seed: int = 42) -> dict:
    """Le classement change-t-il si les poids changent ?

    1) Un poids à la fois : chaque poids est multiplié par (1-delta) puis (1+delta),
       puis on renormalise. On regarde si le 1er change.
    2) Poids aléatoires (graine fixe, résultats reproductibles) : % de victoires du 1er.
    3) Science vs Engineering : ont-ils le même 1er ?
    Stabilité : stable si le 1er ne change jamais en (1) ET gagne >= 80 % en (2) ;
    moderate si >= 50 % ; sinon sensitive.
    """
    if method not in ("wsm", "topsis"):
        raise DecisionInputError("sensitivity method must be 'wsm' or 'topsis'")
    if not (0 < delta < 1):
        raise DecisionInputError("delta must be between 0 and 1")
    if not isinstance(n_random, int) or n_random < 0:
        raise DecisionInputError("n_random must be an integer >= 0")

    base_w = resolve_weights(profile)
    base_order = _order(rows, base_w, method)
    base_top = base_order[0]

    one_at_a_time = []
    for key in CRITERIA:
        for factor in (1 - delta, 1 + delta):
            w = dict(base_w)
            w[key] *= factor
            total = sum(w.values())
            w = {k: v / total for k, v in w.items()}
            order = _order(rows, w, method)
            one_at_a_time.append({
                "criterion": key, "weight_factor": round(factor, 3),
                "top": order[0], "top_changed": order[0] != base_top,
                "order": order,
            })
    top_never_changes = not any(p["top_changed"] for p in one_at_a_time)

    rng = random.Random(seed)
    wins = {lab: 0 for lab in base_order}
    for _ in range(n_random):
        raw = {k: rng.gammavariate(1.0, 1.0) for k in CRITERIA}  # poids aléatoires uniformes
        tot = sum(raw.values())
        wins[_order(rows, {k: v / tot for k, v in raw.items()}, method)[0]] += 1
    win_share = ({lab: round(100 * c / n_random, 1) for lab, c in wins.items()}
                 if n_random else {})

    sci = _order(rows, resolve_weights("science"), method)[0]
    eng = _order(rows, resolve_weights("engineering"), method)[0]

    top_share = win_share.get(base_top, 100.0 if not n_random else 0.0)
    if top_never_changes and top_share >= 80:
        stability = "stable"
    elif top_share >= 50:
        stability = "moderate"
    else:
        stability = "sensitive"
    return {
        "method": method, "profile": profile, "delta": delta,
        "base_order": base_order, "base_top": base_top,
        "one_at_a_time": one_at_a_time, "top_never_changes": top_never_changes,
        "random_weights": {"n": n_random, "seed": seed, "top_win_share_pct": win_share},
        "profile_comparison": {"science_top": sci, "engineering_top": eng, "agree": sci == eng},
        "stability": stability,
    }
