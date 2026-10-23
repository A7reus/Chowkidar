from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import verify_audit_events
from app.db.models import AuditEvent
from app.schemas import AuditEventOut, AuditVerifyOut


async def list_audit_events(
    session: AsyncSession,
    *,
    action: str | None = None,
    entity_type: str | None = None,
    actor_email: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[AuditEventOut], int]:
    conditions = []
    if action:
        conditions.append(AuditEvent.action == action)
    if entity_type:
        conditions.append(AuditEvent.entity_type == entity_type)
    if actor_email:
        conditions.append(AuditEvent.actor_email == actor_email)
    total = (
        await session.execute(
            select(func.count()).select_from(AuditEvent).where(*conditions)
        )
    ).scalar_one()
    events = list(
        (
            await session.execute(
                select(AuditEvent)
                .where(*conditions)
                .order_by(AuditEvent.seq.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return [AuditEventOut.model_validate(event) for event in events], int(total)


async def verify_chain(session: AsyncSession) -> AuditVerifyOut:
    events = list(
        (await session.execute(select(AuditEvent).order_by(AuditEvent.seq.asc())))
        .scalars()
        .all()
    )
    result = verify_audit_events(events)
    return AuditVerifyOut(**result)
