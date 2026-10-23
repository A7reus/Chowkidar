from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas import GraphOut
from app.services.graph import get_graph

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphOut)
async def graph(session: SessionDep, _user: CurrentUser) -> GraphOut:
    return await get_graph(session)
