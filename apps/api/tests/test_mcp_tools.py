from __future__ import annotations

import asyncio

import pytest
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


def test_mcp_cli_serves_streamable_http_with_bearer_token(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(mcp, "auth", None)
    monkeypatch.setenv("CHOWKIDAR_MCP_HTTP_TOKEN", "test-token")
    server.main(["--transport", "http", "--port", "9999"])
    assert calls == [{"transport": "http", "host": "127.0.0.1", "port": 9999}]
    assert mcp.auth is not None


def test_mcp_http_fails_closed_without_a_token(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    monkeypatch.delenv("CHOWKIDAR_MCP_HTTP_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        server.main(["--transport", "http"])
    assert calls == []


def test_mcp_http_allows_explicit_loopback_unauthenticated_mode(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(mcp, "auth", object())
    monkeypatch.delenv("CHOWKIDAR_MCP_HTTP_TOKEN", raising=False)
    server.main(["--transport", "http", "--allow-unauthenticated"])
    assert calls == [{"transport": "http", "host": "127.0.0.1", "port": 8765}]
    assert mcp.auth is None


def test_mcp_http_rejects_unauthenticated_non_loopback_host(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    monkeypatch.delenv("CHOWKIDAR_MCP_HTTP_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        server.main(
            [
                "--transport",
                "http",
                "--allow-unauthenticated",
                "--host",
                "0.0.0.0",  # noqa: S104 - asserting that a non-loopback bind is rejected
            ]
        )
    assert calls == []


def test_mcp_http_rejects_token_with_allow_unauthenticated(monkeypatch) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setenv("CHOWKIDAR_MCP_HTTP_TOKEN", "test-token")
    with pytest.raises(SystemExit):
        server.main(["--transport", "http", "--allow-unauthenticated"])
    assert calls == []
