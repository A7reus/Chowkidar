# Chowkidar — Build Log

**Last updated:** 2026-10-23  
**Status:** Base build complete; local QA and deployment preparation in progress  
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
| Execution | Base build executed as one master-prompt pass; QA follow-up in progress |
| Repo scaffold | Complete |
| Backend | Complete: FastAPI, SQLAlchemy, Alembic, LangGraph, RAG, reports, audit, MCP |
| Frontend | Complete: 12 routes, role-aware UI, EN/BN chrome, graph, search, evals |
| Database | Local Postgres + pgvector seeded; 8 risks, 12 signals, 21 actions, 11 audit events |
| Tests | API 36 passing; web unit 8 passing; Playwright 4 passing |
| Type checks | Pyright 0 errors; `tsc` clean |
| Lint | Ruff clean; ESLint clean |
| Evals | 7/7 golden cases; five metrics at 1.0 in mock mode |
| MCP | Read-only FastMCP server implemented and manually exercised |
| Deployment | Render/Vercel configs + docs ready; cloud accounts/keys pending |

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
Known issues: cloud deployment blocked on accounts; Supabase Auth/Storage not wired into demo UI
Next: deploy, record video, final submission
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

---

## 7. Test and QA evidence

| Check | Command | Result |
|---|---|---|
| API lint | `uv run ruff check app tests` | Pass |
| API types | `uv run pyright` | 0 errors |
| API tests | `uv run pytest` | 36 passed |
| Web lint | `pnpm lint` | Pass |
| Web types | `pnpm typecheck` | Pass |
| Web unit | `pnpm test` | 8 passed |
| Web build | `pnpm build` | Pass; 15 routes |
| Browser smoke | `pnpm test:e2e` | 4 passed |
| Golden set | `make evals` | 7/7; five metrics at 1.0 |
| Container build | `docker build -f apps/api/Dockerfile .` | Pass |
| Container health | `/healthz` + `/docs` on mapped port | Pass |
| API smoke | `/healthz`, `/dashboard/summary`, `/graph`, `/audit/verify` | Pass |
| Source sync | `POST /sources/{id}/sync` | Fixture load + audit event pass |
| Report generation | PDF/JSON/Markdown | Pass |
| Role flows | Analyst mutation, approver decision, admin audit verify | Pass |
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
- [ ] Live demo URL added after deployment.
- [ ] Video link added after recording.

---

## 9. Known gaps

- Public repository is live at <https://github.com/A7reus/Chowkidar>; CI is green.
- Supabase is provisioned, migrated, and seeded; Render and Vercel deployment are pending.
- Supabase Auth token decoding exists, but the hosted login flow is not wired into the demo UI.
- Supabase Storage is not enabled; the free Render deployment uses ephemeral `/tmp`.
- BGE-M3, Docling, RAGAS, and Phoenix are optional and not required for the demo path.
- Golden set is small (7 cases) and synthetic.
- No legal/compliance advisor reviewed the content.
