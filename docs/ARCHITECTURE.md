# Chowkidar — Architecture

**Status:** local-first implementation validated; hosted API and web builds are live. Netlify is the primary web origin with production browser QA passed 2/2; Vercel remains a secondary fallback. See [`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md).
**Last updated:** 2026-10-27

---

## 1. System shape

```
┌────────────────────────────────────────────────────────────────────┐
│ Next.js console (Netlify primary, Vercel fallback)                 │
│ Dashboard · Signals · Risks · Approvals · Reports · Graph · Search │
│ Audit · Evals · i18n (EN/BN) · role-aware navigation               │
└───────────────────────────────┬────────────────────────────────────┘
                                │ REST /api/v1 + OpenAPI types
┌───────────────────────────────▼────────────────────────────────────┐
│ FastAPI (Render Docker)                                            │
│ auth · dashboard · signals · risks · actions · approvals · audit   │
│ reports · graph · search · evals · pipeline · MCP (stdio/HTTP)     │
└───────────────┬──────────────────────────────┬─────────────────────┘
                │                              │
┌───────────────▼──────────────┐   ┌───────────▼─────────────────────┐
│ Postgres + pgvector          │   │ Neo4j Aura (optional)           │
│ signals, obligations, risks, │   │ supply-chain graph projection   │
│ evidence, actions, approvals │   └─────────────────────────────────┘
│ audit events, evals, reports │
└───────────────┬──────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ LangGraph pipeline                                                  │
│ ingest → extract → map → score → remediate → verify → repair       │
│                                              └──────→ persist      │
│ LiteLLM providers / deterministic mock fixtures                    │
└────────────────────────────────────────────────────────────────────┘
```

The pilot keeps a seeded Postgres database so the story is reproducible. Connectors and the agent pipeline can run again over the same signals; mutation tools are role-gated and audited. The hosted service runs `DATA_MODE=hybrid`, `LLM_MODE=hybrid`, and the scheduler; Federal Register live sync is verified, while GDELT falls back under its public rate limit. Hosted live LLM inference is verified (`llm_live_ready=true`; a `mode=live` pipeline run produced a model-generated rationale with confidence `0.96`), and deterministic fallback remains available when providers fail. Provider keys are set in Render and the gitignored local `.env`; they are never committed.

---

## 2. Monorepo

```
apps/
  api/        FastAPI, SQLAlchemy, Alembic, LangGraph, MCP
  web/        Next.js App Router console
data/
  fixtures/   Fictional company, suppliers, signals, evidence
evals/        Golden cases and runner
infra/        Docker Compose, Render blueprint
prompts/      Master prompt used for the build
docs/         Architecture, sources, deployment, build log
scripts/      Local development helpers
```

Root tooling: pnpm workspaces + Turborepo, Makefile, Ruff, Pyright, ESLint, Vitest, pytest, Playwright.

---

## 3. Data model (core)

| Table | Purpose |
|---|---|
| `companies` | Demo exporter and report header |
| `users` | Provisioned workspace identities; local source of truth for role/name/active status |
| `suppliers` | Tier, country, category, ownership, risk notes |
| `sources` | Regulatory/sanctions/news streams and sync health |
| `signals` | Normalized source events with raw text, URL, jurisdiction, severity |
| `obligations` | Extracted obligations with citation quote, section, effective date |
| `risks` | Scored exposure linked to company, supplier, and obligation |
| `risk_evidence` | Verbatim quote, citation URL, confidence, support label |
| `remediation_actions` | Proposed owner, due date, priority, status, automation flag |
| `approvals` | Human decision requests with assigned approver and rationale |
| `audit_events` | Append-only events with previous hash and event hash |
| `evidence_chunks` | Retrieval units with embedding and section path |
| `report_runs` | Generated audit-pack metadata, backend, checksum, size, and optional inline bytes |
| `agent_runs` | Pipeline run status, counts, errors, trace ID |
| `eval_runs` / `eval_cases` | Golden-set results and metric gates |

The Alembic baseline enables `vector` and creates an HNSW index for evidence embeddings.

---

## 4. Data streams

Primary demo streams:

1. **Bangladesh Bank** — foreign-exchange and export-proceeds circulars. Fixture-backed.
2. **EU regulatory** — CSDDD / due-diligence signals. Fixture-backed.
3. **UFLPA / DHS** — forced-labour entity and traceability signals. Fixture-backed.
4. **GDELT** — global operational news for corroboration and supplier events. Live connector; rate-limited, hybrid fallback.
5. **US Federal Register** — trade and supply-chain rules. Live connector.

Each source has a `stream_key`, `connector_key`, jurisdiction, status, last sync, `last_sync_mode`, `last_signal_count`, and a sanitized `last_error`. The seed includes 13 signals across the five streams. The in-process APScheduler job runs the live-capable sources when `ENABLE_SCHEDULER=true`; it is running on Render. n8n remains optional. `DATA_MODE=fixture|hybrid|live` is implemented; a failed hard live run is surfaced as `live_failed`, not a fake healthy sync.

See [`DATA_SOURCES.md`](DATA_SOURCES.md).

---

## 5. Agent pipeline

LangGraph state machine (`apps/api/app/agents/pipeline.py`):

1. **Ingest** — load recent signals, optionally filtered by source IDs, skipping signals that already have obligations.
2. **Extract** — produce an `ExtractedObligation` with a citation quote and URL. Live mode calls Gemini Flash via LiteLLM; failures fall back to the deterministic extractor.
3. **Map** — map the obligation to a supplier/company risk with category, severity, likelihood, exposure, and evidence.
4. **Score** — compute the deterministic weighted score outside the LLM.
5. **Remediate** — draft two or more actions with owner role, priority, due date, and automation flag.
6. **Verify** — deterministic verifier checks quote grounding, citation URL, prohibited legal-advice language, prompt-injection markers, and evidence presence. Live mode can add a verifier model pass; deterministic checks still gate the result.
7. **Repair (conditional)** — if any risk is unresolved and the attempt budget allows, re-retrieve a verbatim quote and citation from the signal/chunks, then re-verify. The loop is bounded to one cycle by default (`PIPELINE_MAX_REPAIR_ATTEMPTS=1`) and never changes severity or invents evidence. Unresolved risks are persisted as `needs_review`.
8. **Persist** — write obligation, risk, evidence, actions, agent run, and audit event in a nested transaction per risk.

Pipeline runs are also exposed as `POST /api/v1/pipeline/run` and recorded in `agent_runs`. The run output stores `repair_attempts`, routing events, and per-risk verification status; risk `extra` stores the repair attempts that touched it.

### Model roles

| Purpose | Model | Fallback |
|---|---|---|
| Extraction | Gemini 3.5 Flash | Groq `gpt-oss-120b`, then optional Ollama |
| Classification/rationale | Groq `gpt-oss-120b` | Gemini 3.5 Flash, then optional Ollama |
| Verification (live) | Gemini 3.5 Flash (Pro slot) | Gemini 3.5 Flash, Groq, optional Ollama |
| Local-first | Ollama (`OLLAMA_MODEL`, default `qwen2.5:7b`) | Configured cloud providers, unless `LLM_LOCAL_ONLY=true` |
| Offline/demo | Deterministic mock | — |
| Embeddings | BGE-M3 (optional) | Hash-based mock |

`LLM_MODE=mock` is the default for a reproducible local demo. `LLM_MODE=hybrid` tries a live provider and falls back deterministically; local hybrid runs succeeded with Gemini 3.5 Flash and Groq. `LLM_PREFER_LOCAL=true` routes every purpose to Ollama first but keeps configured cloud providers as fallback; `LLM_LOCAL_ONLY=true` excludes cloud providers and requires `OLLAMA_ENABLED=true`. A local smoke run with cached `qwen2.5:3b` completed with 0 errors, `repair_attempts=1`, and verification `needs_review`; the default 7B model was not pulled, so no quality claim is made. A 90-second per-provider cooldown limits repeated timeouts. The hosted service reports `llm_mode=hybrid` and `llm_live_ready=true`; a hosted `mode=live` pipeline run on 2026-10-27 produced a model-generated rationale with confidence `0.96`, 0 errors, and 1 verified risk. Deterministic fallback remains available when a provider fails, and provider keys are never committed.

---

## 6. Scoring and prioritization

```
raw = severity_value × 0.40
    + likelihood_value × 0.35
    + exposure_value × 0.25

score = (raw / 4) × 100
```

Values are 1–4. Priority bands:

| Priority | Score |
|---|---|
| Critical | ≥ 80 |
| High | ≥ 60 |
| Medium | ≥ 35 |
| Low | < 35 |

The score breakdown is stored on the risk and shown in the UI, so the LLM cannot silently change the ranking. The LLM writes rationale, not the score.

---

## 7. Retrieval and evidence

- `evidence_chunks` stores source text with section paths, citation labels, and URLs.
- The chunker starts new chunks at recognized legal headings (`Article`, `Section`, `Chapter`, `Part`, `Annex`, `Schedule`, `Rule`, `Title`, `§`), prefixes document/jurisdiction/section, and marks metadata `chunking=structure-aware`. Long sections are sentence-split with overlap, so a chunk can still split within one article; this is not semantic chunking.
- Retrieval combines pgvector cosine similarity with Postgres full-text search, then fuses results.
- `/api/v1/search` returns cited chunks, not generated answers.
- Risk detail links each evidence quote back to its signal and source.
- The UI exposes a "show full chunk" control and suggested queries.

Optional production embeddings use BGE-M3; the seed path uses deterministic mock vectors so the demo works without a GPU.

---

## 8. Human-in-the-loop

- Four roles: **admin**, **analyst**, **approver**, **viewer**.
- Analysts/admins can run the pipeline, create risks/actions, sync sources, and generate reports.
- Approvers/admins can record an approval or rejection with a mandatory rationale (≥ 12 characters).
- Viewers have read access and see lock indicators.
- Approval decisions are single-step for the demo, written to the audit trail with actor, timestamp, and rationale.
- Navigation remains visible but role-gated actions are disabled with an explanation; admin-only pages show an access-denied panel and a role-switch helper.

---

## 9. Audit integrity

`audit_events` is append-only by convention and API design:

- Each event stores `previous_hash` and `event_hash`.
- `event_hash = SHA-256(canonical payload + previous_hash)`.
- `GET /api/v1/audit/verify` recomputes the chain and returns validity, event count, and head hash.
- The audit page exposes integrity cards and expandable event payloads.

The chain detects edits or deletions within the application path; production would additionally restrict database roles and ship the head hash to external storage.

### Risk lineage

`GET /api/v1/risks/{id}/lineage` reconstructs the record’s provenance from the
source through the signal, obligation, risk, evidence, actions, and approvals to
generated reports and audit events. The pipeline persists its `trace_id` in
`risks.metadata`; seeded demo risks use the fixture agent-run trace. The risk
detail page renders the chain, trace ID, linked reports, and recent audit events.
Reports are matched by the `risk_ids` list stored in `report_runs.summary`.
Audit events are matched by entity ID and by `risk_id` in the event payload; the
pipeline-run event is matched by trace ID.

The view is a read-model over existing tables. It does not add OpenTelemetry,
OpenLineage, Phoenix, or a cost/latency dashboard, and those are not claimed.

---

## 10. Reports

Three formats share one data snapshot:

- **PDF** — ReportLab, board-ready audit pack with methodology and limitations.
- **JSON** — machine-readable evidence and action records.
- **Markdown** — review-friendly text for tickets or email.

Report bytes are rendered in memory, hashed with SHA-256, and stored by the
selected backend:

- `local` — `REPORT_STORAGE_DIR` (offline demo; `/tmp/reports` on Render Free).
- `database` — `report_runs.content` in Postgres; durable without object storage.
- `supabase` — private Supabase Storage bucket; falls back to Postgres if the
  bucket/upload is unavailable.

Downloads always go through the authenticated API, with ETag, checksum, and
`Cache-Control: private, no-store`. Supabase Storage buckets are not public.

---

## 11. Frontend

- Next.js App Router with route groups `(auth)` and `(app)`.
- Typed API wrapper over generated OpenAPI schema types.
- TanStack Query for server state; Zustand for persisted session/identity and hydration.
- The login page asks `GET /api/v1/auth/config` and renders either demo role cards or an email/password form. Demo controls are hidden for managed accounts.
- React Hook Form + Zod for approvals, actions, and search.
- Cookie-based locale (`NEXT_LOCALE`) with English and Bengali UI chrome.
- Recharts for posture/trend; React Flow for the supply-chain graph.
- Dark, dense operations-console visual language; Inter + Space Grotesk.

Role switching is a demo control: it reloads the app and issues a new demo token, so API authorization is exercised rather than simulated in the client. It is only shown for `is_demo` users. The `/settings` page shows profile, runtime modes, storage backend, and session controls.

---

## 12. API surface

Base: `/api/v1`

- `GET /healthz` (root), `GET /` (product metadata)
- `GET /auth/config`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/demo-login`, `GET /auth/demo-users`, `GET /auth/me`, `GET /auth/roles`
- `GET /dashboard/summary`
- `GET /signals`, `GET /signals/{id}`
- `GET/POST /risks`, `GET /risks/{id}`, `GET /risks/{id}/lineage`, `GET/POST /risks/{id}/actions`, `GET /risks/{id}/approvals`
- `GET /actions/{id}`, `PATCH /actions/{id}`
- `GET /approvals`, `GET /approvals/pending-count`, `POST /approvals/{id}/decision`
- `GET /audit`, `GET /audit/verify`
- `GET /sources`, `POST /sources/{id}/sync`
- `GET /search`
- `GET /graph`
- `GET /suppliers`
- `POST /pipeline/run`, `GET /pipeline/runs`
- `GET /reports`, `POST /reports`, `GET /reports/{id}`, `GET /reports/{id}/download`, `GET /reports/{id}/file`
- `GET /evals/summary`, `POST /evals/run`
- `GET /meta`

OpenAPI JSON: `/openapi.json`. The web app’s schema types are generated from it.

### MCP server

`apps/api/app/mcp/server.py` exposes six read-only tools, one prompt, and one resource over stdio (default) or Streamable HTTP/SSE (`--transport http` or `sse`). HTTP/SSE fail closed: `CHOWKIDAR_MCP_HTTP_TOKEN` is required, and `--allow-unauthenticated` is restricted to a loopback host. `make mcp-http` refuses to start without a token; `make mcp-tunnel` documents an optional Cloudflare quick tunnel that is not used for the hosted demo. The MCP server is not in the pipeline path and cannot approve or mutate anything.

---

## 13. Security and privacy

- **Dev mode:** demo JWT bearer tokens signed with `DEV_JWT_SECRET`; demo endpoints only work when `AUTH_MODE=dev` and `DEMO_MODE=true`.
- **Supabase mode:** the API proxies password/refresh/logout to Supabase Auth, verifies access tokens against the project JWKS, and maps the verified identity to the local `users` table. The local table is authoritative for role/name/active status; Supabase `app_metadata.role` is not trusted.
- Role checks in API dependencies, not only in the UI.
- CORS restricted by `CORS_ORIGINS`.
- Sliding-window rate limits on auth and mutating endpoints; process-local for the single Render instance.
- Report downloads are authenticated and never expose storage paths or public bucket URLs.
- PII redaction (email, phone, NID, passport) before LLM and verifier processing; raw source text remains stored for evidence. IBAN is **not** in the current pattern set.
- Prompt-injection markers detected and treated as review findings.
- Prohibited legal-advice phrases block verification.
- Sentry hooks for API errors; PostHog is anonymized and optional.
- Secrets live in `.env` locally and platform env vars in deployment; `.env` is gitignored.

---

## 14. Evaluation

The `/evals` page reports five gates over a 13-case golden set (`golden-set-v2`):

1. Extraction accuracy
2. Citation coverage
3. Verifier pass rate
4. No-legal-advice rate
5. Priority agreement

Current mock-path result: **13/13 cases**, all metrics **1.0**. The golden set and expected keywords were authored together, so this demonstrates pipeline-contract compliance and citation grounding across every seeded signal, not generalization to unseen regulations. Live Gemini/Groq routes have been smoke-tested but are not benchmarked here.

---

## 15. Deployment topology

| Layer | Target | Status |
|---|---|---|
| Web | Netlify Free, package directory `apps/web` | Live production pilot; primary origin |
| Web fallback | Vercel Hobby, `apps/web` root | Live secondary; DNS variability caveat on some networks |
| Web fallback 2 | Render Node free, Next.js standalone | Optional; currently `502`, check logs |
| API | Render Docker free, Singapore; `STORAGE_BACKEND=database` | Live: `/healthz` healthy, `auth_mode=supabase`, `demo_mode=false` |
| Database | Supabase Postgres + pgvector, Tokyo | Live: migrated and seeded |
| Auth | Supabase Auth proxy | Live: email/password, JWKS verification, four provisioned accounts, demo login disabled |
| Report storage | Postgres (default hosted) or Supabase Storage | Live on Postgres; checksum-verified across a Render redeploy; Storage optional |
| Graph | Neo4j Aura | Optional; pending account |
| Scheduling | In-process APScheduler (`ENABLE_SCHEDULER=true`) | Deployed and verified at `d1f285f50e67`; first cycle GDELT `09:29:36Z` (`fixture_fallback`) and Federal Register `09:30:00Z` (`live`), next run `10:29:36Z` |
| Monitoring | Sentry + PostHog | Optional keys pending |

See [`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md) for URLs and verification details.

See [`DEPLOYMENT.md`](DEPLOYMENT.md).

---

## 16. Known trade-offs

- The public deployment uses Supabase Auth, not demo auth. The local demo adapter remains for offline reproducibility and is selected only with `AUTH_MODE=dev` + `DEMO_MODE=true`.
- Browser tokens are stored in local storage; a hardened deployment should use HttpOnly cookies.
- Rate limiting is process-local, suitable for one Render instance.
- Mock mode prioritizes deterministic storytelling over live model variability. Hybrid mode is available but remains non-deterministic; the deterministic verifier and human approval still gate output.
- Live connectors are limited to GDELT and the US Federal Register; the other three streams are fixture-backed. GDELT's public rate limit can force a labelled fallback.
- Local Ollama routing is implemented and was smoke-tested with `qwen2.5:3b` only; the default 7B model, hosted local inference, and model-quality/latency claims remain out of scope.
- MCP HTTP/SSE is opt-in and fail-closed; no external MCP server is integrated, and the Cloudflare tunnel target has not been executed for the submission.
- Chunking starts at recognized legal headings but is not semantic; long sections can still split mid-article.
- The repair loop is bounded and deterministic; it does not guarantee that every risk becomes `verified`.
- The graph has a compact fixed layout for 30 nodes; very large supply chains need clustering.
- Reports default to Postgres on hosted deployments; Supabase Storage is an optional adapter.
- The golden set is small and hand-built.
- No legal/compliance advisor was available; conservative language and human approval are the mitigation, not a substitute for counsel.
