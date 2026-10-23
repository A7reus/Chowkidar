from __future__ import annotations

import asyncio

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
