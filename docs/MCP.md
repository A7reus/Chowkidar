# Chowkidar MCP server

Chowkidar exposes a **read-only** [FastMCP](https://gofastmcp.com/) server. It lets another agent inspect the risk register, evidence, pending approvals, and supply-chain graph without mutating state or bypassing human approval.

**Source:** `apps/api/app/mcp/server.py`  
**Transports:** stdio (default) and Streamable HTTP (`--transport http`, SSE also available)  
**Auth:** demo token obtained automatically from the local API; optionally set `CHOWKIDAR_MCP_TOKEN`. Over HTTP, set `CHOWKIDAR_MCP_HTTP_TOKEN` to require a bearer token from MCP clients.

---

## Why read-only?

Material actions in Chowkidar are intentionally human-gated:

- recording an approval or rejection,
- creating or changing remediation actions,
- running the pipeline,
- generating reports.

Exposing those over MCP would create a second, unaudited control plane. The MCP server therefore only reads. Operators use the role-gated web app or REST API for mutations.

---

## Prerequisites

1. Start Postgres and seed the demo:

   ```bash
   make services-up
   make migrate
   make seed
   ```

2. Start the API:

   ```bash
   make api
   ```

3. Run the MCP server:

   ```bash
   make mcp
   # equivalent:
   cd apps/api && uv run python -m app.mcp.server
   ```

The server talks to `CHOWKIDAR_API_URL` (default `http://127.0.0.1:8000`) and logs in with `CHOWKIDAR_DEMO_ROLE` (default `analyst`).

---

## Client configuration

Claude Desktop / compatible MCP client:

```json
{
  "mcpServers": {
    "chowkidar": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/ai-builders-congress/apps/api",
        "python",
        "-m",
        "app.mcp.server"
      ],
      "env": {
        "CHOWKIDAR_API_URL": "http://127.0.0.1:8000",
        "CHOWKIDAR_DEMO_ROLE": "analyst"
      }
    }
  }
}
```

If your client launches from the repository root, use a project flag instead of an absolute path:

```json
{
  "command": "uv",
  "args": ["run", "--project", "apps/api", "python", "-m", "app.mcp.server"]
}
```

For a deployed API:

```json
{
  "env": {
    "CHOWKIDAR_API_URL": "https://<api-domain>",
    "CHOWKIDAR_DEMO_ROLE": "analyst"
  }
}
```

The demo login endpoint is disabled when `AUTH_MODE=supabase`; set `CHOWKIDAR_MCP_TOKEN` to a valid Supabase bearer token in that case.

---

## Remote access: Streamable HTTP + tunnel

Stdio only works for an MCP host on the same machine. To let a remote agent or a
judge connect by URL, serve the same read-only tools over Streamable HTTP and
publish them through a Cloudflare quick tunnel:

```bash
# Terminal 1 — API (see Prerequisites)
make api

# Terminal 2 — MCP over HTTP at http://127.0.0.1:8765/mcp
export CHOWKIDAR_MCP_HTTP_TOKEN=$(openssl rand -hex 16)   # share this with the client
make mcp-http

# Terminal 3 — public https://<random>.trycloudflare.com URL
make mcp-tunnel
```

Client configuration for a URL-based MCP host:

```json
{
  "mcpServers": {
    "chowkidar": {
      "url": "https://<random>.trycloudflare.com/mcp",
      "headers": { "Authorization": "Bearer <CHOWKIDAR_MCP_HTTP_TOKEN>" }
    }
  }
}
```

The tunnel is ephemeral and exposes only the read-only tools. Always set
`CHOWKIDAR_MCP_HTTP_TOKEN` before tunnelling; without it anyone with the URL can
read the workspace. `--host`, `--port`, `CHOWKIDAR_MCP_HOST`, and
`CHOWKIDAR_MCP_PORT` change the bind address.

---

## Tools

| Tool | Arguments | Returns |
|---|---|---|
| `dashboard_summary` | — | Company posture, counts, top risks, source health |
| `list_open_risks` | `priority?`, `limit?` | Open risks sorted by score, with counts by priority |
| `get_risk` | `risk_id` | Risk, score breakdown, evidence, actions, approvals |
| `search_evidence` | `query`, `limit?` | Cited source chunks from hybrid retrieval |
| `list_pending_approvals` | — | Human decisions waiting in the queue |
| `supply_chain_graph` | — | Nodes, edges, and counts by kind |

### Prompt

`risk_review_prompt(risk_id)` builds a conservative review prompt that tells the model to:

1. fetch the risk,
2. search the exact cited language,
3. separate facts, potential exposure, and open questions,
4. avoid legal advice and compliance claims,
5. end with the human decision to record.

### Resource

`chowkidar://methodology` documents the score formula, priority bands, evidence rules, verifier, and approval boundary.

---

## Example session

```text
User: What are the most urgent supplier risks for Padma Apparel?

Agent → dashboard_summary
Agent → list_open_risks(priority="critical")

Agent: Three critical risks:
1. Cotton origin documentation is incomplete for US-bound order LT-4412
   (Sunrise Cotton Growers, score 100).
2. Supplier code and risk mapping are not aligned with CSDDD due diligence
   (Dhaka Knit Composite, score 83.8).
3. Potential UFLPA ownership match requires enhanced due diligence
   (SinoFab Chemicals, score 82.5, in review).

All three are reviewable signals, not legal conclusions. The first has
four pending remediation actions. Human approval is required before any
supplier action is recorded.
```

---

## Safety boundaries

- Read-only tools only; no approval, mutation, pipeline, or report tools.
- Every evidence result keeps its citation label, URL, and signal deep link.
- Tool descriptions and the methodology resource state the not-legal-advice boundary.
- Errors from the API are surfaced as tool errors rather than fabricated data.
- The server does not log prompts or responses.
- The demo role is intentionally the least-privileged role that can read the workspace (`analyst`); it cannot record approvals.

---

## Testing the server

List tools and resources:

```bash
cd apps/api
uv run python - <<'PY'
import asyncio
from app.mcp.server import mcp

async def main():
    print([tool.name for tool in await mcp.list_tools()])
    print([prompt.name for prompt in await mcp.list_prompts()])
    print([str(resource.uri) for resource in await mcp.list_resources()])

asyncio.run(main())
PY
```

Call a tool against a running API:

```bash
cd apps/api
uv run python - <<'PY'
import asyncio
from app.mcp.server import api, mcp

async def main():
    try:
        result = await mcp.call_tool("dashboard_summary", {})
        print(result)
    finally:
        await api.close()

asyncio.run(main())
PY
```

A full MCP client test (list tools, call tools, read resource) is part of the manual QA checklist; the server itself is covered by API contract tests and startup smoke tests.
