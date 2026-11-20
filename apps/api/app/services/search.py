from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.graph_rag import GraphRAGHit, GraphRAGResult, graph_augmented_search
from app.rag.retrieval import search_evidence
from app.schemas import (
    GraphRAGEdge,
    GraphRAGEntity,
    GraphRAGEntityRef,
    GraphRAGNode,
    GraphRAGPath,
    GraphRAGResponse,
    GraphRAGSearchResult,
    GraphRAGSubgraph,
    SearchResponse,
    SearchResult,
)


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


async def run_graph_search(
    session: AsyncSession, query: str, *, limit: int = 8, hops: int = 2
) -> GraphRAGResponse:
    result = await graph_augmented_search(session, query, limit=limit, hops=hops)
    return graph_rag_response(result)


def _graph_hit(hit: GraphRAGHit) -> GraphRAGSearchResult:
    return GraphRAGSearchResult(
        chunk_id=hit.chunk.id,
        content=hit.chunk.content,
        citation_label=hit.chunk.citation_label,
        citation_url=hit.chunk.citation_url,
        section_path=hit.chunk.section_path,
        score=hit.score,
        signal_id=hit.chunk.signal_id,
        document_id=hit.chunk.document_id,
        related_entity_ids=[entity["id"] for entity in hit.related_entities],
        related_entities=[GraphRAGEntityRef(**entity) for entity in hit.related_entities],
        retrieval_score=hit.retrieval_score,
        graph_score=hit.graph_score,
        origin=hit.origin,
    )


def graph_rag_response(result: GraphRAGResult) -> GraphRAGResponse:
    return GraphRAGResponse(
        query=result.query,
        mode=result.mode,
        hops=result.hops,
        results=[_graph_hit(hit) for hit in result.results],
        graph_evidence=[_graph_hit(hit) for hit in result.graph_evidence],
        entities=[
            GraphRAGEntity(
                node_id=mention.node_id,
                kind=mention.kind,
                label=mention.label,
                matched_text=mention.matched_text,
                score=mention.score,
                source=mention.source,
                chunk_id=uuid.UUID(mention.chunk_id) if mention.chunk_id else None,
            )
            for mention in result.entities
        ],
        jurisdictions=result.jurisdictions,
        subgraph=GraphRAGSubgraph(
            nodes=[
                GraphRAGNode(
                    id=node.id,
                    label=node.label,
                    kind=node.kind,
                    detail=node.detail or None,
                    priority=node.priority,
                    hop=node.hop,
                    relevance=node.relevance,
                    seed=node.seed,
                    matched_by=node.matched_by,
                )
                for node in result.nodes
            ],
            edges=[
                GraphRAGEdge(
                    id=edge.id,
                    source=edge.source,
                    target=edge.target,
                    label=edge.label,
                    inferred=edge.inferred,
                )
                for edge in result.edges
            ],
        ),
        paths=[
            GraphRAGPath(node_ids=path.node_ids, description=path.description)
            for path in result.paths
        ],
        traversal_summary=result.traversal_summary,
    )
