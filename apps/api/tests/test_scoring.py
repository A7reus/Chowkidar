from __future__ import annotations

import pytest
from app.services.scoring import priority_from_score, score_risk


def test_maximum_risk_scores_critical() -> None:
    result = score_risk("critical", "likely", "severe")
    assert result["score"] == 100.0
    assert result["priority"] == "critical"
    assert result["severity_weight"] == 0.40
    assert result["likelihood_weight"] == 0.35
    assert result["exposure_weight"] == 0.25


def test_high_risk_band() -> None:
    result = score_risk("high", "possible", "significant")
    assert result["score"] == 75.0
    assert result["priority"] == "high"


def test_medium_risk_band() -> None:
    result = score_risk("medium", "possible", "moderate")
    assert result["score"] == pytest.approx(58.7, abs=0.1)
    assert result["priority"] == "medium"


def test_minimum_risk_scores_low() -> None:
    result = score_risk("low", "rare", "limited")
    assert result["score"] == 25.0
    assert result["priority"] == "low"


def test_unknown_values_are_conservative_defaults() -> None:
    result = score_risk("unknown", "unknown", "unknown")
    assert result["score"] == 25.0
    assert result["priority"] == "low"


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100.0, "critical"),
        (80.0, "critical"),
        (79.9, "high"),
        (60.0, "high"),
        (59.9, "medium"),
        (35.0, "medium"),
        (34.9, "low"),
        (0.0, "low"),
    ],
)
def test_priority_thresholds(score: float, expected: str) -> None:
    assert priority_from_score(score) == expected


def test_formula_is_exposed_for_auditability() -> None:
    result = score_risk("critical", "likely", "severe")
    assert "severity*0.40" in result["formula"]
    assert "likelihood*0.35" in result["formula"]
    assert "exposure*0.25" in result["formula"]
