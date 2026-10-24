from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import ApproverUser, CurrentUser, SessionDep
from app.core.ratelimit import rate_limit
from app.schemas import (
    ApprovalDecisionRequest,
    ApprovalListResponse,
    ApprovalOut,
)
from app.services.approvals import decide_approval, get_pending_count, list_approvals

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=ApprovalListResponse)
async def approvals(
    session: SessionDep,
    _user: CurrentUser,
    status_filter: Annotated[str | None, Query(alias="status")] = "pending",
    assigned_to: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApprovalListResponse:
    items, total = await list_approvals(
        session, status=status_filter, assigned_to=assigned_to, limit=limit, offset=offset
    )
    return ApprovalListResponse(items=items, total=total)


@router.get("/pending-count")
async def pending_count(session: SessionDep, _user: CurrentUser) -> dict[str, int]:
    return {"count": await get_pending_count(session)}


@router.post(
    "/{approval_id}/decision",
    response_model=ApprovalOut,
    dependencies=[Depends(rate_limit("approval-decision", "mutation"))],
)
async def decision(
    approval_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    session: SessionDep,
    user: ApproverUser,
) -> ApprovalOut:
    try:
        approval = await decide_approval(
            session,
            approval_id,
            decision=payload.decision,
            rationale=payload.rationale,
            actor=user,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    await session.commit()
    return approval
