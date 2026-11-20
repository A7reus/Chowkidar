from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.schemas import GraphRAGResponse, SearchResponse
from app.services.search import run_graph_search, run_search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=GraphRAGResponse | SearchResponse)
async def search(
    session: SessionDep,
    _user: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=300)],
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
    graph_augmented: Annotated[
        bool,
        Query(description="Add knowledge-graph context; same as GET /search/graph."),
    ] = False,
) -> GraphRAGResponse | SearchResponse:
    if graph_augmented:
        return await run_graph_search(session, q, limit=limit)
    return await run_search(session, q, limit=limit)


@router.get("/graph", response_model=GraphRAGResponse)
async def search_with_graph(
    session: SessionDep,
    _user: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=300)],
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
    hops: Annotated[int, Query(ge=1, le=3)] = 2,
) -> GraphRAGResponse:
    """Graph RAG: hybrid evidence retrieval fused with multi-hop traversal of the
    supplier, risk, obligation and policy graph."""
    return await run_graph_search(session, q, limit=limit, hops=hops)
