from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.schemas import SearchResponse
from app.services.search import run_search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    session: SessionDep,
    _user: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=300)],
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> SearchResponse:
    return await run_search(session, q, limit=limit)
