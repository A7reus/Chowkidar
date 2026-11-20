"""Graph RAG: hybrid evidence retrieval fused with supply-chain graph traversal.

Plain retrieval (``app.rag.retrieval.search_evidence``) returns isolated text
chunks. An analyst investigating a risk also needs the structure around those
chunks: which suppliers are affected, which obligations govern them, which
buyer contracts and internal policies are in play. This module adds that
structure in four steps:

1. **Hybrid retrieval.** Reuse the pgvector + full-text search with RRF and
   reranking from ``search_evidence``.
2. **Entity resolution.** Resolve named entities in the query and in the
   retrieved chunks against the knowledge graph (supplier, buyer, company and
   policy names; obligation, risk and signal titles), and follow the stored
   evidence links (chunk -> signal, chunk -> risk evidence) into the graph.
3. **Multi-hop traversal.** Walk 1 to 3 hops out from those seed entities over
   the relational graph: suppliers, risks, obligations, signals, buyers and
   policies.
4. **Fusion.** Re-rank the retrieved chunks by how strongly they connect to
   the entities named in the query, attach the entities each chunk links to,
   surface evidence that is reachable only through the graph, and return the
   traversed subgraph with readable traversal paths.

The graph is built from the existing relational tables, so the feature needs
no extra infrastructure. ``KnowledgeGraph`` is a plain in-memory adjacency
structure, which keeps the traversal easy to test and to port to Neo4j later.

The resolution and traversal code is pure and synchronous. Only
``load_knowledge_graph`` and ``graph_augmented_search`` touch the database.
"""

from __future__ import annotations

import math
import re
import uuid
from collections import deque
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Buyer,
    Company,
    EvidenceChunk,
    Obligation,
    Policy,
    Risk,
    RiskEvidence,
    Signal,
    Source,
    Supplier,
)
from app.rag.retrieval import SearchHit, search_evidence

NodeKind = Literal["company", "supplier", "buyer", "policy", "signal", "obligation", "risk"]
MentionSource = Literal["query", "evidence"]

# Relevance halves with every hop away from a seed entity.
HOP_DECAY = 0.5
# Share of the fused score that comes from graph connectivity to the query.
GRAPH_WEIGHT = 0.25
# Hard caps that keep a response small enough for an LLM context window.
MAX_SUBGRAPH_NODES = 40
MAX_RELATED_PER_HIT = 8
MAX_QUERY_KEYWORD_MATCHES = 5
MAX_POLICY_LINKS = 2
# Characters of a description or summary kept for keyword matching.
BODY_CHARS = 300

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_CANONICAL = {
    "labor": "labour",
    "organisation": "organization",
}


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


_STOPWORDS = _words(
    """
    a an and are as at be been by can do does for from has have how in into is it its
    made make may new non not now of on or our over per so such than that the their them
    there these they this to under up was we were what when where which while who why
    will with within without all any about after before more most other own same some
    only also show find list give me my us your get see
    """
)
# Legal suffixes and generic words that never identify an entity on their own.
_GENERIC_NAME_TOKENS = _words(
    """
    ltd limited co inc llc plc corp corporation company group unit partner
    policy procedure sop agreement global
    """
)
# Place names are too ambiguous to stand alone as an entity alias: "Chattogram"
# is both a supplier name prefix and the port in a strike notice.
_PLACE_TOKENS = _words(
    """
    dhaka chattogram chittagong gazipur narayanganj bangladesh india china vietnam
    hanoi singapore germany europe eu us usa hong kong xinjiang
    """
)
# Words shared by most obligations and policies; they say nothing about which
# policy addresses which obligation.
_GENERIC_POLICY_TOKENS = _words(
    """
    policy management supply supplier evidence risk based maintain buyer compliance
    requirement document record review update
    """
)
_JURISDICTION_ALIASES: dict[str, tuple[str, ...]] = {
    "EU": ("eu", "european union", "europe", "csddd", "eudr"),
    "US": ("usa", "united states", "uflpa", "cbp", "dhs", "bis", "federal register"),
    "BD": ("bangladesh", "bangladeshi", "bangladesh bank", "dhaka", "gazipur", "chattogram"),
    "CN": ("china", "chinese", "xinjiang"),
    "IN": ("india", "indian"),
    "VN": ("vietnam", "vietnamese"),
}


# --------------------------------------------------------------------------- #
# Text normalisation
# --------------------------------------------------------------------------- #


def _stem(token: str) -> str:
    """A deliberately small stemmer: plurals and "-ing" ("screening" -> "screen")."""
    if len(token) > 6 and token.endswith("ing"):
        token = token[:-3]
        if token[-1] == token[-2] and token[-1] not in "ls":
            token = token[:-1]  # "spinning" -> "spin"
        return token
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def normalize(text: str) -> str:
    """Lower-case, canonicalise spelling variants and collapse to single spaces."""
    lowered = text.lower()
    for variant, canonical in _CANONICAL.items():
        lowered = re.sub(rf"\b{re.escape(variant)}\b", canonical, lowered)
    return " ".join(_TOKEN_RE.findall(lowered))


def tokens(text: str) -> list[str]:
    """Content tokens: normalised, stemmed, without stopwords."""
    return [_stem(token) for token in normalize(text).split() if token not in _STOPWORDS]


def _phrase_in(phrase: str, text: str) -> bool:
    return bool(phrase) and f" {phrase} " in f" {text} "


def _short(text: str, limit: int = 72) -> str:
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


# --------------------------------------------------------------------------- #
# Knowledge graph
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class KGNode:
    id: str
    kind: NodeKind
    label: str
    detail: str = ""
    priority: str | None = None
    jurisdiction: str | None = None
    # Short descriptive text (category, type, scope) used for matching.
    text: str = ""
    # Longer description or summary, used only to match query keywords.
    body: str = ""
    # Normalised phrases that identify the entity by name.
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class KGEdge:
    source: str
    target: str
    label: str
    inferred: bool = False

    @property
    def id(self) -> str:
        return f"{self.source}->{self.target}"


@dataclass
class KnowledgeGraph:
    nodes: dict[str, KGNode] = field(default_factory=dict)
    edges: dict[str, KGEdge] = field(default_factory=dict)
    adjacency: dict[str, list[tuple[KGEdge, str]]] = field(default_factory=dict)
    # Evidence chunk id -> graph nodes the chunk is stored as evidence for.
    chunk_links: dict[str, set[str]] = field(default_factory=dict)
    # Graph node id -> evidence chunk ids attached to that node.
    node_chunks: dict[str, set[str]] = field(default_factory=dict)
    _idf: dict[str, float] = field(default_factory=dict)

    def add_node(self, node: KGNode) -> None:
        self.nodes.setdefault(node.id, node)
        self.adjacency.setdefault(node.id, [])

    def add_edge(self, source: str, target: str, label: str, *, inferred: bool = False) -> None:
        if source not in self.nodes or target not in self.nodes or source == target:
            return
        edge = KGEdge(source=source, target=target, label=label, inferred=inferred)
        if edge.id in self.edges or f"{target}->{source}" in self.edges:
            return
        self.edges[edge.id] = edge
        self.adjacency[source].append((edge, target))
        self.adjacency[target].append((edge, source))

    def link_chunk(self, chunk_id: str, node_id: str) -> None:
        if node_id not in self.nodes:
            return
        self.chunk_links.setdefault(chunk_id, set()).add(node_id)
        self.node_chunks.setdefault(node_id, set()).add(chunk_id)

    def neighbors(self, node_id: str) -> list[tuple[KGEdge, str]]:
        return self.adjacency.get(node_id, [])

    @property
    def rare_idf(self) -> float:
        """IDF of a token that appears in three nodes."""
        return math.log((len(self.nodes) + 1) / 3.5)

    def idf(self, token: str) -> float:
        if not self._idf:
            self._build_idf()
        return self._idf.get(token, self._idf.get("__unknown__", 1.0))

    def _build_idf(self) -> None:
        document_count = max(len(self.nodes), 1)
        frequency: dict[str, int] = {}
        for node in self.nodes.values():
            for token in set(tokens(f"{node.label} {node.text} {node.body}")):
                frequency[token] = frequency.get(token, 0) + 1
        self._idf = {
            token: math.log((document_count + 1) / (count + 0.5))
            for token, count in frequency.items()
        }
        self._idf["__unknown__"] = math.log((document_count + 1) / 0.5)


def node_id(kind: NodeKind, entity_id: Any) -> str:
    return f"{kind}:{entity_id}"


def _name_aliases(name: str, *, allow_short: bool) -> tuple[str, ...]:
    """Normalised phrases that name an entity: full name, name without legal
    suffix, and (for suppliers and buyers) a distinctive leading phrase."""
    full = normalize(name)
    words = full.split()
    core = [word for word in words if word not in _GENERIC_NAME_TOKENS]
    aliases = {full}
    if len(core) >= 2 and len(core) < len(words):
        aliases.add(" ".join(core))
    lead = words[:2]
    distinctive = [word for word in lead if word not in _GENERIC_NAME_TOKENS | _PLACE_TOKENS]
    if allow_short and len(words) >= 3 and distinctive:
        aliases.add(" ".join(lead))
    return tuple(sorted(alias for alias in aliases if alias))


def _add_single_token_aliases(graph: KnowledgeGraph, kinds: set[str]) -> None:
    """Allow a one-word alias ("SinoFab", "Nordwear") when that word appears in
    exactly one entity name and is not a place or generic word."""
    owners: dict[str, set[str]] = {}
    for node in graph.nodes.values():
        if node.kind not in kinds | {"company"}:
            continue
        for word in normalize(node.label).split():
            owners.setdefault(word, set()).add(node.id)
    for word, ids in owners.items():
        if (
            len(ids) != 1
            or len(word) < 5
            or word in _STOPWORDS
            or word in _GENERIC_NAME_TOKENS
            or word in _PLACE_TOKENS
            or word.isdigit()
        ):
            continue
        (owner,) = tuple(ids)
        node = graph.nodes[owner]
        if node.kind not in kinds:
            continue
        first_word = normalize(node.label).split()[0]
        if word != first_word:
            continue
        graph.nodes[owner] = replace(node, aliases=tuple(sorted({*node.aliases, word})))


def _supplier_detail(supplier: Any) -> str:
    return f"Tier {supplier.tier} supplier · {supplier.country} · {supplier.category}"


def build_knowledge_graph(
    *,
    company: Any | None,
    suppliers: Iterable[Any] = (),
    buyers: Iterable[Any] = (),
    policies: Iterable[Any] = (),
    signals: Iterable[Any] = (),
    obligations: Iterable[Any] = (),
    risks: Iterable[Any] = (),
    risk_evidence: Iterable[tuple[Any, Any, Any]] = (),
    signal_chunks: Iterable[tuple[Any, Any]] = (),
    source_names: dict[Any, str] | None = None,
) -> KnowledgeGraph:
    """Build the in-memory knowledge graph from ORM rows (or look-alike objects).

    ``risk_evidence`` holds ``(risk_id, evidence_chunk_id, chunk_signal_id)``
    tuples and ``signal_chunks`` holds ``(chunk_id, signal_id)`` tuples.
    """
    graph = KnowledgeGraph()
    source_names = source_names or {}
    suppliers = list(suppliers)
    buyers = list(buyers)
    policies = list(policies)
    signals = list(signals)
    obligations = list(obligations)
    risks = list(risks)

    company_node = ""
    if company is not None:
        company_node = node_id("company", company.id)
        graph.add_node(
            KGNode(
                id=company_node,
                kind="company",
                label=company.name,
                detail=f"{company.country} · {company.sector}",
                jurisdiction="BD" if company.country == "Bangladesh" else None,
                text=f"{company.sector}",
                aliases=_name_aliases(company.name, allow_short=False),
            )
        )

    for supplier in suppliers:
        graph.add_node(
            KGNode(
                id=node_id("supplier", supplier.id),
                kind="supplier",
                label=supplier.name,
                detail=_supplier_detail(supplier),
                priority=supplier.risk_level,
                text=f"{supplier.category} {supplier.country}",
                aliases=_name_aliases(supplier.name, allow_short=True),
            )
        )
    for buyer in buyers:
        graph.add_node(
            KGNode(
                id=node_id("buyer", buyer.id),
                kind="buyer",
                label=buyer.name,
                detail=f"Buyer · {buyer.country}",
                text=buyer.requirements_summary or "",
                aliases=_name_aliases(buyer.name, allow_short=True),
            )
        )
    for policy in policies:
        graph.add_node(
            KGNode(
                id=node_id("policy", policy.id),
                kind="policy",
                label=policy.name,
                detail=f"{policy.policy_type} v{policy.version} · {policy.owner}",
                text=policy.summary or "",
                aliases=_name_aliases(policy.name, allow_short=False),
            )
        )
    for signal in signals:
        source = source_names.get(signal.source_id, "")
        graph.add_node(
            KGNode(
                id=node_id("signal", signal.id),
                kind="signal",
                label=_short(signal.title),
                detail=" · ".join(
                    part for part in (source, signal.jurisdiction, signal.severity) if part
                ),
                priority=signal.severity,
                jurisdiction=signal.jurisdiction,
                text=f"{signal.title} {signal.signal_type}",
                body=_short(signal.summary or "", BODY_CHARS),
            )
        )
    for obligation in obligations:
        graph.add_node(
            KGNode(
                id=node_id("obligation", obligation.id),
                kind="obligation",
                label=_short(obligation.title),
                detail=f"{obligation.jurisdiction} · {obligation.obligation_type}"
                + (f" · {obligation.section_path}" if obligation.section_path else ""),
                jurisdiction=obligation.jurisdiction,
                text=" ".join(
                    (obligation.title, obligation.obligation_type, obligation.applies_to or "")
                ),
                body=_short(obligation.description or "", BODY_CHARS),
            )
        )
    for risk in risks:
        graph.add_node(
            KGNode(
                id=node_id("risk", risk.id),
                kind="risk",
                label=_short(risk.title),
                detail=f"Score {risk.score:.1f} · {risk.status} · {risk.category}",
                priority=risk.priority,
                text=f"{risk.title} {risk.category}",
                body=_short(risk.description or "", BODY_CHARS),
            )
        )

    _add_single_token_aliases(graph, {"supplier", "buyer"})

    # Structural edges, all backed by foreign keys or stored fields.
    supplier_nodes = {node_id("supplier", supplier.id): supplier for supplier in suppliers}
    for supplier_node, supplier in supplier_nodes.items():
        if company_node:
            graph.add_edge(company_node, supplier_node, "sources from")
        parent_id = getattr(supplier, "parent_supplier_id", None)
        if parent_id:
            graph.add_edge(supplier_node, node_id("supplier", parent_id), "supplies")
    buyer_by_name = {normalize(buyer.name): node_id("buyer", buyer.id) for buyer in buyers}
    for supplier_node, supplier in supplier_nodes.items():
        profile = supplier.profile if isinstance(supplier.profile, dict) else {}
        for buyer_name in profile.get("buyers", []) or []:
            buyer_node = buyer_by_name.get(normalize(str(buyer_name)))
            if buyer_node:
                graph.add_edge(supplier_node, buyer_node, "produces for")
    for buyer in buyers:
        if company_node:
            graph.add_edge(company_node, node_id("buyer", buyer.id), "sells to")
    for policy in policies:
        if company_node:
            graph.add_edge(company_node, node_id("policy", policy.id), "governed by")
    for signal in signals:
        if signal.supplier_id:
            graph.add_edge(
                node_id("signal", signal.id), node_id("supplier", signal.supplier_id), "mentions"
            )
    for obligation in obligations:
        graph.add_edge(
            node_id("signal", obligation.signal_id),
            node_id("obligation", obligation.id),
            "creates obligation",
        )
    for risk in risks:
        risk_node = node_id("risk", risk.id)
        if risk.supplier_id:
            graph.add_edge(risk_node, node_id("supplier", risk.supplier_id), "affects")
        if risk.obligation_id:
            graph.add_edge(risk_node, node_id("obligation", risk.obligation_id), "arises from")
    for risk_id, chunk_id, chunk_signal_id in risk_evidence:
        risk_node = node_id("risk", risk_id)
        if chunk_signal_id:
            graph.add_edge(risk_node, node_id("signal", chunk_signal_id), "cites evidence from")
        if chunk_id:
            graph.link_chunk(str(chunk_id), risk_node)
    for chunk_id, signal_id in signal_chunks:
        if signal_id:
            graph.link_chunk(str(chunk_id), node_id("signal", signal_id))

    _link_named_entities_to_policies(graph)
    _infer_policy_links(graph)
    return graph


def _link_named_entities_to_policies(graph: KnowledgeGraph) -> None:
    """Supplier or buyer named in a policy ("Dhaka Knit Factory Audit 2025",
    "Nordwear EU Master Supply Agreement") -> explicit edge."""
    policies = [node for node in graph.nodes.values() if node.kind == "policy"]
    named = [node for node in graph.nodes.values() if node.kind in {"supplier", "buyer"}]
    for policy in policies:
        policy_text = normalize(f"{policy.label} {policy.text}")
        for entity in named:
            if any(_phrase_in(alias, policy_text) for alias in entity.aliases):
                graph.add_edge(entity.id, policy.id, "named in")


def _infer_policy_links(graph: KnowledgeGraph) -> None:
    """Link each obligation to the internal policies most likely to address it.

    There is no foreign key between obligations and policies, so this is a
    keyword-overlap inference (IDF weighted). Edges are flagged ``inferred``
    so clients can render them differently from stored relationships.
    """
    policies = [node for node in graph.nodes.values() if node.kind == "policy"]
    if not policies:
        return
    policy_tokens = {
        policy.id: set(tokens(f"{policy.label} {policy.text}")) - _GENERIC_POLICY_TOKENS
        for policy in policies
    }
    for obligation in [node for node in graph.nodes.values() if node.kind == "obligation"]:
        wanted = set(tokens(f"{obligation.label} {obligation.text}")) - _GENERIC_POLICY_TOKENS
        if not wanted:
            continue
        scored: list[tuple[float, str]] = []
        for policy in policies:
            shared = wanted & policy_tokens[policy.id]
            if not shared:
                continue
            weight = sum(graph.idf(token) for token in shared)
            if len(shared) >= 2 and weight >= 3.0:
                scored.append((weight, policy.id))
        scored.sort(reverse=True)
        for _weight, policy_id in scored[:MAX_POLICY_LINKS]:
            graph.add_edge(obligation.id, policy_id, "addressed by", inferred=True)


# --------------------------------------------------------------------------- #
# Entity resolution
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EntityMention:
    node_id: str
    kind: NodeKind
    label: str
    matched_text: str
    score: float
    source: MentionSource
    chunk_id: str | None = None


def extract_jurisdictions(text: str) -> list[str]:
    """Jurisdiction codes named in free text ("EU", "UFLPA" -> US, "Gazipur" -> BD)."""
    normalized = normalize(text)
    found: list[str] = []
    for code, aliases in _JURISDICTION_ALIASES.items():
        if any(_phrase_in(alias, normalized) for alias in aliases):
            found.append(code)
    # "us" is only a jurisdiction when written in capitals.
    if "US" not in found and re.search(r"\bU\.?S\.?\b", text):
        found.append("US")
    return found


def resolve_named_entities(
    graph: KnowledgeGraph, text: str, *, source: MentionSource, chunk_id: str | None = None
) -> list[EntityMention]:
    """Exact alias matches for named entities (suppliers, buyers, company, policies)."""
    normalized = normalize(text)
    mentions: list[EntityMention] = []
    for node in graph.nodes.values():
        if not node.aliases:
            continue
        matched = [alias for alias in node.aliases if _phrase_in(alias, normalized)]
        if not matched:
            continue
        best = max(matched, key=len)
        mentions.append(
            EntityMention(
                node_id=node.id,
                kind=node.kind,
                label=node.label,
                matched_text=best,
                # The company links to every supplier and policy, so naming it
                # says little about what the user is looking for.
                score=0.5 if node.kind == "company" else 1.0,
                source=source,
                chunk_id=chunk_id,
            )
        )
    return mentions


def resolve_keyword_entities(
    graph: KnowledgeGraph, query: str, *, jurisdictions: Iterable[str] = ()
) -> list[EntityMention]:
    """Fuzzy matches for descriptive entities (obligations, risks, signals, policies).

    Score = IDF-weighted share of the query's content words that the entity
    text covers, with a small bonus when the jurisdiction also matches. A
    one-word query only matches when the word is rare in the graph, so
    "risks" does not pull in every risk.
    """
    query_tokens = list(dict.fromkeys(tokens(query)))
    if not query_tokens:
        return []
    if len(query_tokens) == 1 and graph.idf(query_tokens[0]) < graph.rare_idf:
        return []
    jurisdictions = set(jurisdictions) or set(extract_jurisdictions(query))
    total = sum(graph.idf(token) for token in query_tokens) or 1.0
    mentions: list[EntityMention] = []
    for node in graph.nodes.values():
        if node.kind not in {"obligation", "risk", "signal", "policy"}:
            continue
        node_tokens = set(tokens(f"{node.label} {node.text} {node.body}"))
        shared = [token for token in query_tokens if token in node_tokens]
        if not shared:
            continue
        if len(query_tokens) > 1 and len(shared) < 2:
            continue
        score = sum(graph.idf(token) for token in shared) / total
        if node.jurisdiction and node.jurisdiction in jurisdictions:
            score += 0.1
        if score < 0.45:
            continue
        mentions.append(
            EntityMention(
                node_id=node.id,
                kind=node.kind,
                label=node.label,
                matched_text=" ".join(shared),
                # Capped below an exact name match (1.0).
                score=round(min(score, 0.9), 4),
                source="query",
            )
        )
    mentions.sort(key=lambda mention: (-mention.score, mention.node_id))
    return mentions[:MAX_QUERY_KEYWORD_MATCHES]


def resolve_query_entities(graph: KnowledgeGraph, query: str) -> list[EntityMention]:
    """Named entities first; the rest of the query is matched by keywords."""
    named = resolve_named_entities(graph, query, source="query")
    remainder = f" {normalize(query)} "
    for mention in named:
        remainder = remainder.replace(f" {mention.matched_text} ", " ")
    named_ids = {mention.node_id for mention in named}
    keyword = [
        mention
        for mention in resolve_keyword_entities(
            graph, remainder, jurisdictions=extract_jurisdictions(query)
        )
        if mention.node_id not in named_ids
    ]
    return named + keyword


# --------------------------------------------------------------------------- #
# Traversal
# --------------------------------------------------------------------------- #


@dataclass
class Seed:
    node_id: str
    weight: float
    reason: str
    origin: str  # "query" or "chunk:<id>"


@dataclass
class Reach:
    hop: int
    relevance: float
    parent: str | None
    via: KGEdge | None


def traverse(
    graph: KnowledgeGraph, start: str, *, hops: int, weight: float = 1.0
) -> dict[str, Reach]:
    """Breadth-first walk from one seed. The company node is a hub that links
    to every supplier and policy, so it is reached but never expanded."""
    if start not in graph.nodes:
        return {}
    reached: dict[str, Reach] = {start: Reach(hop=0, relevance=weight, parent=None, via=None)}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        depth = reached[current].hop
        if depth >= hops:
            continue
        if graph.nodes[current].kind == "company" and current != start:
            continue
        for edge, neighbor in graph.neighbors(current):
            if neighbor in reached:
                continue
            reached[neighbor] = Reach(
                hop=depth + 1,
                relevance=weight * HOP_DECAY ** (depth + 1),
                parent=current,
                via=edge,
            )
            queue.append(neighbor)
    return reached


@dataclass
class NodeState:
    hop: int
    relevance: float
    seed: bool = False
    matched_by: list[str] = field(default_factory=list)


@dataclass
class TraversalResult:
    states: dict[str, NodeState]
    # Per origin ("query" or "chunk:<id>"): node -> relevance.
    by_origin: dict[str, dict[str, float]]
    # Seed -> reached nodes, kept for path reconstruction.
    walks: dict[str, dict[str, Reach]]


def traverse_from_seeds(
    graph: KnowledgeGraph, seeds: Sequence[Seed], *, hops: int
) -> TraversalResult:
    states: dict[str, NodeState] = {}
    by_origin: dict[str, dict[str, float]] = {}
    walks: dict[str, dict[str, Reach]] = {}
    for seed in seeds:
        walk = walks.get(seed.node_id)
        if walk is None:
            walk = traverse(graph, seed.node_id, hops=hops)
            walks[seed.node_id] = walk
        origin_scores = by_origin.setdefault(seed.origin, {})
        for reached_id, reach in walk.items():
            relevance = seed.weight * HOP_DECAY**reach.hop
            origin_scores[reached_id] = max(origin_scores.get(reached_id, 0.0), relevance)
            state = states.get(reached_id)
            if state is None:
                state = NodeState(hop=reach.hop, relevance=relevance)
                states[reached_id] = state
            else:
                state.hop = min(state.hop, reach.hop)
                state.relevance = max(state.relevance, relevance)
        seed_state = states[seed.node_id]
        seed_state.seed = True
        if seed.reason not in seed_state.matched_by:
            seed_state.matched_by.append(seed.reason)
    return TraversalResult(states=states, by_origin=by_origin, walks=walks)


def _path_to(walk: dict[str, Reach], target: str) -> list[str]:
    path: list[str] = []
    current: str | None = target
    while current is not None:
        path.append(current)
        current = walk[current].parent
    return list(reversed(path))


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #


@dataclass
class GraphRAGHit:
    chunk: Any
    score: float
    mode: str
    related_entities: list[dict[str, Any]]
    retrieval_score: float = 0.0
    graph_score: float = 0.0
    origin: Literal["retrieval", "graph"] = "retrieval"


@dataclass
class SubgraphNode:
    id: str
    kind: NodeKind
    label: str
    detail: str
    priority: str | None
    hop: int
    relevance: float
    seed: bool
    matched_by: list[str]


@dataclass
class SubgraphEdge:
    id: str
    source: str
    target: str
    label: str
    inferred: bool


@dataclass
class TraversalPath:
    node_ids: list[str]
    description: str


@dataclass
class GraphRAGResult:
    query: str
    hops: int
    results: list[GraphRAGHit]
    graph_evidence: list[GraphRAGHit]
    entities: list[EntityMention]
    jurisdictions: list[str]
    nodes: list[SubgraphNode]
    edges: list[SubgraphEdge]
    paths: list[TraversalPath]
    traversal_summary: str
    mode: str


@dataclass
class GraphContext:
    """Output of the pure resolution + traversal stage, before chunk fetching."""

    seeds: list[Seed]
    entities: list[EntityMention]
    jurisdictions: list[str]
    traversal: TraversalResult
    kept: list[str]
    hit_related: dict[str, list[str]]
    hit_graph_scores: dict[str, float]
    paths: list[TraversalPath]


def _hit_weight(rank: int) -> float:
    # Rank 1 -> 0.9, rank 2 -> 0.8 ... floor at 0.4: evidence seeds stay below
    # an exact query mention (1.0) but above a weak keyword match.
    return max(0.4, 0.9 - 0.1 * (rank - 1))


def build_graph_context(
    graph: KnowledgeGraph,
    query: str,
    hits: Sequence[SearchHit],
    *,
    hops: int = 2,
    max_nodes: int = MAX_SUBGRAPH_NODES,
) -> GraphContext:
    """Resolve entities for a query and its retrieved chunks, then traverse."""
    entities = resolve_query_entities(graph, query)
    seeds: list[Seed] = [
        Seed(
            node_id=mention.node_id,
            weight=mention.score,
            reason=f"query: {mention.matched_text}",
            origin="query",
        )
        for mention in entities
    ]
    for rank, hit in enumerate(hits, start=1):
        chunk_id = str(hit.chunk.id)
        origin = f"chunk:{chunk_id}"
        weight = _hit_weight(rank)
        for linked in sorted(graph.chunk_links.get(chunk_id, set())):
            seeds.append(Seed(node_id=linked, weight=weight, reason="evidence link", origin=origin))
        for mention in resolve_named_entities(
            graph, hit.chunk.content, source="evidence", chunk_id=chunk_id
        ):
            if mention.kind == "company":
                continue
            entities.append(mention)
            seeds.append(
                Seed(
                    node_id=mention.node_id,
                    weight=weight * 0.8,
                    reason=f"named in evidence: {mention.matched_text}",
                    origin=origin,
                )
            )

    traversal = traverse_from_seeds(graph, seeds, hops=hops)
    states = traversal.states

    ranked = sorted(
        states,
        key=lambda nid: (not states[nid].seed, -states[nid].relevance, states[nid].hop, nid),
    )
    kept = ranked[:max_nodes]
    kept_set = set(kept)

    query_reach = traversal.by_origin.get("query", {})
    hit_related: dict[str, list[str]] = {}
    hit_graph_scores: dict[str, float] = {}
    for hit in hits:
        chunk_id = str(hit.chunk.id)
        reach = traversal.by_origin.get(f"chunk:{chunk_id}", {})
        related = sorted(
            (nid for nid in reach if nid in kept_set and graph.nodes[nid].kind != "company"),
            key=lambda nid: (-reach[nid], nid),
        )
        hit_related[chunk_id] = related[:MAX_RELATED_PER_HIT]
        # Graph score: how strongly the chunk's own entities overlap with the
        # neighbourhood of the entities named in the query.
        overlap = [
            min(reach[nid], query_reach[nid])
            for nid in reach
            if nid in query_reach and graph.nodes[nid].kind != "company"
        ]
        best = max(overlap, default=0.0)
        top = max(reach.values(), default=0.0)
        hit_graph_scores[chunk_id] = round(best / top, 6) if top else 0.0

    paths = _describe_paths(graph, seeds, traversal, kept_set)
    return GraphContext(
        seeds=seeds,
        entities=_dedupe_mentions(entities),
        jurisdictions=extract_jurisdictions(query),
        traversal=traversal,
        kept=kept,
        hit_related=hit_related,
        hit_graph_scores=hit_graph_scores,
        paths=paths,
    )


def _dedupe_mentions(mentions: Iterable[EntityMention]) -> list[EntityMention]:
    best: dict[tuple[str, str], EntityMention] = {}
    for mention in mentions:
        key = (mention.node_id, mention.source)
        current = best.get(key)
        if current is None or mention.score > current.score:
            best[key] = mention
    return sorted(best.values(), key=lambda m: (m.source != "query", -m.score, m.label))


def _describe_node(node: KGNode) -> str:
    kind = node.kind
    if kind == "supplier":
        tier = node.detail.split(" supplier")[0]
        return f"{node.label} ({tier})"
    return f"{node.label} ({kind})"


_PATH_END_PREFERENCE = {"obligation": 3, "policy": 3, "supplier": 2, "buyer": 2, "risk": 1}


def _describe_path(graph: KnowledgeGraph, walk: dict[str, Reach], node_path: list[str]) -> str:
    parts = [_describe_node(graph.nodes[node_path[0]])]
    for previous, current in zip(node_path, node_path[1:], strict=False):
        edge = walk[current].via
        label = edge.label if edge is not None else "linked to"
        # Arrows follow the stored edge direction, so a path can be read
        # against the grain: "Obligation ←creates obligation— Signal".
        arrow = f"—{label}→" if edge is None or edge.source == previous else f"←{label}—"
        parts.append(f"{arrow} {_describe_node(graph.nodes[current])}")
    return " ".join(parts)


def _describe_paths(
    graph: KnowledgeGraph,
    seeds: Sequence[Seed],
    traversal: TraversalResult,
    kept: set[str],
    *,
    limit: int = 6,
    per_query_seed: int = 3,
) -> list[TraversalPath]:
    """Readable traversal paths, query seeds first.

    For each seed, the walk is split into branches by first hop and the best
    end node of each branch is chosen: deepest first, then obligations and
    policies over plain signals, then relevance. Query seeds contribute up to
    ``per_query_seed`` branches; evidence seeds contribute one.
    """
    paths: list[TraversalPath] = []
    seen: set[frozenset[str]] = set()
    ordered_seeds = sorted(seeds, key=lambda seed: (seed.origin != "query", -seed.weight))
    done: set[str] = set()
    for seed in ordered_seeds:
        if seed.node_id in done:
            continue
        done.add(seed.node_id)
        walk = traversal.walks.get(seed.node_id, {})
        branches: dict[str, str] = {}
        for nid, reach in walk.items():
            if reach.hop == 0 or nid not in kept or graph.nodes[nid].kind == "company":
                continue
            node_path = _path_to(walk, nid)
            if any(graph.nodes[step].kind == "company" for step in node_path):
                continue
            branch = node_path[1]
            current = branches.get(branch)
            if current is None or _end_rank(graph, traversal, walk, nid) > _end_rank(
                graph, traversal, walk, current
            ):
                branches[branch] = nid
        ends = sorted(
            branches.values(),
            key=lambda nid: _end_rank(graph, traversal, walk, nid),
            reverse=True,
        )
        budget = per_query_seed if seed.origin == "query" else 1
        for end in ends[:budget]:
            node_path = _path_to(walk, end)
            key = frozenset(node_path)
            if key in seen:
                continue
            seen.add(key)
            paths.append(
                TraversalPath(
                    node_ids=node_path, description=_describe_path(graph, walk, node_path)
                )
            )
            if len(paths) >= limit:
                return paths
    return paths


def _end_rank(
    graph: KnowledgeGraph, traversal: TraversalResult, walk: dict[str, Reach], nid: str
) -> tuple[int, int, float, str]:
    return (
        walk[nid].hop,
        _PATH_END_PREFERENCE.get(graph.nodes[nid].kind, 0),
        traversal.states[nid].relevance,
        nid,
    )


def _count(value: int, singular: str, plural: str) -> str:
    return f"{value} {singular if value == 1 else plural}"


def summarize_traversal(
    context: GraphContext, *, node_count: int, edge_count: int, hops: int
) -> str:
    query_seeds = {seed.node_id for seed in context.seeds if seed.origin == "query"}
    evidence_seeds = {
        seed.node_id for seed in context.seeds if seed.origin != "query"
    } - query_seeds
    if not context.seeds:
        return "No graph entities matched the query or the retrieved evidence."
    summary = (
        f"Resolved {_count(len(query_seeds), 'entity', 'entities')} from the query and "
        f"{len(evidence_seeds)} from retrieved evidence; traversed up to "
        f"{_count(hops, 'hop', 'hops')} to {_count(node_count, 'node', 'nodes')} and "
        f"{_count(edge_count, 'edge', 'edges')}."
    )
    if context.paths:
        summary += f" Strongest path: {context.paths[0].description}"
    return summary


def _subgraph(
    graph: KnowledgeGraph, context: GraphContext
) -> tuple[list[SubgraphNode], list[SubgraphEdge]]:
    kept = set(context.kept)
    states = context.traversal.states
    nodes = [
        SubgraphNode(
            id=nid,
            kind=graph.nodes[nid].kind,
            label=graph.nodes[nid].label,
            detail=graph.nodes[nid].detail,
            priority=graph.nodes[nid].priority,
            hop=states[nid].hop,
            relevance=round(states[nid].relevance, 4),
            seed=states[nid].seed,
            matched_by=list(states[nid].matched_by),
        )
        for nid in context.kept
    ]
    edges = [
        SubgraphEdge(
            id=edge.id,
            source=edge.source,
            target=edge.target,
            label=edge.label,
            inferred=edge.inferred,
        )
        for edge in graph.edges.values()
        if edge.source in kept and edge.target in kept
    ]
    return nodes, edges


def _entity_ref(graph: KnowledgeGraph, nid: str, relevance: float) -> dict[str, Any]:
    node = graph.nodes[nid]
    return {"id": nid, "kind": node.kind, "label": node.label, "relevance": round(relevance, 4)}


def fuse(
    graph: KnowledgeGraph,
    query: str,
    hits: Sequence[SearchHit],
    *,
    hops: int = 2,
    limit: int = 8,
    graph_chunks: Sequence[tuple[Any, str]] = (),
    max_nodes: int = MAX_SUBGRAPH_NODES,
    context: GraphContext | None = None,
) -> GraphRAGResult:
    """Combine retrieval hits with graph context into a ``GraphRAGResult``.

    ``graph_chunks`` are ``(chunk, node_id)`` pairs: evidence attached to a
    traversed node that plain retrieval did not return.
    """
    context = context or build_graph_context(graph, query, hits, hops=hops, max_nodes=max_nodes)
    nodes, edges = _subgraph(graph, context)
    mode = hits[0].mode if hits else "mock"

    top_retrieval = max((hit.score for hit in hits), default=0.0) or 1.0
    fused: list[GraphRAGHit] = []
    for hit in hits:
        chunk_id = str(hit.chunk.id)
        retrieval = hit.score / top_retrieval
        graph_score = context.hit_graph_scores.get(chunk_id, 0.0)
        reach = context.traversal.by_origin.get(f"chunk:{chunk_id}", {})
        fused.append(
            GraphRAGHit(
                chunk=hit.chunk,
                score=round((1 - GRAPH_WEIGHT) * retrieval + GRAPH_WEIGHT * graph_score, 6),
                mode=hit.mode,
                related_entities=[
                    _entity_ref(graph, nid, reach.get(nid, 0.0))
                    for nid in context.hit_related.get(chunk_id, [])
                ],
                retrieval_score=hit.score,
                graph_score=graph_score,
                origin="retrieval",
            )
        )
    fused.sort(key=lambda item: (-item.score, -item.retrieval_score))
    fused = fused[:limit]

    states = context.traversal.states
    seen_chunks = {str(hit.chunk.id) for hit in hits}
    extra: list[GraphRAGHit] = []
    for chunk, anchor in graph_chunks:
        chunk_id = str(chunk.id)
        if chunk_id in seen_chunks or anchor not in states:
            continue
        seen_chunks.add(chunk_id)
        relevance = states[anchor].relevance
        extra.append(
            GraphRAGHit(
                chunk=chunk,
                score=round(GRAPH_WEIGHT * relevance, 6),
                mode="graph",
                related_entities=[_entity_ref(graph, anchor, relevance)],
                retrieval_score=0.0,
                graph_score=round(relevance, 6),
                origin="graph",
            )
        )
    extra.sort(key=lambda item: (-item.graph_score, str(item.chunk.id)))
    extra = extra[: max(2, limit // 2)]

    return GraphRAGResult(
        query=query,
        hops=hops,
        results=fused,
        graph_evidence=extra,
        entities=context.entities,
        jurisdictions=context.jurisdictions,
        nodes=nodes,
        edges=edges,
        paths=context.paths,
        traversal_summary=summarize_traversal(
            context, node_count=len(nodes), edge_count=len(edges), hops=hops
        ),
        mode=mode,
    )


def graph_evidence_targets(
    graph: KnowledgeGraph, context: GraphContext, *, min_relevance: float = 0.2
) -> dict[str, str]:
    """Signal and risk nodes in the subgraph whose evidence is worth fetching.

    Returns ``{node_id: anchor_node_id}`` for nodes that are relevant to the
    query itself (not only to a retrieved chunk), so graph evidence widens the
    answer around what the user asked about.
    """
    query_reach = context.traversal.by_origin.get("query", {})
    targets: dict[str, str] = {}
    for nid in context.kept:
        if graph.nodes[nid].kind not in {"signal", "risk"}:
            continue
        if query_reach.get(nid, 0.0) >= min_relevance:
            targets[nid] = nid
    return targets


# --------------------------------------------------------------------------- #
# Database layer
# --------------------------------------------------------------------------- #

MAX_GRAPH_ROWS = 500


async def load_knowledge_graph(
    session: AsyncSession, *, extra_signal_ids: Iterable[uuid.UUID] = ()
) -> KnowledgeGraph:
    """Load the relational supply-chain graph for the workspace company."""
    company = (await session.execute(select(Company).limit(1))).scalar_one_or_none()
    suppliers = (
        (await session.execute(select(Supplier).order_by(Supplier.tier, Supplier.name)))
        .scalars()
        .all()
    )
    buyers = (await session.execute(select(Buyer).order_by(Buyer.name))).scalars().all()
    policies = (await session.execute(select(Policy).order_by(Policy.name))).scalars().all()
    obligations = (
        (
            await session.execute(
                select(Obligation).order_by(Obligation.created_at.desc()).limit(MAX_GRAPH_ROWS)
            )
        )
        .scalars()
        .all()
    )
    risks = (
        (await session.execute(select(Risk).order_by(Risk.score.desc()).limit(MAX_GRAPH_ROWS)))
        .scalars()
        .all()
    )
    evidence_rows = (
        await session.execute(
            select(RiskEvidence.risk_id, RiskEvidence.evidence_chunk_id, EvidenceChunk.signal_id)
            .outerjoin(EvidenceChunk, EvidenceChunk.id == RiskEvidence.evidence_chunk_id)
            .limit(MAX_GRAPH_ROWS * 4)
        )
    ).all()

    # Signals: only the ones that connect to something (obligation, supplier,
    # risk evidence) or that the current retrieval returned. A live GDELT feed
    # can hold thousands of unconnected news signals.
    wanted_signals: set[uuid.UUID] = {obligation.signal_id for obligation in obligations}
    for _risk_id, _chunk_id, chunk_signal_id in evidence_rows:
        if chunk_signal_id is not None:
            wanted_signals.add(chunk_signal_id)
    wanted_signals.update(extra_signal_ids)
    signal_stmt = select(Signal).where(
        or_(Signal.id.in_(wanted_signals), Signal.supplier_id.is_not(None))
        if wanted_signals
        else Signal.supplier_id.is_not(None)
    )
    signals = (
        (
            await session.execute(
                signal_stmt.order_by(Signal.published_at.desc()).limit(MAX_GRAPH_ROWS)
            )
        )
        .scalars()
        .all()
    )
    signal_ids = [signal.id for signal in signals]
    signal_chunks = (
        (
            await session.execute(
                select(EvidenceChunk.id, EvidenceChunk.signal_id).where(
                    EvidenceChunk.signal_id.in_(signal_ids)
                )
            )
        ).all()
        if signal_ids
        else []
    )
    source_rows = (await session.execute(select(Source.id, Source.name))).all()

    return build_knowledge_graph(
        company=company,
        suppliers=suppliers,
        buyers=buyers,
        policies=policies,
        signals=signals,
        obligations=obligations,
        risks=risks,
        risk_evidence=[(row[0], row[1], row[2]) for row in evidence_rows],
        signal_chunks=[(row[0], row[1]) for row in signal_chunks],
        source_names={row[0]: row[1] for row in source_rows},
    )


async def _load_graph_chunks(
    session: AsyncSession, graph: KnowledgeGraph, targets: dict[str, str], *, limit: int
) -> list[tuple[EvidenceChunk, str]]:
    chunk_ids: dict[str, str] = {}
    for target, anchor in targets.items():
        for chunk_id in sorted(graph.node_chunks.get(target, set())):
            chunk_ids.setdefault(chunk_id, anchor)
    if not chunk_ids:
        return []
    ids = [uuid.UUID(chunk_id) for chunk_id in list(chunk_ids)[: limit * 4]]
    rows = (
        (await session.execute(select(EvidenceChunk).where(EvidenceChunk.id.in_(ids))))
        .scalars()
        .all()
    )
    return [(chunk, chunk_ids[str(chunk.id)]) for chunk in rows]


Retriever = Callable[..., Awaitable[list[SearchHit]]]


async def graph_augmented_search(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 8,
    hops: int = 2,
    retriever: Retriever = search_evidence,
) -> GraphRAGResult:
    """Hybrid retrieval + entity resolution + multi-hop traversal + fusion."""
    hops = max(1, min(hops, 3))
    hits = await retriever(session, query, limit=limit) if query.strip() else []
    graph = await load_knowledge_graph(
        session,
        extra_signal_ids=[hit.chunk.signal_id for hit in hits if hit.chunk.signal_id],
    )
    context = build_graph_context(graph, query, hits, hops=hops)
    targets = graph_evidence_targets(graph, context)
    graph_chunks = await _load_graph_chunks(session, graph, targets, limit=limit)
    return fuse(
        graph, query, hits, hops=hops, limit=limit, graph_chunks=graph_chunks, context=context
    )
