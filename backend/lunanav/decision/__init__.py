"""LunaNav - module de décision (P4). Module pur : métriques en entrée, verdict en sortie."""
from .verdict import (
    DEFAULT_THRESHOLDS,
    DecisionInputError,
    InvalidMetricsError,
    InvalidThresholdsError,
    build_summary,
    generate_reasons,
    validate_metrics,
    verdict,
)
from .explain import explain_comparison, explain_metric, explain_ranking, explain_verdict
from .ranking import (
    CRITERIA,
    WEIGHT_PROFILES,
    rank_scenarios,
    sensitivity_analysis,
)

__all__ = [
    "DEFAULT_THRESHOLDS", "DecisionInputError", "InvalidMetricsError",
    "InvalidThresholdsError", "build_summary", "generate_reasons",
    "validate_metrics", "verdict", "explain_comparison", "explain_metric",
    "explain_ranking", "explain_verdict", "CRITERIA", "WEIGHT_PROFILES",
    "rank_scenarios", "sensitivity_analysis",
]
