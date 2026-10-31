from __future__ import annotations

import re
import uuid
from datetime import date
from typing import Any, TypedDict, cast

from langgraph.graph import END, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.llm import LLMUnavailable, get_llm_client
from app.agents.mock import extract_mock, map_mock, remediation_mock
from app.agents.prompts import EXTRACTION_SYSTEM, PROMPT_VERSION, RATIONALE_SYSTEM
from app.agents.schemas import ExtractedObligation
from app.agents.verifier import verify_risk, verify_risk_live
from app.core.audit import record_audit
from app.core.auth import UserContext
from app.core.config import get_settings
from app.db.models import (
    Company,
    EvidenceChunk,
    Obligation,
    RemediationAction,
    Risk,
    RiskEvidence,
    Signal,
)
from app.services.scoring import score_risk


class PipelineState(TypedDict, total=False):
    source_ids: list[str] | None
    mode: str
    signals: list[dict[str, Any]]
    extracted: list[dict[str, Any]]
    mapped: list[dict[str, Any]]
    scored: list[dict[str, Any]]
    remediated: list[dict[str, Any]]
    verified: list[dict[str, Any]]
    persisted: list[str]
    errors: list[str]
    counts: dict[str, int]
    trace_id: str
    message: str
    repair_attempts: int
    routing: list[dict[str, Any]]


def _normalize(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def route_after_verify(state: PipelineState, max_attempts: int) -> str:
    """Route to one bounded evidence-repair cycle or straight to persistence."""
    if int(state.get("repair_attempts", 0)) >= max_attempts:
        return "persist"
    unresolved = any(
        item.get("verification_status") != "verified" for item in state.get("verified", [])
    )
    return "repair" if unresolved else "persist"


def repair_evidence(
    risk: dict[str, Any],
    signal: dict[str, Any],
    chunk_contents: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Re-retrieve a verbatim quote and a valid citation for one risk.

    This is deliberately deterministic: repair only changes evidence, never the
    risk severity or the source text. If a verbatim quote cannot be found, the
    risk remains unresolved and is persisted as ``needs_review``.
    """
    source_text = str(signal.get("raw_text") or "")
    normalized_source = _normalize(source_text)
    notes: list[str] = []
    evidence = [dict(item) for item in risk.get("evidence") or []]

    def is_verbatim(quote: str) -> bool:
        normalized = _normalize(quote)
        return bool(normalized) and normalized in normalized_source

    valid_quote = next(
        (
            str(item.get("quote") or "")
            for item in evidence
            if is_verbatim(str(item.get("quote") or ""))
        ),
        "",
    )
    if not valid_quote:
        candidates: list[str] = []
        for item in evidence:
            candidates.append(str(item.get("quote") or ""))
        for content in chunk_contents:
            piece = content.split("\n\n", 1)[-1] if content.startswith("Document:") else content
            candidates.extend(
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+", piece)
                if sentence.strip()
            )
        candidates.extend(
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", source_text)
            if sentence.strip()
        )
        candidates.append(str(signal.get("title") or ""))
        valid_quote = next(
            (candidate for candidate in candidates if is_verbatim(candidate) and len(candidate) >= 20),
            "",
        )
        if not valid_quote and source_text:
            valid_quote = source_text[:400].strip()
        if valid_quote:
            notes.append("Re-retrieved evidence and replaced a non-verbatim quote.")
        else:
            notes.append("No verbatim evidence quote could be re-retrieved.")

    citation_url = next(
        (
            str(item.get("citation_url") or "")
            for item in evidence
            if str(item.get("citation_url") or "").startswith("http")
        ),
        "",
    )
    if not citation_url:
        citation_url = str(signal.get("url") or "")
        if citation_url.startswith("http"):
            notes.append("Restored the source citation URL.")

    if not valid_quote:
        return evidence, notes

    repaired = {
        "quote": valid_quote,
        "citation_url": citation_url,
        "citation_label": str(
            risk.get("citation_label")
            or f"{signal.get('source_name') or 'Monitored source'} — {signal.get('title') or ''}"
        ),
        "confidence": max(
            0.7,
            max(
                (float(item.get("confidence") or 0) for item in evidence),
                default=0,
            ),
        ),
        "supports": "supports",
    }
    if not evidence:
        notes.append("Attached the first verbatim source quote as evidence.")
    return [repaired], notes



def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


class PipelineRunner:
    def __init__(self, session: AsyncSession, actor: UserContext, mode: str = "mock") -> None:
        self.session = session
        self.actor = actor
        self.settings = get_settings()
        self.llm = get_llm_client()
        self.mode = (
            "live"
            if mode == "live"
            and self.settings.llm_mode in {"live", "hybrid"}
            and self.settings.llm_live_ready
            else "mock"
        )

    def _build_graph(self):
        graph = StateGraph(PipelineState)
        graph.add_node("ingest", self._ingest)
        graph.add_node("extract", self._extract)
        graph.add_node("map", self._map)
        graph.add_node("score", self._score)
        graph.add_node("remediate", self._remediate)
        graph.add_node("verify", self._verify)
        graph.add_node("repair", self._repair)
        graph.add_node("persist", self._persist)
        graph.set_entry_point("ingest")
        graph.add_edge("ingest", "extract")
        graph.add_edge("extract", "map")
        graph.add_edge("map", "score")
        graph.add_edge("score", "remediate")
        graph.add_edge("remediate", "verify")
        graph.add_conditional_edges(
            "verify",
            self._route_after_verify,
            {"repair": "repair", "persist": "persist"},
        )
        graph.add_edge("repair", "verify")
        graph.add_edge("persist", END)
        return graph.compile()

    def _route_after_verify(self, state: PipelineState) -> str:
        return route_after_verify(state, self.settings.pipeline_max_repair_attempts)

    async def run(
        self,
        source_ids: list[uuid.UUID] | None = None,
        trace_id: str | None = None,
    ) -> PipelineState:
        trace_id = trace_id or f"run-{uuid.uuid4().hex[:12]}"
        graph = self._build_graph()
        initial: PipelineState = {
            "source_ids": [str(source_id) for source_id in source_ids] if source_ids else None,
            "mode": self.mode,
            "trace_id": trace_id,
            "errors": [],
            "persisted": [],
        }
        result = await graph.ainvoke(initial)
        return cast(PipelineState, result)

    async def _ingest(self, state: PipelineState) -> dict[str, Any]:
        limit = (
            self.settings.pipeline_live_max_signals
            if self.mode == "live"
            else self.settings.pipeline_max_signals
        )
        stmt = (
            select(Signal)
            .options(selectinload(Signal.source), selectinload(Signal.supplier))
            .order_by(Signal.ingested_at.desc())
            .limit(limit)
        )
        source_ids = state.get("source_ids")
        if source_ids:
            stmt = stmt.where(Signal.source_id.in_([uuid.UUID(value) for value in source_ids]))
        signals = list((await self.session.execute(stmt)).scalars().all())
        existing = set(
            (await self.session.execute(select(Obligation.signal_id))).scalars().all()
        )
        payload = [
            {
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
                "has_obligation": signal.id in existing,
            }
            for signal in signals
        ]
        return {"signals": payload}

    async def _extract(self, state: PipelineState) -> dict[str, Any]:
        candidates = [signal for signal in state.get("signals", []) if not signal["has_obligation"]]
        extracted: list[dict[str, Any]] = []
        errors = list(state.get("errors", []))
        for signal in candidates:
            obligation: ExtractedObligation | None = None
            if self.mode == "live" and self.llm.live_enabled:
                try:
                    obligation = await self._live_extract(signal)
                except (LLMUnavailable, ValueError) as exc:
                    errors.append(f"Live extraction fallback for {signal['external_id']}: {exc}")
            if obligation is None:
                obligation = extract_mock(signal)
            if obligation is not None:
                extracted.append(obligation.model_dump(mode="json"))
        message = (
            f"Extracted {len(extracted)} new obligation(s) from {len(candidates)} candidate signal(s)."
            if candidates
            else "No new signals require extraction; the risk register is up to date."
        )
        return {"extracted": extracted, "errors": errors, "message": message}

    async def _live_extract(self, signal: dict[str, Any]) -> ExtractedObligation | None:
        user = (
            f"Signal title: {signal['title']}\n"
            f"Source: {signal['source_name']}\n"
            f"Jurisdiction: {signal['jurisdiction']}\n"
            f"Published: {signal['published_at']}\n"
            f"URL: {signal['url']}\n\n"
            f"Source text:\n{signal['raw_text'][:10000]}"
        )
        parsed, _result = await self.llm.complete_json(
            system=EXTRACTION_SYSTEM, user=user, purpose="extraction"
        )
        items = parsed.get("obligations") or []
        if not items:
            return None
        item = dict(items[0])
        return ExtractedObligation(
            signal_id=str(signal["id"]),
            source_id=str(signal["source_id"]),
            signal_title=str(signal["title"]),
            **item,
        )

    async def _map(self, state: PipelineState) -> dict[str, Any]:
        by_id = {signal["id"]: signal for signal in state.get("signals", [])}
        mapped: list[dict[str, Any]] = []
        errors = list(state.get("errors", []))
        for obligation in state.get("extracted", []):
            signal = by_id.get(obligation["signal_id"])
            if signal is None:
                errors.append(f"Missing signal for obligation {obligation['title']}")
                continue
            risk = map_mock(signal, obligation)
            if self.mode == "live" and self.llm.live_enabled:
                try:
                    risk.rationale = await self._live_rationale(signal, risk.model_dump())
                except LLMUnavailable as exc:
                    errors.append(f"Live rationale fallback for {signal['external_id']}: {exc}")
            risk_dict = risk.model_dump(mode="json")
            risk_dict["evidence"] = [
                {
                    "quote": risk.evidence_quote,
                    "citation_url": risk.citation_url,
                    "citation_label": risk.citation_label,
                    "confidence": risk.confidence,
                    "supports": "supports",
                }
            ]
            mapped.append(risk_dict)
        return {"mapped": mapped, "errors": errors}

    async def _live_rationale(self, signal: dict[str, Any], risk: dict[str, Any]) -> str:
        user = (
            f"Signal: {signal['title']}\n{signal['summary']}\n\n"
            f"Risk title: {risk['title']}\n"
            f"Severity: {risk['severity']}, likelihood: {risk['likelihood']}, exposure: {risk['exposure']}\n"
            f"Evidence quote: {risk['evidence_quote']}\n"
            "Write 2-3 sentences of rationale."
        )
        parsed, _result = await self.llm.complete_json(
            system=RATIONALE_SYSTEM, user=user, purpose="rationale"
        )
        rationale = str(parsed.get("rationale") or "").strip()
        return rationale or str(risk["rationale"])

    async def _score(self, state: PipelineState) -> dict[str, Any]:
        scored: list[dict[str, Any]] = []
        for risk in state.get("mapped", []):
            score_data = score_risk(risk["severity"], risk["likelihood"], risk["exposure"])
            scored.append(
                {
                    **risk,
                    "score": score_data["score"],
                    "priority": score_data["priority"],
                    "score_breakdown": score_data,
                }
            )
        return {"scored": scored}

    async def _remediate(self, state: PipelineState) -> dict[str, Any]:
        by_id = {signal["id"]: signal for signal in state.get("signals", [])}
        remediated: list[dict[str, Any]] = []
        for risk in state.get("scored", []):
            signal = by_id.get(risk["signal_id"])
            if signal is None:
                continue
            actions = remediation_mock(signal, risk)
            remediated.append(
                {
                    **risk,
                    "actions": [action.model_dump(mode="json") for action in actions],
                }
            )
        return {"remediated": remediated}

    async def _verify(self, state: PipelineState) -> dict[str, Any]:
        by_id = {signal["id"]: signal for signal in state.get("signals", [])}
        verified: list[dict[str, Any]] = []
        for risk in state.get("remediated", []):
            signal = by_id.get(risk["signal_id"])
            if signal is None:
                continue
            result = (
                await verify_risk_live(risk, signal)
                if self.mode == "live"
                else verify_risk(risk, signal)
            )
            verified.append(
                {
                    **risk,
                    "verification_status": result.status,
                    "verification_notes": result.notes,
                    "verification_confidence": result.confidence,
                }
            )
        routing = list(state.get("routing", []))
        statuses: dict[str, int] = {}
        for item in verified:
            status = str(item.get("verification_status") or "unknown")
            statuses[status] = statuses.get(status, 0) + 1
        routing.append(
            {
                "node": "verify",
                "attempt": int(state.get("repair_attempts", 0)),
                "statuses": statuses,
            }
        )
        return {"verified": verified, "routing": routing}

    async def _repair(self, state: PipelineState) -> dict[str, Any]:
        by_id = {signal["id"]: signal for signal in state.get("signals", [])}
        attempt = int(state.get("repair_attempts", 0)) + 1
        routing = list(state.get("routing", []))
        repaired: list[dict[str, Any]] = []
        for risk in state.get("verified", []):
            if risk.get("verification_status") == "verified":
                repaired.append(risk)
                continue
            signal = by_id.get(risk["signal_id"])
            if signal is None:
                repaired.append(risk)
                continue
            chunks = list(
                (
                    await self.session.execute(
                        select(EvidenceChunk.content)
                        .where(EvidenceChunk.signal_id == uuid.UUID(risk["signal_id"]))
                        .limit(3)
                    )
                )
                .scalars()
                .all()
            )
            evidence, notes = repair_evidence(risk, signal, chunks)
            routing.append(
                {
                    "node": "repair",
                    "attempt": attempt,
                    "risk": risk.get("title"),
                    "previous_status": risk.get("verification_status"),
                    "notes": notes,
                    "chunks_retrieved": len(chunks),
                }
            )
            repaired.append(
                {
                    **risk,
                    "evidence": evidence,
                    "verification_notes": [
                        *(risk.get("verification_notes") or []),
                        *notes,
                    ],
                }
            )
        return {
            "verified": repaired,
            "repair_attempts": attempt,
            "routing": routing,
        }

    async def _persist(self, state: PipelineState) -> dict[str, Any]:
        company_id = (await self.session.execute(select(Company.id).limit(1))).scalar_one_or_none()
        if company_id is None:
            return {
                "persisted": [],
                "errors": [*state.get("errors", []), "No company exists; seed the database first."],
                "counts": {"signals": len(state.get("signals", [])), "risks": 0, "actions": 0},
            }

        obligations_by_signal = {
            obligation["signal_id"]: obligation for obligation in state.get("extracted", [])
        }
        persisted: list[str] = []
        errors = list(state.get("errors", []))
        action_count = 0
        for risk_data in state.get("verified", []):
            signal_uuid = uuid.UUID(risk_data["signal_id"])
            signal = await self.session.get(Signal, signal_uuid)
            if signal is None:
                errors.append(f"Signal disappeared during persist: {risk_data['signal_id']}")
                continue
            obligation_data = obligations_by_signal.get(risk_data["signal_id"])
            if obligation_data is None:
                errors.append(f"Missing obligation data for signal {risk_data['signal_id']}")
                continue

            try:
                async with self.session.begin_nested():
                    existing_obligation = (
                        await self.session.execute(
                            select(Obligation).where(Obligation.signal_id == signal_uuid).limit(1)
                        )
                    ).scalar_one_or_none()
                    if existing_obligation is None:
                        obligation = Obligation(
                            signal_id=signal_uuid,
                            source_id=uuid.UUID(obligation_data["source_id"]),
                            title=obligation_data["title"],
                            description=obligation_data.get("description", ""),
                            jurisdiction=obligation_data.get("jurisdiction", "GLOBAL"),
                            obligation_type=obligation_data.get(
                                "obligation_type", "due_diligence"
                            ),
                            applies_to=obligation_data.get("applies_to", "company"),
                            effective_date=_parse_date(obligation_data.get("effective_date")),
                            confidence=float(obligation_data.get("confidence", 0.7)),
                            citation_url=obligation_data.get("citation_url", ""),
                            citation_quote=obligation_data.get("citation_quote", ""),
                            section_path=obligation_data.get("section_path", ""),
                            status="active",
                        )
                        self.session.add(obligation)
                        await self.session.flush()
                    else:
                        obligation = existing_obligation

                    risk = Risk(
                        company_id=company_id,
                        supplier_id=uuid.UUID(risk_data["supplier_id"])
                        if risk_data.get("supplier_id")
                        else None,
                        obligation_id=obligation.id,
                        title=risk_data["title"],
                        description=risk_data["description"],
                        category=risk_data["category"],
                        severity=risk_data["severity"],
                        likelihood=risk_data["likelihood"],
                        exposure=risk_data["exposure"],
                        score=float(risk_data["score"]),
                        priority=risk_data["priority"],
                        status="open",
                        rationale=risk_data["rationale"],
                        confidence=float(risk_data.get("confidence", 0.75)),
                        verification_status=risk_data["verification_status"],
                        score_breakdown=risk_data["score_breakdown"],
                        extra={
                            "generated_by": "langgraph-pipeline",
                            "prompt_version": PROMPT_VERSION,
                            "mode": self.mode,
                            "trace_id": state.get("trace_id"),
                            "verification_notes": risk_data.get("verification_notes", []),
                            "repair_attempts": int(state.get("repair_attempts", 0)),
                            "routing": [
                                event
                                for event in state.get("routing", [])
                                if event.get("risk") == risk_data["title"]
                            ],
                        },
                    )
                    self.session.add(risk)
                    await self.session.flush()

                    chunks = list(
                        (
                            await self.session.execute(
                                select(EvidenceChunk).where(EvidenceChunk.signal_id == signal_uuid)
                            )
                        )
                        .scalars()
                        .all()
                    )
                    for evidence in risk_data.get("evidence", []):
                        quote = str(evidence.get("quote") or "")
                        chunk = next(
                            (
                                item
                                for item in chunks
                                if quote and quote.lower() in item.content.lower()
                            ),
                            chunks[0] if chunks else None,
                        )
                        self.session.add(
                            RiskEvidence(
                                risk_id=risk.id,
                                evidence_chunk_id=chunk.id if chunk else None,
                                quote=quote,
                                citation_url=evidence.get("citation_url", ""),
                                citation_label=evidence.get("citation_label", ""),
                                confidence=float(evidence.get("confidence", 0.75)),
                                supports=evidence.get("supports", "supports"),
                            )
                        )

                    for action_data in risk_data.get("actions", []):
                        self.session.add(
                            RemediationAction(
                                risk_id=risk.id,
                                title=action_data["title"],
                                description=action_data.get("description", ""),
                                owner_role=action_data.get("owner_role", "analyst"),
                                due_date=_parse_date(action_data.get("due_date")),
                                priority=action_data.get("priority", "medium"),
                                status="draft",
                                automated=bool(action_data.get("automated", False)),
                            )
                        )

                    signal.status = "processed"
                    await record_audit(
                        self.session,
                        actor=self.actor,
                        action="risk.created",
                        entity_type="risk",
                        entity_id=str(risk.id),
                        payload={
                            "risk_title": risk.title,
                            "priority": risk.priority,
                            "score": risk.score,
                            "signal_external_id": signal.external_id,
                            "verification_status": risk.verification_status,
                            "mode": self.mode,
                            "demo": True,
                        },
                    )
                    persisted.append(str(risk.id))
                    action_count += len(risk_data.get("actions", []))
            except Exception as exc:
                errors.append(f"Persist failed for {risk_data['title']}: {type(exc).__name__}: {exc}")

        counts = {
            "signals": len(state.get("signals", [])),
            "candidate_signals": len(state.get("extracted", [])),
            "obligations": len(state.get("extracted", [])),
            "risks": len(persisted),
            "actions": action_count,
        }
        await record_audit(
            self.session,
            actor=self.actor,
            action="pipeline.run",
            entity_type="agent_run",
            entity_id=state.get("trace_id", ""),
            payload={**counts, "mode": self.mode, "demo": True},
        )
        message = (
            f"Created {len(persisted)} cited risk(s) and {action_count} draft action(s)."
            if persisted
            else state.get("message", "No new risks were created.")
        )
        return {
            "persisted": persisted,
            "errors": errors,
            "counts": counts,
            "message": message,
        }
