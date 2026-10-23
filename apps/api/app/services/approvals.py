from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import record_audit
from app.core.auth import Role, UserContext
from app.db.models import Approval
from app.schemas import ApprovalOut
from app.services.serializers import approval_out


async def list_approvals(
    session: AsyncSession,
    *,
    status: str | None = "pending",
    assigned_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ApprovalOut], int]:
    conditions = []
    if status and status != "all":
        conditions.append(Approval.status == status)
    if assigned_to:
        conditions.append(Approval.assigned_to == assigned_to)
    total = (
        await session.execute(
            select(func.count()).select_from(Approval).where(*conditions)
        )
    ).scalar_one()
    approvals = list(
        (
            await session.execute(
                select(Approval)
                .options(selectinload(Approval.risk), selectinload(Approval.action))
                .where(*conditions)
                .order_by(
                    Approval.status.asc(),
                    Approval.created_at.desc(),
                )
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return [approval_out(approval) for approval in approvals], int(total)


async def decide_approval(
    session: AsyncSession,
    approval_id: uuid.UUID,
    *,
    decision: str,
    rationale: str,
    actor: UserContext,
) -> ApprovalOut | None:
    approval = (
        await session.execute(
            select(Approval)
            .options(selectinload(Approval.risk), selectinload(Approval.action))
            .where(Approval.id == approval_id)
        )
    ).scalar_one_or_none()
    if approval is None:
        return None
    if approval.status != "pending":
        raise ValueError("Approval has already been decided")
    if actor.role == Role.APPROVER and actor.email != approval.assigned_to:
        raise PermissionError("This approval is assigned to a different approver")

    approval.status = "approved" if decision == "approve" else "rejected"
    approval.decision = decision
    approval.rationale = rationale
    approval.decided_at = datetime.now(UTC)
    approval.extra = {
        **(approval.extra or {}),
        "decided_by_email": actor.email,
        "decided_by_name": actor.name,
        "decided_by_role": actor.role.value,
    }

    if approval.action is not None:
        approval.action.status = "approved" if decision == "approve" else "rejected"
    if approval.risk is not None and decision == "approve":
        approval.risk.status = "mitigating"

    await session.flush()
    await record_audit(
        session,
        actor=actor,
        action="approval.approved" if decision == "approve" else "approval.rejected",
        entity_type="approval",
        entity_id=str(approval.id),
        payload={
            "risk_id": str(approval.risk_id),
            "risk_title": approval.risk.title if approval.risk else "",
            "action_id": str(approval.action_id) if approval.action_id else "",
            "decision": decision,
            "rationale": rationale,
            "demo": True,
        },
    )
    return approval_out(approval)


async def get_pending_count(session: AsyncSession, assigned_to: str | None = None) -> int:
    conditions = [Approval.status == "pending"]
    if assigned_to:
        conditions.append(Approval.assigned_to == assigned_to)
    return int(
        (
            await session.execute(
                select(func.count()).select_from(Approval).where(*conditions)
            )
        ).scalar_one()
    )
