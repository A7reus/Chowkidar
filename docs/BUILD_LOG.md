# Chowkidar — Build Log

**Last updated:** 2026-10-25
**Status:** Base build complete; local QA and hosted QA against Vercel passed. The hosted API and both web builds are live as a production pilot with Supabase email/password auth and durable Postgres reports. Netlify is now the primary web origin; Vercel is the secondary fallback. Netlify browser QA is pending the Render CORS cutover. See [`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md).
**Purpose:** Record how the build was produced, especially the master prompt execution, confirmation triggers, and manual changes. This supports the submission's "Build Level" and "Prompt Library" fields.

---

## 1. Rules

1. Record the **master prompt version** used.
2. Record the **model/tool** used to execute it.
3. Record **confirmation triggers** used after the initial execution.
4. Record **manual changes** with reason, author, and files.
5. Record **model/prompt versions** for runtime agents.
6. Never claim a build level that is not true.
7. Link commits/PRs where possible.

---

## 2. Current build status

| Item | Status |
|---|---|
| Master prompt | **v1.0** (`prompts/MASTER_PROMPT.md`), frozen 2026-10-23 |
| Execution | Base build executed as one master-prompt pass; production auth cutover, QA, and submission prep followed |
| Repo scaffold | Complete |
| Backend | Complete: FastAPI, SQLAlchemy, Alembic, LangGraph, RAG, reports, audit, MCP |
| Frontend | Complete: 12 routes, role-aware UI, EN/BN chrome, graph, search, evals |
| Database | Local Postgres + pgvector seeded; hosted Supabase migrated and seeded; 8 risks, 12 signals, 21 actions, 11 audit events |
| Tests | API 57 passing; web unit 8 passing; local Playwright 4 passing; hosted production Playwright 2 passing |
| Type checks | Pyright 0 errors; `tsc` clean |
| Lint | Ruff clean; ESLint clean |
| Evals | 7/7 golden cases; five metrics at 1.0 in mock mode |
| MCP | Read-only FastMCP server implemented and manually exercised |
| Deployment | Live production pilot: Render API + Netlify primary web + Vercel secondary web + Supabase Auth/Postgres; prior runtime QA at `fcd7fd8`; Netlify CORS cutover pending |

### Verified demo baseline

```
companies: 1
users: 4
suppliers: 8
sources: 4
signals: 12
obligations: 11
risks: 8             (3 critical, 3 high, 1 medium, 1 low)
actions: 21
approvals: 5         (4 pending)
audit_events: 11
evidence_chunks: 12
```

---

## 3. Session log

### 2026-10-23 — Planning session
- Reviewed MCP knowledge base, public event data, and Risk Sentinel brief.
- Chose JusticeSphere → Risk Sentinel → Chowkidar.
- Confirmed team strengths (AI/full-stack, data engineering), no legal advisor, no per-domain counts.
- User confirmed final name **Chowkidar**, team **JU_StackMind**, one-prompt rule applies to the **whole build**, AI agent builds the base alone, team modifies later.
- User added requirements: clean, human-followable commit history; ask before every stack decision.
- Created planning docs: `STRATEGY.md`, `DECISIONS.md`, `PRODUCT_SPEC.md`, `BUILD_PLAN.md`, `prompts/MASTER_PROMPT.md`, `README.md`, `docs/DATA_SOURCES.md`, `docs/BUILD_LOG.md`, `docs/COMMIT_CONVENTIONS.md`.

### 2026-10-23 — Stack freeze
- User approved the complete stack: TypeScript, pnpm, Turborepo, Next.js App Router, FastAPI, Postgres + pgvector, SQLAlchemy 2 + Alembic, Supabase, Tailwind + shadcn-style UI, TanStack Query + Zustand, React Hook Form + Zod, Recharts, React Flow, LiteLLM, LangGraph, LlamaIndex, BGE-M3, Neo4j Aura, n8n, Docling, Docker, GitHub Actions, Sentry, PostHog, RAGAS, Phoenix, FastMCP.
- Stack frozen. Later changes require explicit approval.
- Two exceptions recorded with approval: **ReportLab** instead of Playwright for PDF generation; **TypeScript 5.9.3** pin for `openapi-typescript` compatibility.

### 2026-10-23 — Master-prompt build session
- Created monorepo scaffold, root config, Makefile, scripts, `.env.example`, MIT license.
- Added Docker Compose for Postgres/pgvector, Neo4j, Ollama, n8n; added n8n workflow fixture.
- Applied Alembic baseline with pgvector extension and HNSW index.
- Seeded fictional **Padma Apparel Ltd.** and the CSDDD + UFLPA scenario.
- Implemented API: auth, audit, security, models, schemas, scoring, LLM adapter, RAG, LangGraph pipeline, verifier, services, routers.
- Implemented web console: login, dashboard, signals, sources, risks, risk detail, approvals, reports, audit, graph, search, evals.
- Added role-aware navigation and a demo role switcher that reissues API tokens.
- Added PDF/JSON/Markdown reports, hash-chain verification, approval decision flow, action creation.
- Added pytest, Vitest, Playwright, FastMCP server, CI workflow, Render/Vercel deployment configs.
- Validated LiteLLM fallback (Gemini Flash → Groq; Gemini Pro → Gemini Flash). Kept `LLM_MODE=mock` as the demo default for reproducibility.
- Reseeded the database after mutation tests and verified the baseline.

---

## 4. Master prompt execution log

| Date | Prompt version | Tool/model | Scope | Confirmation triggers | Manual changes | Commit |
|---|---|---|---|---|---|---|
| 2026-10-23 | v1.0 | OpenCode coding agent (DeepSeek V4.1 Flash Free) | Whole repository: infra, API, web, agents, tests, docs | Stack approval before execution; no iterative implementation prompts; only QA/fix confirmations | See §6 | See `git log` |

### Execution notes

```
Date: 2026-10-23
Prompt version: v1.0
Tool/model: OpenCode coding agent / DeepSeek V4.1 Flash Free
Command/IDE: OpenCode shell + editor tools
Scope generated: Monorepo, FastAPI API, Next.js console, seed data, agents, reports, tests, MCP, docs
Files created: apps/, data/fixtures/, evals/, infra/, docs/, prompts/
Confirmation triggers used: stack decisions before build; no intervening implementation prompts
Manual changes: QA fixes listed in §6
Known issues: no live source connectors; no demo video/design link; team-diversity facts unconfirmed; Supabase database password still needs rotation
Next: record video, confirm design/team facts, rotate the database password, then fill the official form
```

### AI involvement disclosure

- The base repository was produced by an AI coding agent from the single master prompt.
- The agent used shell, file, browser, and test tools; it did not receive a sequence of implementation prompts.
- Human input was limited to stack/architecture decisions, scope constraints, and approval of the two stack exceptions above.
- Subsequent QA fixes and documentation updates were also agent-assisted and are logged here for transparency.
- Build-level classification is left to the submission form; this log states what actually happened rather than asserting a level.

---

## 5. Runtime prompt versions

The runtime prompts live in `apps/api/app/agents/prompts.py`, not in separate markdown files. `PROMPT_VERSION = 2026-10-23.1`.

| Agent | Prompt constant | Version | Model (live mode) | Last eval |
|---|---|---|---|---|
| Extractor | `EXTRACTION_SYSTEM` | 2026-10-23.1 | Gemini Flash, fallback Groq | 7/7 golden cases |
| Remediation planner | `REMEDIATION_SYSTEM` | 2026-10-23.1 | Groq Llama, fallback Gemini Flash | 7/7 |
| Evidence verifier | `VERIFIER_SYSTEM` | 2026-10-23.1 | Gemini Pro, fallback Gemini Flash | 7/7 deterministic gates |
| Rationale writer | `RATIONALE_SYSTEM` | 2026-10-23.1 | Groq Llama, fallback Gemini Flash | 7/7 |

The deterministic mock path (`app/agents/mock.py`) is the default for the demo and is what produced the verified 7/7 result. Live mode was smoke-tested against the configured providers.

---

## 6. Manual change log

| Date | File(s) | Change | Reason | Author |
|---|---|---|---|---|
| 2026-10-23 | `apps/web/src/components/ui/button.tsx` | Branch on `asChild` before rendering loader children | Slot/button runtime crash with generated children | AI agent + QA |
| 2026-10-23 | `apps/web/src/lib/auth/store.ts`, `providers.tsx` | Mark hydration complete from `onRehydrateStorage` and on mount | Zustand hydration deadlock blocked the app shell | AI agent + QA |
| 2026-10-23 | `apps/web/src/app/(app)/signals/page.tsx` | Map `source_name` to source icons; use `SourceIcon` component | Icons were blank; also satisfied React static-component lint | AI agent + QA |
| 2026-10-23 | `apps/web/src/app/(app)/graph/page.tsx` | Compact 5-column layout, 640px canvas, explicit fitView, inspector below graph | Graph nodes were clipped; inspector was below the fold | AI agent + QA |
| 2026-10-23 | `apps/web/src/app/(app)/evals/page.tsx` | Title-case case names; remove unused icon | Correct labels and lint | AI agent + QA |
| 2026-10-23 | `apps/web/src/app/(app)/search/page.tsx` | Read initial query from `useSearchParams` | Deep-linked search worked but state initialization was an effect | AI agent + QA |
| 2026-10-23 | `apps/web/e2e/smoke.spec.ts` | Use heading role for score breakdown | Strict-mode locator collision | AI agent + QA |
| 2026-10-23 | `apps/api/app/agents/pipeline.py`, `services/serializers.py`, `services/reports.py`, `rag/parsing.py`, `agents/llm.py` | Type casts, optional-source guard, optional Docling suppression, ReportLab row typing | Pyright cleanup to zero errors | AI agent + QA |
| 2026-10-23 | `apps/api/app/core/config.py` | Normalize `postgres://` / `postgresql://` to `postgresql+psycopg://` | Supabase/Render connection strings use the generic scheme | AI agent + QA |
| 2026-10-23 | `apps/api/app/services/reports.py` | Honor `REPORT_STORAGE_DIR` | Allow persistent disk on Render | AI agent + QA |
| 2026-10-23 | `apps/api/app/mcp/server.py` | Add read-only MCP tools, prompt, resource | Let other agents inspect evidence without bypassing approval | AI agent |
| 2026-10-23 | `apps/api/app/core/config.py`, `db/seed.py`, `services/sources.py`, `apps/api/Dockerfile`, `infra/render.yaml` | Container-safe project-root discovery; copy demo fixture into the image; use repo-root Docker context | `parents[4]` crashed inside `/app`; source sync and seed need the fixture in the container | AI agent + QA |
| 2026-10-23 | `apps/api/scripts/run_evals.py`, `Makefile` | Add database-backed golden-set CLI; use `uv` from PATH; add `docker` and `mcp` targets | `make evals` referenced a missing script; hard-coded `~/.local/bin/uv` was not portable | AI agent + QA |
| 2026-10-23 | `README.md`, `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, `docs/MCP.md`, `docs/BUILD_LOG.md` | Document current build, trust model, MCP, deployment | Submission and handoff quality | AI agent |
| 2026-10-24 | `infra/render.yaml`, `.env.example`, `README.md`, `docs/*` | Supabase migration/seed; free Render API; Vercel web; document Vercel edge-IP workaround and hosted env vars | Live demo deployment and context preservation | AI agent + QA |
| 2026-10-24 | `.agents/skills/*`, `skills-lock.json` | Install pinned Supabase agent skills | Official Supabase agent guidance | AI agent |
| 2026-10-24 | `apps/api/app/core/supabase_auth.py`, `api/v1/auth.py`, `api/deps.py`, `services/users.py` | Supabase Auth password/refresh/logout proxy, JWKS verification, local role mapping, demo gating | Production-auth path | AI agent + QA |
| 2026-10-24 | `apps/api/app/core/ratelimit.py`, API mutating routes | Process-local sliding-window rate limits | Bound auth and mutation bursts | AI agent |
| 2026-10-24 | `apps/api/app/core/storage.py`, `services/reports.py`, `db/models.py`, migration `82eceac00bcf` | Local/database/Supabase report storage, checksums, ETag downloads, Postgres fallback | Durable reports on free hosting | AI agent + QA |
| 2026-10-24 | `apps/web` login, auth store, app shell, `/settings` | Password login, automatic refresh, pilot/demo labels, runtime settings | Production UI without demo leakage | AI agent + QA |
| 2026-10-24 | `scripts/provision_supabase_users.py`, `docs/PRODUCTION.md`, env/docs | One-time Supabase account provisioning and cutover/runbook | Repeatable hosted cutover | AI agent |
| 2026-10-24 | `apps/api/app/core/supabase_auth.py`, `storage.py`, `scripts/provision_supabase_users.py` | Support `sb_publishable_*` / `sb_secret_*` keys and legacy HS256 tokens; add auth-only provisioning | Current Supabase key format and cutover without database access | AI agent + QA |
| 2026-10-24 | Render/Supabase environment, hosted database | Enabled Supabase auth, disabled demo login, provisioned four confirmed accounts, migrated durable report storage, and ran hosted API/browser QA | Complete the production-pilot cutover | AI agent + QA |
| 2026-10-24 | `apps/web/src/components/common/access-denied.tsx`, auth UI, messages, reports/evals/search/sources copy | Hide demo role-switch controls for managed accounts and replace stale demo-only wording | Managed viewers were seeing a demo action that would fail in production | AI agent + QA |
| 2026-10-24 | `apps/api/tests/test_config.py` | Construct isolated settings with `_env_file=None` | Local `.env` Supabase values made config tests order/environment-dependent | AI agent + QA |
| 2026-10-24 | `infra/render.yaml`, `.env.example`, `README.md`, `docs/*` | Record production auth as the hosted default and refresh deployment, production, status, limitation, and submission docs | Keep repository docs consistent with the live pilot | AI agent + QA |
| 2026-10-25 | `netlify.toml`, `apps/web/next.config.ts`, `.gitignore`, `README.md`, `.env.example`, `docs/*` | Add Netlify primary build config, retain Vercel as the secondary fallback, and document the dual-origin CORS values and Netlify credit limits | Netlify-primary hosting without discarding the working Vercel deploy | AI agent + QA |

---

## 7. Test and QA evidence

| Check | Command | Result |
|---|---|---|
| API lint | `uv run ruff check app tests` | Pass |
| API types | `uv run pyright` | 0 errors |
| API tests | `uv run pytest` | 57 passed |
| Web lint | `pnpm lint` | Pass |
| Web types | `pnpm typecheck` | Pass |
| Web unit | `pnpm test` | 8 passed |
| Web build | `pnpm build` | Pass; 15 routes |
| Browser smoke | `pnpm test:e2e` | 4 passed locally in demo mode |
| Hosted production browser QA (Vercel) | Playwright against Vercel + hosted API | 2 passed with real Supabase admin/viewer accounts |
| Hosted web deploy (Netlify) | Production build + `/login` request | Live; real login page renders; browser QA pending CORS |
| Hosted CORS | Preflight from both web origins | Vercel `200`; Netlify `400` until Render `CORS_ORIGINS` is updated |
| Hosted API auth QA | Login/refresh/role checks | Four accounts passed; wrong password `401`; demo login `403`; unprovisioned user `403` |
| Hosted report persistence | Generate, redeploy, download | PDF/JSON/Markdown checksums matched after Render redeploy |
| Hosted rate limit | Burst login requests | `429` with `Retry-After` |
| Golden set | `make evals` | 7/7; five metrics at 1.0 |
| Container build | `docker build -f apps/api/Dockerfile .` | Pass |
| Container health | `/healthz` + `/docs` on mapped port | Pass |
| API smoke | `/healthz`, `/dashboard/summary`, `/graph`, `/audit/verify` | Pass locally and hosted |
| Source sync | `POST /sources/{id}/sync` | Fixture load + audit event pass |
| Report generation | PDF/JSON/Markdown | Pass locally and hosted; checksums verified |
| Role flows | Analyst mutation, approver decision, admin audit verify | Pass locally and hosted |
| Reseed | `python -m app.db.seed` | Baseline restored |

Manual visual QA covered every route at 1440×1000. Known cosmetic trade-off: the UI is dense at laptop scale; use a 1440p display or browser zoom for the demo video.

---

## 8. Submission claims checklist

- [x] Build level is accurate (not asserted beyond the evidence here).
- [x] Master prompt version matches `prompts/MASTER_PROMPT.md`.
- [x] Runtime prompts are in `apps/api/app/agents/prompts.py` and referenced here.
- [x] Manual changes are documented.
- [x] Model/tool names are recorded.
- [x] No exaggerated claims about legal capability.
- [x] Disclaimers are present in UI, API root, reports, and docs.
- [x] Live pilot URL added after deployment.
- [ ] Video link added after recording.

---

## 9. Known gaps

- Public repository is live at <https://github.com/A7reus/Chowkidar>; CI is green at `8fdd413`.
- Render API, Netlify primary web, and Vercel secondary web are live. Netlify CORS is pending the Render environment update; some networks cannot reach Vercel’s new edge IPs, which now affects only the fallback. See `CLOUD_DEPLOYMENT_STATUS.md`.
- Supabase Auth is **enabled on the live service** with four provisioned accounts, local role mapping, and demo login disabled. Hosted auth, refresh, role, and browser QA passed against Vercel; Netlify rerun is pending.
- Report storage is durable on the hosted API (`STORAGE_BACKEND=database`) and survived a Render redeploy; Supabase Storage remains an optional adapter. The previous image used ephemeral `/tmp`.
- Rate limits are process-local (single Render instance).
- Browser tokens are stored in local storage; HttpOnly cookies are a hardening backlog item.
- The Supabase database password is weak and rotation is pending.
- Vercel default DNS is variable on some networks; the prior hosted QA used a reachable Vercel edge IP. Netlify is now primary, so this affects only the fallback.
- Live source connectors are not implemented; `DATA_MODE=live` remains unsupported.
- BGE-M3, Docling, RAGAS, and Phoenix are optional and not required for the demo path.
- Golden set is small (7 cases) and synthetic.
- No legal/compliance advisor reviewed the content.
- No demo video or final Figma/design link yet; team-diversity facts are unconfirmed.
