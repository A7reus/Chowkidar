from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Company, Policy, Risk, Supplier
from app.schemas import GraphEdge, GraphNode, GraphOut


def _short(text: str, limit: int = 58) -> str:
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


async def get_graph(session: AsyncSession) -> GraphOut:
    company = (await session.execute(select(Company).limit(1))).scalar_one_or_none()
    suppliers = list(
        (await session.execute(select(Supplier).order_by(Supplier.tier, Supplier.name)))
        .scalars()
        .all()
    )
    risks = list(
        (
            await session.execute(
                select(Risk)
                .options(selectinload(Risk.supplier), selectinload(Risk.obligation))
                .order_by(Risk.score.desc())
                .limit(8)
            )
        )
        .scalars()
        .all()
    )
    policies = list(
        (await session.execute(select(Policy).order_by(Policy.name).limit(5))).scalars().all()
    )

    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}

    def add_node(node: GraphNode) -> None:
        nodes.setdefault(node.id, node)

    def add_edge(source: str, target: str, label: str) -> None:
        edge_id = f"{source}->{target}"
        edges.setdefault(edge_id, GraphEdge(id=edge_id, source=source, target=target, label=label))

    if company is not None:
        company_node_id = f"company:{company.id}"
        add_node(
            GraphNode(
                id=company_node_id,
                label=company.name,
                kind="company",
                detail=f"{company.country} · {company.sector}",
            )
        )
    else:
        company_node_id = ""

    for supplier in suppliers:
        supplier_node_id = f"supplier:{supplier.id}"
        add_node(
            GraphNode(
                id=supplier_node_id,
                label=supplier.name,
                kind="supplier",
                detail=f"Tier {supplier.tier} · {supplier.country}",
            )
        )
        if company_node_id:
            add_edge(company_node_id, supplier_node_id, "sources from")

    for policy in policies:
        policy_node_id = f"policy:{policy.id}"
        add_node(
            GraphNode(
                id=policy_node_id,
                label=policy.name,
                kind="policy",
                detail=f"v{policy.version} · {policy.owner}",
            )
        )
        if company_node_id:
            add_edge(company_node_id, policy_node_id, "governed by")

    for risk in risks:
        risk_node_id = f"risk:{risk.id}"
        add_node(
            GraphNode(
                id=risk_node_id,
                label=_short(risk.title),
                kind="risk",
                priority=risk.priority,
                detail=f"Score {risk.score:.1f} · {risk.status}",
            )
        )
        if risk.supplier_id:
            add_edge(risk_node_id, f"supplier:{risk.supplier_id}", "affects")
        if risk.obligation is not None:
            obligation_node_id = f"obligation:{risk.obligation.id}"
            add_node(
                GraphNode(
                    id=obligation_node_id,
                    label=_short(risk.obligation.title),
                    kind="obligation",
                    detail=f"{risk.obligation.jurisdiction} · {risk.obligation.obligation_type}",
                )
            )
            add_edge(risk_node_id, obligation_node_id, "arises from")

    return GraphOut(nodes=list(nodes.values()), edges=list(edges.values()))
