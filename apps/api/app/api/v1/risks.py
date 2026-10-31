from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AnalystUser, CurrentUser, SessionDep
from app.schemas import (
    ActionCreateRequest,
    ActionOut,
    ActionUpdateRequest,
    ApprovalCreateRequest,
    ApprovalOut,
    RiskDetail,
    RiskLineageOut,
    RiskListResponse,
    RiskUpdateRequest,
)
from app.services.risks import (
    create_action,
    get_risk,
    get_risk_lineage,
    list_risks,
    request_approval,
    update_action,
    update_risk_status,
)

router = APIRouter(tags=["risks"])


@router.get("/risks", response_model=RiskListResponse)
async def risks(
    session: SessionDep,
    _user: CurrentUser,
    priority: str | None = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    verification_status: str | None = None,
    supplier_id: uuid.UUID | None = None,
    category: str | None = None,
    q: str | None = None,
    sort: Annotated[str, Query(pattern="^(score|created_at|updated_at|priority)$")] = "score",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RiskListResponse:
    return await list_risks(
        session,
        priority=priority,
        status=status_filter,
        verification_status=verification_status,
        supplier_id=supplier_id,
        category=category,
        query=q,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/risks/{risk_id}", response_model=RiskDetail)
async def risk_detail(risk_id: uuid.UUID, session: SessionDep, _user: CurrentUser) -> RiskDetail:
    risk = await get_risk(session, risk_id)
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    return risk


@router.get("/risks/{risk_id}/lineage", response_model=RiskLineageOut)
async def risk_lineage(
    risk_id: uuid.UUID, session: SessionDep, _user: CurrentUser
) -> RiskLineageOut:
    lineage = await get_risk_lineage(session, risk_id)
    if lineage is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    return lineage


@router.patch("/risks/{risk_id}", response_model=RiskDetail)
async def patch_risk(
    risk_id: uuid.UUID,
    payload: RiskUpdateRequest,
    session: SessionDep,
    user: AnalystUser,
) -> RiskDetail:
    risk = await update_risk_status(session, risk_id, payload, user)
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    await session.commit()
    return risk


@router.post("/risks/{risk_id}/actions", response_model=ActionOut)
async def add_action(
    risk_id: uuid.UUID,
    payload: ActionCreateRequest,
    session: SessionDep,
    user: AnalystUser,
) -> ActionOut:
    action = await create_action(session, risk_id, payload, user)
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    await session.commit()
    return action


@router.patch("/actions/{action_id}", response_model=ActionOut)
async def patch_action(
    action_id: uuid.UUID,
    payload: ActionUpdateRequest,
    session: SessionDep,
    user: AnalystUser,
) -> ActionOut:
    action = await update_action(session, action_id, payload, user)
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
    await session.commit()
    return action


@router.post("/risks/{risk_id}/approvals", response_model=ApprovalOut)
async def create_approval(
    risk_id: uuid.UUID,
    payload: ApprovalCreateRequest,
    session: SessionDep,
    user: AnalystUser,
) -> ApprovalOut:
    approval = await request_approval(session, risk_id, payload, user)
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk or action not found",
        )
    await session.commit()
    return approval
