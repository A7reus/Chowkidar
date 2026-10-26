from __future__ import annotations

from typing import Any, cast

from app.agents.pipeline import (
    PipelineState,
    repair_evidence,
    route_after_verify,
)

SIGNAL: dict[str, Any] = {
    "id": "00000000-0000-0000-0000-000000000101",
    "title": "BIS revises the Entity List",
    "url": "https://www.federalregister.gov/documents/2026/17231",
    "raw_text": (
        "BIS revises the Export Administration Regulations. "
        "The rule removes two addresses from the Entity List. "
        "Importers should review counterparties."
    ),
    "source_name": "US Federal Register",
}


def _state(**values: Any) -> PipelineState:
    return cast(PipelineState, values)


def test_route_after_verify_repairs_unresolved_risk_once() -> None:
    state = _state(
        repair_attempts=0,
        verified=[
            {"title": "A", "verification_status": "verified"},
            {"title": "B", "verification_status": "needs_review"},
        ],
    )
    assert route_after_verify(state, 1) == "repair"


def test_route_after_verify_persists_when_all_verified() -> None:
    state = _state(
        repair_attempts=0,
        verified=[{"title": "A", "verification_status": "verified"}],
    )
    assert route_after_verify(state, 1) == "persist"


def test_route_after_verify_enforces_attempt_cap() -> None:
    state = _state(
        repair_attempts=1,
        verified=[{"title": "B", "verification_status": "needs_review"}],
    )
    assert route_after_verify(state, 1) == "persist"


def test_route_after_verify_persists_empty_state() -> None:
    assert route_after_verify(_state(repair_attempts=0, verified=[]), 1) == "persist"


def test_repair_evidence_replaces_non_verbatim_quote() -> None:
    risk = {
        "title": "Entity-list exposure",
        "evidence": [
            {
                "quote": "A paraphrase that is not in the source.",
                "citation_url": "",
                "citation_label": "US Federal Register",
                "confidence": 0.4,
            }
        ],
    }
    evidence, notes = repair_evidence(risk, SIGNAL, [])
    assert evidence[0]["quote"] == "BIS revises the Export Administration Regulations."
    assert evidence[0]["citation_url"] == SIGNAL["url"]
    assert evidence[0]["confidence"] == 0.7
    assert any("non-verbatim" in note for note in notes)


def test_repair_evidence_keeps_a_verbatim_quote_and_valid_citation() -> None:
    risk = {
        "title": "Entity-list exposure",
        "evidence": [
            {
                "quote": "The rule removes two addresses from the Entity List.",
                "citation_url": "https://example.com/rule",
                "citation_label": "Rule",
                "confidence": 0.9,
            }
        ],
    }
    evidence, notes = repair_evidence(risk, SIGNAL, [])
    assert evidence[0]["quote"] == "The rule removes two addresses from the Entity List."
    assert evidence[0]["citation_url"] == "https://example.com/rule"
    assert evidence[0]["confidence"] == 0.9
    assert notes == []


def test_repair_evidence_attaches_evidence_when_missing() -> None:
    risk = {"title": "Entity-list exposure", "evidence": []}
    evidence, notes = repair_evidence(risk, SIGNAL, [])
    assert len(evidence) == 1
    assert evidence[0]["quote"] == "BIS revises the Export Administration Regulations."
    assert evidence[0]["citation_url"] == SIGNAL["url"]
    assert any("Attached" in note for note in notes)


def test_repair_evidence_uses_retrieved_chunk_text() -> None:
    signal = {
        **SIGNAL,
        "raw_text": (
            "The retrieved chunk contains the verbatim rule text. "
            "It also contains a second sentence."
        ),
    }
    chunk = (
        "Document: Entity List rule\nJurisdiction: US\nSection: Signal body\n\n"
        "The retrieved chunk contains the verbatim rule text. It also contains a second sentence."
    )
    risk = {
        "title": "Entity-list exposure",
        "evidence": [{"quote": "wrong", "citation_url": "", "confidence": 0.5}],
    }
    evidence, notes = repair_evidence(risk, signal, [chunk])
    assert evidence[0]["quote"] == "The retrieved chunk contains the verbatim rule text."
    assert any("non-verbatim" in note for note in notes)
