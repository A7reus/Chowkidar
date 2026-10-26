# Chowkidar — P0/P1 Gap Analysis and Remediation Tracker

**Last updated:** 2026-10-26  
**Owner:** JU_StackMind  
**Purpose:** Durable record of every material shortcoming found in the 2026-10-26 evaluation, the evidence for it, and the work required to close or honestly disclose it. This file is the recovery point if the conversation context is lost.

**Authority order for current-state claims:**

1. `docs/LIMITATIONS.md` — the honest capability boundary.
2. `docs/GAP_ANALYSIS.md` — this tracker, including implementation status.
3. `docs/CLOUD_DEPLOYMENT_STATUS.md` and `docs/PRODUCTION.md` — verified hosted state.
4. `docs/SUBMISSION.md` — form-ready wording.
5. Planning documents (`STRATEGY.md`, `BUILD_PLAN.md`, `PRODUCT_SPEC.md`, `DECISIONS.md`) — historical intent, not proof of implementation.

**Rules**

- Do not mark a P0/P1 item complete unless the code, tests, and documentation agree.
- Do not check a form box for an unverified capability.
- Keep secrets out of this file and out of git.
- Update the status table and session log after every material change.
- Re-read this file, `docs/LIMITATIONS.md`, `DECISIONS.md`, and `docs/SUBMISSION.md` after any context reset.

**Status legend**

| Status | Meaning |
|---|---|
| `open` | Not started, or only documented as a gap |
| `in_progress` | Code or documentation work underway |
| `implemented` | Code exists and is covered by tests; deployment/config may still be pending |
| `verified` | Implemented, tested, and verified in the target environment |
| `blocked` | Requires user input, credentials, a third-party asset, or a decision |
| `accepted` | Deliberately not done for the preliminary; must be disclosed |

---

## 1. P0 — challenge-critical and credibility-critical

| ID | Shortcoming | Evidence (2026-10-26) | Scoring / risk impact | Required outcome | Status |
|---|---|---|---|---|---|
| **P0-1** | No autonomous live monitoring; source sync replays fixtures | Originally `DATA_MODE=fixture`; `sources.py` loaded only `data/fixtures/demo.json`; no scheduler. **Now:** live GDELT + US Federal Register connectors, `fixture|live|hybrid` data modes, dedupe by `(source_id, external_id)`, APScheduler job, and honest `last_sync_mode` labels | Fails the challenge's first specific ask; weakens Story, AI-Native Build, Data Lifecycle, Innovation, and Impact | Implement at least two real live connectors (GDELT + Federal Register), persist signals with dedupe, expose live/fallback mode, and schedule ingestion. Fixture mode must remain available and clearly labeled. | `verified` for live connectors — hosted Federal Register `mode=live` (8 signals, second run 0), GDELT `fixture_fallback`; scheduler fix deployed at `94c2a19f91c4` and job armed, first cycle pending. Render Free spin-down also pauses the in-process scheduler; production needs an always-on instance or external scheduler |
| **P0-2** | Hosted AI is deterministic mock mode; no real model inference | Originally `/healthz` reported `llm_mode=mock`; no hosted Gemini/Groq call. **Now:** `LLM_MODE=mock|live|hybrid`, LiteLLM calls with deterministic fallback, provider cooldown, sanitized errors, and `llm_live_ready` in health/meta. Hosted env is `LLM_MODE=hybrid` but `llm_live_ready=false` because no provider keys are set on Render; working Gemini/Groq keys exist only in the gitignored local `.env` and were probed successfully | Judges may see a rules engine, not AI; weakens AI-Native and agent scores | Add a truthful `hybrid` LLM mode: try Gemini/Groq through LiteLLM, fall back to deterministic mock, and expose `llm_live_ready` in health/meta. Enable on the hosted service only when keys are present. | `implemented` — local hybrid verified; hosted keys missing, so hosted inference is still deterministic fallback |
| **P0-3** | "Agentic" is a fixed linear DAG | Originally `_build_graph()` had fixed edges only. **Now:** conditional `verify → repair|persist`, one bounded repair cycle, verbatim-quote re-retrieval, routing metadata, and `repair_attempts` persisted on the run and risk | Undercuts the central agentic claim and the agent/orchestration form field | Add conditional routing and a bounded repair loop: verifier failure triggers evidence re-retrieval and one re-verification; unresolved risks are marked `needs_review`. Persist routing/attempt metadata. | `implemented` — local repair smoke + tests; hosted pipeline run completed (8 verified risks, no repair triggered) |
| **P0-4** | No commercial validation | `STRATEGY.md` validation plan was future tense; no interviews, LOIs, design partners, revenue, or pricing tests in the repo | Business Value 20%; Story/Proof credibility | Create a validation kit and evidence log. Execute interviews/LOIs only if real evidence can be collected; never invent traction. If not executed, disclose `0 interviews` in the form. | `implemented` — kit created; evidence log is honestly `0 interviews` |
| **P0-5** | Submission data gaps | No Figma/design link; team size, NRB status, and female-member status unknown; video not produced (out of scope per instruction) | Up to 19 form points at risk; presentation criterion | Create a public design artifact (architecture + wireframes) usable as the design link; add a team-data checklist with blanks; assign video owner. Do not invent team data. | `implemented` — `docs/DESIGN.md` public link verified `200`; team fields intentionally blank and video placeholder per user decision; form packet prepared |

### P0 acceptance criteria

- **P0-1:** `POST /api/v1/sources/{id}/sync` for `gdelt` and `us_federal_register` makes a real HTTP request, inserts new signals with citations, deduplicates by `(source_id, external_id)`, records `last_sync_mode=live`, and returns `mode=live`. A failure sets `status=error` (or `degraded` in hybrid fallback) and never reports a fake healthy live sync. A scheduler can run the same path without an HTTP request.
- **P0-2:** `LLM_MODE=hybrid` attempts a real LiteLLM call when keys are present; on failure it records the fallback and continues deterministically. `/healthz` exposes `llm_mode` and `llm_live_ready`. No secret is logged.
- **P0-3:** The graph contains at least one conditional edge and one bounded repair cycle. A failed verification can be repaired once from retrieved evidence, then either verifies or is persisted as `needs_review`. Tests cover the route decision and attempt cap.
- **P0-4:** `docs/VALIDATION.md` contains the interview guide, LOI template, pricing hypotheses, and an evidence log that states exactly what has and has not been done.
- **P0-5:** `docs/DESIGN.md` and a public design artifact exist; `docs/SUBMISSION.md` has a team-data checklist with unknown values clearly marked, not guessed.

### Implementation evidence (2026-10-26)

- **P0-1 — live connectors and scheduler**
  - `apps/api/app/connectors/` contains `gdelt.py`, `federal_register.py`, `base.py`, and a registry. Both connectors are key-free and normalize into the shared `ConnectorSignal` contract.
  - `apps/api/app/services/sources.py` supports `fixture`, `live`, and `hybrid`; it dedupes on `(source_id, external_id)`, stores evidence chunks, matches suppliers only on exact name mentions, and writes `last_sync_mode`, `last_signal_count`, and `last_error`.
  - `apps/api/app/services/scheduler.py` runs the same service path through APScheduler when `ENABLE_SCHEDULER=true`; `main.py` starts and stops it in the lifespan.
  - `POST /api/v1/sources/{id}/sync` persists failed-run state and audit evidence before returning `502` for a hard live failure.
  - Migration `9c1e4f2a7b10_live_connectors.py` applied; `make migrate` and `make seed` passed with 5 sources, 13 signals, 11 obligations, 8 risks, 21 actions, 5 approvals, 12 audit events, and 13 evidence chunks.
  - **Federal Register live evidence:** `mode=live`, 8 signals created, source `healthy`; a second run returned `mode=live` and `0` new signals because of dedupe.
  - **GDELT fallback evidence:** the public API returned `429` and rate-limit HTML despite the connector's five-second retry. Hybrid sync returned `mode=fixture_fallback`, source `degraded`, `0` new signals, and a sanitized `last_error`. It never reported a fake healthy live sync.
  - **Hosted status (verified):** Render reports `data_mode=hybrid`, `live_connectors_enabled=true`, `scheduler_enabled=true`, and `scheduler_running=true`. The live connector evidence was captured at revision `8caca3eef555`. Revision `94c2a19f91c4` exposes `scheduler_next_run_at=2026-10-26T09:17:40Z` in `/healthz` and `/api/v1/meta`, confirming the job is armed; docs-only pushes may advance the reported revision without changing runtime behavior. A hosted Federal Register sync returned `mode=live` with 8 signals and source `healthy`; a second sync returned `mode=live` with 0 signals because of dedupe. A hosted GDELT sync returned `mode=fixture_fallback`, source `degraded`, and the sanitized rate-limit error. No scheduled cycle has been observed yet. The scheduler initially reported `scheduler_running=true`, but inspection showed no source had synced since the manual run. Root cause: `next_run_time=None` was passed explicitly when `SCHEDULER_RUN_ON_START=false`, which left the APScheduler job paused. The code now omits that option so the interval trigger arms normally; `scheduler_next_run_at` is exposed in `/healthz` and `/api/v1/meta`; `apps/api/tests/test_scheduler.py` covers both `run_on_start` branches. The fix is deployed and armed; the first observed cycle remains pending.

- **P0-2 — hybrid LLM path**
  - `apps/api/app/agents/llm.py` accepts `mock|live|hybrid`, routes by model prefix, adds a 90-second per-provider cooldown after failures, and stores only sanitized provider error types.
  - Default model slots now use `gemini/gemini-3.5-flash`; `gemini-3.8-flash` timed out locally and `gemini-pro-latest` had zero free-tier quota. Groq `openai/gpt-oss-120b` remains the fallback.
  - `/healthz` exposes `llm_live_ready`; `/api/v1/meta` lists five streams with connector/mode and exposes live-connector and scheduler readiness.
  - **Local hybrid evidence:** a live pipeline run completed in 18.4 seconds with 2 signals, 2 obligations, 2 risks, 4 actions, and no errors. Gemini/Groq calls succeeded; one risk verified and one persisted as `needs_review`.
  - **Hosted status:** Render now reports `llm_mode=hybrid`, but `llm_live_ready=false` because `GEMINI_API_KEY` and `GROQ_API_KEY` are absent. Hosted pipeline inference therefore still uses the deterministic fallback. Do not claim live hosted inference until `/healthz` shows `llm_live_ready=true`.

- **P0-3 — bounded repair loop**
  - `route_after_verify()` sends unresolved risks to one repair cycle, then persists; `pipeline_max_repair_attempts` bounds the cycle.
  - `repair_evidence()` re-retrieves a verbatim quote from the signal/chunks, restores a valid citation URL, and never changes severity or invents facts. Unresolved evidence remains `needs_review`.
  - Routing and `repair_attempts` are persisted in `AgentRun.output` and risk `extra`.
  - **Smoke evidence:** routing showed `verify attempt 0` → `repair attempt 1` (`chunks_retrieved=1`, replaced a non-verbatim quote) → `verify attempt 1`; one risk still remained `needs_review` because the repaired quote did not satisfy the verifier.
  - **Hosted evidence:** a hosted pipeline run over 8 Federal Register signals created 8 obligations, 8 risks, and 16 actions with 0 errors; all 8 risks verified on `verify attempt 0`, and `repair_attempts=0`. The deployed conditional route exists and is exercised by tests and the local smoke, but this hosted run did not need a repair.
  - **Tests:** `apps/api/tests/test_connectors.py` and `apps/api/tests/test_pipeline_routing.py` cover connector normalization/dedupe/failure wrapping and the repair route/attempt cap/verbatim repair.

- **P0-4 — validation kit**
  - `docs/VALIDATION.md` contains the interview guide, LOI template, pricing hypotheses, and an evidence log.
  - **Honest status:** `0` interviews, `0` LOIs, `0` design partners, `0` revenue. No traction may be claimed.

- **P0-5 — design artifact**
  - `docs/DESIGN.md` contains the design principles, information architecture, user flows, screen wireframes, design tokens, component inventory, accessibility notes, and the evidence/approval interaction model.
  - The public link is the GitHub-rendered file: `https://github.com/A7reus/Chowkidar/blob/main/docs/DESIGN.md` (verified `200` on 2026-10-26). No Figma account was created; this document is the design artifact substitute.
  - Team size, member names, team lead, NRB status, and female-member status are intentionally left blank by the user's 2026-10-26 decision; no diversity bonus is claimed. The video remains a placeholder and no recording is claimed.

---

## 2. P1 — high-impact capability and documentation gaps

| ID | Gap | Evidence (2026-10-26) | Impact | Required outcome | Status |
|---|---|---|---|---|---|
| **P1-1** | RAG depth is overstated | `apps/api/app/rag/chunking.py` prefixes document/jurisdiction/section metadata; `SentenceSplitter` is not semantic chunking; `apps/api/app/rag/embeddings.py` uses hash embeddings in mock mode; no late interaction; no graph RAG; BGE-M3/reranker optional; Neo4j not wired | RAG rows/bonus; technical credibility | Run BGE-M3 + cross-encoder if feasible; add semantic chunking; otherwise claim only context-enriched chunking + pgvector/FTS hybrid with RRF and lexical reranking. | `open` |
| **P1-2** | MCP is built but not used in the product path | `apps/api/app/mcp/server.py` exposes one read-only FastMCP stdio server with six tools, one prompt, one resource; no external MCP server; no SSE; pipeline does not call MCP | MCP category 20+ | Integrate one external MCP server (fetch/Postgres) into an agent step, or disclose only "built" and "stdio architecture." | `open` |
| **P1-3** | n8n workflow is inactive and inconsistent | `infra/n8n/workflows/stream-sync.json` is `active: false`; calls `/sources/bd_bank/sync` but route expects UUID; sends `X-Internal-Key` but route requires analyst JWT; fixture replay anyway. **Now:** the in-process APScheduler is the supported ingestion path; n8n remains an optional scaffold | Automation bonus; Data Lifecycle | Fix route/auth or replace with the in-process scheduler; activate and run once, or remove active claims. | `accepted` — replaced by the scheduler; n8n is not claimed as active |
| **P1-4** | Ollama/local models not run | Compose service exists; no model pulled or executed; no local inference evidence | Up to 13 checklist points | Run a small model locally, execute one extraction, capture logs; or leave as honest zero. | `open` |
| **P1-5** | Evals are weak and internally inconsistent | 7 synthetic cases, all metrics `1.0`, same deterministic path; no adversarial/held-out set; `docs/EVALS.md` and `docs/ARCHITECTURE.md` list different five-gate sets; duplicate remediation call in `services/evals.py` | Evals field; technical trust | Add 10–20 edge/adversarial cases, report failures, remove duplicate call, reconcile gate names to code. | `open` |
| **P1-6** | No real observability or lineage | `agent_runs.trace_id`, audit log, `last_synced_at` only; no OpenLineage/Phoenix/Sentry/PostHog; no cost/latency dashboard; no end-to-end lineage view | Lineage field; Data Lifecycle | Add a lineage view/table (source → signal → obligation → risk → action → report) and structured logs with trace IDs. | `open` |
| **P1-7** | PII/responsible-AI doc/code mismatch | `core/security.py` redacts email, phone, NID, passport; docs claimed IBAN; no Presidio/Llama Guard; browser tokens in local storage; no MFA/RLS/DPA/retention policy. **Now:** IBAN claim removed; docs state the boundary | Privacy/guardrails; Responsible AI 20% | Add IBAN pattern or remove claim; add retention/data-flow/DPA notes; document local-storage risk; do not claim Presidio/Llama Guard. | `implemented` — claim removed; broader privacy gaps disclosed |
| **P1-8** | Admin and multi-tenancy gaps | Script-based provisioning; no invite/role-change UI; single workspace; no billing | Business/scalability; product completeness | Disclose as single-workspace pilot; add admin UI only if time; never claim SaaS readiness. | `accepted` for preliminary |
| **P1-9** | Data quality and licensing | Fixture data for three streams; dedupe by `external_id` now implemented; no freshness SLO or source license/ToS review. **Now:** source licensing disclosure and freshness expectations added to `docs/DATA_SOURCES.md` | Data Lifecycle 25 | Add validation/dedupe/freshness metrics and a source license table; document fixture provenance. | `implemented` — dedupe, license disclosure, and freshness expectations documented; no enforced SLO or formal terms review |
| **P1-10** | Checklist gaps | No listed frontend AI tool, no listed AI-DLC framework, no fine-tuning, no tunneling | AI stack points | Honest zeros. Optional truthful quick wins: Cloudflare Tunnel for local demo, OpenCode in an "other" field if available. Do not check unimplemented boxes. | `accepted` for preliminary |

---

## 3. Documentation and claim reconciliation

| File / claim | Problem | Required action | Status |
|---|---|---|---|
| `STRATEGY.md` | "Status: Decision draft — no product code yet"; aspirational graph RAG, n8n, Ollama, 3 MCP servers, Cloudflare Tunnel, RAGAS/DeepEval/Presidio/Llama Guard | Add "historical strategy, superseded by LIMITATIONS" banner; mark unbuilt items as future | `resolved` — banner added; unbuilt items named |
| `BUILD_PLAN.md` | Draft plan with unbuilt admin invite, local Ollama path, graph RAG, MCP clients | Add status banner and link to `LIMITATIONS.md` | `resolved` — banner added |
| `PRODUCT_SPEC.md` | F12 admin invite/role change, F16 local model path, graph RAG described as current | Mark as planned/not implemented | `resolved` — banner added; unimplemented features named |
| `DECISIONS.md` | Status said cutover blocked on Supabase Auth keys; stack table implied Neo4j/n8n/Ollama active | Update to production-pilot status; mark optional components not wired | `resolved` — status, stack table, and session log updated |
| `docs/API.md` | Called hosted service a "demo"; source sync described as fixture-only | Rename to production pilot (single workspace) and note data/LLM modes | `resolved` — base URL, health/meta/sync notes, and `502` behavior updated |
| `README.md` | "monitors" without fixture qualifier; Compose line implied Neo4j/Ollama/n8n active | Qualify live vs fixture; clarify optional services | `resolved` — implemented table and limitations updated |
| `docs/RESPONSIBLE_AI.md`, `docs/ARCHITECTURE.md` | Claimed IBAN redaction not present in code | Add IBAN pattern or remove claim | `resolved` — claim removed; code boundary stated |
| `docs/EVALS.md` vs `docs/ARCHITECTURE.md` | Different five-gate names | Reconcile to the code and one list | `resolved` — both now use extraction accuracy, citation coverage, verifier pass rate, no-legal-advice rate, priority agreement |
| `docs/SUBMISSION.md` | One-liner said "monitors" while limitations say fixture | Qualify the one-liner immediately | `resolved` — current data reality added immediately below the one-liner |

### Form-safe wording

Use these until the corresponding capability is verified:

- **Monitoring:** "Five labelled streams: Bangladesh Bank, EUR-Lex, and UFLPA are fixture-backed; GDELT and the US Federal Register have real live connectors with dedupe and an in-process scheduler. Hybrid mode falls back to fixtures and labels the run `fixture_fallback`; a failed live run is never reported as healthy."
- **Agentic:** "LangGraph-orchestrated seven-stage risk pipeline with conditional evidence repair, human-in-the-loop approval, and deterministic fallback."
- **RAG:** "Context-enriched chunking + pgvector/Postgres FTS hybrid retrieval with reciprocal rank fusion and lexical reranking."
- **MCP:** "Built a read-only FastMCP stdio server exposing six tools; external MCP integration is not in the product path."
- **Deployment:** "Single-workspace production pilot with Supabase auth, RBAC, audit trail, and durable reports; not multi-tenant SaaS. GDELT and US Federal Register live ingestion, hybrid modes, and scheduled ingestion are deployed; Federal Register live sync is hosted-verified. Hosted LLM inference is not enabled (`llm_live_ready=false`), so the hosted pipeline uses deterministic fallback until provider keys are added."
- **Evals:** "Seven synthetic golden cases, all five gates pass; demo-scale, not a legal benchmark."

---

## 4. Do-not-claim list

Do not claim any of the following unless the status changes to `verified` with evidence:

- Autonomous monitoring of live streams beyond the connectors actually enabled.
- Real LLM inference on the hosted service when `llm_live_ready=false`.
- Multi-agent autonomy, planning, memory, or agent-to-agent delegation.
- Semantic chunking, late interaction, Anthropic-style contextual RAG, or graph RAG.
- Neo4j or a graph database in the product path.
- External MCP servers used in the product path.
- Active n8n automation.
- Local Ollama models run in the demo.
- Fine-tuning, LoRA, or a training-data pipeline.
- Customer discovery, LOIs, pilots, revenue, or pricing validation.
- Multi-tenancy, SSO, billing, SOC 2, MFA, RLS, DPA, or retention policy.
- Legal advice or legal compliance determinations.

---

## 5. Remediation sequence

| Order | Work | Why | Status |
|---:|---|---|---|
| 1 | Record this gap analysis and update `DECISIONS.md` | Prevent context loss and claim drift | `implemented` |
| 2 | Implement GDELT + Federal Register connectors, source mode fields, scheduler, and tests | Closes P0-1; directly addresses challenge fit | `implemented` |
| 3 | Add `hybrid` LLM mode and live-readiness reporting | Closes P0-2 without making the demo fragile | `implemented` |
| 4 | Add conditional routing + bounded repair loop to the LangGraph pipeline | Closes P0-3 | `implemented` |
| 5 | Add `docs/VALIDATION.md` and `docs/DESIGN.md` + design artifact | Closes P0-4/P0-5 documentation portions | `implemented` |
| 6 | Reconcile current-state docs and update `LIMITATIONS.md` | Prevents judge-visible contradictions | `implemented` |
| 7 | Run tests, local live-connector smoke, and hosted QA | Verify before form | `in_progress` — local checks pass; hosted hybrid env, Federal Register live sync, GDELT fallback, pipeline run, and scheduler arming verified; first scheduled cycle and hosted LLM keys pending |
| 8 | Fill the official form with placeholders and stop before submission | User approved filling with placeholders on 2026-10-26; submission still needs separate explicit approval | `in_progress` — form packet prepared in `docs/SUBMISSION.md` section 10; portal session unavailable |

---

## 6. Verification checklist

Run from the repository root:

```bash
make check                 # ruff, pyright, API tests, web tests
make migrate               # after adding the source columns
make seed                  # local fixture demo
make api                   # local API
make web                   # local web
```

Live connector smoke (local, with Postgres running):

```bash
# Start Postgres only
docker compose -f infra/docker-compose.yml up -d postgres

# Apply the new migration and reseed
make migrate
make seed

# Start the API with live-capable modes for the smoke test
cd apps/api
DATA_MODE=hybrid LLM_MODE=hybrid ENABLE_SCHEDULER=false \
  uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

# In another shell, obtain a demo analyst token and sync the live sources.
# Do not paste real credentials into logs.
```

Expected source response after a Federal Register live sync:

```json
{
  "signals_created": 8,
  "message": "Synced US Federal Register — Trade & supply-chain rules: 8 new live signal(s).",
  "mode": "live",
  "connector": "federal_register"
}
```

A second run should return `signals_created: 0` with `mode: "live"` because of dedupe. A GDELT rate-limit failure in hybrid mode should return `mode: "fixture_fallback"`, `source.status: "degraded"`, and a sanitized `last_error` — never `mode: "live"` with a healthy status.

Expected health after enabling hybrid mode with keys:

```json
{
  "status": "ok",
  "llm_mode": "hybrid",
  "llm_live_ready": true,
  "data_mode": "hybrid",
  "scheduler_enabled": true,
  "scheduler_running": true,
  "scheduler_next_run_at": "2026-10-26T09:10:00+00:00"
}
```

Current hosted state (2026-10-26): `llm_mode=hybrid`, `llm_live_ready=false`, `data_mode=hybrid`, `scheduler_enabled=true`, `scheduler_running=true`, `scheduler_next_run_at=2026-10-26T09:17:40Z`. The hosted pipeline is therefore deterministic until provider keys are added to Render; the form must say so. Working Gemini/Groq keys are present only in the gitignored local `.env` and were probed successfully. The scheduler arming fix is deployed and the job is armed; the first cycle is not yet observed.

---

## 7. Open blockers and user decisions

| Blocker | Why it matters | Owner | Status |
|---|---|---|---|
| Team size, member names, team lead, NRB status, female-member status | Up to 7 Team points; cannot be invented | User | `accepted` — intentionally blank per user decision; no bonus claimed |
| Public design link | `docs/DESIGN.md` is public at the GitHub URL (verified 2026-10-26). A Figma file would need a user account. | User/operator | `resolved` — substitute live |
| Gemini/Groq keys available on Render | Real LLM inference on hosted service; currently `llm_live_ready=false` and the pipeline falls back deterministically. Keys are in the local `.env` and both providers were probed successfully. | User/operator | `blocked` — Render dashboard/API access unavailable |
| Observe one scheduled ingestion cycle | Confirms the APScheduler path fires on Render, not just that it is running | Operator | `pending` — scheduler fix deployed at `94c2a19f91c4` and job armed (`scheduler_next_run_at=2026-10-26T09:17:40Z`); first cycle not yet observed |
| Video owner and recording | Official form requires a YouTube URL; explicitly out of scope for this work | User | `accepted` — placeholder only; no recording claimed |
| Supabase database password rotation | Security hygiene; requires updating Render `DATABASE_URL` | User/operator | `accepted` — zero-real-user pilot; rotate before real users; not a submission blocker |

---

## 8. Session log

| Date | Change | Files | Verification |
|---|---|---|---|
| 2026-10-26 | Recorded the full P0/P1 evaluation, evidence, acceptance criteria, form-safe wording, and blockers | `docs/GAP_ANALYSIS.md` | Documentation review |
| 2026-10-26 | Implemented live connectors, hybrid modes, scheduler, and bounded repair loop; added validation/design artifacts | API, web, fixtures, migration, tests, docs | Local live connector smoke, hybrid pipeline smoke, API 75 tests |
| 2026-10-26 | Reconciled current-state docs and added historical banners to planning documents | `README.md`, `DECISIONS.md`, `STRATEGY.md`, `BUILD_PLAN.md`, `PRODUCT_SPEC.md`, `docs/*` | `make check` clean; fresh-database migration test; `make seed` baseline 5/13/11/8/21/5/12/13 |
| 2026-10-26 | Committed and pushed the P0 implementation and documentation reconciliation; verified the public design link | `main` at `5f224ca` | Design URL `200`; hosted health still on `2bfaed71372c` (`mock`/`fixture`) pending Render deploy |
| 2026-10-26 | Render deployed the new code; verified hosted five-stream UI and new health fields; corrected docs to distinguish deployed code from pending env cutover | `main` at `8caca3e` | Hosted health `revision=5f224ca4e060`, `llm_mode=mock`, `data_mode=fixture`; Netlify pilot login + `/sources` five-stream check passed |
| 2026-10-26 | Render applied the hybrid/scheduler environment; verified hosted Federal Register live sync, dedupe, GDELT fallback, and a full pipeline run; added `scheduler_running` to meta | `main` after `ef6de4a`; `meta.py`, `test_api_contract.py`, docs | Hosted health at `8caca3eef555`: `data_mode=hybrid`, `scheduler_running=true`, `llm_live_ready=false`; FedReg `mode=live` 8→0; GDELT `fixture_fallback`; pipeline 8 signals → 8 risks → 16 actions, 0 errors, all verified |
| 2026-10-26 | Committed and pushed the hosted-state reconciliation and `scheduler_running` meta field; verified the new deploy | `main` at `8710ab2` | Hosted health and `/api/v1/meta` at `8710ab2aedce`: `data_mode=hybrid`, `llm_mode=hybrid`, `llm_live_ready=false`, `scheduler_enabled=true`, `scheduler_running=true`, five streams; `make check` 76 API + 8 web tests |
| 2026-10-26 | Stored user-supplied Gemini/Groq keys only in the gitignored local `.env` (mode `600`) and probed both providers with minimal calls | `.env` (untracked) | Gemini 3.5 Flash OK (~2.1s), Groq `gpt-oss-120b` OK (~0.5s); Render still lacks the keys, so hosted `llm_live_ready=false` |
| 2026-10-26 | Recorded user decisions on team data, Supabase password, video, and form filling; prepared the form-ready packet with placeholders | `DECISIONS.md`, `docs/SUBMISSION.md`, `docs/LIMITATIONS.md`, `README.md` | Team fields intentionally blank; password accepted for zero-real-user pilot; video placeholder; form packet prepared, not submitted |
| 2026-10-26 | Verified current hosted deploy and refreshed current-state docs | `main` after `b423e5b` | Hosted health at `b423e5b3a001`: `status=ok`, `database=ok`, `auth_mode=supabase`, `llm_mode=hybrid`, `llm_live_ready=false`, `data_mode=hybrid`, `scheduler_running=true`; design link `200` |
| 2026-10-26 | Found and fixed the paused APScheduler job: explicit `next_run_time=None` with `SCHEDULER_RUN_ON_START=false` left the job unscheduled | `apps/api/app/services/scheduler.py`, `health.py`, `meta.py`, `schemas.py`, `tests/test_scheduler.py`, `test_api_contract.py` | Local scheduler test proves `next_run_time` is armed for both `run_on_start` branches; `scheduler_next_run_at` added to health/meta; API tests 78 passed |
| 2026-10-26 | Pushed and deployed the scheduler arming fix; verified the hosted job is armed | `main` at `94c2a19`; hosted revision `94c2a19f91c4` | `/healthz` and `/api/v1/meta` both report `scheduler_next_run_at=2026-10-26T09:17:40Z`; `scheduler_running=true`; first cycle pending |

---

## 9. Context recovery protocol

If the conversation is compacted or restarted:

1. Read this file completely.
2. Read `docs/LIMITATIONS.md`, `DECISIONS.md`, and `docs/SUBMISSION.md`.
3. Check `git status` and `git log --oneline -10`.
4. Check `/healthz` and the source rows for `last_sync_mode`.
5. Continue from the first `in_progress` or `open` P0 item; do not re-open completed work without evidence.
6. Update this file before ending the session.
