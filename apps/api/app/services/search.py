from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.retrieval import search_evidence
from app.schemas import SearchResponse, SearchResult


async def run_search(
    session: AsyncSession, query: str, *, limit: int = 8
) -> SearchResponse:
    hits = await search_evidence(session, query, limit=limit)
    results = [
        SearchResult(
            chunk_id=hit.chunk.id,
            content=hit.chunk.content,
            citation_label=hit.chunk.citation_label,
            citation_url=hit.chunk.citation_url,
            section_path=hit.chunk.section_path,
            score=hit.score,
            signal_id=hit.chunk.signal_id,
            document_id=hit.chunk.document_id,
        )
        for hit in hits
    ]
    mode = hits[0].mode if hits else "mock"
    return SearchResponse(query=query, results=results, mode=mode)
