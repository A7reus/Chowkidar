from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import record_audit
from app.core.auth import UserContext
from app.db.models import Approval, RemediationAction, Risk
from app.schemas import (
    ActionCreateRequest,
    ActionOut,
    ActionUpdateRequest,
    ApprovalCreateRequest,
    ApprovalOut,
    RiskDetail,
    RiskListResponse,
    RiskUpdateRequest,
)
from app.services.serializers import action_out, approval_out, risk_detail, risk_list_item


def _risk_options():
    return (
        selectinload(Risk.supplier),
        selectinload(Risk.obligation),
        selectinload(Risk.evidence),
        selectinload(Risk.actions),
        selectinload(Risk.approvals),
    )


async def list_risks(
    session: AsyncSession,
    *,
    priority: str | None = None,
    status: str | None = None,
    verification_status: str | None = None,
    supplier_id: uuid.UUID | None = None,
    category: str | None = None,
    query: str | None = None,
    sort: str = "score",
    limit: int = 50,
    offset: int = 0,
) -> RiskListResponse:
    conditions = []
    if priority:
        conditions.append(Risk.priority == priority)
    if status:
        conditions.append(Risk.status == status)
    if verification_status:
        conditions.append(Risk.verification_status == verification_status)
    if supplier_id:
        conditions.append(Risk.supplier_id == supplier_id)
    if category:
        conditions.append(Risk.category == category)
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(
            or_(
                Risk.title.ilike(pattern),
                Risk.description.ilike(pattern),
                Risk.rationale.ilike(pattern),
            )
        )

    total = (
        await session.execute(select(func.count()).select_from(Risk).where(*conditions))
    ).scalar_one()
    order_by = {
        "score": Risk.score.desc(),
        "created_at": Risk.created_at.desc(),
        "updated_at": Risk.updated_at.desc(),
        "priority": Risk.priority.asc(),
    }.get(sort, Risk.score.desc())
    risks = list(
        (
            await session.execute(
                select(Risk)
                .options(*_risk_options())
                .where(*conditions)
                .order_by(order_by)
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    priority_rows = (
        await session.execute(select(Risk.priority, func.count(Risk.id)).group_by(Risk.priority))
    ).all()
    counts = {priority_name: 0 for priority_name in ("critical", "high", "medium", "low")}
    for priority_name, count in priority_rows:
        counts[str(priority_name)] = int(count)
    return RiskListResponse(
        items=[risk_list_item(risk) for risk in risks],
        total=int(total),
        counts_by_priority=counts,
    )


async def get_risk(session: AsyncSession, risk_id: uuid.UUID) -> RiskDetail | None:
    risk = (
        await session.execute(select(Risk).options(*_risk_options()).where(Risk.id == risk_id))
    ).scalar_one_or_none()
    if risk is None:
        return None
    return risk_detail(risk)


async def create_action(
    session: AsyncSession,
    risk_id: uuid.UUID,
    payload: ActionCreateRequest,
    actor: UserContext,
) -> ActionOut | None:
    risk = await session.get(Risk, risk_id)
    if risk is None:
        return None
    action = RemediationAction(
        risk_id=risk.id,
        title=payload.title,
        description=payload.description,
        owner_role=payload.owner_role,
        due_date=payload.due_date,
        priority=payload.priority,
        status="draft",
        automated=False,
    )
    session.add(action)
    await session.flush()
    await record_audit(
        session,
        actor=actor,
        action="action.created",
        entity_type="remediation_action",
        entity_id=str(action.id),
        payload={
            "risk_id": str(risk.id),
            "title": action.title,
            "priority": action.priority,
            "demo": True,
        },
    )
    return action_out(action)


async def update_action(
    session: AsyncSession,
    action_id: uuid.UUID,
    payload: ActionUpdateRequest,
    actor: UserContext,
) -> ActionOut | None:
    action = await session.get(RemediationAction, action_id)
    if action is None:
        return None
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(action, field, value)
    await session.flush()
    await record_audit(
        session,
        actor=actor,
        action="action.updated",
        entity_type="remediation_action",
        entity_id=str(action.id),
        payload={
            "risk_id": str(action.risk_id),
            "changed": sorted(updates),
            "status": action.status,
            "demo": True,
        },
    )
    return action_out(action)


async def update_risk_status(
    session: AsyncSession,
    risk_id: uuid.UUID,
    payload: RiskUpdateRequest,
    actor: UserContext,
) -> RiskDetail | None:
    risk = (
        await session.execute(select(Risk).options(*_risk_options()).where(Risk.id == risk_id))
    ).scalar_one_or_none()
    if risk is None:
        return None
    previous = risk.status
    risk.status = payload.status
    risk.updated_at = datetime.now(UTC)
    await session.flush()
    await record_audit(
        session,
        actor=actor,
        action="risk.status_changed",
        entity_type="risk",
        entity_id=str(risk.id),
        payload={
            "from": previous,
            "to": risk.status,
            "title": risk.title,
            "demo": True,
        },
    )
    return risk_detail(risk)


async def request_approval(
    session: AsyncSession,
    risk_id: uuid.UUID,
    payload: ApprovalCreateRequest,
    actor: UserContext,
) -> ApprovalOut | None:
    risk = await session.get(Risk, risk_id)
    if risk is None:
        return None
    action = await session.get(RemediationAction, payload.action_id)
    if action is None or action.risk_id != risk.id:
        return None
    existing = (
        await session.execute(
            select(Approval)
            .where(
                Approval.action_id == action.id,
                Approval.status == "pending",
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return approval_out(existing, risk_title=risk.title, action_title=action.title)

    approval = Approval(
        risk_id=risk.id,
        action_id=action.id,
        requested_by=actor.email,
        assigned_to=payload.assigned_to,
        status="pending",
        extra={"note": payload.note, "demo": True},
    )
    action.status = "pending_approval"
    session.add(approval)
    await session.flush()
    await record_audit(
        session,
        actor=actor,
        action="approval.requested",
        entity_type="approval",
        entity_id=str(approval.id),
        payload={
            "risk_id": str(risk.id),
            "risk_title": risk.title,
            "action_id": str(action.id),
            "action_title": action.title,
            "assigned_to": approval.assigned_to,
            "demo": True,
        },
    )
    return approval_out(approval, risk_title=risk.title, action_title=action.title)
