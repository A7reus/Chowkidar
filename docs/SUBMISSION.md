# Chowkidar — Submission Packet

**Team:** JU_StackMind  
**Event:** International AI Builders Congress 2026  
**Track:** Idea to Unicorn  
**Domain:** JusticeSphere AI  
**Challenge:** Risk Sentinel  
**Deadline:** 2026-10-31, 11:59 PM GMT+6  
**Target submission:** 6:00 PM GMT+6

---

## 1. One-liner

**Chowkidar is an agentic compliance risk sentinel for export supply chains: it monitors regulatory and supplier-risk streams, maps them to obligations, and turns them into evidence-backed remediation that a human approves.**

**Tagline:** *See the risk. Approve the fix.*

**Current data reality:** five labelled streams. GDELT and the US Federal Register
have real live connectors with dedupe and a deployed scheduler; Bangladesh Bank,
EUR-Lex, and UFLPA are fixture-backed. A rate-limited GDELT run is labelled
`fixture_fallback`, never reported as a healthy live sync. Render runs
`DATA_MODE=hybrid`, and Federal Register live sync is hosted-verified. The
scheduler arming fix is deployed at revision `94c2a19f91c4` and
`scheduler_next_run_at` reports `2026-10-26T09:17:40Z`; the first cycle has not
been observed yet, so no completed scheduled cycle is claimed.
`llm_live_ready=false` because provider keys are absent **on Render**, so hosted
pipeline inference still uses the deterministic fallback. Working Gemini and Groq
keys exist only in the gitignored local `.env`; both providers were probed
successfully, and the keys are never committed or shown in the form.

---

## 2. What judges can verify

| Requirement | Where to verify |
|---|---|
| Two or more distinct data streams | `/sources` and `/signals` show Bangladesh Bank, EUR-Lex, UFLPA/DHS, GDELT, and the US Federal Register, with live/fixture/fallback labels |
| Prioritized risk audit | `/dashboard`, `/risks`, and the PDF audit pack |
| Automated remediation | Risk detail shows proposed actions, owners, due dates, priorities |
| Human-in-the-loop approval | `/approvals`; approver/admin decision with rationale |
| Evidence and citations | Risk detail evidence quote + source URL; `/search` cited chunks |
| Auditability | `/audit` hash-chain verification (admin) |
| Quality evaluation | `/evals`, 7/7 golden cases, five metrics |
| Supabase email/password auth | `/login`; `/api/v1/auth/config`; role-gated routes |
| Durable hosted reports | PDF/JSON/Markdown downloads backed by Postgres |
| AI-agent build provenance | [`docs/BUILD_LOG.md`](BUILD_LOG.md), [`prompts/MASTER_PROMPT.md`](../prompts/MASTER_PROMPT.md) |
| Design artifact | [`docs/DESIGN.md`](DESIGN.md) (public GitHub link) |
| Validation kit | [`docs/VALIDATION.md`](VALIDATION.md) — evidence log honestly at 0 interviews |
| Not legal advice | API root, UI, reports, README, methodology resource |

- **Repository URL:** <https://github.com/A7reus/Chowkidar>
- **Live pilot URL:** <https://ch0wkidar.netlify.app/> — Netlify primary, verified with production browser QA: Supabase email/password auth, four managed accounts, demo login disabled, PDF generation/download, and viewer read-only access. Secondary fallback: <https://chowkidar-wheat.vercel.app/> (Vercel DNS may vary on some networks; see [`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md)).
- **API URL:** <https://chowkidar-api.onrender.com/>
- **Hosted access:** Supabase accounts use the emails `admin@chowkidar.app`, `analyst@chowkidar.app`, `approver@chowkidar.app`, and `viewer@chowkidar.app`. Passwords are held in the private, gitignored access note and must be supplied to judges only through the form's private access field or another controlled channel.
- **Production status:** live and verified as a production pilot. Netlify browser QA passed 2/2 at the previously verified revision `2bfaed71372c`: `/healthz` reports `auth_mode=supabase`, `demo_mode=false`, `database=ok`; admin and viewer flows passed; PDF generation/download matched SHA-256; reports use Postgres; viewer role restrictions returned `403`; and both web origins pass CORS preflight. This is a single-workspace pilot, not commercial SaaS readiness. **Render runs the hybrid environment; the hosted health check on 2026-10-26 reported revision `94c2a19f91c4` (`data_mode=hybrid`, `llm_mode=hybrid`, `scheduler_running=true`, `scheduler_next_run_at=2026-10-26T09:17:40Z`); docs-only pushes may advance the reported revision without runtime change. The scheduler job is armed, but the first cycle has not been observed. Federal Register live sync, dedupe, GDELT fallback, and a hosted pipeline run are verified. `llm_live_ready=false` because provider keys are absent on Render; hosted inference still falls back deterministically. Working Gemini/Groq keys are present only in the local `.env`.**
- **Video URL:** `[PLACEHOLDER — not recorded]` — required for the official form; no recording is claimed.

> The official form and MCP knowledge base both reward a public live demo and a 2–3 minute video. A local-only demo is not enough for maximum preliminary score. See [`COMPETITION_CONTEXT.md`](COMPETITION_CONTEXT.md) for the captured form, scoring signals, and the authoritative domain list.

---

## 3. Local judge runbook

```bash
cp .env.example .env
make setup
make services-up
make migrate
make seed
make api    # terminal 1
make web    # terminal 2
```

Open **http://localhost:3000** and choose any demo account.

### Hosted pilot accounts

The hosted login uses Supabase email/password, not the demo cards. The four
accounts follow the pattern `<role>@chowkidar.app`; the passwords are in the
private access note. A managed account cannot switch roles from the UI: role
changes are made by an administrator in the local `users` table. Local demo
accounts remain available for offline judging.

### Local demo accounts

| Role | Name | Email |
|---|---|---|
| Admin | Ayesha Rahman | `admin@chowkidar.demo` |
| Analyst | Rafiq Hasan | `analyst@chowkidar.demo` |
| Approver | Nusrat Jahan | `approver@chowkidar.demo` |
| Viewer | Imran Chowdhury | `viewer@chowkidar.demo` |

The local demo login page uses one-click accounts. Role switching in the app reissues a token and reloads so API authorization is exercised, not just hidden in the client. A production deployment instead shows email/password from `/api/v1/auth/config`.

### Seed baseline

```
1 company · 4 users · 8 suppliers · 5 sources · 13 signals
11 obligations · 8 risks (3 critical, 3 high, 1 medium, 1 low)
21 actions · 5 approvals (4 pending) · 12 audit events · 13 evidence chunks
```

---

## 4. Five-minute demo script

| Time | Screen | Say |
|---|---|---|
| 0:00–0:20 | Login | "Exporters face a moving wall of EU, US, and Bangladesh rules plus supplier risk. Chowkidar watches the streams, finds what applies, and prepares the fix for human approval. It is compliance risk intelligence, not legal advice." |
| 0:20–0:55 | Dashboard | "Padma Apparel is a fictional Gazipur RMG exporter. Thirteen signals produced eight cited risks: three critical, three high. Source health shows five streams, including live GDELT and Federal Register connectors with mode labels. The agent run explains what it ingested and produced, including any bounded repair." |
| 0:55–1:35 | Risk detail | "This US-bound order is critical. The score is deterministic: severity 4, likelihood 4, exposure 4. The exact UFLPA quote and citation are shown, the verifier is marked, and the proposed actions have owners and due dates." |
| 1:35–2:10 | Signals + graph | "Signals keep the raw source text. The graph maps the company to buyers, suppliers, obligations, and risks. Each node has an inspector; clicking a risk opens its evidence." |
| 2:10–2:50 | Approvals as approver | "As Nusrat, the approver, I review the rationale and record a decision. The API enforces the role and the decision writes an audit event. Nothing material happens without this gate." |
| 2:50–3:25 | Audit as admin | "The audit log is append-only and hash-chained. Verify recomputes every link. Ayesha, the admin, can inspect the before/after payload and the decision event." |
| 3:25–4:00 | Reports | "Generate a board-ready PDF audit pack, JSON, or Markdown. It contains the score method, evidence, actions, approvals, limitations, and the not-legal-advice boundary." |
| 4:00–4:30 | Search + evals | "Search returns cited source chunks, not generated answers. The evaluation page shows 7/7 golden cases and five gates: extraction, citation coverage, verifier pass, legal-advice guard, and priority agreement." |
| 4:30–5:00 | Close | "Chowkidar turns two or more streams into a ranked audit, a remediation plan, and a signed human decision with a trail. See the risk. Approve the fix." |

---

## 5. Submission-form copy

### Short description

Chowkidar is an agentic compliance risk sentinel for export supply chains. It monitors regulatory, sanctions, and news streams; extracts cited obligations; maps them to suppliers and controls; scores and prioritizes risk; drafts remediation; and requires human approval before material action.

### Problem

Export-focused SMEs and mid-market manufacturers face overlapping EU, US, and home-country rules, sanctions/watchlists, buyer codes, and supplier incidents. They often lack in-house legal/compliance capacity, so changes are tracked in spreadsheets and email. The result is missed obligations, shipment delays, buyer penalties, and no defensible audit trail.

### Solution

An evidence-first risk workspace:

1. Monitor at least two distinct streams.
2. Extract structured obligations with a verbatim quote and citation.
3. Map exposure to company, supplier, and policy context.
4. Score deterministically; use the LLM for rationale, not ranking.
5. Draft owned, dated remediation actions.
6. Verify evidence and guard against legal advice.
7. Route material actions to a named human approver.
8. Export a board-ready audit pack and keep a hash-chained log.

### AI architecture

- **LangGraph** state machine: ingest → extract → map → score → remediate → verify → conditional repair → persist. One bounded repair cycle re-retrieves verbatim evidence; unresolved risks remain `needs_review`.
- **LiteLLM** provider fallback: Gemini 3.5 Flash → Groq `gpt-oss-120b` → optional Ollama. Verification/report calls prefer the Gemini Pro slot, which defaults to Gemini 3.5 Flash.
- **Hybrid LLM mode** tries a live provider and falls back to the deterministic path; `/healthz` reports `llm_live_ready` honestly.
- **Deterministic mock mode** for reproducible judging.
- **Hybrid retrieval**: pgvector + Postgres full-text search over cited chunks.
- **Verifier**: quote grounding, citation URL, prohibited-language, prompt-injection, and evidence checks.
- **Live ingestion**: GDELT + US Federal Register connectors with dedupe, mode labels, and an in-process APScheduler job. Bangladesh Bank, EUR-Lex, and UFLPA remain fixture-backed.
- **MCP**: read-only FastMCP server for other agents to inspect risks and evidence; not in the product path.

### Why this team

JU_StackMind combines AI/full-stack engineering and data engineering. The build demonstrates the full path from source ingestion to evidence-grounded agent output, operational UI, role-gated approval, audit integrity, tests, evaluation, and deployment configuration.

### Next

Pilot with an RMG exporter and a compliance reviewer; add Gemini/Groq keys to Render and verify one live hosted pipeline; observe a scheduled ingestion cycle; optionally enable the private Supabase Storage adapter; expand the golden set; add tenant isolation, HttpOnly sessions, MFA/SSO, and external audit anchoring.

---

## 6. Build provenance

- Base implementation produced by an AI coding agent from one frozen master prompt, v1.0.
- No iterative implementation prompts; subsequent work was QA, tests, and documentation.
- Full session record, manual changes, model names, and test evidence: [`docs/BUILD_LOG.md`](BUILD_LOG.md).
- Runtime prompt version: `2026-10-23.1` in `apps/api/app/agents/prompts.py`.
- Build-level classification is left to the submission form; this packet does not assert one beyond the evidence.

---

## 7. Known limitations

- **Live connectors are implemented for GDELT and the US Federal Register only.** Bangladesh Bank, EUR-Lex, and DHS/UFLPA remain fixture-backed. GDELT is externally rate-limited and falls back to fixtures with a `fixture_fallback` label. Render runs `DATA_MODE=hybrid`; Federal Register live sync and dedupe are hosted-verified.
- **Scheduled ingestion is implemented and deployed; the job is armed, but its first hosted cycle has not been observed.** The in-process APScheduler job is enabled by `ENABLE_SCHEDULER=true` and `scheduler_running=true`. An arming bug left the job paused with `SCHEDULER_RUN_ON_START=false`; the fix is deployed at revision `94c2a19f91c4`, and `/healthz`/`/api/v1/meta` report `scheduler_next_run_at=2026-10-26T09:17:40Z`. Do not claim a completed scheduled cycle until `last_synced_at` advances. n8n remains optional and is not the pilot path.
- The hosted app is a **single-workspace production pilot**, not demo mode: `AUTH_MODE=supabase`, `DEMO_MODE=false`, four provisioned accounts, demo login `403`. It is not a multi-tenant commercial deployment.
- Reports use Postgres on the hosted API, with private Supabase Storage as an optional adapter. Local `/tmp` reports are not durable.
- Rate limits are process-local; browser tokens are in local storage rather than HttpOnly cookies. The Supabase database password is weak but is accepted for this zero-real-user pilot; it is not a submission blocker and must be rotated before any real-user deployment.
- Netlify is primary; the Vercel secondary fallback has DNS variability on some networks. Use the documented edge-IP workaround or a custom domain if the fallback is needed.
- BGE-M3, Docling, RAGAS, Phoenix, Neo4j, and n8n are optional and not on the hosted pilot path.
- Golden set is small and synthetic (7 cases). No real exporter data or accuracy benchmark. No customer interviews, LOIs, design partners, or revenue; the validation evidence log is at zero.
- No legal/compliance advisor reviewed the content. No legal advice is provided; every finding is a reviewable signal.
- No final demo video. The form uses a clearly marked placeholder; no recording is claimed. The design artifact is [`DESIGN.md`](DESIGN.md), not a Figma file.
- Team-diversity facts are intentionally left blank by the user's decision. The team name `JU_StackMind` is the only confirmed team value; no diversity bonus is claimed.
- The official form has not been opened or filled. The user approved filling it with placeholders for unknown or unfinished data on 2026-10-26; submission still requires separate explicit approval.

---

## 8. Asset checklist

- [x] Local build runs end to end.
- [x] Demo seed reproducible.
- [x] Screenshots in [`docs/assets`](assets).
- [x] README, architecture, deployment, MCP, and build log.
- [x] API tests, web tests, and Playwright smoke.
- [x] Docker image and Render/Netlify/Vercel configs.
- [x] GitHub remote and public repository URL.
- [x] Supabase project and database; migrated and seeded.
- [x] Render API deploy.
- [x] Netlify primary web deploy.
- [x] Vercel secondary web deploy.
- [x] Supabase Auth enabled with four provisioned accounts; demo login disabled.
- [x] Production-mode live URL verified through the hosted browser QA matrix against Netlify (2/2).
- [x] Hosted role restrictions, rate limiting, audit verification, report downloads, and mobile layout checked.
- [x] Durable reports verified across a Render redeploy with matching checksums.
- [x] CI green and local `make check` passing after the hosted fixes.
- [x] Live GDELT + Federal Register connectors, hybrid modes, scheduler, and bounded repair loop implemented and locally verified.
- [x] Hosted hybrid environment applied: `data_mode=hybrid`, `llm_mode=hybrid`, `scheduler_running=true`; Federal Register live sync and dedupe verified; GDELT fallback verified; hosted pipeline run completed with 0 errors.
- [x] Scheduler arming bug fixed with a regression test; `scheduler_next_run_at` added to health/meta and verified on the hosted revision `94c2a19f91c4` (`2026-10-26T09:17:40Z`). First scheduled cycle pending observation.
- [x] Local Gemini and Groq keys present in gitignored `.env`; both providers probed successfully without exposing the keys.
- [ ] Hosted live LLM inference verified (`llm_live_ready=true`); currently blocked on adding the provider keys to Render.
- [x] Validation kit with interview guide, LOI template, pricing hypotheses, and an honest zero-evidence log.
- [x] Design artifact [`DESIGN.md`](DESIGN.md) with wireframes, flows, tokens, and accessibility notes.
- [ ] Two-to-three-minute demo video recorded and linked; the form packet uses a placeholder.
- [ ] Team-diversity facts supplied; intentionally left blank by user decision, and no diversity bonus is claimed.
- [x] Public design link live (GitHub URL resolves; verified 2026-10-26).
- [x] Form-ready packet prepared with placeholders for unknown team/video data (section 10).
- [ ] Official form filled in the portal and submitted after separate explicit approval.

---

## 9. Team-data checklist (do not guess)

The official form asks for team information. On 2026-10-26 the user decided to
use `JU_StackMind` only and leave every other team field blank. These values are
**not invented**, and no team-diversity points are claimed:

| Field | Value | Status |
|---|---|---|
| Team name | JU_StackMind | known |
| Team size | _blank_ | **intentionally blank per user decision** |
| Member names and roles | _blank_ | **intentionally blank per user decision** |
| Team lead / contact | _blank_ | **intentionally blank per user decision** |
| NRB status (non-resident Bangladeshi) | _blank / prefer not to say_ | **intentionally blank; no bonus claimed** |
| Female team member(s) | _blank / prefer not to say_ | **intentionally blank; no bonus claimed** |
| Design link | `https://github.com/A7reus/Chowkidar/blob/main/docs/DESIGN.md` | live (verified 2026-10-26) |
| Video URL | `[PLACEHOLDER — not recorded]` | **placeholder; no recording claimed** |

If the form requires a value that is not known, leave it blank or use the
form's "prefer not to say" option. Do not fill a guess.

---

## 10. Official form fill packet (prepared, not submitted)

**Status:** The official form has **not** been opened, filled, or submitted. The
user approved filling it with placeholders for unknown or unfinished data on
2026-10-26, but submission requires a separate explicit approval. The portal
session is not available in this environment.

### 10.1 Short fields

| Form field | Ready-to-paste value |
|---|---|
| Project Name | `Chowkidar` |
| Elevator Pitch | Chowkidar is an agentic compliance risk sentinel for export supply chains: it monitors regulatory and supplier-risk streams, maps them to obligations, and turns them into evidence-backed remediation that a human approves. |
| Domain | `JusticeSphere AI` |
| Challenge | `Risk Sentinel` |
| YouTube Video | `[PLACEHOLDER — 2–3 minute demo video not recorded]` |
| GitHub Repository | `https://github.com/A7reus/Chowkidar` |
| Live Demo URL | `https://ch0wkidar.netlify.app/` |
| Secondary Live URL | `https://chowkidar-wheat.vercel.app/` (Vercel DNS varies on some networks) |
| API URL | `https://chowkidar-api.onrender.com/` |
| Figma / Design Link | `https://github.com/A7reus/Chowkidar/blob/main/docs/DESIGN.md` |
| Other Link 1 | `https://chowkidar-api.onrender.com/docs` (OpenAPI) |
| Other Link 2 | `https://github.com/A7reus/Chowkidar/blob/main/docs/ARCHITECTURE.md` |
| Other Link 3 | `https://github.com/A7reus/Chowkidar/blob/main/docs/MCP.md` |
| Access Note | Four hosted Supabase accounts (`admin@`, `analyst@`, `approver@`, `viewer@chowkidar.app`). Passwords are supplied privately through the form's access field or another controlled channel; demo login is disabled. |
| Team Name | `JU_StackMind` |
| Team Size | `[LEAVE BLANK — user decision]` |
| Member Names / Roles | `[LEAVE BLANK — user decision]` |
| Team Lead / Contact | `[LEAVE BLANK — user decision]` |
| NRB Member Bonus | `[LEAVE BLANK / PREFER NOT TO SAY — no bonus claimed]` |
| Female Member Bonus | `[LEAVE BLANK / PREFER NOT TO SAY — no bonus claimed]` |

### 10.2 Long-form copy

**Public Summary**

Chowkidar is a working, deployed compliance risk sentinel for export supply chains. It watches regulatory and supplier-risk streams, extracts cited obligations, maps them to a company's suppliers and controls, scores the resulting risk deterministically, and drafts owned remediation actions. A human approver must sign off before material action, and every material mutation writes a hash-chained audit event. The pilot exposes five labelled streams, two real live connectors (US Federal Register and GDELT), a hybrid live/fixture fallback, Supabase email/password authentication, durable Postgres reports, and a read-only MCP server. It is a single-workspace production pilot, not a commercial multi-tenant platform, and it does not provide legal advice.

**Problem Statement**

Export-focused SMEs and mid-market manufacturers face overlapping EU, US, and home-country rules, sanctions and watchlists, buyer codes, and supplier incidents. They often lack in-house legal and compliance capacity, so changes are tracked in spreadsheets and email. The result is missed obligations, shipment delays, buyer penalties, and no defensible audit trail. Generic chatbots do not solve this: they produce fluent answers without a reliable citation, an owner, a deadline, or a human decision record.

**Solution Description**

Chowkidar turns monitored signals into an evidence-first risk workflow. It (1) monitors at least two distinct streams; (2) extracts structured obligations with a verbatim quote and citation; (3) maps exposure to the company, suppliers, and policy context; (4) scores risk deterministically and uses the LLM for rationale rather than ranking; (5) drafts owned, dated remediation actions; (6) verifies quote grounding, citation presence, prohibited legal-advice language, and prompt-injection markers; (7) routes material actions to a named human approver; and (8) exports a board-ready audit pack with a hash-chained audit trail. A conditional repair step re-retrieves verbatim evidence once when verification fails; unresolved risks remain `needs_review` rather than being silently accepted.

**Data & AI Provenance**

The base product was built by an AI coding agent (OpenCode) from one frozen master prompt, v1.0, with no iterative implementation prompts; the build story, model names, manual changes, and test evidence are in `docs/BUILD_LOG.md`. Runtime AI uses LangGraph for the ingest → extract → map → score → remediate → verify → conditional repair → persist workflow, LiteLLM for provider fallback, Gemini 3.5 Flash and Groq `gpt-oss-120b` on free tiers, and a deterministic mock path for reproducibility. Data comes from five labelled streams: US Federal Register and GDELT have real live connectors with dedupe; Bangladesh Bank, EUR-Lex, and DHS/UFLPA remain fixture-backed. GDELT is publicly rate-limited and is labelled `fixture_fallback` when it fails. The hosted service currently reports `llm_live_ready=false` because provider keys are absent on Render, so hosted inference falls back deterministically; the local `.env` has working keys but they are never committed. No fine-tuning, LoRA, or training-data pipeline was used.

**Tooling & IDE**

OpenCode (AI coding agent), Python 3.14 with `uv`, FastAPI, SQLAlchemy 2, Alembic, Postgres with pgvector, LangGraph, LiteLLM, LlamaIndex, Next.js App Router, TypeScript, pnpm, Tailwind CSS, shadcn-style components, TanStack Query, React Hook Form, Zod, Recharts, React Flow, Docker, GitHub Actions, Supabase Auth/Postgres, Render, Netlify, and Vercel. Tests use pytest, Vitest, and Playwright.

### 10.3 Structured-tab copy

| Tab / field | Ready-to-paste copy | Honest status |
|---|---|---|
| Prompt Strategy | The build used one frozen master prompt, v1.0, to generate the base in one pass. Runtime prompts are versioned (`2026-10-23.1`) and separated into extraction, rationale, and verification roles. Extraction returns JSON validated against a Pydantic obligation model with title, citation URL, verbatim quote, severity, likelihood, exposure, and rationale; the verifier checks quote grounding and prohibited language. We do not request or expose hidden chain-of-thought. | Implemented |
| Token Optimization | Context is bounded by a six-signal live-pipeline limit, raw-text truncation, chunked evidence retrieval, and compact JSON outputs. Provider fallback and a 90-second per-provider cooldown avoid repeated timeout spend; one bounded repair cycle prevents unbounded retries. Mock mode is deterministic for repeatable judging. No prompt caching or fine-tuning is claimed. | Implemented |
| AI-DLC Process | The base was built by OpenCode from a single frozen master prompt; subsequent work was QA, tests, deployment, and documentation rather than iterative implementation prompts. Persistent decision, gap-analysis, build-log, and limitations files preserve context across sessions. Changes were verified with API/web tests, lint, type-checking, local smoke tests, and hosted browser QA. | Implemented |
| Agent / Orchestration | LangGraph runs a typed state machine: ingest → extract → map → score → remediate → verify → conditional repair or persist. The verifier routes only unresolved risks into one bounded repair cycle that re-retrieves verbatim evidence. Database tools persist obligations, risks, actions, evidence links, and audit events. Material actions still require a human approval; the agent cannot approve its own work. | Implemented |
| Fine-Tuning / Adaptation | No fine-tuning, LoRA, instruction tuning, or training-data curation was used. Adaptation is through prompt and JSON-schema design, deterministic risk scoring, verifier rules, and a seven-case golden evaluation set. Fine-tuning on real exporter data is future work and is not claimed. | Not implemented |
| Evaluation and Quality | The evaluation page runs seven golden cases and five gates: extraction, citation coverage, verifier pass, legal-advice guard, and priority agreement. The repository has 76 API tests and 8 web tests, plus lint, type-checking, local smoke tests, and hosted browser QA. The golden set is small and synthetic; there is no real-world accuracy benchmark. | Implemented with disclosed limits |
| Guardrails / Safety / Privacy | PII is redacted before LLM and verifier processing; raw source text remains stored for evidence. Outputs are checked for prohibited legal-advice language and prompt-injection markers; every risk must carry a verbatim quote and citation. Mutations are role-gated and audited with a SHA-256 hash chain. The browser never receives provider or service-role keys. The product is decision support, not legal advice, and a human approves material actions. | Implemented |
| Tunneling Usage | Not used. Chowkidar is publicly hosted on Netlify (primary) and Render (API), with Vercel as a secondary web fallback, so no ngrok, Cloudflare Tunnel, localtunnel, or Tailscale Funnel is required. The local judge path uses `localhost` only. | Not used; do not claim tunneling points |
| Data Quality | Signals use a normalized schema, source and jurisdiction labels, `(source_id, external_id)` dedupe, mode labels (`live`, `fixture`, `fixture_fallback`), and sanitized source errors. Fixture fallback is visibly degraded, never reported as a healthy live sync. The seed is reproducible and the golden set is source-grounded. Source licensing, fixture provenance, and freshness expectations are disclosed in `docs/DATA_SOURCES.md`; there is no enforced freshness SLO or formal terms review. | Implemented with disclosed limits |
| Privacy and Compliance | The pilot has no real customer data. Hosted auth uses Supabase email/password with local role mapping; reports are stored in Postgres, with private Supabase Storage as an optional adapter. Rate limits are process-local. There is no SOC 2, GDPR certification, legal review, or multi-tenant isolation claim. | Pilot boundary |
| Lineage and Observability | Every risk links to its signal, source URL, verbatim quote, and evidence chunk. Agent runs record workflow, mode, prompt version, routing, repair attempts, and verification outcomes; source records expose last sync mode, count, and sanitized error. Material mutations append hash-chained audit events. Hosted Sentry/Phoenix tracing is not enabled. | Implemented with disclosed gaps |
| MCP Usage | A read-only FastMCP server over stdio exposes six tools, one prompt, and one resource for inspecting risks, evidence, approvals, and the supply-chain graph. No external MCP server is integrated into the product path, and the pipeline does not call MCP. | Built, not used in product path |
| Agent Frameworks | LangGraph is the only agent framework used. CrewAI, AutoGen, OpenAI Swarm, and similar frameworks are not used. | Implemented |
| AI Models Used | Gemini 3.5 Flash through LiteLLM for extraction and rationale; Groq `gpt-oss-120b` as the fallback provider; a deterministic mock path for reproducible runs. The hosted service currently uses the deterministic fallback because provider keys are absent on Render. | Implemented; hosted live inference pending keys |
| Local / Open-Source LLMs | An optional Ollama adapter exists in the LiteLLM client, but no local model was run for the hosted pilot or claimed in the submission. BGE-M3 embeddings and Docling are optional and not on the hosted path. | Not used in pilot |
| Frontend AI Tools | None. The web UI was built directly with Next.js, TypeScript, Tailwind CSS, and shadcn-style components; no Lovable, v0, Bolt.new, Cursor, or canvas tool was used. | Honest zero |
| Workflow Automation Tools | LangGraph and the in-process APScheduler are used for the agent workflow and scheduled ingestion. n8n, Zapier, Make, Airflow, Temporal, Dagster, Prefect, and Windmill are not used. | Implemented subset |
| Build Level | Working deployed production pilot: single workspace, Supabase auth, durable reports, live Federal Register ingestion, GDELT fallback, and human approval. Not a commercial multi-tenant SaaS. | Honest classification |

### 10.4 Fields that must not be guessed

- **Team size, member names/roles, team lead, NRB status, female-member status:**
  leave blank or use "prefer not to say." The user chose this on 2026-10-26.
- **YouTube URL:** leave the placeholder until a real 2–3 minute recording
  exists. Do not link an unrelated video.
- **Hosted live inference:** do not claim it while `/healthz` reports
  `llm_live_ready=false`. After the keys are added to Render, verify
  `llm_live_ready=true` and one pipeline run before changing the wording.
- **Fine-tuning, local models, external MCP integration, tunneling:** record the
  honest "not used" status above. Do not check boxes for them.
