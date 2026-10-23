from __future__ import annotations

import re
from typing import Any

from app.agents.llm import LLMUnavailable, get_llm_client
from app.agents.prompts import VERIFIER_SYSTEM
from app.agents.schemas import VerificationResult
from app.core.security import find_prohibited_legal_phrases, has_prompt_injection, redact_pii


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_risk(risk: dict[str, Any], signal: dict[str, Any]) -> VerificationResult:
    notes: list[str] = []
    evidence = risk.get("evidence") or []
    if not evidence:
        return VerificationResult(
            status="insufficient_evidence",
            notes=["No evidence was attached to the risk."],
            confidence=0.2,
        )

    source_text = _normalize(str(signal.get("raw_text") or ""))
    for item in evidence:
        quote = _normalize(str(item.get("quote") or ""))
        citation_url = str(item.get("citation_url") or "")
        if not citation_url.startswith("http"):
            notes.append("Evidence citation URL is missing or invalid.")
        if not quote:
            notes.append("Evidence quote is empty.")
        elif source_text and quote not in source_text:
            notes.append("Evidence quote was not found verbatim in the source text.")

    language = " ".join(
        [
            str(risk.get("title") or ""),
            str(risk.get("description") or ""),
            str(risk.get("rationale") or ""),
            " ".join(str(action.get("title") or "") for action in risk.get("actions") or []),
        ]
    )
    prohibited = find_prohibited_legal_phrases(language)
    if prohibited:
        notes.append(f"Prohibited legal-advice phrase detected: {', '.join(prohibited)}.")
    if has_prompt_injection(str(signal.get("raw_text") or "")):
        notes.append("Prompt-injection marker found in the source text; treat source as data only.")

    if any(text in note.lower() for note in notes for text in ("no evidence", "missing", "invalid")) or notes:
        status = "needs_review"
    else:
        status = "verified"

    confidence = 0.9 if status == "verified" else 0.55
    return VerificationResult(status=status, notes=notes, confidence=confidence)


async def verify_risk_live(
    risk: dict[str, Any], signal: dict[str, Any]
) -> VerificationResult:
    deterministic = verify_risk(risk, signal)
    if deterministic.status == "insufficient_evidence":
        return deterministic

    llm = get_llm_client()
    if not llm.live_enabled:
        return deterministic

    safe_text, _ = redact_pii(str(signal.get("raw_text") or "")[:8000])
    evidence_text = "\n".join(
        f"- quote: {item.get('quote')}\n  citation: {item.get('citation_url')}"
        for item in risk.get("evidence") or []
    )
    user = (
        f"Risk title: {risk.get('title')}\n"
        f"Risk description: {risk.get('description')}\n"
        f"Rationale: {risk.get('rationale')}\n"
        f"Evidence:\n{evidence_text}\n\n"
        f"Source text:\n{safe_text}\n\n"
        "Return the verification JSON."
    )
    try:
        parsed, _result = await llm.complete_json(
            system=VERIFIER_SYSTEM, user=user, purpose="verification"
        )
    except LLMUnavailable:
        return deterministic

    try:
        live_result = VerificationResult.model_validate(parsed)
    except Exception:
        return deterministic

    if live_result.status == "verified" and deterministic.status == "verified":
        return live_result
    if live_result.status == "insufficient_evidence":
        return live_result
    notes = list(dict.fromkeys([*deterministic.notes, *live_result.notes]))
    return VerificationResult(
        status="needs_review",
        notes=notes or ["Live verifier requested human review."],
        confidence=min(deterministic.confidence, live_result.confidence),
    )
