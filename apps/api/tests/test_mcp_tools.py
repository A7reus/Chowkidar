from __future__ import annotations

import asyncio

from app.mcp import server
from app.mcp.server import api, mcp


def test_mcp_exposes_read_only_risk_tools() -> None:
    names = asyncio.run(_tool_names())
    assert names == {
        "dashboard_summary",
        "list_open_risks",
        "get_risk",
        "search_evidence",
        "list_pending_approvals",
        "supply_chain_graph",
    }


def test_mcp_exposes_review_prompt_and_methodology() -> None:
    prompts = asyncio.run(mcp.list_prompts())
    resources = asyncio.run(mcp.list_resources())
    assert [prompt.name for prompt in prompts] == ["risk_review_prompt"]
    assert [str(resource.uri) for resource in resources] == ["chowkidar://methodology"]


async def _tool_names() -> set[str]:
    try:
        tools = await mcp.list_tools()
        return {tool.name for tool in tools}
    finally:
        await api.close()


def test_mcp_cli_defaults_to_stdio(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    server.main([])
    assert calls == [{}]


def test_mcp_cli_serves_streamable_http_with_optional_bearer_token(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(mcp, "auth", None)
    monkeypatch.setenv("CHOWKIDAR_MCP_HTTP_TOKEN", "test-token")
    server.main(["--transport", "http", "--port", "9999"])
    assert calls == [{"transport": "http", "host": "127.0.0.1", "port": 9999}]
    assert mcp.auth is not None
