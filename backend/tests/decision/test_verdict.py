import copy
import json

import pytest

from lunanav.decision import (DEFAULT_THRESHOLDS, DecisionInputError,
                              InvalidMetricsError, InvalidThresholdsError,
                              build_summary, generate_reasons, validate_metrics,
                              verdict)


# --- Cas obligatoires du cahier des charges (tests 1 à 8) -------------------
def test_1_viable(good):
    v = verdict(good)
    assert v["level"] == "viable"
    assert len(v["reasons"]) == 4


def test_2_not_viable_long_night(good):
    assert verdict({**good, "longest_darkness_h": 120})["level"] == "not_viable"


def test_3_not_viable_low_sunlight(good):
    assert verdict({**good, "sunlight_pct": 20})["level"] == "not_viable"


def test_4_not_viable_low_earth(good):
    v = verdict({**good, "earth_visibility_pct": 10})
    assert v["level"] == "not_viable"


def test_5_marginal(good):
    v = verdict({**good, "longest_comms_gap_h": 347})
    assert v["level"] == "marginal"
    assert "347" in v["reasons"][0] and "72" in v["reasons"][0]


def test_6_missing_data(good):
    bad = dict(good)
    del bad["sunlight_pct"]
    with pytest.raises(InvalidMetricsError):
        verdict(bad)


@pytest.mark.parametrize("key,value", [
    ("sunlight_pct", 120), ("sunlight_pct", -1), ("earth_visibility_pct", 101),
    ("longest_darkness_h", -5), ("longest_comms_gap_h", -0.1)])
def test_7_out_of_range(good, key, value):
    with pytest.raises(InvalidMetricsError):
        verdict({**good, key: value})


def test_8_custom_thresholds(good):
    m = {**good, "longest_darkness_h": 60}
    assert verdict(m)["level"] == "marginal"
    v = verdict(m, {"longest_darkness_h_max": 80})
    assert v["level"] == "viable"
    assert v["thresholds"]["longest_darkness_h_max"] == 80   # seuil réellement utilisé


# --- Tests supplémentaires --------------------------------------------------
def test_output_keys_and_types(good):
    v = verdict(good)
    assert set(v) == {"level", "reasons", "summary", "thresholds"}
    assert isinstance(v["reasons"], list) and all(isinstance(r, str) for r in v["reasons"])
    assert isinstance(v["summary"], str) and v["summary"]
    assert v["thresholds"] == DEFAULT_THRESHOLDS


def test_json_serializable(good):
    json.dumps(verdict(good))


def test_none_values_rejected(good):
    with pytest.raises(InvalidMetricsError):
        verdict({**good, "earth_visibility_pct": None})


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), "50", True])
def test_non_numeric_rejected(good, bad):
    with pytest.raises(InvalidMetricsError):
        validate_metrics({**good, "sunlight_pct": bad})


def test_not_a_dict():
    with pytest.raises(InvalidMetricsError):
        verdict([1, 2, 3])


def test_not_viable_checked_before_viable(good):
    # 3 conditions « viable » OK mais nuit de 120 h : doit rester not_viable
    assert verdict({**good, "longest_darkness_h": 120})["level"] == "not_viable"


def test_boundaries_are_strict(good):
    # == 100 h : pas not_viable (règle ">") ; == 50 h : encore viable (règle "<=")
    assert verdict({**good, "longest_darkness_h": 100})["level"] == "marginal"
    assert verdict({**good, "longest_darkness_h": 50})["level"] == "viable"
    assert verdict({**good, "sunlight_pct": 60})["level"] == "viable"
    assert verdict({**good, "sunlight_pct": 30})["level"] == "marginal"
    assert verdict({**good, "earth_visibility_pct": 20})["level"] == "marginal"
    assert verdict({**good, "longest_comms_gap_h": 72})["level"] == "viable"


def test_relay_message_when_earth_never_visible(good):
    v = verdict({**good, "earth_visibility_pct": 0, "longest_comms_gap_h": 708})
    assert v["level"] == "not_viable"
    assert any("relay" in r for r in v["reasons"])


def test_unknown_or_incoherent_thresholds(good):
    with pytest.raises(InvalidThresholdsError):
        verdict(good, {"foo": 1})
    with pytest.raises(InvalidThresholdsError):
        verdict(good, {"sunlight_pct_min": 20})          # < sunlight_pct_not_viable (30)
    with pytest.raises(InvalidThresholdsError):
        verdict(good, {"longest_darkness_h_max": -3})
    with pytest.raises(InvalidThresholdsError):
        verdict(good, "oops")


def test_inputs_not_mutated(good):
    m, t = copy.deepcopy(good), {"longest_darkness_h_max": 70}
    m0, t0 = copy.deepcopy(m), copy.deepcopy(t)
    verdict(m, t)
    assert m == m0 and t == t0


def test_extra_keys_ignored(good):
    full = {**good, "power_and_comms_pct": 50, "n_sunsets": 1, "libration_lat_range_deg": [0, 1]}
    assert verdict(full)["level"] == "viable"


def test_summary_consistent_with_reasons(good):
    v = verdict({**good, "longest_comms_gap_h": 347})
    assert "communication" in v["summary"].lower() or "relay" in v["summary"].lower()
    n = verdict({**good, "longest_darkness_h": 269})
    assert "night" in n["summary"].lower()


def test_helpers_reject_bad_level(good):
    with pytest.raises(DecisionInputError):
        generate_reasons("excellent", good)
    with pytest.raises(DecisionInputError):
        build_summary("excellent", good)


# --- Données réelles de P3 (acceptées sans modification) --------------------
def test_real_compare_four_sites(compare_rows):
    levels = {r["label"].split(" @")[0]: verdict(r["metrics"])["level"] for r in compare_rows}
    assert sorted(levels.values()) == ["marginal", "not_viable", "not_viable", "not_viable"]
    connecting = next(v for k, v in levels.items() if "connecting ridge" in k)
    assert connecting == "marginal"


def test_real_date_sweep(sweep_rows):
    levels = {r["label"]: verdict(r["metrics"])["level"] for r in sweep_rows}
    assert levels["2027-01-10"] == "marginal"
    assert levels["2027-02-08"] == "marginal"
    assert levels["2027-03-10"] == "not_viable"
    assert levels["2027-10-02"] == "marginal"
    assert "viable" not in levels.values()   # coupure radio > 72 h toute l'année
