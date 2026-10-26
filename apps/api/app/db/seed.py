from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.auth import DEMO_USERS, Role
from app.core.config import ROOT_DIR
from app.db.base import Base
from app.db.models import (
    AgentRun,
    Approval,
    Buyer,
    Company,
    EvidenceChunk,
    Obligation,
    Policy,
    RemediationAction,
    Risk,
    RiskEvidence,
    Signal,
    Source,
    Supplier,
    User,
)
from app.db.session import AsyncSessionLocal
from app.rag.chunking import build_signal_chunks
from app.services.scoring import score_risk

FIXTURE_PATH = ROOT_DIR / "data" / "fixtures" / "demo.json"


def load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def iso_now() -> datetime:
    return datetime.now(UTC)


async def truncate_all(session: AsyncSession) -> None:
    table_names = [table.name for table in Base.metadata.sorted_tables]
    quoted = ", ".join(f'"{name}"' for name in table_names)
    await session.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))


async def seed() -> dict[str, int]:
    fixture = load_fixture()
    now = iso_now()
    counts = {
        "companies": 0,
        "users": 0,
        "suppliers": 0,
        "sources": 0,
        "signals": 0,
        "obligations": 0,
        "risks": 0,
        "actions": 0,
        "approvals": 0,
        "audit_events": 0,
        "evidence_chunks": 0,
    }

    async with AsyncSessionLocal() as session:
        await truncate_all(session)

        company_data = fixture["company"]
        company = Company(
            name=company_data["name"],
            country=company_data["country"],
            sector=company_data["sector"],
            profile=company_data.get("profile", {}),
        )
        session.add(company)
        await session.flush()
        company_id = company.id
        counts["companies"] += 1

        user_ids: dict[str, uuid.UUID] = {}
        for user_data in fixture["users"]:
            role = Role(user_data["role"])
            demo_user = DEMO_USERS[role]
            user = User(
                id=uuid.UUID(demo_user.id),
                email=user_data["email"],
                name=user_data["name"],
                role=role.value,
                is_active=True,
            )
            session.add(user)
            user_ids[user_data["key"]] = user.id
        await session.flush()
        counts["users"] = len(fixture["users"])

        buyer_ids: dict[str, uuid.UUID] = {}
        for buyer_data in fixture["buyers"]:
            buyer = Buyer(
                company_id=company_id,
                name=buyer_data["name"],
                country=buyer_data["country"],
                requirements_summary=buyer_data["requirements_summary"],
            )
            session.add(buyer)
            await session.flush()
            buyer_ids[buyer_data["key"]] = buyer.id

        supplier_ids: dict[str, uuid.UUID] = {}
        for supplier_data in fixture["suppliers"]:
            supplier = Supplier(
                company_id=company_id,
                name=supplier_data["name"],
                country=supplier_data["country"],
                tier=supplier_data["tier"],
                category=supplier_data["category"],
                status=supplier_data["status"],
                risk_level=supplier_data["risk_level"],
                profile=supplier_data.get("profile", {}),
            )
            session.add(supplier)
            await session.flush()
            supplier_ids[supplier_data["key"]] = supplier.id
        counts["suppliers"] = len(supplier_ids)

        for policy_data in fixture["policies"]:
            session.add(
                Policy(
                    company_id=company_id,
                    name=policy_data["name"],
                    policy_type=policy_data["policy_type"],
                    version=policy_data["version"],
                    owner=policy_data["owner"],
                    status=policy_data["status"],
                    summary=policy_data["summary"],
                )
            )

        source_ids: dict[str, uuid.UUID] = {}
        source_names: dict[str, str] = {}
        for source_data in fixture["sources"]:
            source = Source(
                name=source_data["name"],
                stream_key=source_data["stream_key"],
                source_type=source_data["source_type"],
                jurisdiction=source_data["jurisdiction"],
                url=source_data["url"],
                cadence=source_data["cadence"],
                status=source_data["status"],
                connector_key=source_data.get("connector_key", "fixture"),
                connector_config=source_data.get("connector_config", {}),
                last_sync_mode="fixture",
                last_signal_count=sum(
                    1
                    for item in fixture["signals"]
                    if item["source_key"] == source_data["key"]
                ),
                last_synced_at=now
                - timedelta(hours=source_data.get("last_synced_hours_ago", 1)),
                last_error=source_data.get("last_error"),
            )
            session.add(source)
            await session.flush()
            source_ids[source_data["key"]] = source.id
            source_names[source_data["key"]] = source_data["name"]
        counts["sources"] = len(source_ids)

        signal_ids: dict[str, uuid.UUID] = {}
        signal_chunks: dict[str, list[EvidenceChunk]] = {}
        for signal_data in fixture["signals"]:
            source_id = source_ids[signal_data["source_key"]]
            supplier_key = signal_data.get("supplier_key")
            signal = Signal(
                source_id=source_id,
                supplier_id=supplier_ids.get(supplier_key) if supplier_key else None,
                external_id=signal_data["external_id"],
                title=signal_data["title"],
                summary=signal_data["summary"],
                raw_text=signal_data["raw_text"],
                url=signal_data["url"],
                jurisdiction=signal_data["jurisdiction"],
                signal_type=signal_data["signal_type"],
                severity=signal_data["severity"],
                published_at=datetime.fromisoformat(signal_data["published_at"]),
                ingested_at=now - timedelta(days=signal_data.get("ingested_days_ago", 1)),
                status=signal_data["status"],
                extra=signal_data.get("metadata", {}),
            )
            session.add(signal)
            await session.flush()
            signal_ids[signal_data["key"]] = signal.id

            chunks = build_signal_chunks(
                title=signal.title,
                raw_text=signal.raw_text,
                jurisdiction=signal.jurisdiction,
                citation_url=signal.url,
                citation_label=f"{source_names[signal_data['source_key']]} — {signal.title}",
                section_path="Signal body",
                extra={"signal_key": signal_data["key"], "demo": True},
            )
            stored_chunks: list[EvidenceChunk] = []
            for chunk in chunks:
                evidence = EvidenceChunk(
                    signal_id=signal.id,
                    content=chunk.content,
                    citation_label=chunk.citation_label,
                    citation_url=chunk.citation_url,
                    section_path=chunk.section_path,
                    embedding=chunk.embedding,
                    search_vector=func.to_tsvector("english", chunk.content),
                    extra=chunk.metadata,
                )
                session.add(evidence)
                stored_chunks.append(evidence)
            await session.flush()
            signal_chunks[signal_data["key"]] = stored_chunks
            counts["signals"] += 1
            counts["evidence_chunks"] += len(stored_chunks)

        obligation_ids: dict[str, uuid.UUID] = {}
        for obligation_data in fixture["obligations"]:
            signal_id = signal_ids[obligation_data["signal_key"]]
            signal = await session.get(Signal, signal_id)
            if signal is None:
                raise RuntimeError(f"Missing signal for obligation: {obligation_data['key']}")
            effective_date = (
                date.fromisoformat(obligation_data["effective_date"])
                if obligation_data.get("effective_date")
                else None
            )
            obligation = Obligation(
                signal_id=signal_id,
                source_id=signal.source_id,
                title=obligation_data["title"],
                description=obligation_data["description"],
                jurisdiction=obligation_data["jurisdiction"],
                obligation_type=obligation_data["obligation_type"],
                applies_to=obligation_data["applies_to"],
                effective_date=effective_date,
                confidence=obligation_data["confidence"],
                citation_url=obligation_data["citation_url"],
                citation_quote=obligation_data["citation_quote"],
                section_path=obligation_data["section_path"],
                status=obligation_data["status"],
            )
            session.add(obligation)
            await session.flush()
            obligation_ids[obligation_data["key"]] = obligation.id
        counts["obligations"] = len(obligation_ids)

        risk_ids: dict[str, uuid.UUID] = {}
        action_ids: dict[tuple[str, int], uuid.UUID] = {}
        approval_ids: dict[str, uuid.UUID] = {}
        for risk_data in fixture["risks"]:
            score_data = score_risk(
                risk_data["severity"], risk_data["likelihood"], risk_data["exposure"]
            )
            created_at = now - timedelta(days=risk_data.get("created_days_ago", 0))
            supplier_key = risk_data.get("supplier_key")
            risk = Risk(
                company_id=company_id,
                supplier_id=supplier_ids.get(supplier_key) if supplier_key else None,
                obligation_id=obligation_ids.get(risk_data["obligation_key"]),
                title=risk_data["title"],
                description=risk_data["description"],
                category=risk_data["category"],
                severity=risk_data["severity"],
                likelihood=risk_data["likelihood"],
                exposure=risk_data["exposure"],
                score=score_data["score"],
                priority=score_data["priority"],
                status=risk_data["status"],
                rationale=risk_data["rationale"],
                confidence=risk_data["confidence"],
                verification_status=risk_data["verification_status"],
                score_breakdown=score_data,
                extra={"demo": True, "created_days_ago": risk_data.get("created_days_ago", 0)},
                created_at=created_at,
                updated_at=created_at + timedelta(hours=2),
            )
            session.add(risk)
            await session.flush()
            risk_ids[risk_data["key"]] = risk.id

            for evidence_data in risk_data.get("evidence", []):
                chunks = signal_chunks.get(evidence_data["signal_key"], [])
                quote = evidence_data["quote"]
                chunk = next(
                    (item for item in chunks if quote.lower() in item.content.lower()),
                    chunks[0] if chunks else None,
                )
                session.add(
                    RiskEvidence(
                        risk_id=risk.id,
                        evidence_chunk_id=chunk.id if chunk else None,
                        quote=quote,
                        citation_url=evidence_data["citation_url"],
                        citation_label=evidence_data["citation_label"],
                        confidence=evidence_data["confidence"],
                        supports=evidence_data.get("supports", "supports"),
                    )
                )

            first_action: RemediationAction | None = None
            for action_index, action_data in enumerate(risk_data.get("actions", [])):
                action = RemediationAction(
                    risk_id=risk.id,
                    title=action_data["title"],
                    description=action_data["description"],
                    owner_role=action_data["owner_role"],
                    due_date=date.fromisoformat(action_data["due_date"])
                    if action_data.get("due_date")
                    else None,
                    priority=action_data["priority"],
                    status=action_data["status"],
                    automated=action_data["automated"],
                )
                session.add(action)
                await session.flush()
                action_ids[(risk_data["key"], action_index)] = action.id
                if first_action is None or action.status in {"pending_approval", "approved"}:
                    first_action = action
                counts["actions"] += 1

            approval_data = risk_data.get("approval")
            if approval_data and first_action is not None:
                decided_at = (
                    now - timedelta(days=approval_data.get("decided_days_ago", 0))
                    if approval_data.get("decided_days_ago") is not None
                    else None
                )
                approval = Approval(
                    risk_id=risk.id,
                    action_id=first_action.id,
                    requested_by=approval_data["requested_by"],
                    assigned_to=approval_data["assigned_to"],
                    status=approval_data["status"],
                    decision=approval_data.get("decision"),
                    rationale=approval_data.get("rationale"),
                    decided_at=decided_at,
                    extra={"demo": True},
                    created_at=now - timedelta(days=2),
                )
                session.add(approval)
                await session.flush()
                approval_ids[risk_data["key"]] = approval.id
                counts["approvals"] += 1

        counts["risks"] = len(risk_ids)

        agent_data = fixture["agent_run"]
        started_at = now - timedelta(days=agent_data.get("started_days_ago", 1))
        session.add(
            AgentRun(
                workflow=agent_data["workflow"],
                status=agent_data["status"],
                input=agent_data["input"],
                output=agent_data["output"],
                started_at=started_at,
                finished_at=started_at
                + timedelta(seconds=agent_data.get("duration_seconds", 30)),
                trace_id=agent_data["trace_id"],
            )
        )

        await session.flush()

        admin = DEMO_USERS[Role.ADMIN]
        for source_key, source_id in source_ids.items():
            source_data = next(
                item for item in fixture["sources"] if item["key"] == source_key
            )
            await record_audit(
                session,
                actor=admin,
                action="source.sync",
                entity_type="source",
                entity_id=str(source_id),
                payload={
                    "stream_key": source_key,
                    "source_name": source_names[source_key],
                    "connector": source_data.get("connector_key", "fixture"),
                    "mode": "fixture",
                    "demo": True,
                },
            )
            counts["audit_events"] += 1

        await record_audit(
            session,
            actor=admin,
            action="pipeline.run",
            entity_type="agent_run",
            entity_id="demo-trace-2026-10-23",
            payload={
                "mode": "mock",
                "signals": counts["signals"],
                "obligations": counts["obligations"],
                "risks": counts["risks"],
                "actions": counts["actions"],
                "demo": True,
            },
        )
        counts["audit_events"] += 1

        for risk_data in fixture["risks"]:
            approval_data = risk_data.get("approval")
            if not approval_data:
                continue
            risk_id = risk_ids[risk_data["key"]]
            approval_id = approval_ids[risk_data["key"]]
            action_id = action_ids[(risk_data["key"], 0)]
            await record_audit(
                session,
                actor=admin,
                action="approval.requested",
                entity_type="approval",
                entity_id=str(approval_id),
                payload={
                    "risk_id": str(risk_id),
                    "risk_title": risk_data["title"],
                    "action_id": str(action_id),
                    "assigned_to": approval_data["assigned_to"],
                    "status": approval_data["status"],
                    "demo": True,
                },
            )
            counts["audit_events"] += 1
            if approval_data["status"] == "approved":
                await record_audit(
                    session,
                    actor=DEMO_USERS[Role.APPROVER],
                    action="approval.approved",
                    entity_type="approval",
                    entity_id=str(approval_id),
                    payload={
                        "risk_id": str(risk_id),
                        "decision": "approve",
                        "rationale": approval_data.get("rationale", ""),
                        "demo": True,
                    },
                )
                counts["audit_events"] += 1

        await session.commit()

    return counts


def main() -> None:
    counts = asyncio.run(seed())
    print("Seed complete:")
    for key, value in counts.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
