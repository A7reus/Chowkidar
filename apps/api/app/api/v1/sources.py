from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AnalystUser, CurrentUser, SessionDep
from app.db.models import Source
from app.schemas import SourceOut, SourceSyncResponse
from app.services.sources import list_sources, sync_source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def get_sources(session: SessionDep, _user: CurrentUser) -> list[SourceOut]:
    return await list_sources(session)


@router.post("/{source_id}/sync", response_model=SourceSyncResponse)
async def sync(
    source_id: uuid.UUID,
    session: SessionDep,
    user: AnalystUser,
) -> SourceSyncResponse:
    source = (
        await session.execute(select(Source).where(Source.id == source_id))
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    result = await sync_source(session, source, user)
    await session.commit()
    return result
