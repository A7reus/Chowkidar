from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, SessionDep
from app.schemas import AuditListResponse, AuditVerifyOut
from app.services.audit import list_audit_events, verify_chain

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
async def audit_events(
    session: SessionDep,
    _user: AdminUser,
    action: str | None = None,
    entity_type: str | None = None,
    actor_email: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditListResponse:
    items, total = await list_audit_events(
        session,
        action=action,
        entity_type=entity_type,
        actor_email=actor_email,
        limit=limit,
        offset=offset,
    )
    return AuditListResponse(items=items, total=total)


@router.get("/verify", response_model=AuditVerifyOut)
async def verify(session: SessionDep, _user: AdminUser) -> AuditVerifyOut:
    return await verify_chain(session)
