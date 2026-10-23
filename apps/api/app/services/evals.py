from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.mock import extract_mock, map_mock, remediation_mock
from app.agents.verifier import verify_risk
from app.core.security import find_prohibited_legal_phrases
from app.db.models import EvalRun, Signal
from app.schemas import EvalCaseResult, EvalSummary
from app.services.scoring import score_risk

GOLDEN_CASES = [
    {
        "case_id": "export-proceeds-repatriation",
        "external_id": "bb-fepd-2026-26",
        "expected_keyword": "export-proceeds",
        "expected_priority": "high",
    },
    {
        "case_id": "csddd-due-diligence",
        "external_id": "eu-csddd-2024-1760",
        "expected_keyword": "due diligence",
        "expected_priority": "medium",
    },
    {
        "case_id": "uflpa-forced-labour",
        "external_id": "dhs-uflpa-2026-07-31",
        "expected_keyword": "forced-labour",
        "expected_priority": "critical",
    },
    {
        "case_id": "port-disruption",
        "external_id": "gdelt-2026-10-20-port",
        "expected_keyword": "port",
        "expected_priority": "high",
    },
    {
        "case_id": "factory-fire",
        "external_id": "gdelt-2026-10-18-fire",
        "expected_keyword": "safety",
        "expected_priority": "high",
    },
    {
        "case_id": "flood-freight",
        "external_id": "gdelt-2026-10-22-flood",
        "expected_keyword": "freight",
        "expected_priority": "high",
    },
    {
        "case_id": "export-incentive",
        "external_id": "bb-fepd-2026-25",
        "expected_keyword": "incentive",
        "expected_priority": "high",
    },
]


def _signal_payload(signal: Signal) -> dict[str, Any]:
    return {
        "id": str(signal.id),
        "source_id": str(signal.source_id),
        "source_name": signal.source.name if signal.source else "",
        "supplier_id": str(signal.supplier_id) if signal.supplier_id else None,
        "supplier_name": signal.supplier.name if signal.supplier else None,
        "external_id": signal.external_id,
        "title": signal.title,
        "summary": signal.summary,
        "raw_text": signal.raw_text,
        "url": signal.url,
        "jurisdiction": signal.jurisdiction,
        "signal_type": signal.signal_type,
        "severity": signal.severity,
        "published_at": signal.published_at.isoformat(),
        "metadata": signal.extra or {},
        "status": signal.status,
    }


async def run_evals(session: AsyncSession) -> EvalSummary:
    signals = list(
        (
            await session.execute(
                select(Signal).options(selectinload(Signal.source), selectinload(Signal.supplier))
            )
        )
        .scalars()
        .all()
    )
    by_external_id = {signal.external_id: signal for signal in signals}
    results: list[EvalCaseResult] = []
    extraction_hits = 0
    citation_hits = 0
    verifier_hits = 0
    no_advice_hits = 0
    priority_hits = 0

    for case in GOLDEN_CASES:
        notes: list[str] = []
        signal = by_external_id.get(case["external_id"])
        if signal is None:
            results.append(
                EvalCaseResult(
                    case_id=case["case_id"],
                    passed=False,
                    citation_coverage=0.0,
                    verifier_pass=False,
                    no_legal_advice=True,
                    notes=["Signal fixture is missing."],
                )
            )
            continue
        payload = _signal_payload(signal)
        obligation = extract_mock(payload)
        if obligation is None:
            results.append(
                EvalCaseResult(
                    case_id=case["case_id"],
                    passed=False,
                    citation_coverage=0.0,
                    verifier_pass=False,
                    no_legal_advice=True,
                    notes=["Extraction returned no obligation."],
                )
            )
            continue
        keyword_hit = case["expected_keyword"].lower() in (
            f"{obligation.title} {obligation.description}".lower()
        )
        extraction_hits += int(keyword_hit)
        if not keyword_hit:
            notes.append(f"Expected keyword '{case['expected_keyword']}' in extraction.")

        mapped = map_mock(payload, obligation.model_dump(mode="json"))
        score_data = score_risk(mapped.severity, mapped.likelihood, mapped.exposure)
        actions = remediation_mock(payload, {**mapped.model_dump(mode="json"), **score_data})
        risk_payload = {
            **mapped.model_dump(mode="json"),
            **score_data,
            "evidence": [
                {
                    "quote": mapped.evidence_quote,
                    "citation_url": mapped.citation_url,
                    "citation_label": mapped.citation_label,
                    "confidence": mapped.confidence,
                    "supports": "supports",
                }
            ],
            "actions": [action.model_dump(mode="json") for action in actions],
        }
        citation_ok = bool(mapped.evidence_quote) and (
            mapped.evidence_quote.lower() in signal.raw_text.lower()
        )
        citation_hits += int(citation_ok)
        if not citation_ok:
            notes.append("Citation quote was not found in the source text.")

        verification = verify_risk(risk_payload, payload)
        verifier_ok = verification.status == "verified"
        verifier_hits += int(verifier_ok)
        if not verifier_ok:
            notes.extend(verification.notes or ["Verifier requested review."])

        language = " ".join(
            [
                obligation.title,
                obligation.description,
                mapped.title,
                mapped.description,
                mapped.rationale,
                *[action.title for action in actions],
            ]
        )
        no_advice_ok = not find_prohibited_legal_phrases(language)
        no_advice_hits += int(no_advice_ok)
        if not no_advice_ok:
            notes.append("Prohibited legal-advice language detected.")

        priority_ok = score_data["priority"] == case["expected_priority"]
        priority_hits += int(priority_ok)
        if not priority_ok:
            notes.append(
                f"Expected priority {case['expected_priority']}, got {score_data['priority']}."
            )

        passed = keyword_hit and citation_ok and verifier_ok and no_advice_ok and priority_ok
        results.append(
            EvalCaseResult(
                case_id=case["case_id"],
                passed=passed,
                citation_coverage=1.0 if citation_ok else 0.0,
                verifier_pass=verifier_ok,
                no_legal_advice=no_advice_ok,
                notes=notes,
            )
        )

    total = len(results)
    passed_cases = sum(1 for result in results if result.passed)
    summary = EvalSummary(
        name="golden-set-v1",
        total_cases=total,
        passed_cases=passed_cases,
        extraction_accuracy=round(extraction_hits / total, 3) if total else 0.0,
        citation_coverage=round(citation_hits / total, 3) if total else 0.0,
        verifier_pass_rate=round(verifier_hits / total, 3) if total else 0.0,
        no_legal_advice_rate=round(no_advice_hits / total, 3) if total else 0.0,
        priority_agreement=round(priority_hits / total, 3) if total else 0.0,
        results=results,
        generated_at=datetime.now(UTC),
    )
    session.add(
        EvalRun(
            name=summary.name,
            metrics=summary.model_dump(mode="json"),
        )
    )
    await session.flush()
    return summary
