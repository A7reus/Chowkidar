from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

import httpx
import pytest
from app.api.v1 import search as search_api
from app.db.models import (
    Buyer,
    Company,
    EvidenceChunk,
    Obligation,
    Policy,
    Risk,
    Signal,
    Source,
    Supplier,
)
from app.db.session import get_session
from app.main import app
from app.mcp import evidence_server
from app.mcp.server import api
from app.rag import graph_rag
from app.rag.graph_rag import (
    KnowledgeGraph,
    build_graph_context,
    build_knowledge_graph,
    extract_jurisdictions,
    fuse,
    node_id,
    normalize,
    resolve_query_entities,
    tokens,
    traverse,
)
from app.rag.retrieval import SearchHit
from app.schemas import GraphRAGResponse
from app.services.search import graph_rag_response

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


def _id() -> uuid.UUID:
    return uuid.uuid4()


@dataclass
class World:
    """A small supply chain mirroring the demo fixture."""

    company: Company
    suppliers: dict[str, Supplier]
    buyers: dict[str, Buyer]
    policies: dict[str, Policy]
    signals: dict[str, Signal]
    obligations: dict[str, Obligation]
    risks: dict[str, Risk]
    chunks: dict[str, EvidenceChunk]
    graph: KnowledgeGraph = field(init=False)

    def __post_init__(self) -> None:
        self.graph = self.build()

    def build(self) -> KnowledgeGraph:
        evidence = [
            (
                self.risks["sanctions"].id,
                self.chunks["entity_match"].id,
                self.signals["entity_match"].id,
            ),
            (self.risks["traceability"].id, self.chunks["uflpa"].id, self.signals["uflpa"].id),
        ]
        return build_knowledge_graph(
            company=self.company,
            suppliers=self.suppliers.values(),
            buyers=self.buyers.values(),
            policies=self.policies.values(),
            signals=self.signals.values(),
            obligations=self.obligations.values(),
            risks=self.risks.values(),
            risk_evidence=evidence,
            signal_chunks=[(chunk.id, chunk.signal_id) for chunk in self.chunks.values()],
            source_names={self.signals["uflpa"].source_id: "DHS — UFLPA Entity List"},
        )

    def nid(self, kind: str, key: str) -> str:
        table: dict[str, Any] = {
            "supplier": self.suppliers,
            "buyer": self.buyers,
            "policy": self.policies,
            "signal": self.signals,
            "obligation": self.obligations,
            "risk": self.risks,
        }[kind]
        return node_id(kind, table[key].id)  # type: ignore[arg-type]


def _world() -> World:
    company = Company(id=_id(), name="Padma Apparel Ltd.", country="Bangladesh", sector="RMG")
    source = Source(
        id=_id(),
        name="DHS — UFLPA Entity List",
        stream_key="dhs_uflpa",
        source_type="sanctions",
        jurisdiction="US",
        url="https://example.gov",
    )

    def supplier(name: str, tier: int, country: str, category: str, **profile: Any) -> Supplier:
        return Supplier(
            id=_id(),
            company_id=company.id,
            name=name,
            tier=tier,
            country=country,
            category=category,
            risk_level="medium",
            profile=profile,
        )

    suppliers = {
        "dhaka_knit": supplier(
            "Dhaka Knit Composite Ltd.", 1, "Bangladesh", "Knitting", buyers=["Nordwear EU"]
        ),
        "chattogram": supplier("Chattogram Spinning Mills", 2, "Bangladesh", "Yarn spinning"),
        "sinofab": supplier("SinoFab Chemicals Co.", 2, "China", "Dyes & chemical auxiliaries"),
        "sunrise": supplier("Sunrise Cotton Growers", 3, "India", "Cotton ginning"),
    }
    suppliers["sunrise"].parent_supplier_id = suppliers["chattogram"].id
    buyers = {
        "nordwear": Buyer(
            id=_id(),
            company_id=company.id,
            name="Nordwear EU",
            country="Germany",
            requirements_summary="CSDDD-aligned due diligence.",
        )
    }

    def policy(name: str, summary: str, policy_type: str = "policy") -> Policy:
        return Policy(
            id=_id(),
            company_id=company.id,
            name=name,
            policy_type=policy_type,
            version="1.0",
            owner="Compliance",
            summary=summary,
        )

    policies = {
        "cotton": policy(
            "Cotton Traceability Procedure",
            "Tier-3 origin documentation is required for cotton lots.",
        ),
        "nordwear_msa": policy(
            "Nordwear EU Master Supply Agreement",
            "Buyer may request due-diligence evidence.",
            "contract",
        ),
        "export": policy("Export Proceeds SOP", "Monthly reconciliation of export proceeds."),
    }

    def signal(title: str, jurisdiction: str, supplier_key: str | None = None) -> Signal:
        return Signal(
            id=_id(),
            source_id=source.id,
            supplier_id=suppliers[supplier_key].id if supplier_key else None,
            external_id=title[:20],
            title=title,
            summary=title,
            raw_text=title,
            url="https://example.gov/signal",
            jurisdiction=jurisdiction,
            signal_type="regulatory",
            severity="high",
            published_at=NOW,
            status="processed",
        )

    signals = {
        "uflpa": signal("DHS expands UFLPA Entity List, including cotton and apparel", "US"),
        "entity_match": signal(
            "Potential UFLPA name match in chemical supplier ownership chain", "US", "sinofab"
        ),
        "port": signal("Chattogram port workers announce 48-hour strike", "BD"),
    }

    def obligation(key: str, title: str, jurisdiction: str, signal_key: str) -> Obligation:
        return Obligation(
            id=_id(),
            signal_id=signals[signal_key].id,
            source_id=source.id,
            title=title,
            description=title,
            jurisdiction=jurisdiction,
            obligation_type="trade_compliance",
            applies_to="US-bound supply chains",
            effective_date=date(2026, 7, 31),
            section_path=key,
        )

    obligations = {
        "uflpa_traceability": obligation(
            "uflpa",
            "Maintain UFLPA traceability evidence for cotton and garment inputs",
            "US",
            "uflpa",
        ),
        "screening": obligation(
            "screening",
            "Screen suppliers for restricted-party and ownership matches",
            "US",
            "entity_match",
        ),
    }

    def risk(title: str, supplier_key: str | None, obligation_key: str | None) -> Risk:
        return Risk(
            id=_id(),
            company_id=company.id,
            supplier_id=suppliers[supplier_key].id if supplier_key else None,
            obligation_id=obligations[obligation_key].id if obligation_key else None,
            title=title,
            description=title,
            category="trade_compliance",
            score=8.0,
            priority="high",
            status="open",
        )

    risks = {
        "traceability": risk(
            "Cotton origin documentation is incomplete for order LT-4412",
            "sunrise",
            "uflpa_traceability",
        ),
        "sanctions": risk(
            "Potential UFLPA ownership match requires enhanced due diligence",
            "sinofab",
            "screening",
        ),
    }

    def chunk(signal_key: str, content: str) -> EvidenceChunk:
        return EvidenceChunk(
            id=_id(),
            signal_id=signals[signal_key].id,
            content=content,
            citation_label=signals[signal_key].title,
            citation_url="https://example.gov/chunk",
            section_path="Signal body",
        )

    chunks = {
        "uflpa": chunk("uflpa", "DHS added cotton and apparel producers to the UFLPA Entity List."),
        "entity_match": chunk(
            "entity_match",
            "A shareholder of SinoFab Chemicals may match a listed entity. Review required.",
        ),
        "port": chunk("port", "Chattogram port workers announced a 48-hour strike."),
    }
    return World(
        company=company,
        suppliers=suppliers,
        buyers=buyers,
        policies=policies,
        signals=signals,
        obligations=obligations,
        risks=risks,
        chunks=chunks,
    )


def _hit(chunk: EvidenceChunk, score: float) -> SearchHit:
    return SearchHit(chunk=chunk, score=score, mode="mock")


# --------------------------------------------------------------------------- #
# Entity extraction
# --------------------------------------------------------------------------- #


def test_normalisation_folds_spelling_and_plurals() -> None:
    assert normalize("Forced-Labor  violations!") == "forced labour violations"
    assert tokens("Suppliers with forced labor violations") == [
        "supplier",
        "forced",
        "labour",
        "violation",
    ]


def test_jurisdictions_from_trade_query() -> None:
    assert extract_jurisdictions("UFLPA cotton exposure for EU and US buyers") == ["EU", "US"]
    assert extract_jurisdictions("Gazipur factory inspection") == ["BD"]
    # Lower-case "us" is a pronoun, not the United States.
    assert extract_jurisdictions("show us the cotton lots") == []


def test_supplier_aliases_are_distinctive_but_not_place_names() -> None:
    world = _world()
    sinofab = world.graph.nodes[world.nid("supplier", "sinofab")]
    chattogram = world.graph.nodes[world.nid("supplier", "chattogram")]
    assert "sinofab" in sinofab.aliases
    assert "chattogram spinning" in chattogram.aliases
    # "Chattogram" alone also names the port, so it must not resolve the mill.
    assert "chattogram" not in chattogram.aliases


def test_query_entities_resolve_named_and_keyword_matches() -> None:
    world = _world()
    mentions = resolve_query_entities(world.graph, "SinoFab ownership match screening")
    by_id = {mention.node_id: mention for mention in mentions}
    assert by_id[world.nid("supplier", "sinofab")].score == 1.0
    assert by_id[world.nid("supplier", "sinofab")].matched_text == "sinofab"
    assert world.nid("obligation", "screening") in by_id
    assert all(mention.source == "query" for mention in mentions)


def test_company_mention_is_weak_and_generic_words_do_not_match() -> None:
    world = _world()
    company = resolve_query_entities(world.graph, "Padma Apparel")
    assert [(m.kind, m.score) for m in company] == [("company", 0.5)]
    assert resolve_query_entities(world.graph, "risks") == []


def test_buyer_and_supplier_names_link_to_policies() -> None:
    world = _world()
    edges = world.graph.edges.values()
    nordwear = world.nid("buyer", "nordwear")
    assert any(
        edge.source == nordwear
        and edge.target == world.nid("policy", "nordwear_msa")
        and edge.label == "named in"
        and not edge.inferred
        for edge in edges
    )
    assert any(
        edge.source == world.nid("supplier", "dhaka_knit")
        and edge.target == nordwear
        and edge.label == "produces for"
        for edge in edges
    )


def test_policy_links_without_a_foreign_key_are_marked_inferred() -> None:
    world = _world()
    edge = world.graph.edges.get(
        f"{world.nid('obligation', 'uflpa_traceability')}->{world.nid('policy', 'cotton')}"
    )
    assert edge is not None
    assert edge.inferred
    assert edge.label == "addressed by"
    # Unrelated policy is not linked.
    assert not any(
        e.target == world.nid("policy", "export") and e.inferred for e in world.graph.edges.values()
    )


# --------------------------------------------------------------------------- #
# Traversal
# --------------------------------------------------------------------------- #


def test_one_hop_reaches_direct_risks_and_signals_only() -> None:
    world = _world()
    reached = traverse(world.graph, world.nid("supplier", "sinofab"), hops=1)
    assert reached[world.nid("risk", "sanctions")].hop == 1
    assert reached[world.nid("signal", "entity_match")].hop == 1
    assert world.nid("obligation", "screening") not in reached


def test_two_hops_reach_governing_obligations() -> None:
    world = _world()
    reached = traverse(world.graph, world.nid("supplier", "sinofab"), hops=2)
    screening = reached[world.nid("obligation", "screening")]
    assert screening.hop == 2
    assert screening.relevance == pytest.approx(0.25)
    assert screening.parent in {world.nid("risk", "sanctions"), world.nid("signal", "entity_match")}


def test_tier_chain_is_traversed() -> None:
    world = _world()
    reached = traverse(world.graph, world.nid("supplier", "sunrise"), hops=1)
    assert world.nid("supplier", "chattogram") in reached
    assert reached[world.nid("supplier", "chattogram")].via.label == "supplies"  # type: ignore[union-attr]


def test_company_hub_is_reached_but_not_expanded() -> None:
    world = _world()
    reached = traverse(world.graph, world.nid("supplier", "sinofab"), hops=3)
    assert node_id("company", world.company.id) in reached
    # Other suppliers only connect to SinoFab through the company hub.
    assert world.nid("supplier", "dhaka_knit") not in reached
    assert world.nid("policy", "export") not in reached


# --------------------------------------------------------------------------- #
# Fusion
# --------------------------------------------------------------------------- #


def test_fusion_attaches_entities_and_reranks_by_graph_connectivity() -> None:
    world = _world()
    # Lexically the port chunk scores a little higher, but only the SinoFab
    # chunk connects to the supplier named in the query.
    hits = [_hit(world.chunks["port"], 0.6), _hit(world.chunks["entity_match"], 0.5)]
    result = fuse(world.graph, "SinoFab exposure", hits, hops=2, limit=5)

    assert [str(hit.chunk.id) for hit in result.results] == [
        str(world.chunks["entity_match"].id),
        str(world.chunks["port"].id),
    ]
    top = result.results[0]
    assert top.graph_score > 0
    assert top.retrieval_score == 0.5
    related = {entity["id"] for entity in top.related_entities}
    assert world.nid("risk", "sanctions") in related
    assert world.nid("supplier", "sinofab") in related
    assert result.results[1].graph_score == 0

    node_ids = {node.id for node in result.nodes}
    assert world.nid("obligation", "screening") in node_ids
    edge_ids = {edge.id for edge in result.edges}
    assert all(edge.source in node_ids and edge.target in node_ids for edge in result.edges)
    assert f"{world.nid('risk', 'sanctions')}->{world.nid('supplier', 'sinofab')}" in edge_ids
    seeds = [node for node in result.nodes if node.seed]
    assert any(node.id == world.nid("supplier", "sinofab") for node in seeds)
    assert result.paths and result.paths[0].node_ids[0] == world.nid("supplier", "sinofab")
    assert "SinoFab Chemicals Co. (Tier 2)" in result.traversal_summary


def test_evidence_links_seed_the_graph_without_query_entities() -> None:
    world = _world()
    hits = [_hit(world.chunks["uflpa"], 0.9)]
    context = build_graph_context(world.graph, "listed producers", hits, hops=2)
    seeds = {seed.node_id for seed in context.seeds}
    assert world.nid("signal", "uflpa") in seeds
    assert world.nid("risk", "traceability") in seeds
    reached = set(context.kept)
    # Chunk -> risk evidence -> affected tier-3 supplier.
    assert world.nid("supplier", "sunrise") in reached
    assert world.nid("obligation", "uflpa_traceability") in reached


def test_graph_evidence_is_kept_separate_from_retrieved_chunks() -> None:
    world = _world()
    context = build_graph_context(world.graph, "SinoFab", [], hops=2)
    targets = graph_rag.graph_evidence_targets(world.graph, context)
    assert world.nid("signal", "entity_match") in targets
    result = fuse(
        world.graph,
        "SinoFab",
        [],
        hops=2,
        graph_chunks=[(world.chunks["entity_match"], world.nid("signal", "entity_match"))],
        context=context,
    )
    assert result.results == []
    assert [hit.origin for hit in result.graph_evidence] == ["graph"]
    assert result.graph_evidence[0].retrieval_score == 0.0


def test_empty_results_fall_back_cleanly() -> None:
    world = _world()
    result = fuse(world.graph, "zz", [], hops=2)
    assert result.results == []
    assert result.graph_evidence == []
    assert result.nodes == []
    assert result.edges == []
    assert result.mode == "mock"
    assert result.traversal_summary.startswith("No graph entities matched")
    response = graph_rag_response(result)
    assert response.subgraph.nodes == []


def test_empty_graph_is_handled() -> None:
    result = fuse(KnowledgeGraph(), "SinoFab", [], hops=2)
    assert result.nodes == [] and result.paths == []


def test_subgraph_is_capped() -> None:
    world = _world()
    context = build_graph_context(world.graph, "SinoFab", [], hops=3, max_nodes=3)
    assert len(context.kept) == 3
    assert world.nid("supplier", "sinofab") in context.kept


@pytest.mark.asyncio
async def test_graph_augmented_search_orchestrates_retrieval_and_traversal(monkeypatch) -> None:
    world = _world()
    calls: dict[str, Any] = {}

    async def fake_retriever(session: Any, query: str, *, limit: int) -> list[SearchHit]:
        calls["retriever"] = (query, limit)
        return [_hit(world.chunks["entity_match"], 0.7)]

    async def fake_load(session: Any, *, extra_signal_ids: Any = ()) -> KnowledgeGraph:
        calls["signals"] = list(extra_signal_ids)
        return world.graph

    async def fake_chunks(session: Any, graph: Any, targets: dict[str, str], *, limit: int):
        calls["targets"] = targets
        return []

    monkeypatch.setattr(graph_rag, "load_knowledge_graph", fake_load)
    monkeypatch.setattr(graph_rag, "_load_graph_chunks", fake_chunks)
    result = await graph_rag.graph_augmented_search(
        None,  # type: ignore[arg-type]
        "SinoFab ownership",
        limit=4,
        hops=5,
        retriever=fake_retriever,
    )
    assert calls["retriever"] == ("SinoFab ownership", 4)
    assert calls["signals"] == [world.signals["entity_match"].id]
    assert world.nid("signal", "entity_match") in calls["targets"]
    assert result.hops == 3  # clamped
    assert result.results[0].related_entities


# --------------------------------------------------------------------------- #
# REST endpoint
# --------------------------------------------------------------------------- #


async def _no_session():
    yield None


@pytest.fixture
def graph_client(monkeypatch):
    world = _world()

    async def fake_run(session: Any, query: str, *, limit: int = 8, hops: int = 2):
        hits = [_hit(world.chunks["entity_match"], 0.7)]
        return graph_rag_response(fuse(world.graph, query, hits, hops=hops, limit=limit))

    monkeypatch.setattr(search_api, "run_graph_search", fake_run)
    app.dependency_overrides[get_session] = _no_session
    try:
        yield httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_graph_search_endpoint_returns_subgraph(graph_client) -> None:
    async with graph_client as client:
        response = await client.get(
            "/api/v1/search/graph",
            params={"q": "SinoFab ownership", "hops": 2},
            headers={"X-Demo-Role": "analyst"},
        )
    assert response.status_code == 200
    payload = GraphRAGResponse.model_validate(response.json())
    assert payload.hops == 2
    assert payload.subgraph.nodes and payload.subgraph.edges
    assert payload.results[0].related_entity_ids
    assert payload.results[0].origin == "retrieval"
    assert any(entity.kind == "supplier" for entity in payload.entities)
    assert payload.traversal_summary


@pytest.mark.asyncio
async def test_search_endpoint_supports_graph_augmented_flag(graph_client) -> None:
    async with graph_client as client:
        response = await client.get(
            "/api/v1/search",
            params={"q": "SinoFab", "graph_augmented": "true"},
            headers={"X-Demo-Role": "viewer"},
        )
    assert response.status_code == 200
    assert "subgraph" in response.json()


@pytest.mark.asyncio
async def test_graph_search_requires_auth_and_validates_hops(graph_client) -> None:
    async with graph_client as client:
        unauthenticated = await client.get("/api/v1/search/graph", params={"q": "SinoFab"})
        too_deep = await client.get(
            "/api/v1/search/graph",
            params={"q": "SinoFab", "hops": 4},
            headers={"X-Demo-Role": "analyst"},
        )
    assert unauthenticated.status_code == 401
    assert too_deep.status_code == 422


# --------------------------------------------------------------------------- #
# MCP tool
# --------------------------------------------------------------------------- #


def test_mcp_graph_tool_returns_chunks_and_subgraph(monkeypatch) -> None:
    world = _world()
    response = graph_rag_response(
        fuse(world.graph, "SinoFab", [_hit(world.chunks["entity_match"], 0.7)], hops=2)
    )
    seen: dict[str, Any] = {}

    async def fake_get(path: str, params: dict[str, Any] | None = None) -> Any:
        seen["path"] = path
        seen["params"] = params
        return response.model_dump(mode="json")

    monkeypatch.setattr(api, "get", fake_get)

    async def call() -> Any:
        try:
            tool = await evidence_server.mcp.get_tool("search_evidence_with_graph")
            assert tool is not None
            result = await tool.run({"query": " SinoFab ", "limit": 50, "hops": 9})
            return result.structured_content
        finally:
            await api.close()

    data = asyncio.run(call())
    assert seen == {
        "path": "/api/v1/search/graph",
        "params": {"q": "SinoFab", "limit": 20, "hops": 3},
    }
    assert data["results"][0]["related_entities"]
    assert data["nodes"] and data["edges"]
    assert data["paths"] and data["traversal_summary"]
    assert {"source", "target", "label", "inferred"} <= set(data["edges"][0])


def test_mcp_graph_tool_rejects_short_queries() -> None:
    async def call() -> None:
        try:
            tool = evidence_server.search_evidence_with_graph
            await getattr(tool, "fn", tool)("x")
        finally:
            await api.close()

    with pytest.raises(ValueError):
        asyncio.run(call())
