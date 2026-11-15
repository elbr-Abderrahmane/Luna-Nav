import math

import pytest

from lunanav.decision import (CRITERIA, WEIGHT_PROFILES, DecisionInputError,
                              explain_ranking, rank_scenarios, sensitivity_analysis)
from lunanav.decision.ranking import normalize_minmax, resolve_weights


def _row(label, **kw):
    base = {"sunlight_pct": 50, "longest_darkness_h": 100, "earth_visibility_pct": 50,
            "longest_comms_gap_h": 100, "power_and_comms_pct": 25,
            "vertical_panel_energy_kwh_m2": 500}
    return {"label": label, "metrics": {**base, **kw}}


def test_profiles_sum_to_one():
    for p in WEIGHT_PROFILES.values():
        assert math.isclose(sum(p.values()), 1.0) and set(p) == set(CRITERIA)


def test_normalization_direction_and_range():
    vals = [r["metrics"] for r in (_row("a", sunlight_pct=10, longest_darkness_h=300),
                                   _row("b", sunlight_pct=90, longest_darkness_h=0))]
    n = normalize_minmax(vals)
    assert n[1]["sunlight_pct"] == 1.0 and n[0]["sunlight_pct"] == 0.0        # max = mieux
    assert n[1]["longest_darkness_h"] == 1.0 and n[0]["longest_darkness_h"] == 0.0  # min = mieux
    assert n[0]["earth_visibility_pct"] == 1.0                                  # colonne constante


def test_obvious_winner_both_methods():
    best = _row("best", sunlight_pct=100, longest_darkness_h=0, earth_visibility_pct=100,
                longest_comms_gap_h=0, power_and_comms_pct=100, vertical_panel_energy_kwh_m2=900)
    worst = _row("worst", sunlight_pct=10, longest_darkness_h=300, earth_visibility_pct=10,
                 longest_comms_gap_h=300, power_and_comms_pct=5, vertical_panel_energy_kwh_m2=100)
    for prof in WEIGHT_PROFILES:
        r = rank_scenarios([worst, best], profile=prof)
        assert r["ranking"][0]["label"] == "best"
        assert r["ranking"][0]["wsm_score"] == 1.0
        assert r["ranking"][0]["topsis_rank"] == 1 and r["ranking"][1]["topsis_rank"] == 2


def test_scores_between_0_and_1_and_n_scenarios(compare_rows):
    r = rank_scenarios(compare_rows)
    assert len(r["ranking"]) == 4
    for x in r["ranking"]:
        assert 0 <= x["wsm_score"] <= 1 and 0 <= x["topsis_score"] <= 1


def test_two_scenarios_and_methods():
    rows = [_row("a", sunlight_pct=90), _row("b", sunlight_pct=20)]
    assert "topsis_score" not in rank_scenarios(rows, method="wsm")["ranking"][0]
    assert "wsm_score" not in rank_scenarios(rows, method="topsis")["ranking"][0]


def test_custom_weights_normalized():
    w = resolve_weights(weights={"sunlight_pct": 2, "longest_darkness_h": 2})
    assert math.isclose(sum(w.values()), 1.0) and w["sunlight_pct"] == 0.5
    rows = [_row("sun", sunlight_pct=100), _row("dark", longest_darkness_h=0, sunlight_pct=10)]
    assert rank_scenarios(rows, weights={"sunlight_pct": 1})["ranking"][0]["label"] == "sun"


def test_weights_change_ranking(compare_rows):
    sci = rank_scenarios(compare_rows, profile="science", method="topsis")["ranking"][0]["label"]
    eng = rank_scenarios(compare_rows, profile="engineering", method="topsis")["ranking"][0]["label"]
    assert "connecting ridge" in sci.lower() and "malapert" in eng.lower()


def test_verdict_attached_and_note(compare_rows):
    r = rank_scenarios(compare_rows)
    assert {x["verdict_level"] for x in r["ranking"]} == {"marginal", "not_viable"}
    assert "relative" in r["note"]


@pytest.mark.parametrize("bad_rows", [[], [_row("only")], "x",
                                      [_row("a"), _row("a")],
                                      [_row("a"), {"label": "b", "metrics": {"sunlight_pct": 5}}],
                                      [_row("a"), _row("b", sunlight_pct=150)]])
def test_invalid_rows(bad_rows):
    with pytest.raises(DecisionInputError):
        rank_scenarios(bad_rows)


def test_invalid_options():
    rows = [_row("a"), _row("b", sunlight_pct=80)]
    with pytest.raises(DecisionInputError):
        rank_scenarios(rows, profile="marketing")
    with pytest.raises(DecisionInputError):
        rank_scenarios(rows, method="magic")
    with pytest.raises(DecisionInputError):
        rank_scenarios(rows, weights={"foo": 1})
    with pytest.raises(DecisionInputError):
        rank_scenarios(rows, weights={"sunlight_pct": 0})


def test_sensitivity_structure_and_reproducible(compare_rows):
    a = sensitivity_analysis(compare_rows)
    b = sensitivity_analysis(compare_rows)
    assert a == b                                           # graine fixe
    assert len(a["one_at_a_time"]) == 2 * len(CRITERIA)
    assert a["stability"] in {"stable", "moderate", "sensitive"}
    assert math.isclose(sum(a["random_weights"]["top_win_share_pct"].values()), 100, abs_tol=0.5)


def test_sensitivity_stable_when_dominant():
    best = _row("best", sunlight_pct=100, longest_darkness_h=0, earth_visibility_pct=100,
                longest_comms_gap_h=0, power_and_comms_pct=100, vertical_panel_energy_kwh_m2=900)
    worst = _row("worst", sunlight_pct=10, longest_darkness_h=300, earth_visibility_pct=10,
                 longest_comms_gap_h=300, power_and_comms_pct=5, vertical_panel_energy_kwh_m2=100)
    s = sensitivity_analysis([best, worst])
    assert s["stability"] == "stable" and s["profile_comparison"]["agree"]


def test_sensitivity_detects_profile_disagreement(compare_rows):
    s = sensitivity_analysis(compare_rows)
    assert s["profile_comparison"]["agree"] is False


def test_sensitivity_invalid_args(compare_rows):
    with pytest.raises(DecisionInputError):
        sensitivity_analysis(compare_rows, delta=1.5)
    with pytest.raises(DecisionInputError):
        sensitivity_analysis(compare_rows, method="both")


def test_explain_ranking_real(compare_rows):
    r = rank_scenarios(compare_rows)
    s = sensitivity_analysis(compare_rows)
    t = explain_ranking(r, s)
    assert "not_viable" in t and "sensitive" in t
    assert explain_ranking(r)                                 # sans sensibilité


def test_sweep_ranks_12_dates(sweep_rows):
    r = rank_scenarios(sweep_rows)
    assert len(r["ranking"]) == 12
    assert r["ranking"][0]["label"] in {"2027-08-04", "2027-09-03", "2027-10-02", "2027-11-01"}
