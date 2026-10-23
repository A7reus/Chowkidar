from __future__ import annotations

from datetime import date

from app.agents.mock import citation_quote, extract_mock, map_mock, remediation_mock
from app.agents.verifier import verify_risk
from app.services.scoring import score_risk

SIGNAL = {
    "id": "00000000-0000-0000-0000-000000000101",
    "source_id": "00000000-0000-0000-0000-000000000201",
    "source_name": "DHS — UFLPA Entity List",
    "title": "DHS expands UFLPA Entity List to 187 entities, including cotton and apparel",
    "summary": (
        "DHS added 43 entities to the UFLPA Entity List. CBP applies a rebuttable presumption "
        "to goods linked to listed entities."
    ),
    "raw_text": (
        "DHS expands UFLPA Entity List to 187 entities, including cotton and apparel. "
        "DHS added 43 entities to the UFLPA Entity List. CBP applies a rebuttable presumption "
        "to goods linked to listed entities. Importers should maintain traceability records."
    ),
    "signal_type": "sanctions",
    "jurisdiction": "US",
    "supplier_id": "00000000-0000-0000-0000-000000000301",
    "url": "https://example.gov/uflpa",
    "metadata": {},
}


def test_citation_quote_is_verbatim_source_text() -> None:
    quote = citation_quote(SIGNAL)
    assert quote
    assert quote in SIGNAL["raw_text"]


def test_extract_mock_builds_grounded_obligation() -> None:
    obligation = extract_mock(SIGNAL)
    assert obligation is not None
    assert obligation.obligation_type == "sanctions"
    assert obligation.citation_url == SIGNAL["url"]
    assert obligation.citation_quote in SIGNAL["raw_text"]
    assert obligation.signal_id == SIGNAL["id"]
    assert obligation.jurisdiction == "US"


def test_map_mock_produces_critical_sanctions_risk() -> None:
    obligation = extract_mock(SIGNAL)
    assert obligation is not None
    mapped = map_mock(SIGNAL, obligation.model_dump())
    assert mapped.category == "sanctions"
    assert mapped.severity == "critical"
    assert mapped.supplier_id == SIGNAL["supplier_id"]
    scored = score_risk(mapped.severity, mapped.likelihood, mapped.exposure)
    assert scored["priority"] == "critical"
    assert mapped.evidence_quote in SIGNAL["raw_text"]
    assert "not a confirmed finding" in mapped.rationale


def test_remediation_mock_creates_reviewable_actions() -> None:
    obligation = extract_mock(SIGNAL)
    assert obligation is not None
    mapped = map_mock(SIGNAL, obligation.model_dump())
    actions = remediation_mock(SIGNAL, mapped.model_dump())
    assert actions
    for action in actions:
        assert action.owner_role in {"analyst", "approver", "admin"}
        assert action.priority in {"low", "medium", "high", "critical"}
        assert isinstance(action.automated, bool)
        assert action.due_date is not None
        assert action.due_date >= date.today()
    assert any(action.automated for action in actions)


def test_verifier_accepts_grounded_risk() -> None:
    risk = {
        "title": "Potential forced-labour exposure requires review",
        "description": "The supplier may be linked to a listed entity; confirm traceability.",
        "rationale": "Review the evidence and document the decision.",
        "evidence": [{"quote": SIGNAL["raw_text"], "citation_url": SIGNAL["url"]}],
        "actions": [{"title": "Obtain lot-level traceability records"}],
    }
    result = verify_risk(risk, SIGNAL)
    assert result.status == "verified"
    assert result.confidence == 0.9


def test_verifier_flags_missing_quote() -> None:
    risk = {
        "title": "Potential forced-labour exposure requires review",
        "description": "Review required.",
        "rationale": "Review required.",
        "evidence": [{"quote": "A quote that is absent", "citation_url": SIGNAL["url"]}],
        "actions": [],
    }
    result = verify_risk(risk, SIGNAL)
    assert result.status == "needs_review"
    assert any("not found verbatim" in note for note in result.notes)


def test_verifier_blocks_prohibited_legal_advice() -> None:
    risk = {
        "title": "This is legal advice",
        "description": "You are compliant.",
        "rationale": "No further review is needed.",
        "evidence": [{"quote": SIGNAL["raw_text"], "citation_url": SIGNAL["url"]}],
        "actions": [],
    }
    result = verify_risk(risk, SIGNAL)
    assert result.status == "needs_review"
    assert any("Prohibited legal-advice phrase" in note for note in result.notes)


def test_verifier_requires_evidence() -> None:
    result = verify_risk({"title": "No evidence", "evidence": []}, SIGNAL)
    assert result.status == "insufficient_evidence"
