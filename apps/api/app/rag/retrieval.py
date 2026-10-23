from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvidenceChunk
from app.rag.embeddings import get_embedding_service


@dataclass
class SearchHit:
    chunk: EvidenceChunk
    score: float
    mode: str


async def search_evidence(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 8,
    candidate_limit: int = 24,
) -> list[SearchHit]:
    if not query.strip():
        return []

    service = get_embedding_service()
    query_embedding = service.embed_query(query)
    vector_distance = EvidenceChunk.embedding.cosine_distance(query_embedding).label("distance")
    vector_stmt = (
        select(EvidenceChunk, vector_distance)
        .where(EvidenceChunk.embedding.is_not(None))
        .order_by(vector_distance)
        .limit(candidate_limit)
    )
    vector_rows = (await session.execute(vector_stmt)).all()

    ts_query = func.websearch_to_tsquery("english", query)
    fts_rank = func.ts_rank_cd(EvidenceChunk.search_vector, ts_query).label("rank")
    fts_stmt = (
        select(EvidenceChunk, fts_rank)
        .where(EvidenceChunk.search_vector.op("@@")(ts_query))
        .order_by(desc(fts_rank))
        .limit(candidate_limit)
    )
    fts_rows = (await session.execute(fts_stmt)).all()

    candidates: dict = {}
    scores: dict = {}
    for rank, (chunk, _distance) in enumerate(vector_rows, start=1):
        candidates[chunk.id] = chunk
        scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (60 + rank)
    for rank, (chunk, _rank) in enumerate(fts_rows, start=1):
        candidates[chunk.id] = chunk
        scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (60 + rank)

    ordered = sorted(candidates.values(), key=lambda chunk: scores.get(chunk.id, 0.0), reverse=True)
    if not ordered:
        return []

    rerank_candidates = ordered[: max(limit * 3, limit)]
    reranked = service.rerank(query, [chunk.content for chunk in rerank_candidates], top_k=limit)
    results: list[SearchHit] = []
    for index, rerank_score in reranked:
        chunk = rerank_candidates[index]
        fused = scores.get(chunk.id, 0.0)
        results.append(
            SearchHit(
                chunk=chunk,
                score=round(float(rerank_score) * 0.7 + fused * 0.3, 6),
                mode="live" if service.live_ready else "mock",
            )
        )
    return results
