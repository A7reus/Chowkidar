from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Literal

from app.agents.schemas import DraftAction, ExtractedObligation, MappedRisk

ActionPriority = Literal["low", "medium", "high", "critical"]


def _has_word(text: str, *words: str) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def _first_sentence(text: str, max_chars: int = 320) -> str:
    compact = " ".join(text.split())
    if not compact:
        return ""
    for delimiter in (". ", "! ", "? "):
        index = compact.find(delimiter)
        if 20 <= index <= max_chars:
            return compact[: index + 1]
    return compact[:max_chars]


def citation_quote(signal: dict[str, Any]) -> str:
    metadata = signal.get("metadata") or {}
    quote = str(metadata.get("quote") or "").strip()
    if quote and quote.lower() in str(signal.get("raw_text", "")).lower():
        return quote
    return _first_sentence(str(signal.get("raw_text") or signal.get("summary") or signal["title"]))


def extract_mock(signal: dict[str, Any]) -> ExtractedObligation | None:
    text = f"{signal['title']} {signal.get('summary', '')}".lower()
    quote = citation_quote(signal)
    if not quote:
        return None

    if _has_word(text, "flood", "freight"):
        title = "Assess and mitigate inland freight disruption"
        obligation_type = "operational"
        applies_to = "Logistics and commercial teams"
        section_path = "Operational signal"
    elif _has_word(text, "port", "strike"):
        title = "Assess and mitigate port-disruption exposure"
        obligation_type = "operational"
        applies_to = "Logistics and commercial teams"
        section_path = "Operational signal"
    elif _has_word(text, "fire"):
        title = "Verify worker safety after a factory incident"
        obligation_type = "operational"
        applies_to = "Factory operations and EHS"
        section_path = "Operational signal"
    elif _has_word(text, "uflpa", "forced", "sanction"):
        title = "Screen for forced-labour and restricted-party exposure"
        obligation_type = "sanctions"
        applies_to = "US-bound supply chain"
        section_path = "Trade-compliance signal"
    elif "export proceeds" in text or "repatriat" in text:
        title = "Review export-proceeds reporting and repatriation controls"
        obligation_type = "financial_regulatory"
        applies_to = "Finance and authorized dealer bank"
        section_path = "Regulatory signal"
    elif signal.get("signal_type") == "regulatory":
        title = f"Review potential obligation: {signal['title']}"
        obligation_type = "regulatory"
        applies_to = "Compliance and accountable business owner"
        section_path = "Regulatory signal"
    else:
        title = f"Assess operational signal: {signal['title']}"
        obligation_type = "operational"
        applies_to = "Compliance and operations"
        section_path = "Signal body"

    return ExtractedObligation(
        signal_id=str(signal["id"]),
        source_id=str(signal["source_id"]),
        title=title,
        description=(
            f"Potential obligation arising from {signal.get('source_name', 'a monitored source')}. "
            f"{signal.get('summary', '')} The accountable owner should review the source, "
            "confirm applicability, and document the decision."
        ).strip(),
        jurisdiction=str(signal.get("jurisdiction") or "GLOBAL"),
        obligation_type=obligation_type,
        applies_to=applies_to,
        effective_date=None,
        confidence=0.68 if signal.get("signal_type") == "news" else 0.78,
        citation_url=str(signal.get("url") or ""),
        citation_quote=quote,
        section_path=section_path,
        signal_title=str(signal["title"]),
    )


def map_mock(signal: dict[str, Any], obligation: dict[str, Any]) -> MappedRisk:
    text = f"{signal['title']} {signal.get('summary', '')} {obligation['title']}".lower()
    supplier_id = signal.get("supplier_id")
    if _has_word(text, "flood", "freight"):
        title = "Flooding may delay inland freight and export shipments"
        category = "operational"
        severity, likelihood, exposure = "medium", "likely", "moderate"
        rationale = (
            "The signal reports flooding on the Dhaka–Chattogram corridor. The exposure is "
            "time-bound but affects two export shipments. Review the revised ETAs, preserve "
            "carrier notices, and notify buyers of the potential 24–48 hour delay."
        )
    elif _has_word(text, "port", "strike"):
        title = "Port disruption may delay export shipments"
        category = "operational"
        severity, likelihood, exposure = "medium", "likely", "moderate"
        rationale = (
            "The signal reports a port strike. The main risk is a missed delivery window and "
            "demurrage. Confirm the affected shipments and evaluate rerouting before the strike window."
        )
    elif _has_word(text, "fire"):
        title = "Factory incident requires safety verification before production resumes"
        category = "operational"
        severity, likelihood, exposure = "high", "possible", "significant"
        rationale = (
            "The signal reports a factory fire and unverified safety conditions. Production should "
            "not resume until the incident report, electrical inspection, and fire-safety re-inspection "
            "are reviewed by the accountable owner."
        )
    elif _has_word(text, "uflpa", "forced", "sanction"):
        title = "Potential forced-labour or sanctions exposure requires review"
        category = "sanctions"
        severity, likelihood, exposure = "critical", "unlikely", "severe"
        rationale = (
            "The signal creates a potential traceability or restricted-party exposure. It is not a "
            "confirmed finding. Enhanced due diligence, ownership review, and a documented human "
            "decision are required before new orders or US-bound shipments."
        )
    elif "export proceeds" in text or "repatriat" in text:
        title = "Export-proceeds reporting may not meet the prescribed timeline"
        category = "financial_regulatory"
        severity, likelihood, exposure = "high", "possible", "significant"
        rationale = (
            "The signal reinforces the obligation to repatriate proceeds within the prescribed period "
            "and report delays. The existing manual reconciliation does not provide an exception alert."
        )
    elif "csddd" in text or "due diligence" in text:
        title = "EU CSDDD supervisory activity may increase buyer evidence requests"
        category = "regulatory"
        severity, likelihood, exposure = "medium", "possible", "moderate"
        rationale = (
            "The signal points to active CSDDD implementation and supervisory preparation. The direct "
            "legal obligation may sit with the EU buyer, but the buyer is likely to request supplier "
            "evidence. Map the request to the supplier code, grievance mechanism, and tier-2 records."
        )
    else:
        title = "Potential regulatory obligation requires review"
        category = "regulatory"
        severity, likelihood, exposure = "high", "possible", "significant"
        rationale = (
            "The source may create a new obligation or change an existing control expectation. "
            "The accountable owner should confirm applicability, map affected suppliers and policies, "
            "and document the evidence used for the decision."
        )

    source_name = signal.get("source_name") or "monitored source"
    return MappedRisk(
        signal_id=str(signal["id"]),
        obligation_title=str(obligation["title"]),
        supplier_id=str(supplier_id) if supplier_id else None,
        title=title,
        description=f"{obligation['description']} Source signal: {signal.get('summary', '')}".strip(),
        category=category,
        severity=severity,
        likelihood=likelihood,
        exposure=exposure,
        rationale=rationale,
        confidence=float(obligation.get("confidence", 0.72)),
        evidence_quote=str(obligation.get("citation_quote") or citation_quote(signal)),
        citation_url=str(obligation.get("citation_url") or signal.get("url") or ""),
        citation_label=f"{source_name} — {signal['title']}",
    )


def remediation_mock(signal: dict[str, Any], risk: dict[str, Any]) -> list[DraftAction]:
    today = date.today()
    text = f"{risk['title']} {risk.get('category', '')}".lower()
    actions: list[tuple[str, str, str, int, ActionPriority, bool]] = []
    if _has_word(text, "flood", "freight"):
        actions = [
            (
                "Reroute inland freight and update shipment ETAs",
                "Contact the logistics provider, confirm alternate routing, and publish revised ETAs for the affected shipments.",
                "analyst",
                3,
                "high",
                False,
            ),
            (
                "Notify buyers of the potential 24–48 hour delay",
                "Send a short buyer update with the revised delivery window and the contingency plan.",
                "analyst",
                1,
                "medium",
                False,
            ),
        ]
    elif _has_word(text, "port", "strike"):
        actions = [
            (
                "Book alternate freight and confirm revised ETAs",
                "Evaluate air or alternate-port options for the urgent shipments and capture the cost variance.",
                "analyst",
                2,
                "high",
                False,
            ),
            (
                "Notify buyers and track demurrage exposure",
                "Send a buyer update and open a demurrage log for the affected containers.",
                "analyst",
                1,
                "medium",
                False,
            ),
        ]
    elif _has_word(text, "fire"):
        actions = [
            (
                "Obtain the incident report and verify fire safety",
                "Request the factory and insurer reports, then commission an independent fire-safety inspection.",
                "analyst",
                3,
                "high",
                False,
            ),
            (
                "Hold production until inspection findings are closed",
                "Do not resume production until the accountable safety owner signs off on the findings.",
                "analyst",
                2,
                "high",
                False,
            ),
        ]
    elif _has_word(text, "sanction", "forced", "uflpa"):
        actions = [
            (
                "Run enhanced ownership and traceability due diligence",
                "Collect the full ownership chart, beneficial-ownership declarations, and lot-level origin records; document the review.",
                "analyst",
                4,
                "critical",
                True,
            ),
            (
                "Freeze new orders pending human review",
                "Pause new purchase orders until the compliance owner records a decision and the evidence pack is complete.",
                "analyst",
                1,
                "high",
                True,
            ),
        ]
    elif (
        "export proceeds" in text
        or "export-proceeds" in text
        or "repatriat" in text
    ):
        actions = [
            (
                "Reconcile outstanding export bills",
                "Match shipment, invoice, and repatriation records and assign a finance owner for each exception.",
                "analyst",
                5,
                "high",
                True,
            ),
            (
                "File the required report with the authorized dealer bank",
                "Prepare and retain the filing evidence for any overdue proceeds.",
                "analyst",
                8,
                "high",
                False,
            ),
        ]
    else:
        actions = [
            (
                "Map the potential obligation to policies and suppliers",
                "Identify the accountable owner, affected suppliers, and internal policy; record the evidence used.",
                "analyst",
                7,
                "high",
                False,
            ),
            (
                "Request evidence from the accountable owner",
                "Ask for the documents needed to confirm applicability and close the evidence gap.",
                "analyst",
                10,
                "medium",
                False,
            ),
        ]

    return [
        DraftAction(
            title=title,
            description=description,
            owner_role=owner_role,
            due_date=today + timedelta(days=days),
            priority=priority,
            automated=automated,
        )
        for title, description, owner_role, days, priority, automated in actions
    ]
