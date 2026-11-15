"""LunaNav - P4 : règle de verdict (viable / marginal / not_viable).

Module PUR : il reçoit un dictionnaire de métriques (fourni par P3) et renvoie
un verdict. Il n'importe ni astro/, ni terrain/, ni FastAPI, et ne calcule
aucun phénomène astronomique.

Les seuils décrivent un atterrisseur solaire avec ~4 jours de batterie et une
communication directe avec la Terre. Ce sont NOS hypothèses, pas une norme NASA.
"""
from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS: dict[str, float] = {
    "sunlight_pct_min": 60,
    "sunlight_pct_not_viable": 30,
    "longest_darkness_h_max": 50,
    "longest_darkness_h_not_viable": 100,
    "earth_visibility_pct_min": 50,
    "earth_visibility_pct_not_viable": 20,
    "longest_comms_gap_h_max": 72,
}

LEVELS = ("viable", "marginal", "not_viable")

REQUIRED_METRICS = (
    "sunlight_pct",
    "longest_darkness_h",
    "earth_visibility_pct",
    "longest_comms_gap_h",
)
_PERCENT_METRICS = {"sunlight_pct", "earth_visibility_pct"}


class DecisionInputError(ValueError):
    """Erreur contrôlée : données ou seuils invalides."""

    code = "INVALID_INPUT"


class InvalidMetricsError(DecisionInputError):
    code = "INVALID_METRICS"


class InvalidThresholdsError(DecisionInputError):
    code = "INVALID_THRESHOLDS"


# ---------------------------------------------------------------------------
# Outils internes
# ---------------------------------------------------------------------------
def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _fmt(x: float) -> str:
    """Nombre lisible : 346.898 -> '347', 53.27 -> '53.3', 100.0 -> '100'."""
    x = round(x) if x >= 100 else round(x, 1)
    return f"{x:g}"


# ---------------------------------------------------------------------------
# 1. Validation
# ---------------------------------------------------------------------------
def validate_metrics(metrics: Any) -> dict[str, float]:
    """Vérifie les 4 métriques nécessaires et renvoie une copie propre (floats).

    Une donnée manquante, None, non numérique, négative ou un pourcentage
    hors 0-100 déclenche InvalidMetricsError. Jamais d'interprétation
    silencieusement favorable.
    """
    if not isinstance(metrics, dict):
        raise InvalidMetricsError("metrics must be a dict")

    problems: list[str] = []
    clean: dict[str, float] = {}
    for key in REQUIRED_METRICS:
        value = metrics.get(key)
        if value is None:
            problems.append(f"{key} is missing or None")
        elif not _is_number(value):
            problems.append(f"{key} must be a finite number, got {value!r}")
        elif value < 0:
            problems.append(f"{key} must be >= 0, got {value}")
        elif key in _PERCENT_METRICS and value > 100:
            problems.append(f"{key} must be between 0 and 100, got {value}")
        else:
            clean[key] = float(value)
    if problems:
        raise InvalidMetricsError("; ".join(problems))
    return clean


_THRESHOLD_ALIASES: dict[str, str] = {
    "viable_sunlight_pct_min": "sunlight_pct_min",
    "not_viable_sunlight_pct_below": "sunlight_pct_not_viable",
    "viable_longest_darkness_h_max": "longest_darkness_h_max",
    "not_viable_longest_darkness_h_above": "longest_darkness_h_not_viable",
    "viable_earth_visibility_pct_min": "earth_visibility_pct_min",
    "not_viable_earth_visibility_pct_below": "earth_visibility_pct_not_viable",
    "viable_longest_comms_gap_h_max": "longest_comms_gap_h_max",
}


def resolve_thresholds(thresholds: dict | None = None) -> dict[str, float]:
    """Fusionne les seuils personnalisés avec les seuils par défaut et les vérifie."""
    merged = dict(DEFAULT_THRESHOLDS)
    if thresholds is not None:
        if not isinstance(thresholds, dict):
            raise InvalidThresholdsError("thresholds must be a dict or None")
        mapped: dict[str, Any] = {
            _THRESHOLD_ALIASES.get(k, k): v for k, v in thresholds.items()
        }
        unknown = sorted(set(mapped) - set(DEFAULT_THRESHOLDS))
        if unknown:
            raise InvalidThresholdsError(f"unknown threshold(s): {', '.join(unknown)}")
        for key, value in mapped.items():
            if not _is_number(value) or value < 0:
                raise InvalidThresholdsError(f"{key} must be a number >= 0, got {value!r}")
            merged[key] = value

    t = merged
    for pct_key in ("sunlight_pct_min", "sunlight_pct_not_viable",
                    "earth_visibility_pct_min", "earth_visibility_pct_not_viable"):
        if t[pct_key] > 100:
            raise InvalidThresholdsError(f"{pct_key} must be <= 100")
    # Cohérence : le seuil « not viable » doit être plus sévère que le seuil « viable ».
    if t["sunlight_pct_not_viable"] > t["sunlight_pct_min"]:
        raise InvalidThresholdsError("sunlight_pct_not_viable must be <= sunlight_pct_min")
    if t["earth_visibility_pct_not_viable"] > t["earth_visibility_pct_min"]:
        raise InvalidThresholdsError(
            "earth_visibility_pct_not_viable must be <= earth_visibility_pct_min")
    if t["longest_darkness_h_not_viable"] < t["longest_darkness_h_max"]:
        raise InvalidThresholdsError(
            "longest_darkness_h_not_viable must be >= longest_darkness_h_max")
    return merged


# ---------------------------------------------------------------------------
# 2. Conditions et raisons
# ---------------------------------------------------------------------------
def _not_viable_hits(m: dict, t: dict) -> list[str]:
    hits = []
    if m["longest_darkness_h"] > t["longest_darkness_h_not_viable"]:
        hits.append(
            f"Longest night is {_fmt(m['longest_darkness_h'])} h, above the "
            f"{_fmt(t['longest_darkness_h_not_viable'])} h hard limit.")
    if m["sunlight_pct"] < t["sunlight_pct_not_viable"]:
        hits.append(
            f"Sunlight is available only {_fmt(m['sunlight_pct'])} % of the time, below the "
            f"{_fmt(t['sunlight_pct_not_viable'])} % minimum.")
    if m["earth_visibility_pct"] < t["earth_visibility_pct_not_viable"]:
        if m["earth_visibility_pct"] == 0:
            hits.append("Earth is never visible from this site: a relay satellite would be required.")
        else:
            hits.append(
                f"Earth is visible only {_fmt(m['earth_visibility_pct'])} % of the time, below the "
                f"{_fmt(t['earth_visibility_pct_not_viable'])} % minimum.")
    return hits


def _viable_misses(m: dict, t: dict) -> list[str]:
    misses = []
    if m["sunlight_pct"] < t["sunlight_pct_min"]:
        misses.append(
            f"Sunlight is {_fmt(m['sunlight_pct'])} % of the time, below the "
            f"{_fmt(t['sunlight_pct_min'])} % target.")
    if m["longest_darkness_h"] > t["longest_darkness_h_max"]:
        misses.append(
            f"Longest night is {_fmt(m['longest_darkness_h'])} h, above the "
            f"{_fmt(t['longest_darkness_h_max'])} h limit.")
    if m["earth_visibility_pct"] < t["earth_visibility_pct_min"]:
        misses.append(
            f"Earth is visible {_fmt(m['earth_visibility_pct'])} % of the time, below the "
            f"{_fmt(t['earth_visibility_pct_min'])} % target.")
    if m["longest_comms_gap_h"] > t["longest_comms_gap_h_max"]:
        misses.append(
            f"Longest comms gap is {_fmt(m['longest_comms_gap_h'])} h, above the "
            f"{_fmt(t['longest_comms_gap_h_max'])} h limit.")
    return misses


def _classify(m: dict, t: dict) -> tuple[str, list[str], list[str]]:
    """Ordre obligatoire : not_viable d'abord, puis viable, sinon marginal."""
    hits = _not_viable_hits(m, t)
    if hits:
        return "not_viable", hits, _viable_misses(m, t)
    misses = _viable_misses(m, t)
    if not misses:
        return "viable", hits, misses
    return "marginal", hits, misses


def generate_reasons(level: str, metrics: dict, thresholds: dict | None = None) -> list[str]:
    """Raisons (en anglais, affichées par l'UI) générées à partir des vraies valeurs."""
    if level not in LEVELS:
        raise DecisionInputError(f"unknown level: {level!r}")
    m = validate_metrics(metrics)
    t = resolve_thresholds(thresholds)
    if level == "not_viable":
        return _not_viable_hits(m, t) or _viable_misses(m, t)
    if level == "marginal":
        return _viable_misses(m, t)
    return [
        f"Sunlight {_fmt(m['sunlight_pct'])} % of the time (target >= {_fmt(t['sunlight_pct_min'])} %).",
        f"Longest night {_fmt(m['longest_darkness_h'])} h (limit {_fmt(t['longest_darkness_h_max'])} h).",
        f"Earth visible {_fmt(m['earth_visibility_pct'])} % of the time (target >= {_fmt(t['earth_visibility_pct_min'])} %).",
        f"Longest comms gap {_fmt(m['longest_comms_gap_h'])} h (limit {_fmt(t['longest_comms_gap_h_max'])} h).",
    ]


# ---------------------------------------------------------------------------
# 3. Résumé
# ---------------------------------------------------------------------------
def build_summary(level: str, metrics: dict, thresholds: dict | None = None) -> str:
    """Une phrase simple pour la carte du scénario."""
    if level not in LEVELS:
        raise DecisionInputError(f"unknown level: {level!r}")
    m = validate_metrics(metrics)
    t = resolve_thresholds(thresholds)

    power_ok = (m["sunlight_pct"] >= t["sunlight_pct_min"]
                and m["longest_darkness_h"] <= t["longest_darkness_h_max"])
    comms_ok = (m["earth_visibility_pct"] >= t["earth_visibility_pct_min"]
                and m["longest_comms_gap_h"] <= t["longest_comms_gap_h_max"])

    if level == "viable":
        return ("Good sunlight and direct-to-Earth communication throughout the window: "
                "both power and comms targets are met.")
    if level == "marginal":
        if power_ok and not comms_ok:
            return ("Sunlight is favorable for power, but communication interruptions "
                    "remain a concern and a relay satellite may be needed.")
        if comms_ok and not power_ok:
            return ("Direct-to-Earth communication is good, but the nights are long: "
                    "power and battery sizing are the main concern.")
        return "Neither power nor communications fully meet the targets, but no limit is exceeded."
    # not_viable
    hits = _not_viable_hits(m, t)
    if m["earth_visibility_pct"] < t["earth_visibility_pct_not_viable"]:
        return "Earth is almost never in view: direct-to-Earth communication is not realistic without a relay."
    if m["sunlight_pct"] < t["sunlight_pct_not_viable"]:
        return "The site is dark most of the time: solar power is not realistic."
    if hits:
        return ("The night is too long for a solar lander with about four days of battery "
                "under our assumptions.")
    return "The site does not meet the minimum conditions under our assumptions."


# ---------------------------------------------------------------------------
# 4. Fonction principale (signature imposée par le README)
# ---------------------------------------------------------------------------
def verdict(metrics: dict, thresholds: dict | None = None) -> dict:
    """Renvoie {level, reasons, summary, thresholds}.

    Lève DecisionInputError (ValueError) si les métriques ou les seuils sont invalides.
    `thresholds` renvoyé = les seuils réellement utilisés (défauts + personnalisés).
    """
    m = validate_metrics(metrics)
    t = resolve_thresholds(thresholds)
    level, _, _ = _classify(m, t)
    return {
        "level": level,
        "reasons": generate_reasons(level, m, t),
        "summary": build_summary(level, m, t),
        "thresholds": dict(t),
    }
