# Credits

## PR #1 — hackathon readiness review

Parts of this repository were adapted from
[PR #1](https://github.com/A7reus/Chowkidar/pull/1), contributed by
[@shihab3point14](https://github.com/shihab3point14) (Shihab).

The PR was reviewed in full but **not merged as a whole** because its branch
conflicted with `main`. The useful parts were re-applied, reviewed, hardened,
and tested on current `main`. The PR was closed unmerged on 2026-10-27 after
the public credit comment.

### Adapted

| Area | What was taken | Where it landed |
|---|---|---|
| Local LLM routing | Ollama as a usable live provider, local-first routing, provider filtering, and the `/api/v1/meta` local-LLM flags | `apps/api/app/core/config.py`, `apps/api/app/agents/llm.py`, `apps/api/app/api/v1/meta.py` |
| MCP transport | Streamable HTTP/SSE transport flags, host/port options, bearer-token auth, and the `mcp-http` / `mcp-tunnel` / `ollama-pull` Make targets | `apps/api/app/mcp/server.py`, `Makefile` |
| Chunking | Structure-aware splitting at recognized legal headings, with section paths on each chunk | `apps/api/app/rag/chunking.py` |

The adaptation also added behavior that was not in the original PR:

- `LLM_LOCAL_ONLY` hard-disables cloud providers and fails closed without Ollama.
- MCP HTTP requires a bearer token by default; unauthenticated mode is loopback-only
  and must be requested explicitly.
- Expanded tests for local-only routing, fail-closed MCP auth, loopback binding,
  token conflicts, and heading-based chunking.

### Not taken

- `.github/workflows/keep-warm.yml` — rejected to avoid consuming roughly 744 of
  Render Free's 750 monthly instance hours and to avoid relying on GitHub cron
  scheduling for the pilot.
- The PR's `README.md` hunk — it conflicted with the current README and was
  rewritten separately.

### Commits

Original PR commits:

- `c94e9b8` — local LLM routing, MCP over HTTP, structure-aware chunking
  (its keep-warm workflow hunk was not taken)
- `e6662e5` — seed baseline for article-level chunks

Adapted and deployed on `main`:

- `322bc24` — `feat: adapt selected PR #1 improvements`
- `48ad95b` — `docs: record PR #1 deploy and hosted revision`

The commit that adds this file carries the GitHub co-author trailer for Shihab.

## License

This project is MIT-licensed; see [`LICENSE`](LICENSE). This file records
attribution for adapted contributions and does not replace the license notice.
