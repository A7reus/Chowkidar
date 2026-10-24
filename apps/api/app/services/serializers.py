from __future__ import annotations

from typing import cast

from app.db.models import (
    AgentRun,
    Approval,
    Obligation,
    RemediationAction,
    ReportRun,
    Risk,
    RiskEvidence,
    Signal,
    Source,
    Supplier,
)
from app.schemas import (
    ActionOut,
    AgentRunOut,
    ApprovalOut,
    ApprovalStatusLiteral,
    EvidenceOut,
    ObligationOut,
    ReportOut,
    RiskDetail,
    RiskListItem,
    SignalOut,
    SourceOut,
    SupplierOut,
    VerificationLiteral,
)


def source_out(source: Source) -> SourceOut:
    return SourceOut.model_validate(source)


def signal_out(signal: Signal) -> SignalOut:
    return SignalOut(
        id=signal.id,
        source_id=signal.source_id,
        supplier_id=signal.supplier_id,
        external_id=signal.external_id,
        title=signal.title,
        summary=signal.summary,
        url=signal.url,
        jurisdiction=signal.jurisdiction,
        signal_type=signal.signal_type,
        severity=signal.severity,
        published_at=signal.published_at,
        ingested_at=signal.ingested_at,
        status=signal.status,
        source_name=signal.source.name if signal.source else None,
        supplier_name=signal.supplier.name if signal.supplier else None,
    )


def supplier_out(supplier: Supplier) -> SupplierOut:
    return SupplierOut.model_validate(supplier)


def obligation_out(obligation: Obligation) -> ObligationOut:
    return ObligationOut.model_validate(obligation)


def evidence_out(evidence: RiskEvidence) -> EvidenceOut:
    return EvidenceOut.model_validate(evidence)


def action_out(action: RemediationAction) -> ActionOut:
    return ActionOut.model_validate(action)


def approval_out(
    approval: Approval,
    *,
    risk_title: str | None = None,
    action_title: str | None = None,
) -> ApprovalOut:
    return ApprovalOut(
        id=approval.id,
        risk_id=approval.risk_id,
        action_id=approval.action_id,
        requested_by=approval.requested_by,
        assigned_to=approval.assigned_to,
        status=cast(ApprovalStatusLiteral, approval.status),
        decision=approval.decision,
        rationale=approval.rationale,
        decided_at=approval.decided_at,
        created_at=approval.created_at,
        risk_title=risk_title or (approval.risk.title if approval.risk else None),
        action_title=action_title or (approval.action.title if approval.action else None),
    )


def risk_list_item(risk: Risk) -> RiskListItem:
    return RiskListItem(
        id=risk.id,
        title=risk.title,
        description=risk.description,
        category=risk.category,
        severity=risk.severity,
        likelihood=risk.likelihood,
        exposure=risk.exposure,
        score=risk.score,
        priority=risk.priority,
        status=risk.status,
        confidence=risk.confidence,
        verification_status=cast(VerificationLiteral, risk.verification_status),
        supplier_name=risk.supplier.name if risk.supplier else None,
        obligation_title=risk.obligation.title if risk.obligation else None,
        evidence_count=len(risk.evidence),
        action_count=len(risk.actions),
        created_at=risk.created_at,
        updated_at=risk.updated_at,
    )


def risk_detail(risk: Risk) -> RiskDetail:
    item = risk_list_item(risk)
    action_titles = {action.id: action.title for action in risk.actions}
    return RiskDetail(
        **item.model_dump(),
        rationale=risk.rationale,
        score_breakdown=risk.score_breakdown or {},
        supplier=supplier_out(risk.supplier) if risk.supplier else None,
        obligation=obligation_out(risk.obligation) if risk.obligation else None,
        evidence=[evidence_out(evidence) for evidence in risk.evidence],
        actions=[action_out(action) for action in risk.actions],
        approvals=[
            approval_out(
                approval,
                risk_title=risk.title,
                action_title=(
                    action_titles.get(approval.action_id) if approval.action_id else None
                ),
            )
            for approval in risk.approvals
        ],
    )


def report_out(report: ReportRun) -> ReportOut:
    return ReportOut(
        id=report.id,
        format=report.format,
        status=report.status,
        storage_backend=report.storage_backend,
        content_sha256=report.content_sha256,
        size_bytes=report.size_bytes,
        summary=report.summary or {},
        generated_at=report.generated_at,
    )


def agent_run_out(run: AgentRun) -> AgentRunOut:
    return AgentRunOut.model_validate(run)
