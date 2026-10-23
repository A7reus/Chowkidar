from __future__ import annotations

from typing import Any

SEVERITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3, "critical": 4}
LIKELIHOOD_WEIGHTS = {"rare": 1, "unlikely": 2, "possible": 3, "likely": 4}
EXPOSURE_WEIGHTS = {"limited": 1, "moderate": 2, "significant": 3, "severe": 4}

SEVERITY_FACTOR = 0.40
LIKELIHOOD_FACTOR = 0.35
EXPOSURE_FACTOR = 0.25

PRIORITY_THRESHOLDS = (
    ("critical", 80.0),
    ("high", 60.0),
    ("medium", 35.0),
    ("low", 0.0),
)


def _value(weights: dict[str, int], key: str) -> int:
    return weights.get(key.lower(), 1)


def priority_from_score(score: float) -> str:
    for priority, threshold in PRIORITY_THRESHOLDS:
        if score >= threshold:
            return priority
    return "low"


def score_risk(severity: str, likelihood: str, exposure: str) -> dict[str, Any]:
    severity_value = _value(SEVERITY_WEIGHTS, severity)
    likelihood_value = _value(LIKELIHOOD_WEIGHTS, likelihood)
    exposure_value = _value(EXPOSURE_WEIGHTS, exposure)
    weighted = (
        severity_value * SEVERITY_FACTOR
        + likelihood_value * LIKELIHOOD_FACTOR
        + exposure_value * EXPOSURE_FACTOR
    )
    score = round((weighted / 4.0) * 100.0, 1)
    priority = priority_from_score(score)
    return {
        "severity": severity.lower(),
        "likelihood": likelihood.lower(),
        "exposure": exposure.lower(),
        "severity_weight": SEVERITY_FACTOR,
        "likelihood_weight": LIKELIHOOD_FACTOR,
        "exposure_weight": EXPOSURE_FACTOR,
        "severity_value": severity_value,
        "likelihood_value": likelihood_value,
        "exposure_value": exposure_value,
        "score": score,
        "priority": priority,
        "formula": (
            "score = ((severity*0.40 + likelihood*0.35 + exposure*0.25) / 4) * 100; "
            "critical >= 80, high >= 60, medium >= 35"
        ),
    }
