from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from app.db.models import (
    AgentRun,
    Approval,
    AuditEvent,
    Obligation,
    RemediationAction,
    ReportRun,
    Risk,
    RiskEvidence,
    Signal,
    Source,
)
from app.services.serializers import risk_lineage_out

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


def _lineage_fixture() -> tuple[Risk, ReportRun, AuditEvent, AgentRun]:
    source = Source(
        id=uuid.uuid4(),
        name="US Federal Register",
        stream_key="us_federal_register",
        source_type="regulatory",
        jurisdiction="US",
        url="https://example.gov/source",
        cadence="daily",
        status="active",
        connector_key="federal_register",
        last_signal_count=0,
    )
    signal = Signal(
        id=uuid.uuid4(),
        source_id=source.id,
        source=source,
        supplier_id=None,
        external_id="fr-2026-17231",
        title="BIS revises the Entity List",
        summary="Entity List revision.",
        raw_text="BIS revises the Entity List.",
        url="https://example.gov/signal",
        jurisdiction="US",
        signal_type="regulatory",
        severity="high",
        published_at=NOW,
        status="processed",
        extra={},
    )
    obligation = Obligation(
        id=uuid.uuid4(),
        signal_id=signal.id,
        source_id=source.id,
        signal=signal,
        title="Review Entity List revision",
        description="Review the revised Entity List.",
        jurisdiction="US",
        obligation_type="regulatory",
        applies_to="Compliance",
        effective_date=date(2026, 10, 1),
        confidence=0.8,
        citation_url="https://example.gov/rule",
        citation_quote="BIS revises the Entity List.",
        section_path="Entity List",
        status="active",
    )
    risk = Risk(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        supplier_id=None,
        obligation_id=obligation.id,
        obligation=obligation,
        title="Entity List change requires review",
        description="Review the change.",
        category="regulatory",
        severity="high",
        likelihood="possible",
        exposure="significant",
        score=75.0,
        priority="high",
        status="open",
        rationale="Confirm applicability.",
        confidence=0.8,
        verification_status="verified",
        score_breakdown={},
        extra={"trace_id": "trace-123"},
        created_at=NOW,
        updated_at=NOW,
    )
    risk.evidence = [
        RiskEvidence(
            id=uuid.uuid4(),
            risk_id=risk.id,
            quote="BIS revises the Entity List.",
            citation_url="https://example.gov/rule",
            citation_label="Federal Register",
            confidence=0.9,
            supports="supports",
        )
    ]
    risk.actions = [
        RemediationAction(
            id=uuid.uuid4(),
            risk_id=risk.id,
            title="Review the revised rule",
            description="Check affected suppliers.",
            owner_role="analyst",
            due_date=date(2026, 11, 15),
            priority="high",
            status="draft",
            automated=True,
            created_at=NOW,
        )
    ]
    risk.approvals = [
        Approval(
            id=uuid.uuid4(),
            risk_id=risk.id,
            action_id=risk.actions[0].id,
            requested_by="analyst@example.com",
            assigned_to="approver@example.com",
            status="pending",
            extra={},
            created_at=NOW,
        )
    ]
    report = ReportRun(
        id=uuid.uuid4(),
        company_id=risk.company_id,
        format="json",
        status="ready",
        storage_backend="database",
        content_sha256="abc123",
        size_bytes=1024,
        summary={"risk_ids": [str(risk.id)]},
        generated_at=NOW,
    )
    audit = AuditEvent(
        id=uuid.uuid4(),
        actor_id="user-1",
        actor_email="analyst@example.com",
        action="risk.created",
        entity_type="risk",
        entity_id=str(risk.id),
        payload={"risk_id": str(risk.id)},
        prev_hash="GENESIS",
        hash="hash-1",
        created_at=NOW,
    )
    run = AgentRun(
        id=uuid.uuid4(),
        workflow="ingest_extract_map_score_remediate_verify",
        status="completed",
        input={},
        output={},
        error=None,
        started_at=NOW,
        finished_at=NOW,
        trace_id="trace-123",
    )
    return risk, report, audit, run


def test_risk_lineage_links_source_to_report_and_audit() -> None:
    risk, report, audit, run = _lineage_fixture()

    lineage = risk_lineage_out(risk, reports=[report], audit_events=[audit], agent_run=run)

    assert lineage.risk_id == risk.id
    assert lineage.trace_id == "trace-123"
    assert lineage.agent_run is not None
    assert lineage.agent_run.trace_id == "trace-123"
    assert [node.kind for node in lineage.nodes] == [
        "source",
        "signal",
        "obligation",
        "risk",
        "evidence",
        "action",
        "approval",
        "report",
    ]
    assert lineage.nodes[0].label == "US Federal Register"
    assert lineage.nodes[3].detail == "high · score 75.0"
    assert lineage.nodes[7].href == "/reports"
    assert lineage.reports[0].id == report.id
    assert lineage.audit_events[0].action == "risk.created"


def test_risk_lineage_without_trace_is_explicitly_empty() -> None:
    risk, _report, _audit, _run = _lineage_fixture()
    risk.extra = {}
    risk.obligation = None
    risk.evidence = []
    risk.actions = []
    risk.approvals = []

    lineage = risk_lineage_out(risk, reports=[], audit_events=[], agent_run=None)

    assert lineage.trace_id is None
    assert lineage.agent_run is None
    assert [node.kind for node in lineage.nodes] == ["risk"]
