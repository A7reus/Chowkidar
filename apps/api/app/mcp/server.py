"""Read-only MCP server for the Chowkidar compliance risk API.

The server deliberately exposes only retrieval tools. Material actions such as
recording an approval or generating a report remain behind the authenticated
web application and its human-in-the-loop workflow.

Run it with the API available:

    cd apps/api
    uv run python -m app.mcp.server                      # stdio (local MCP hosts)
    uv run python -m app.mcp.server --transport http     # Streamable HTTP on :8765/mcp

The HTTP transport lets remote MCP hosts connect by URL, for example through a
Cloudflare quick tunnel (``make mcp-tunnel``). Set ``CHOWKIDAR_MCP_HTTP_TOKEN``
to require ``Authorization: Bearer <token>`` on every HTTP request.

Example client configuration:

    {
      "mcpServers": {
        "chowkidar": {
          "command": "uv",
          "args": ["run", "--project", "apps/api", "python", "-m", "app.mcp.server"],
          "env": {"CHOWKIDAR_API_URL": "http://127.0.0.1:8000"}
        }
      }
    }
"""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="chowkidar",
    instructions=(
        "Chowkidar is compliance risk intelligence for export supply chains. "
        "Use these read-only tools to inspect prioritized risks, source evidence, "
        "pending human approvals, and the supply-chain graph. Never describe a "
        "signal as a legal conclusion. Every material action requires human approval."
    ),
    version="0.1.0",
)

API_URL = os.getenv("CHOWKIDAR_API_URL", "http://127.0.0.1:8000").rstrip("/")
DEMO_ROLE = os.getenv("CHOWKIDAR_DEMO_ROLE", "analyst")
STATIC_TOKEN = os.getenv("CHOWKIDAR_MCP_TOKEN", "")


class _Api:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = STATIC_TOKEN or None
        self._lock = asyncio.Lock()

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=API_URL, timeout=25.0)
        return self._client

    async def _auth_token(self) -> str:
        if self._token:
            return self._token
        async with self._lock:
            if self._token:
                return self._token
            client = await self._http()
            response = await client.post(
                "/api/v1/auth/demo-login",
                json={"role": DEMO_ROLE},
            )
            response.raise_for_status()
            self._token = str(response.json()["access_token"])
            return self._token

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        client = await self._http()
        token = await self._auth_token()
        response = await client.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 401:
            self._token = None
            token = await self._auth_token()
            response = await client.get(
                path,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code >= 400:
            detail = response.text[:500]
            raise RuntimeError(f"Chowkidar API returned {response.status_code}: {detail}")
        return response.json()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


api = _Api()


def _risk_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "priority": item.get("priority"),
        "score": item.get("score"),
        "status": item.get("status"),
        "verification_status": item.get("verification_status"),
        "supplier": item.get("supplier_name"),
        "obligation": item.get("obligation_title"),
        "evidence_count": item.get("evidence_count"),
        "action_count": item.get("action_count"),
        "updated_at": item.get("updated_at"),
    }


@mcp.tool
async def dashboard_summary() -> dict[str, Any]:
    """Return the current risk posture: counts, trend, top risks, and source health."""
    data = await api.get("/api/v1/dashboard/summary")
    return {
        "company": data.get("company_name"),
        "total_risks": data.get("total_risks"),
        "open_risks": data.get("open_risks"),
        "critical_risks": data.get("critical_risks"),
        "high_risks": data.get("high_risks"),
        "pending_approvals": data.get("pending_approvals"),
        "signals_last_7_days": data.get("signals_last_7_days"),
        "verified_evidence_rate": data.get("verified_evidence_rate"),
        "top_risks": data.get("top_risks", [])[:5],
        "source_health": data.get("source_health", []),
    }


@mcp.tool
async def list_open_risks(
    priority: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """List open risks, optionally filtered by priority (critical, high, medium, low)."""
    params: dict[str, Any] = {
        "status": "open",
        "limit": max(1, min(limit, 50)),
        "sort": "score",
    }
    if priority:
        if priority not in {"critical", "high", "medium", "low"}:
            raise ValueError("priority must be critical, high, medium, or low")
        params["priority"] = priority
    data = await api.get("/api/v1/risks", params=params)
    return {
        "total": data.get("total"),
        "counts_by_priority": data.get("counts_by_priority", {}),
        "risks": [_risk_row(item) for item in data.get("items", [])],
    }


@mcp.tool
async def get_risk(risk_id: str) -> dict[str, Any]:
    """Return one risk with its score breakdown, evidence citations, actions, and approvals."""
    data = await api.get(f"/api/v1/risks/{risk_id}")
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "description": data.get("description"),
        "rationale": data.get("rationale"),
        "category": data.get("category"),
        "priority": data.get("priority"),
        "score": data.get("score"),
        "status": data.get("status"),
        "verification_status": data.get("verification_status"),
        "score_breakdown": data.get("score_breakdown"),
        "supplier": data.get("supplier"),
        "obligation": data.get("obligation"),
        "evidence": data.get("evidence", []),
        "actions": data.get("actions", []),
        "approvals": data.get("approvals", []),
    }


@mcp.tool
async def search_evidence(query: str, limit: int = 5) -> dict[str, Any]:
    """Search cited source chunks with hybrid retrieval. Returns source text, never a generated answer."""
    if len(query.strip()) < 2:
        raise ValueError("query must contain at least two characters")
    data = await api.get(
        "/api/v1/search",
        params={"q": query.strip(), "limit": max(1, min(limit, 20))},
    )
    return {
        "query": data.get("query"),
        "mode": data.get("mode"),
        "results": [
            {
                "chunk_id": item.get("chunk_id"),
                "content": item.get("content"),
                "citation": item.get("citation_label"),
                "citation_url": item.get("citation_url"),
                "section_path": item.get("section_path"),
                "score": item.get("score"),
                "signal_id": item.get("signal_id"),
            }
            for item in data.get("results", [])
        ],
    }


@mcp.tool
async def list_pending_approvals() -> dict[str, Any]:
    """List remediation decisions waiting for a human approver."""
    data = await api.get("/api/v1/approvals", params={"status": "pending"})
    return {
        "total": data.get("total"),
        "approvals": [
            {
                "id": item.get("id"),
                "risk_id": item.get("risk_id"),
                "risk_title": item.get("risk_title"),
                "action_title": item.get("action_title"),
                "requested_by": item.get("requested_by"),
                "assigned_to": item.get("assigned_to"),
                "created_at": item.get("created_at"),
            }
            for item in data.get("items", [])
        ],
    }


@mcp.tool
async def supply_chain_graph() -> dict[str, Any]:
    """Return the company, supplier, risk, obligation, and policy graph with counts."""
    data = await api.get("/api/v1/graph")
    nodes = data.get("nodes", [])
    counts: dict[str, int] = {}
    for node in nodes:
        kind = str(node.get("kind"))
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "counts": counts,
        "nodes": nodes,
        "edges": data.get("edges", []),
    }


@mcp.prompt
def risk_review_prompt(risk_id: str) -> str:
    """Build a conservative evidence-review prompt for a risk record."""
    return (
        f"Review risk {risk_id} using Chowkidar tools. First call get_risk, then "
        "search_evidence for the exact cited language. Summarize only what the "
        "sources support. Separate facts, potential exposure, and open questions. "
        "Do not give legal advice or claim compliance. End with the human decision "
        "that should be recorded."
    )


@mcp.resource("chowkidar://methodology")
def methodology() -> str:
    """Explain the scoring, evidence, verification, and human-approval boundaries."""
    return (
        "Chowkidar is compliance risk intelligence, not legal advice.\n"
        "Risk score = ((severity*0.40 + likelihood*0.35 + exposure*0.25) / 4) * 100.\n"
        "Priority bands: critical >= 80, high >= 60, medium >= 35, low < 35.\n"
        "Every risk must carry a verbatim source quote and citation URL.\n"
        "A deterministic verifier checks quote grounding, prohibited legal-advice "
        "phrases, prompt-injection markers, and missing evidence.\n"
        "Automation can propose remediation; a named human must approve material actions.\n"
        "All material mutations append to a SHA-256 hash-chained audit log."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chowkidar read-only MCP server")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default="stdio")
    parser.add_argument("--host", default=os.getenv("CHOWKIDAR_MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("CHOWKIDAR_MCP_PORT", "8765")))
    args = parser.parse_args(argv)

    if args.transport == "stdio":
        mcp.run()
        return

    http_token = os.getenv("CHOWKIDAR_MCP_HTTP_TOKEN", "")
    if http_token:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

        mcp.auth = StaticTokenVerifier(
            tokens={http_token: {"client_id": "chowkidar-mcp-http", "scopes": []}}
        )
    mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
