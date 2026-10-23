# Chowkidar — Master Prompt (v1.0)

**Last updated:** 2026-10-23  
**Status:** Frozen — approved stack; execute as one build pass  
**Purpose:** Single master prompt for the Idea to Unicorn build. The AI agent is the sole initial builder; the team improves the base afterward.

---

## How to use

1. Read `DECISIONS.md`, `PRODUCT_SPEC.md`, and `BUILD_PLAN.md`.
2. Copy the prompt below into the AI coding tool.
3. Execute it once. Do not ask for iterative implementation prompts; only explicit confirmation triggers are allowed.
4. Record the execution and any manual changes in `docs/BUILD_LOG.md`.
5. Do not claim a build level that is not true.

> **One-prompt rule (confirmed):** applies to the whole build. Commits are logical checkpoints of the single build pass, not separate prompts. The team modifies and improves the base afterward.

---

## Master prompt

```text
You are the lead architect, full-stack engineer, AI engineer, and technical writer for Chowkidar, a production-grade hackathon project.

## 1. CONTEXT

Event: International AI Builders Congress 2026
Track: Idea to Unicorn — Preliminary Submission
Deadline: 2026-10-31, 11:59 PM GMT+6
Domain: JusticeSphere AI
Challenge: Risk Sentinel
Team: JU_StackMind
Team strengths: AI/full-stack engineering, data engineering
Initial builder: AI agent (OpenCode), building the base alone from this prompt
Later: JU_StackMind modifies and improves the base
Constraint: No legal/compliance advisor. Chowkidar is compliance risk intelligence, not legal advice.

Official Risk Sentinel brief:
"Develop a functional AI agent prototype that autonomously monitors at least two distinct data streams to generate a prioritized risk audit report with automated remediation suggestions. The solution must demonstrate a clear human-in-the-loop interface for approving AI-generated risk mitigation actions."

## 2. PRODUCT

Chowkidar monitors regulatory changes and supplier-risk signals, maps them to a company's obligations, policies, contracts, and suppliers, and turns them into a prioritized risk register with evidence-backed remediation plans and human approval.

Tagline: "See the risk. Approve the fix."

Demo company: Padma Apparel Ltd., a fictional 2,000-worker RMG exporter in Gazipur, Bangladesh. EU buyer Nordwear EU, US buyer Liberty Threads, 8 suppliers across Bangladesh, China, Vietnam, and India.

Primary persona: Ayesha, Head of Compliance. She manages buyer codes, regulators, and multi-tier suppliers with a small team.

Core loop:
1. Ingest signals from at least two distinct streams.
2. Extract obligations/entities with citations.
3. Map them to internal policies, contracts, suppliers, and evidence.
4. Score and prioritize risk with deterministic, explainable factors.
5. Draft remediation actions with owners and deadlines.
6. Require a human with the right role to approve/reject with rationale.
7. Generate an audit-ready report.
8. Record every decision in a tamper-evident audit log.

## 3. NON-NEGOTIABLE CONSTRAINTS

1. Evidence-first: every obligation, risk, and recommendation cites a primary source (URL, article/section, exact quote, effective date, retrieval timestamp). No evidence -> "insufficient evidence."
2. No legal advice: never say "you are compliant," "this is legal," "this contract is enforceable," or give legal conclusions. Use "potential obligation," "risk signal," "requires review," "recommended action."
3. Human-in-the-loop: no automated filing, sending, payments, or irreversible actions. A named human approves.
4. Source-grounded: if evidence is insufficient, escalate; do not guess.
5. Data sovereignty: redact PII before external LLM calls; support local Ollama fallback and deterministic mock mode.
6. Auditability: log actor, action, timestamp, before/after, rationale, model, prompt version.
7. Demo reliability: fixture-first; the demo must work without live APIs or cloud accounts. Live mode is opt-in.
8. Honesty: synthetic data must be labeled; no fake claims of legal review, real customers, or production usage.

## 4. APPROVED STACK (FROZEN)

Language: TypeScript for frontend/shared code; Python 3.14 for backend.
Package manager: pnpm 12; monorepo with pnpm workspaces + Turborepo.
Frontend: Next.js App Router + React + Tailwind CSS + shadcn/ui-style components + Lucide icons + Inter/Space Grotesk + dark theme.
Data fetching: TanStack Query + openapi-typescript/openapi-fetch.
Forms: React Hook Form + Zod.
State: Zustand for small UI state.
Charts: Recharts. Graph: React Flow.
i18n: next-intl, cookie-based locale, English + Bengali UI toggle. Translate UI chrome/labels only; legal source text stays original with a translation disclaimer.
Backend: FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic + Postgres + pgvector.
Auth: Supabase Auth in production; local dev auth adapter with seeded demo users (AUTH_MODE=dev).
AI: LiteLLM; Gemini 2.5 Flash (extraction), Groq Llama 3.3 70B (fast classification), Gemini 2.5 Pro (verifier); local Ollama fallback; deterministic mock mode.
Agents: LangGraph state machine.
RAG: LlamaIndex for document/chunk abstractions; Postgres FTS + pgvector hybrid retrieval; BGE-M3 embeddings and BGE-reranker-v2-m3 reranker via Python FlagEmbedding; mock embedding mode for offline dev.
Parsing: Docling for PDFs/tables; plain-text/Markdown fallback; PyMuPDF fallback for simple PDFs.
Graph: Neo4j Aura in deployment; local Neo4j in Docker Compose.
Orchestration: n8n for connector scheduling (local Docker); FastAPI cron fallback for deployed demo.
MCP: FastMCP server exposing risk/evidence/audit tools.
Evals: RAGAS adapter + custom source-grounded golden set.
Observability: Phoenix (Arize), optional; Sentry for errors; PostHog anonymized analytics.
Testing: pytest (API/agents), Vitest (web utilities), Playwright (one approval E2E).
CI: GitHub Actions.
Local services: Docker Compose (Postgres/pgvector, Neo4j, Ollama, n8n).
Deployment: Vercel (web), Render (API), Supabase (Postgres/Auth/Storage), Neo4j Aura, Singapore region.
Secrets: .env + dotenv locally; GitHub Actions/Render/Vercel env vars in deployment. Never commit keys.
License: MIT.
Commits: Conventional Commits; main-only initial build; one logical change per commit.

## 5. REPO LAYOUT

Use this structure (adjust only if a file genuinely does not apply):

chowkidar/
  apps/
    web/                    Next.js app
    api/                    FastAPI app
      app/
        api/v1/             routers
        agents/             LangGraph pipeline, prompts, LLM client
        core/               config, auth, security, audit
        db/                 models, session, seed
        rag/                chunking, embeddings, retrieval, parsing
        services/           business logic
        mcp_server.py       FastMCP entrypoint
      alembic/              migrations
      tests/
  packages/
    shared/                 shared TypeScript types/constants (optional)
  infra/
    docker-compose.yml
    Dockerfile.api
    n8n/workflows/
  data/fixtures/            demo signals, documents, seed JSON
  evals/                    golden set + runner
  docs/
  prompts/
  scripts/
  .github/workflows/
  .env.example
  Makefile
  README.md
  LICENSE

Do not create a separate `packages/agents` Python package; keep Python code under `apps/api/app` for simplicity. Use `packages/shared` only for cross-app TypeScript constants/types if useful.

## 6. DATA MODEL

Use SQLAlchemy 2 models and Alembic migrations. Postgres 16+ with pgvector.

Core tables:
- companies: id, name, country, sector, created_at
- users: id, email, name, role (admin|analyst|approver|viewer), supabase_user_id nullable, created_at
- suppliers: id, company_id, parent_supplier_id nullable, name, country, tier, category, status, risk_level, created_at
- buyers: id, company_id, name, country, requirements_summary
- policies: id, company_id, name, policy_type (policy|contract|code|audit), version, owner, status, summary
- sources: id, name, stream_key, source_type, jurisdiction, url, cadence, status, last_synced_at, last_error
- signals: id, source_id, external_id, title, summary, raw_text, url, jurisdiction, signal_type, severity, published_at, ingested_at, status, supplier_id nullable, metadata JSONB
- documents: id, company_id, supplier_id nullable, title, doc_type, storage_path, mime_type, sha256, parsed_text, status, uploaded_at
- evidence_chunks: id, document_id nullable, signal_id nullable, content, citation_label, citation_url, section_path, embedding vector(1024), search_vector tsvector, metadata JSONB
- obligations: id, signal_id, source_id, title, description, jurisdiction, obligation_type, applies_to, effective_date, confidence, citation_url, citation_quote, section_path, status
- risks: id, company_id, supplier_id nullable, obligation_id nullable, title, description, category, severity (low|medium|high|critical), likelihood (rare|unlikely|possible|likely), exposure (limited|moderate|significant|severe), score, priority (low|medium|high|critical), status (open|in_review|mitigating|closed), rationale, confidence, verification_status (verified|needs_review|insufficient_evidence), created_at, updated_at
- risk_evidence: id, risk_id, evidence_chunk_id nullable, quote, citation_url, citation_label, confidence, supports (supports|contradicts|context)
- remediation_actions: id, risk_id, title, description, owner_role, due_date, priority, status (draft|pending_approval|approved|in_progress|done|rejected), automated, created_at
- approvals: id, risk_id, action_id nullable, requested_by, assigned_to, status (pending|approved|rejected), decision, rationale, decided_at, created_at
- audit_events: id, actor_id, actor_email, action, entity_type, entity_id, payload JSONB, prev_hash, hash, created_at
- agent_runs: id, workflow, status, input JSONB, output JSONB, error, started_at, finished_at, trace_id
- report_runs: id, company_id, format (pdf|json|markdown), status, storage_path, summary JSONB, generated_at
- eval_runs: id, name, metrics JSONB, created_at

Indexes: risks(priority, score), signals(ingested_at), evidence_chunks GIN(search_vector), evidence_chunks ivfflat/hnsw(embedding), audit_events(created_at), approvals(status).

Seed data (fixture-first):
- 1 company, 2 buyers, 8 suppliers, 12 factories/contacts (as supplier metadata), 10 policies/contracts, 4 sources, 12 signals, 8 obligations, 6 risks, 12 remediation actions, 4 approvals, audit events.
- Scenarios: EU CSDDD due diligence, Bangladesh Bank export-proceeds circular, UFLPA traceability gap, sanctions/ownership match, port disruption.
- Label all data as synthetic in `data/fixtures/README.md` and in the UI footer.

## 7. API SURFACE

FastAPI, REST, OpenAPI. Prefix `/api/v1`.

- GET /health
- POST /api/v1/auth/demo-login  (dev mode only; body: role)
- GET /api/v1/me
- GET /api/v1/dashboard/summary
- GET /api/v1/sources
- POST /api/v1/sources/{id}/sync  (admin, or X-Internal-Key for n8n)
- GET /api/v1/signals
- GET /api/v1/signals/{id}
- POST /api/v1/pipeline/run  (body: source_ids?, mode=mock|live)
- GET /api/v1/agent-runs/{id}
- GET /api/v1/risks
- GET /api/v1/risks/{id}
- POST /api/v1/risks/{id}/actions  (analyst/admin)
- PATCH /api/v1/actions/{id}
- GET /api/v1/approvals
- POST /api/v1/approvals/{id}/decision  (approver/admin; body: decision, rationale)
- GET /api/v1/audit
- GET /api/v1/audit/verify
- GET /api/v1/reports
- POST /api/v1/reports  (body: format)
- GET /api/v1/reports/{id}/download
- GET /api/v1/search?q=...
- GET /api/v1/graph
- GET /api/v1/evals/summary

Auth:
- AUTH_MODE=dev: POST /auth/demo-login returns an HS256 JWT for a seeded role. No Supabase required.
- AUTH_MODE=supabase: verify Supabase JWT via JWKS; map role from app_metadata.role or users table.
- Server-side RBAC on every sensitive endpoint. Viewer read-only; analyst can run pipeline/draft actions; approver can decide approvals; admin can do all + source sync.
- Use dependency injection for current user and role checks.

## 8. AGENT PIPELINE

Implement a LangGraph state machine with nodes:
ingest -> extract -> map -> score -> remediate -> verify -> persist

State fields: source_ids, signals, obligations, risks, actions, verification, errors, trace_id.

- Ingest: read fixtures or call live connectors; normalize into signals; deduplicate by external_id/hash.
- Extract: structured Pydantic output with obligation title, description, jurisdiction, type, applies_to, effective_date, citation_url, citation_quote, section_path, confidence. Use Gemini Flash via LiteLLM in live mode; deterministic fixture extractor in mock mode.
- Map: match obligations to company, suppliers, policies, documents. Use hybrid retrieval; every mapping includes evidence. Unknown -> insufficient evidence.
- Score: deterministic weighted formula; LLM writes rationale only. Never let the LLM invent the score.
- Remediate: template + LLM drafting; actions are drafts, never auto-executed. Include owner role, due date, priority.
- Verify: custom checks + optional Gemini Pro in live mode. Validate citations, quote presence in source text, prohibited legal-advice phrases, and schema. Mark verified/needs_review/insufficient_evidence.
- Persist: write risks, evidence, actions, agent_run; emit audit events.

LLM client:
- LiteLLM `completion()` with retries, timeout, fallback chain.
- Primary extraction: gemini/gemini-2.5-flash
- Classification: groq/llama-3.3-70b-versatile
- Verifier: gemini/gemini-2.5-pro
- Local fallback: ollama/qwen2.5:7b (or llama3.1:8b)
- LLM_MODE=mock must work with no keys and no network.
- Log model, prompt version, token usage, latency; never log secrets or full PII.

## 9. RAG

- Parse documents with Docling when available; fallback to PyMuPDF for PDFs and plain text for Markdown/JSON.
- Chunk by legal section/heading where possible; use LlamaIndex SentenceSplitter as fallback.
- Prepend contextual metadata (title, jurisdiction, effective date, section path) to each chunk.
- Generate embeddings with BGE-M3 via FlagEmbedding in live mode; use deterministic hash embeddings in mock mode (same 1024 dimensions).
- Hybrid retrieval: Postgres full-text search + pgvector cosine similarity, fused with reciprocal rank fusion; rerank with BGE-reranker-v2-m3 in live mode, lexical overlap in mock mode.
- Citations: every retrieved chunk carries citation_label, citation_url, section_path, quote. Verifier checks quote presence.
- Graph RAG: Neo4j relationships company -> supplier -> obligation -> policy; expose `/graph` for React Flow. If Neo4j is unavailable, derive a graph from Postgres relations and return it.

## 10. FRONTEND

Next.js App Router, TypeScript strict, Tailwind, dark theme, responsive.

Screens:
1. /login: demo role cards (Admin, Analyst, Approver, Viewer); in production, Supabase email/password form.
2. /: dashboard with risk counts, trend chart, top risks, pending approvals, source health.
3. /risks: filterable risk register (priority, status, category, supplier, source) with score and verification badge.
4. /risks/[id]: risk summary, deterministic score breakdown, evidence cards with citations, supplier/obligation graph (React Flow), remediation actions, approval panel, audit trail.
5. /signals: source-filtered signal feed with severity and "Run pipeline" action.
6. /approvals: pending approvals, evidence preview, approve/reject with required rationale.
7. /reports: generate PDF/JSON/Markdown, list report runs, download.
8. /sources: source health, last sync, stream type, run sync.
9. /audit: audit events and hash-chain verification status.
10. /settings: company profile, language toggle, demo reset (admin), disclaimers.

UI requirements:
- App shell with sidebar, top bar, language toggle (EN/BN), user menu, demo-mode badge.
- Bengali toggle translates UI chrome and labels only; legal source text remains original. Show a translation disclaimer.
- Clear disclaimer visible in footer and report: "Chowkidar is compliance risk intelligence, not legal advice."
- No fake "certified compliant" claims. Use "potential obligation," "risk signal," "requires review."
- Loading, empty, and error states. Accessible labels and keyboard navigation.
- Use seeded demo data; do not require live APIs to render.

API client:
- Generate TypeScript types from FastAPI OpenAPI with openapi-typescript.
- Use openapi-fetch + TanStack Query hooks.
- Store the demo token in localStorage; redirect to /login when missing.
- Zustand for filter/UI state only.

## 11. REPORTS

- Report content: executive summary, scope/methodology, top risks, signals/changes, affected suppliers/policies, remediation actions, approvals, evidence appendix with citations, disclaimers, generated timestamp.
- Formats: JSON, Markdown, PDF.
- PDF: server-side HTML template rendered with Playwright Chromium. If Chromium is unavailable, return a clear 503 with instructions; never silently return HTML as PDF.
- Store generated reports in Supabase Storage in production; local filesystem adapter in dev.
- Every report includes a "not legal advice" disclaimer and source links.
- Report generation is read-only and does not change risk status.

## 12. SECURITY, PRIVACY, RBAC

- Validate all inputs with Pydantic/Zod.
- Enforce RBAC server-side, not just in UI.
- Rate-limit auth and pipeline endpoints; simple in-memory limiter is acceptable for the demo.
- Redact emails, phone numbers, and ID-like strings before external LLM calls; keep an allowlist for company names.
- Do not send uploaded documents to external LLMs unless DATA_MODE=live and the user has enabled it; default to mock/local.
- Prompt-injection defenses: treat retrieved text as data, not instructions; use a tool allowlist; strip/flag instruction-like content.
- Audit every approval, rejection, action update, source sync, report generation, and pipeline run.
- Hash chain: hash = sha256(prev_hash + canonical_json(payload)); verify endpoint recomputes.
- Secrets only in .env; .env.example has placeholders; no keys in logs, docs, commits, or client bundles.
- Demo mode must be clearly labeled and disabled in production.

## 13. TESTS AND EVALS

pytest:
- health endpoint
- scoring formula and priority thresholds
- verifier detects missing citation/prohibited phrase
- audit hash chain validity and tamper detection
- RBAC: viewer cannot approve; approver can
- pipeline mock mode creates risks/actions and agent_run
- API smoke tests for dashboard, risks, approvals

Vitest:
- priority/score formatting utilities
- i18n message key parity between en/bn
- API error normalization

Playwright:
- demo login as approver -> open a risk -> approve with rationale -> see confirmation -> audit page shows event.
- If Chromium is unavailable, document the command and skip gracefully in CI.

Evals:
- `evals/golden_set.json`: at least 8 cases across EU CSDDD, Bangladesh Bank, UFLPA, sanctions.
- Custom metrics: extraction field accuracy, citation coverage, verifier pass rate, no-legal-advice pass rate, priority agreement.
- RAGAS adapter optional; if ragas is not installed, run custom metrics and say so.
- Write results to `evals/results/latest.json` and a readable summary.

## 14. CI, DEPLOYMENT, OPS

- GitHub Actions: web lint/typecheck/test/build; api ruff/pyright/pytest (Postgres service with pgvector).
- Docker Compose: postgres (pgvector), neo4j, ollama, n8n; api and web run natively for fast dev (optional containers).
- `.env.example`, Makefile, health checks, structured logs.
- Render: `render.yaml` for API (Docker), health check `/health`, Singapore region.
- Vercel: `vercel.json` if needed; env vars documented.
- Supabase: Postgres/Auth/Storage; RLS not required for the demo API but document the production plan.
- Neo4j Aura: env vars; fallback to derived graph if unavailable.
- n8n: workflow JSON for Bangladesh Bank and EU sync; local Docker; FastAPI cron fallback when `ENABLE_SCHEDULER=true`.
- Include `docs/RUNBOOK.md` with deploy, rollback, backup, rotate keys, reset demo.

## 15. DOCUMENTATION

Generate:
- README.md: overview, screenshot placeholders, architecture, quickstart, demo script, eval summary, limitations, disclaimer.
- docs/ARCHITECTURE.md: components, data flow, agents, RAG, graph, security, deployment.
- docs/API.md: endpoint examples.
- docs/SETUP.md: local setup, env vars, seed, troubleshooting.
- docs/RUNBOOK.md: deploy, rollback, monitoring, key rotation, reset.
- docs/EVALS.md: dataset, metrics, results, limitations.
- docs/RESPONSIBLE_AI.md: no-legal-advice, evidence-first, human approval, PII, data sovereignty, limitations.
- docs/DEMO_SCRIPT.md: 2–3 minute script.
- docs/PITCH_DECK.md: 10-slide outline.
- docs/LIMITATIONS.md: what is not built and why.
- docs/BUILD_LOG.md: prompt version, tool/model, commits, confirmations, manual changes.

Do not claim legal review, real customers, production scale, or regulatory certification.

## 16. COMMIT SEQUENCE

Use Conventional Commits and logical checkpoints. Expected sequence (adjust only if needed):
1. chore(repo): initialize monorepo and planning docs
2. chore(infra): add Docker Compose and local services
3. feat(api): add FastAPI skeleton, config, auth, health
4. db: add core schema, migration, and seed data
5. feat(api): add signals, risks, approvals, audit, reports endpoints
6. feat(agents): add LangGraph pipeline and mock/live LLM adapters
7. feat(rag): add hybrid retrieval, embeddings, and document parsing
8. feat(mcp): add FastMCP tools
9. feat(web): add app shell, dashboard, and risk register
10. feat(web): add risk detail, approvals, and audit trail
11. feat(web): add signals, sources, reports, and Bengali toggle
12. test: add API, agent, and E2E tests
13. docs: add architecture, setup, API, eval, and responsible AI docs
14. ci: add GitHub Actions and deployment configs

Each commit must be coherent and leave the repo buildable where practical. Do not commit secrets, generated artifacts, node_modules, .venv, .next, or __pycache__.

## 17. ACCEPTANCE CRITERIA

The base is complete when:
- `docker compose up -d postgres neo4j` starts local services.
- `make setup && make migrate && make seed` works from a clean checkout.
- API starts and `/health` returns ok.
- Web starts and demo login works for all four roles.
- Dashboard shows counts, top risks, pending approvals, and source health.
- At least two distinct streams are visible (Bangladesh Bank + EU regulatory; UFLPA as supporting third).
- Running the pipeline in mock mode creates cited obligations, scored risks, and draft actions.
- Risk detail shows evidence, citations, score breakdown, graph, and actions.
- Approver can approve/reject with rationale; viewer cannot.
- Audit log chains and verification endpoint returns valid.
- Report exports JSON, Markdown, and PDF (PDF if Chromium is available).
- Evals run and produce a metrics file.
- Tests pass or documented skips are honest.
- README reproduces setup and demo.
- Disclaimers are visible.
- No secrets are committed.

## 18. TONE AND QUALITY

Production-grade, not a toy. Clear types, small modules, meaningful names, accessible UI, honest limitations. No fake data presented as real. No legal conclusions. No dark patterns. Explain tradeoffs.

If a feature cannot be completed in this build pass, mark it explicitly in docs/LIMITATIONS.md rather than pretending it exists. Core features must not be placeholders.
```

---

## Acceptance criteria for the master prompt itself

- Covers the official Risk Sentinel ask: two streams, prioritized report, remediation, human approval.
- Covers the 5 × 20 final rubric: innovation, architecture, business value, scalability/impact, responsible AI/presentation.
- Uses only the approved stack.
- Includes no-legal-advice, evidence-first, human-in-the-loop, PII, and data-sovereignty constraints.
- Includes tests, evals, docs, deployment, seed data, and a clean commit sequence.
- Executable in one build pass without iterative human prompts.

---

## Version history

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-10-23 | Initial draft based on `PRODUCT_SPEC.md` and `BUILD_PLAN.md` |
| v0.2 | 2026-10-23 | Added one-prompt confirmation, Chowkidar name, sole-builder model |
| v1.0 | 2026-10-23 | Froze approved stack; scoped local-first MVP; exact API, schema, agent, RAG, UI, tests, and commit plan |
