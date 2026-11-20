"""Read-only MCP server for regulatory evidence and citation checks."""

from __future__ import annotations

import argparse
import os
from typing import Any

from fastmcp import FastMCP

from app.mcp.server import api

mcp = FastMCP(
    name="chowkidar-evidence",
    instructions=(
        "Read-only tools for Chowkidar source evidence: search cited source "
        "chunks, check that a quote appears verbatim in retrieved text, and "
        "inspect regulatory streams and extracted obligations. Never describe "
        "a signal as a legal conclusion."
    ),
    version="0.1.0",
)


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


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
async def verify_citation(quote: str, chunk_id: str | None = None) -> dict[str, Any]:
    """Check whether a quote appears word for word in a retrieved source chunk.

    This is a simple verbatim match over search results. It is not the full
    Chowkidar verifier and gives no legal conclusion.
    """
    wanted = _norm(quote)
    if len(wanted) < 10:
        raise ValueError("quote must contain at least ten characters")
    data = await api.get(
        "/api/v1/search", params={"q": quote.strip()[:300], "limit": 20}
    )
    matches = []
    for item in data.get("results", []):
        if chunk_id and item.get("chunk_id") != chunk_id:
            continue
        if wanted in _norm(str(item.get("content") or "")):
            matches.append(
                {
                    "chunk_id": item.get("chunk_id"),
                    "citation": item.get("citation_label"),
                    "citation_url": item.get("citation_url"),
                }
            )
    return {"verbatim_match": bool(matches), "matches": matches}


@mcp.tool
async def get_regulatory_source(stream_key: str) -> dict[str, Any]:
    """Return health and sync details for monitored streams whose details match stream_key."""
    data = await api.get("/api/v1/sources")
    items = data if isinstance(data, list) else data.get("items", [])
    needle = stream_key.strip().lower()
    found = [
        item
        for item in items
        if needle and needle in " ".join(str(v).lower() for v in item.values())
    ]
    return {"query": stream_key, "total": len(found), "sources": found}


@mcp.tool
async def list_active_obligations(limit: int = 10) -> dict[str, Any]:
    """List obligation nodes from the supply-chain and obligation graph."""
    data = await api.get("/api/v1/graph")
    nodes = [n for n in data.get("nodes", []) if str(n.get("kind")) == "obligation"]
    cap = max(1, min(limit, 50))
    return {"total": len(nodes), "obligations": nodes[:cap]}


@mcp.prompt
def citation_audit_prompt(claim_text: str) -> str:
    """Build a conservative prompt that checks a claim against cited evidence."""
    return (
        f"Check this claim using Chowkidar tools: {claim_text}\n"
        "Call search_evidence for the supporting language, then verify_citation "
        "on any quote you rely on. Report only what the sources support. Do not "
        "give legal advice or claim compliance."
    )


@mcp.resource("chowkidar://regulatory-streams")
async def regulatory_streams() -> str:
    """List the monitored regulatory, sanctions, and news streams."""
    data = await api.get("/api/v1/sources")
    items = data if isinstance(data, list) else data.get("items", [])
    return "\n".join(
        f"- {item.get('name')} ({item.get('mode') or item.get('last_sync_mode')})"
        for item in items
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chowkidar evidence MCP server")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default="stdio")
    parser.add_argument("--host", default=os.getenv("CHOWKIDAR_MCP_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("CHOWKIDAR_MCP_EVIDENCE_PORT", "8766"))
    )
    parser.add_argument("--allow-unauthenticated", action="store_true")
    args = parser.parse_args(argv)

    if args.transport == "stdio":
        mcp.run()
        return

    http_token = os.getenv("CHOWKIDAR_MCP_HTTP_TOKEN", "")
    if http_token and args.allow_unauthenticated:
        parser.error("--allow-unauthenticated cannot be combined with CHOWKIDAR_MCP_HTTP_TOKEN")
    if not http_token and not args.allow_unauthenticated:
        parser.error("CHOWKIDAR_MCP_HTTP_TOKEN is required for HTTP/SSE transports")
    if args.allow_unauthenticated and args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("--allow-unauthenticated is only allowed with a loopback --host")

    mcp.auth = None
    if http_token:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

        mcp.auth = StaticTokenVerifier(
            tokens={http_token: {"client_id": "chowkidar-mcp-http", "scopes": []}}
        )
    mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
