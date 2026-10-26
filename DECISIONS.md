# Chowkidar — Decision Log & Persistent Context

**Last updated:** 2026-10-26

**Status:** Active — base build complete; hosted production pilot live; hybrid data/LLM modes and scheduler deployed; first scheduled cycle verified at revision `d1f285f50e67`; Federal Register live sync verified; hosted LLM keys absent

**Owner:** JU_StackMind  
**Purpose:** Single source of truth for decisions, constraints, assumptions, and session history. Read this before starting any new work session.

---

## 1. Project identity

| Field | Value |
|---|---|
| Event | International AI Builders Congress 2026 |
| Track | Idea to Unicorn — Preliminary Submission |
| Deadline | 2026-10-31, 11:59 PM GMT+6 |
| Domain | JusticeSphere AI |
| Challenge | Risk Sentinel |
| Product | **Chowkidar** (final name) |
| One-liner | An agentic risk sentinel that monitors regulatory and supplier risk signals, maps them to a company's obligations, and turns them into approved remediation plans with an audit trail. |
| Team | JU_StackMind |
| Team strengths | AI/full-stack engineering, data engineering |
| Legal/compliance advisor | **None** — must design around this |
| Per-domain submission counts | **Not available** — organizers will not reveal |
| Initial builder | **AI agent (OpenCode)** builds the base from the master prompt; team modifies/improves later |
| Commit history | Clean, logical, human-followable commits required |
| Stack decisions | **User approval required for every stack choice** |

---

## 2. Decisions

| Date | Decision | Rationale | Status |
|---|---|---|---|
| 2026-10-23 | Choose **JusticeSphere AI → Risk Sentinel** | Likely lower saturation than Health/Fin/Learn/Commerce; Risk Sentinel likely least crowded challenge in the domain; official brief is specific and demoable | Accepted |
| 2026-10-23 | Narrow Risk Sentinel to **regulatory + supplier risk for export supply chains** | Generic GRC dashboard is weak; this wedge matches the official "specific ask" 1:1 and has a strong Bangladesh beachhead | Accepted |
| 2026-10-23 | Product name **Chowkidar** | Watchman/guard; fits monitoring; user selected it | Accepted (final) |
| 2026-10-23 | Position as **compliance risk intelligence**, not legal advice | Team has no legal advisor; avoids unauthorized-practice and hallucination risk; keeps human in control | Accepted |
| 2026-10-23 | Use **evidence-first architecture** | Every obligation/risk must cite a primary source; no evidence → "insufficient evidence" | Accepted |
| 2026-10-23 | **Human-in-the-loop for every action** | Required by Risk Sentinel brief; mitigates no-advisor risk; builds audit trail | Accepted |
| 2026-10-23 | Use **source-grounded evaluation** instead of legal expertise | Gold labels from official texts; measure extraction/citation/mapping accuracy, not legal opinion | Accepted |
| 2026-10-23 | Build in **8 days**, submit early | Deadline Oct 31; portal load risk; buffer day | Accepted |
| 2026-10-23 | Maintain persistent docs as external memory | Context window is limited; avoid losing decisions between sessions | Accepted |
| 2026-10-23 | **One-prompt rule applies to the whole build** | Confirmed by user; master prompt must generate/initialize the entire base in one pass | Accepted |
| 2026-10-23 | **AI agent builds the base alone** | User confirmed team will modify/improve later; no role assignment needed yet | Accepted |
| 2026-10-23 | **Clean, human-followable commit history** | User requirement; logical commits, Conventional Commits, each commit coherent | Accepted |
| 2026-10-23 | **Ask user before every stack decision** | User requirement; no assumptions about language, package manager, framework, libraries, DB, deploy | Accepted |
| 2026-10-24 | Treat **production-ready** as the master-prompt production path, not commercial SaaS readiness | Close the concrete gaps: Supabase Auth, durable report storage, demo lockout, rate limits, settings, runbooks; disclose remaining limits | Accepted |
| 2026-10-24 | **Local `users` table is authoritative for role/name**, not Supabase `app_metadata` | Prevents a token claim or Supabase dashboard edit from silently granting workspace privileges | Accepted |
| 2026-10-24 | Report storage supports **local / database / Supabase Storage** | Database gives durable reports on free Render immediately; Supabase Storage is an optional object-store path with Postgres fallback | Accepted |
| 2026-10-24 | Rate limits are **process-local** for now | Single Render free instance; document the multi-instance limitation rather than add unverified infrastructure | Accepted |
| 2026-10-24 | Keep demo auth live until **all** production keys and hosted QA are ready | Avoid breaking the working judge URL; never claim the live URL is production before cutover | Accepted |
| 2026-10-26 | Use **JU_StackMind only** and leave all other team fields blank | User decision; team size, member names, lead, NRB status, and female-member status are not confirmed and must not be invented; no diversity bonus claimed | Accepted |
| 2026-10-26 | Accept the weak Supabase database password for the **zero-real-user pilot** | No real users or customer data; not a submission blocker. Rotate before any real-user or multi-tenant deployment | Accepted (pilot only) |
| 2026-10-26 | Use a **placeholder** for the demo video | Video production is out of scope for this work and no recording exists; never claim a video that is not real | Accepted |
| 2026-10-26 | Prepare and fill the official form with **placeholders** for unknown or unfinished data, but do not submit | User approved filling; submission still requires separate explicit approval. Portal access was not available in this session | Accepted |

### 2.1 Approved stack decisions (batches 1–3)

| Area | Decision | Notes |
|---|---|---|
| Language | **TypeScript** | Frontend and shared contracts |
| Package manager | **pnpm** | Installed (v12.15.0) |
| Repo structure | **Monorepo** | `apps/web`, `apps/api`, `packages/*` |
| Frontend | **Next.js App Router** | React, SSR, Vercel |
| Backend | **FastAPI** | Python, async, OpenAPI |
| API style | **REST + OpenAPI** | MCP-friendly, debuggable |
| Primary DB | **Postgres** | Supabase-hosted likely |
| DB layer | **SQLAlchemy + Alembic** | Explicit migrations |
| Auth | **Supabase Auth** | Managed auth, RBAC |
| Deployment | **Vercel + Render + Supabase** | Backend target: Render |
| Python deps | **uv** | Install first |
| Python version | **3.14** | Current environment |
| Node version | **26** | Current environment |
| Styling | **Tailwind CSS** | Utility-first |
| UI components | **shadcn/ui** | Radix + Tailwind |
| Data fetching | **TanStack Query** | Caching, mutations |
| Forms | **React Hook Form + Zod** | Typed validation |
| Charts | **Recharts** | Dashboards |
| Graph view | **React Flow** | Supplier/obligation graph |
| LLM access | **Groq + Google AI Studio** | Free tiers; keys only in `.env` |
| Model routing | **LiteLLM** | Fallbacks, retries, cost tracking |
| Agent framework | **LangGraph** | Stateful multi-agent + HITL |
| RAG framework | **LlamaIndex** | Ingestion, hybrid retrieval, citations |
| Vector store | **pgvector** | Inside Postgres |
| Graph DB | **Neo4j Aura** | Cypher, graph RAG |
| Embeddings | **BGE-M3 local** | Multilingual, data sovereignty |
| Reranker | **BGE-reranker-v2-m3 local** | Citation precision |
| Local runtime | **Ollama** | Local models and embeddings |
| Evals | **RAGAS + custom golden set** | Source-grounded evaluation |
| Observability | **Phoenix (Arize)** | Local-first tracing |
| Orchestration | **LangGraph + in-process APScheduler** | Agent workflow; connector scheduling. n8n remains optional and is not the pilot path. |
| MCP server | **FastMCP** | Tools/resources for other agents |
| Doc parsing | **Docling** | Local PDF/table/layout parsing |
| Fine-tuning | **None; document LoRA plan** | Synthetic dataset + readiness plan |
| CI | **GitHub Actions** | Lint, typecheck, tests, build |
| Testing | **Vitest + Playwright + pytest** | Unit/API + one E2E approval flow |
| Local services | **Docker Compose** | Postgres/pgvector, Neo4j, Ollama, n8n |
| License | **MIT** | Permissive, judge-friendly |
| Error tracking | **Sentry** | Free tier; disabled locally |
| Analytics | **PostHog, anonymized** | No PII; env-flag disable |
| Secrets | **.env + dotenv** | GitHub Actions secrets in CI |
| Git workflow | **Conventional Commits + main-only** | Matches commit conventions |
| Monorepo tooling | **pnpm workspaces + Turborepo** | Cached tasks and clean pipelines |
| API client | **openapi-typescript + openapi-fetch** | Typed from FastAPI OpenAPI |
| Client state | **TanStack Query + Zustand** | Server cache + small UI state |
| Lint/format | **ESLint + Prettier + Ruff** | TS and Python |
| Type checking | **TypeScript strict + Pyright** | Fast, Pydantic-friendly |
| Pre-commit | **pre-commit + lint-staged** | Python and TS changed files |
| Icons/fonts/theme | **Lucide + Inter/Space Grotesk + dark** | Modern dashboard baseline |
| Languages | **English + Bengali UI toggle** | Scope to be defined; legal text stays source-language with translation disclaimer |
| Background jobs | **FastAPI BackgroundTasks + LangGraph** | No extra queue for MVP |
| PDF export | **ReportLab (server-side)** | Deterministic audit pack generated in memory; no browser dependency |
| Data streams | **Bangladesh Bank + EU regulatory** | Primary two; UFLPA/sanctions as supporting third for the demo scenario |
| Demo scenario | **EU CSDDD + UFLPA, RMG exporter** | Bangladeshi RMG exporter, EU buyer, US importer, multi-tier suppliers |
| Data mode | **Fixture default; hybrid/live implemented** | Deterministic demo by default; GDELT + Federal Register live connectors with fallback and honest labels |
| Risk scoring | **Deterministic weights + LLM explanation** | Auditable score; LLM drafts rationale and citations |
| Report formats | **PDF + JSON + Markdown** | Audit-ready plus machine-readable |
| File storage | **Supabase Storage + Postgres + local adapter** | Private bucket via authenticated API; database fallback; local for offline dev. No public/signed URLs. |
| Guardrails | **Custom verifier + policy checks** | Citation validation, schema checks, no-legal-advice classifier |
| PII handling | **Regex + allowlist** | Redact emails/phones/IDs; Presidio documented as upgrade |
| RBAC | **4 roles + single-step approval** | Admin, Analyst, Approver, Viewer; optional second approver for high risk |
| Auth flow | **Supabase email/password + seeded demo accounts** | Demo login only when `AUTH_MODE=dev` and `DEMO_MODE=true`; production uses the API's Supabase Auth proxy. |
| Audit log | **Append-only table + hash chain** | Tamper-evident approval trail |
| Search | **Postgres FTS + pgvector hybrid** | Reciprocal rank fusion |
| Model mix | **Gemini 3.5 Flash + Groq `gpt-oss-120b`; Ollama optional** | LiteLLM routing with provider cooldown; verification/report uses the Gemini Pro slot (also 3.5 Flash by default) |
| Embeddings runtime | **Python FlagEmbedding** | BGE-M3 + BGE-reranker-v2-m3; torch installed; mock vectors remain the demo default |
| i18n | **next-intl** | Cookie-based locale, no URL prefix required |
| Bengali scope | **UI chrome + labels only** | Legal source text stays original; translation disclaimer |
| Notifications | **In-app only** | Bell, approval queue, activity feed |
| Build start | **Local-first now** | Docker Compose; cloud wiring later |
| Ingestion scheduler | **In-process APScheduler; n8n optional** | Same service path as manual sync; n8n is not the pilot path |
| Deployment region | **Singapore** | Closest to Bangladesh; Supabase/Render support |

**Stack freeze:** 2026-10-23. No implementation choice changes without user approval.

**Current implementation status (2026-10-26):** the frozen stack is the target,
not a claim that every component is wired. Neo4j is optional and not in the
product path; Ollama is an optional fallback and has not been run in the demo;
n8n is optional and inactive; BGE-M3/reranker, RAGAS, Phoenix, Docling, Sentry,
and PostHog are optional and not on the hosted pilot path. The product path is
Postgres + pgvector/FTS, LangGraph, LiteLLM, FastMCP (stdio), and the in-process
scheduler. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

**Free-tier fallback:** Groq and Google AI Studio have rate limits. The pipeline
degrades to a deterministic mock mode without breaking the demo; Gemini 3.8
Flash timed out locally and Gemini Pro Latest had zero free-tier quota, so the
defaults use Gemini 3.5 Flash.

**Remaining external action:** Supabase, Render, Netlify, and Vercel are live.
The hybrid/scheduler cutover is applied. Gemini/Groq keys exist in the gitignored
local `.env` and were probed successfully, but they still need to be added to
Render to enable hosted live inference. The Supabase password is accepted for the
zero-real-user pilot and is not a submission blocker.

### 2.2 Secrets handling

- API keys are stored **only** in `.env` (gitignored), never in docs, commits, screenshots, or client bundles.
- `.env.example` contains placeholders only.
- AI keys are server-side only; never expose them via `NEXT_PUBLIC_*`.
- The keys shared during planning should be rotated before public submission.
- The demo must work without live keys via mock/fixture mode.

---

## 3. Constraints and implications

### 3.1 No legal/compliance advisor

**Implication:** We cannot credibly sell "AI legal advice" or make legal conclusions. Judges may probe domain depth.

**Mitigation:**
- Product is a **compliance risk intelligence and remediation workflow**, not a lawyer.
- AI extracts obligations, maps them to internal artifacts, scores risk, and drafts actions — a human approves.
- Every claim must quote a primary source (article/section, URL, effective date).
- A **Verifier Agent** checks citations and flags unsupported claims.
- Conservative language: "potential obligation," "requires review," "risk signal," "recommended action."
- No "you are compliant," "this is legal," "this contract is enforceable," or automated filings.
- Prominent disclaimer in UI, README, and demo.
- Optional quality check: a law student/compliance professional as a 1-hour beta tester (not a dependency).
- Eval set uses **explicit, unambiguous obligations** from official texts, not ambiguous legal interpretation.

**Positioning line:**  
> "We don't replace lawyers. We give compliance teams an evidence-linked view of what changed, what it touches, and what to do next — with human approval."

### 3.2 No per-domain submission counts

**Implication:** Saturation analysis is directional, not measured.

**Mitigation:**
- Treat JusticeSphere/Risk Sentinel as a high-expected-value bet, not a certainty.
- Focus on execution quality and differentiation.
- If the domain turns out to be crowded, the product still stands on its own merit.
- Do not over-invest in "saturation research"; invest in the demo and evidence.

### 3.3 Eight-day deadline

**Implication:** Scope must be brutally narrow.

**Mitigation:**
- One persona, one risk domain, two external data streams, one approval workflow.
- Must-have vs nice-to-have vs non-goals are explicit in `PRODUCT_SPEC.md`.
- Cut list is pre-approved in `BUILD_PLAN.md`.
- Submit by 6 PM on Oct 31, not 11:59 PM.

### 3.4 One-prompt rule — confirmed, applies to the whole build

**Implication:** The entire base must be generated/initialized from **one master prompt**, followed only by explicit confirmation triggers. No iterative human prompting during the build.

**Mitigation:**
- Finalize `prompts/MASTER_PROMPT.md` before execution.
- Execute it as a **single build pass** with the AI agent; commits are logical checkpoints of that pass, not separate prompts.
- Keep a build log (`docs/BUILD_LOG.md`) recording the prompt version, tool/model, confirmation triggers, and any manual changes.
- Do not misrepresent the build level; the form asks "How much did AI do?"
- The team's later modifications are post-base improvements, clearly separated from the initial build.

---

## 4. Assumptions

- The official Risk Sentinel brief and 5 × 20 final rubric are current.
- The preliminary auto-scoring rewards AI-native stack completeness; exact point values may be outdated.
- Public data sources (Federal Register, EUR-Lex, GDELT, OpenSanctions/UFLPA) are accessible for the demo.
- A live demo and 2–3 minute video are required and feasible.
- The AI agent can build the base in one pass; the team will modify/improve afterward.
- Synthetic internal data is acceptable if clearly labeled.
- The portal accepts a GitHub repo, live URL, YouTube video, Figma link, and up to 3 other links.
- Stack choices will be approved by the user before implementation.

---

## 5. Open questions

| Question | Why it matters | Owner | Status |
|---|---|---|---|
| Stack decisions (language, package manager, frameworks, DB, auth, AI stack, deploy) | User wants to approve every choice | User | Resolved — stack frozen 2026-10-23 |
| Cloud accounts and keys (Supabase, Render, Vercel, Neo4j Aura, Sentry, PostHog) | Public demo URL and hosted data | Team | Open — local demo works without them |
| Which live data sources work reliably from Bangladesh | Demo reliability | Team | Resolved — Federal Register live; GDELT rate-limited with labelled fallback; other streams fixture-backed |
| Do we have any pilot user / compliance contact? | Validation and story | Team | Open — validation kit created; 0 interviews |
| Can a law student review the demo for 1 hour? | Quality check, not dependency | Team | Optional |

---

## 6. Context management protocol

To avoid losing details between sessions:

1. **Read order at session start:** `README.md` → `DECISIONS.md` → `PRODUCT_SPEC.md` → `BUILD_PLAN.md`.
2. **Update after every meaningful decision:** append to `DECISIONS.md` with date, decision, rationale.
3. **Keep strategy and execution separate:** `STRATEGY.md` for the case; `PRODUCT_SPEC.md` for the product; `BUILD_PLAN.md` for execution.
4. **Store research and data source notes in `docs/`** rather than chat.
5. **Every doc has `Last updated` and `Status`.**
6. **Append a session log entry** at the end of each work session: what changed, what's next, blockers.
7. **Do not duplicate large content across docs.** Cross-reference instead.
8. **Before submission, freeze docs and tag a version.**

---

## 7. Session log

### 2026-10-23 — Session 1
- Retrieved MCP knowledge base (`cloudcamp://knowledge-base`) and public event data.
- Confirmed 572 teams / 3,108 participants / 50 challenges; per-domain counts private.
- Evaluated JusticeSphere → Risk Sentinel; chose it with a narrowed wedge.
- User confirmed team strengths (AI/full-stack, data engineering), no legal advisor, no per-domain counts.
- Created `STRATEGY.md`, `DECISIONS.md`, `PRODUCT_SPEC.md`, `BUILD_PLAN.md`, `prompts/MASTER_PROMPT.md`, `README.md`, `docs/DATA_SOURCES.md`, `docs/BUILD_LOG.md`.
- Next: confirm team roles/hours, one-prompt rule, product name; start scaffold.

### 2026-10-23 — Session 2
- User confirmed: final name **Chowkidar**, team **JU_StackMind**, one-prompt rule applies to the **whole build**, AI agent builds the base alone, team modifies later.
- User added two requirements: **clean, human-followable commit history** and **ask before every stack decision**.
- Renamed project docs from Argus to Chowkidar.
- No product code yet; waiting on stack decisions.
- Next: ask stack questions in batches, finalize master prompt v1.0, initialize git, build base in one pass with logical commits.

### 2026-10-23 — Session 3
- Approved and froze the complete stack; recorded two explicit exceptions: ReportLab for PDF generation and TypeScript 5.9.3 for `openapi-typescript` compatibility.
- Executed the v1.0 master prompt as one build pass with the AI coding agent.
- Built and committed the monorepo scaffold, local services, seeded Postgres schema, full FastAPI backend, and full Next.js console.
- Implemented the LangGraph pipeline, deterministic scoring, verifier, hybrid retrieval, PDF/JSON/Markdown reports, hash-chained audit log, role-gated approvals, and read-only MCP server.
- Validated local runtime flows, live LiteLLM fallback, report downloads, role switching, approval decisions, and action creation.
- Added backend pytest (36), web Vitest (8), Playwright smoke (4), Ruff/Pyright/ESLint/tsc clean, and a production build.

### 2026-10-23 — Session 4
- Fixed frontend runtime issues: `Button asChild`, Zustand hydration, signal source icons, graph clipping, search deep links.
- Reduced Pyright errors to zero across the API.
- Added Render Docker blueprint, Vercel framework config, CI workflow, architecture/deployment/MCP docs, and refreshed README and build log.
- Confirmed demo baseline at that time: 8 risks (3 critical, 3 high, 1 medium, 1 low), 4 pending approvals, 12 signals, 11 audit events, 7/7 evals.
- Next: generate submission screenshots, record demo video, deploy once accounts/keys exist, and add the public URL/video link.
- Blockers: cloud accounts/keys; no legal/compliance advisor; no Git remote configured.

### 2026-10-24 — Session 5
- User rejected the earlier “demo mode is sufficient” position: the live service is still a demo and must become a genuine production pilot before the form is filled.
- Re-read the persistent docs and the master prompt’s required production paths.
- Implemented Supabase Auth config/login/refresh/logout proxies, JWKS verification, and local role mapping; demo login is gated by `AUTH_MODE=dev` + `DEMO_MODE=true`.
- Implemented durable report storage with `local`, `database`, and `supabase` backends, checksum/ETag headers, and Postgres fallback.
- Added process-local rate limits for auth and mutating endpoints.
- Added production-mode login UI, automatic token refresh, pilot/demo labels, and `/settings`.
- Added the Supabase account provisioning script, migration `82eceac00bcf`, tests, and production/cutover docs.
- Verified locally with a mock Supabase Auth/JWKS server: production login, refresh, `/auth/me`, demo lockout (`403`), report generation/download, pilot badge, and settings page. API 57 tests, web 8 tests, Ruff/Pyright/`tsc`/ESLint clean.
- Live service remains **demo** (`AUTH_MODE=dev`, `DEMO_MODE=true`); new code is not yet deployed or committed at the end of this session. The official form remains untouched.
- Blockers: Supabase URL/anon/service-role keys; Render/Vercel dashboard access; demo video; Figma/design link; team-diversity facts; Supabase password rotation.
- Next: commit/push the production pass, deploy `STORAGE_BACKEND=database`, provision Supabase users, cut over auth, run hosted QA, then record assets and fill the form.

### 2026-10-26 — Session 6
- Completed a full evaluation against the official preliminary form signals and the final 5 × 20% rubric; recorded every P0/P1 gap in `docs/GAP_ANALYSIS.md`.
- Implemented live GDELT + US Federal Register connectors, `fixture|live|hybrid` data modes, dedupe by `(source_id, external_id)`, source mode/error fields, and the APScheduler ingestion path.
- Added migration `9c1e4f2a7b10_live_connectors.py`; `make migrate` and `make seed` passed with 5 sources and 13 signals.
- Verified Federal Register live sync (`mode=live`, 8 signals, second run 0 due to dedupe) and GDELT hybrid fallback (`mode=fixture_fallback`, `status=degraded`, sanitized error) locally.
- Added `LLM_MODE=mock|live|hybrid`, provider cooldown, sanitized provider errors, and `llm_live_ready` / live-connector / scheduler fields in health and meta.
- Verified a local hybrid pipeline run: 2 signals → 2 obligations → 2 risks → 4 actions in 18.4s, no errors; Gemini 3.5 Flash and Groq succeeded.
- Added conditional `verify → repair|persist` routing, one bounded repair cycle, verbatim-quote re-retrieval, routing metadata, and `repair_attempts` in run/risk records.
- Updated the five-stream source UI, mode badges, dashboard pipeline/source panels, OpenAPI types, Render config, `.env.example`, and local `.env` model defaults.
- Created `docs/VALIDATION.md` (interview guide, LOI template, pricing hypotheses, evidence log at 0) and `docs/DESIGN.md` (design artifact and wireframes).
- Reconciled `LIMITATIONS.md`, `SUBMISSION.md`, `DATA_SOURCES.md`, `ARCHITECTURE.md`, `ENVIRONMENT.md`, `README.md`, `PRODUCTION.md`, `CLOUD_DEPLOYMENT_STATUS.md`, and `RESPONSIBLE_AI.md`.
- Tests: API 75 passed; Ruff and Pyright clean; web typecheck/lint clean; web tests 8/8 passed.
- User supplied working Gemini and Groq keys. They were written only to the gitignored `.env` (mode `600`) and both providers were probed successfully with minimal LiteLLM calls; the keys were never printed or committed. Render still lacks the keys, so hosted `llm_live_ready=false`.
- User decisions recorded: keep `JU_StackMind` only and leave other team fields blank; accept the weak Supabase password for the zero-real-user pilot; keep a video placeholder; fill the official form with placeholders but do not submit.
- Prepared the official form fill packet in `docs/SUBMISSION.md` section 10, including long-form copy, structured-tab copy, and explicit "not used" disclosures for fine-tuning, local models, external MCP, and tunneling.
- Tests after the hosted-state reconciliation: API 76 passed; web 8/8 passed; Ruff, Pyright, ESLint, and `tsc` clean.
- Found a scheduler arming bug: with `SCHEDULER_RUN_ON_START=false`, explicit `next_run_time=None` left the APScheduler job paused even though `scheduler_running=true`. Fixed by omitting the argument, added `scheduler_next_run_at` to health/meta, and added `apps/api/tests/test_scheduler.py` for both branches. `make check` then passed with API 78 tests and web 8/8. Pushed as `94c2a19`; Render deployed `94c2a19f91c4` and both endpoints reported a non-null next-run time.
- Observed the first hosted scheduled cycle at revision `d1f285f50e67`: GDELT `last_synced_at=2026-10-26T09:29:36.732196Z` (`fixture_fallback`, 0 new) and Federal Register `09:30:00.053271Z` (`live`, 0 new due to dedupe); `scheduler_next_run_at` advanced from `09:29:36Z` to `10:29:36Z`.
- Blockers: hosted provider keys absent (`llm_live_ready=false`) and no portal session for the official form. The scheduled-cycle blocker is resolved. Team/video fields remain intentional placeholders; the form remains unsubmitted.

### Template for future sessions
```
### YYYY-MM-DD — Session N
- What changed:
- Decisions:
- Files updated:
- Blockers:
- Next:
```
