from __future__ import annotations

import json

from app.core.config import ROOT_DIR
from app.services.evals import GOLDEN_CASES, GOLDEN_SET_NAME

VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def _fixture_signals() -> list[dict[str, object]]:
    fixture = json.loads((ROOT_DIR / "data" / "fixtures" / "demo.json").read_text(encoding="utf-8"))
    return list(fixture["signals"])


def test_golden_cases_are_unique_and_well_formed() -> None:
    case_ids = [case["case_id"] for case in GOLDEN_CASES]
    external_ids = [case["external_id"] for case in GOLDEN_CASES]

    assert len(case_ids) == len(set(case_ids))
    assert len(external_ids) == len(set(external_ids))
    assert GOLDEN_SET_NAME == "golden-set-v2"
    for case in GOLDEN_CASES:
        assert case["case_id"]
        assert case["external_id"]
        assert case["expected_keyword"]
        assert case["expected_priority"] in VALID_PRIORITIES


def test_golden_set_covers_every_seeded_signal() -> None:
    seeded = {str(signal["external_id"]) for signal in _fixture_signals()}
    covered = {case["external_id"] for case in GOLDEN_CASES}

    assert len(seeded) == 13
    assert covered == seeded
