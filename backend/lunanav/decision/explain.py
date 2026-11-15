"""LunaNav - P4 : explications en langage simple (anglais, affichées par l'UI).

Aucun calcul astronomique : on met en mots des résultats déjà calculés.
"""
from __future__ import annotations

import math
from typing import Any

from .verdict import LEVELS, DecisionInputError, _fmt, verdict

LEVEL_MEANING = {
    "viable": "Viable: conditions are broadly favorable for power and direct-to-Earth communication.",
    "marginal": "Marginal: workable, but with constraints that need a plan (bigger battery, a relay, a different date).",
    "not_viable": "Not viable: at least one condition is unfavorable under our simplified criteria.",
}
_LEVEL_ORDER = {"viable": 0, "marginal": 1, "not_viable": 2}

# nom -> (libellé, unité, pourquoi c'est important)
METRIC_INFO = {
    "sunlight_pct": ("Sunlight", "%",
        "the share of the time the Sun is above the horizon. More sunlight means more solar power."),
    "longest_darkness_h": ("Longest night", "h",
        "the longest stretch without Sun. The battery and heaters must survive it."),
    "earth_visibility_pct": ("Earth visibility", "%",
        "the share of the time Earth is above the horizon, so direct radio contact is geometrically possible."),
    "longest_comms_gap_h": ("Longest comms gap", "h",
        "the longest stretch without Earth in view. Without a relay satellite, no direct contact during it."),
    "power_and_comms_pct": ("Power + comms together", "%",
        "the share of the time both Sun and Earth are up: the lander can be powered and talk to Earth."),
    "vertical_panel_energy_kwh_m2": ("Vertical panel energy", "kWh/m2",
        "the solar energy collected by a Sun-facing vertical panel over the window."),
}


def _num(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DecisionInputError(f"{name} must be a finite number, got {value!r}")
    return float(value)


def explain_metric(metric_name: str, value: float) -> str:
    """Explique une métrique avec son unité et son importance."""
    if metric_name not in METRIC_INFO:
        raise DecisionInputError(f"unknown metric: {metric_name!r}")
    v = _num(value, metric_name)
    label, unit, why = METRIC_INFO[metric_name]
    return f"{label}: {_fmt(v)} {unit}. This is {why}"


def explain_verdict(verdict_data: dict) -> str:
    """Explique un verdict : sens du niveau + résumé + raisons."""
    if not isinstance(verdict_data, dict) or verdict_data.get("level") not in LEVELS:
        raise DecisionInputError("verdict_data must be a dict with a valid 'level'")
    level = verdict_data["level"]
    parts = [LEVEL_MEANING[level]]
    if verdict_data.get("summary"):
        parts.append(str(verdict_data["summary"]))
    reasons = verdict_data.get("reasons") or []
    if reasons:
        label = "Why" if level != "viable" else "Because"
        parts.append(f"{label}: " + " ".join(reasons))
    parts.append("This is an indicative assessment under our simplified assumptions, not a NASA certification.")
    return " ".join(parts)


def _leaders(rows, key, best="max"):
    vals = [r["metrics"][key] for r in rows]
    target = max(vals) if best == "max" else min(vals)
    return [r["label"] for r in rows if r["metrics"][key] == target], target


def _names(labels):
    return labels[0] if len(labels) == 1 else f"{len(labels)} scenarios tie"


def explain_comparison(rows: list) -> str:
    """Compare plusieurs scénarios : niveaux, meilleur en soleil/communication, conclusion."""
    if not isinstance(rows, list) or not rows:
        raise DecisionInputError("rows must be a non-empty list")
    prepared = []
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or not isinstance(r.get("metrics"), dict):
            raise DecisionInputError(f"row {i} must be a dict with a 'metrics' dict")
        v = r.get("verdict") or verdict(r["metrics"])
        prepared.append({"label": r.get("label") or f"scenario-{i + 1}",
                         "metrics": r["metrics"], "level": v["level"]})
    n = len(prepared)
    counts = {lv: sum(1 for p in prepared if p["level"] == lv) for lv in LEVELS}
    out = [f"{n} scenario{'s' if n > 1 else ''} compared: {counts['viable']} viable, "
           f"{counts['marginal']} marginal, {counts['not_viable']} not viable."]

    if n > 1:
        sun, sun_v = _leaders(prepared, "sunlight_pct", "max")
        gap, gap_v = _leaders(prepared, "longest_comms_gap_h", "min")
        out.append(f"Most sunlight: {_names(sun)} ({_fmt(sun_v)} %).")
        out.append(f"Shortest comms gap: {_names(gap)} ({_fmt(gap_v)} h).")
        if not set(sun) & set(gap):
            out.append("No single scenario is best on both power and communications: it is a trade-off.")

    best_level = min((p["level"] for p in prepared), key=_LEVEL_ORDER.get)
    cands = [p for p in prepared if p["level"] == best_level]
    key = "power_and_comms_pct" if all("power_and_comms_pct" in p["metrics"] for p in cands) else "sunlight_pct"
    pick = max(cands, key=lambda p: p["metrics"][key])
    if best_level == "not_viable":
        out.append("No scenario meets the minimum conditions under our assumptions; "
                   "consider other sites or dates.")
    else:
        out.append(f"Best option under our assumptions: {pick['label']} ({best_level}).")
    return " ".join(out)


def explain_ranking(ranking: dict, sensitivity: dict | None = None) -> str:
    """Justifie un classement (rank_scenarios) et, si fourni, sa stabilité."""
    if not isinstance(ranking, dict) or not ranking.get("ranking"):
        raise DecisionInputError("ranking must be the output of rank_scenarios")
    top = ranking["ranking"][0]
    profile = ranking.get("profile", "custom")
    w = ranking.get("weights", {})
    main = sorted(w, key=w.get, reverse=True)[:2]
    names = " and ".join(ranking["criteria"][k]["label"].lower() for k in main) if main else "the criteria"
    out = [f"With the {profile} weights (most weight on {names}), "
           f"{top['label']} ranks first."]
    if top["verdict_level"] != "viable":
        out.append(f"Note: its verdict is {top['verdict_level']}, so ranking first only means "
                   "it is the best of the compared options, not that it is safe.")
    if sensitivity:
        share = sensitivity["random_weights"]["top_win_share_pct"].get(sensitivity["base_top"])
        msg = {"stable": "The result is stable: changing the weights does not change the winner.",
               "moderate": "The result is moderately stable: the winner changes for some weightings.",
               "sensitive": "The result is sensitive to the weights: treat the ranking with caution."}
        out.append(msg[sensitivity["stability"]])
        if share is not None:
            out.append(f"With random weights, {sensitivity['base_top']} wins {_fmt(share)} % of the time.")
        pc = sensitivity["profile_comparison"]
        out.append("Science and engineering weights agree on the winner." if pc["agree"]
                   else f"Science favors {pc['science_top']}, engineering favors {pc['engineering_top']}.")
    return " ".join(out)
