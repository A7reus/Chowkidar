from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.schemas import SignalDetail, SignalListResponse
from app.services.signals import get_signal, list_signals

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=SignalListResponse)
async def signals(
    session: SessionDep,
    _user: CurrentUser,
    source_id: uuid.UUID | None = None,
    jurisdiction: str | None = None,
    severity: str | None = None,
    signal_type: str | None = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SignalListResponse:
    items, total = await list_signals(
        session,
        source_id=source_id,
        jurisdiction=jurisdiction,
        severity=severity,
        signal_type=signal_type,
        status=status_filter,
        query=q,
        limit=limit,
        offset=offset,
    )
    return SignalListResponse(items=items, total=total)


@router.get("/{signal_id}", response_model=SignalDetail)
async def signal_detail(
    signal_id: uuid.UUID, session: SessionDep, _user: CurrentUser
) -> SignalDetail:
    signal = await get_signal(session, signal_id)
    if signal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")
    return signal
