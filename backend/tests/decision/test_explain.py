import pytest

from lunanav.decision import (DecisionInputError, explain_comparison, explain_metric,
                              explain_verdict, verdict)


def test_explain_metric_unit_and_value():
    t = explain_metric("longest_comms_gap_h", 347)
    assert "347 h" in t and "relay" in t
    assert "48 %" in explain_metric("earth_visibility_pct", 48.0)


def test_explain_metric_errors():
    with pytest.raises(DecisionInputError):
        explain_metric("nope", 1)
    with pytest.raises(DecisionInputError):
        explain_metric("sunlight_pct", None)


def test_explain_verdict(good):
    text = explain_verdict(verdict({**good, "longest_comms_gap_h": 347}))
    assert text.startswith("Marginal")
    assert "347" in text and "not a NASA certification" in text


def test_explain_verdict_invalid():
    with pytest.raises(DecisionInputError):
        explain_verdict({"level": "great"})
    with pytest.raises(DecisionInputError):
        explain_verdict(None)


def test_explain_comparison_real(compare_rows):
    t = explain_comparison(compare_rows)
    assert "4 scenarios compared: 0 viable, 1 marginal, 3 not viable." in t
    assert "connecting ridge" in t.lower()
    assert "3 scenarios tie" in t
    assert "trade-off" in t


def test_explain_comparison_none_viable(good):
    rows = [{"label": "A", "metrics": {**good, "longest_darkness_h": 200}},
            {"label": "B", "metrics": {**good, "sunlight_pct": 10}}]
    assert "No scenario meets" in explain_comparison(rows)


def test_explain_comparison_errors():
    with pytest.raises(DecisionInputError):
        explain_comparison([])
    with pytest.raises(DecisionInputError):
        explain_comparison([{"label": "A"}])
