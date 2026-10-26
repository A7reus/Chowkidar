# Chowkidar — Limitations

**Last updated:** 2026-10-26

**Status:** Honest inventory for the preliminary submission. This file takes
precedence over any optimistic wording elsewhere.

Chowkidar is a working, seeded pilot with a live Supabase-authenticated
deployment. It is not a commercial SaaS, a live regulatory feed, or a substitute
for legal counsel. The list below records what is **not** built, what is **not
enabled**, and what is **pilot-only**, so judges and future maintainers can
calibrate the claims.

> **Current hosted state (2026-10-26):** live connectors, hybrid modes, the
> bounded repair loop, and the scheduler are deployed and enabled on Render.
> `/healthz` reports `data_mode=hybrid`, `llm_mode=hybrid`,
> `scheduler_running=true`, and `llm_live_ready=false`. The scheduler job was
> found paused when `SCHEDULER_RUN_ON_START=false`; the arming fix was verified
> at revision `94c2a19f91c4`, and the first scheduled cycle fired at revision
> `d1f285f50e67`: GDELT `2026-10-26T09:29:36Z` (`fixture_fallback`, 0 new),
> Federal Register `09:30:00Z` (`live`, 0 new due to dedupe), next run advanced
> to `10:29:36Z`. A later docs-only deploy at `56df4142eda8` re-armed the
> scheduler; every deploy resets the interval. Render Free spin-down still
> pauses the in-process scheduler.
> Federal Register live
> sync and dedupe are hosted-verified; GDELT reports `fixture_fallback` under its
> public rate limit. Hosted pipeline inference still uses the deterministic
> fallback because Gemini/Groq keys are absent **on Render**. Working keys exist
> only in the gitignored local `.env` and were probed successfully. Do not claim
> hosted live LLM inference until `/healthz` shows `llm_live_ready=true`.

---

## 1. Live deployment status

- **The hosted app is a production pilot, not demo mode.**
  `https://ch0wkidar.netlify.app/` is the primary origin and runs against
  `AUTH_MODE=supabase` and `DEMO_MODE=false`. Email/password login, token
  refresh, local-role mapping, demo lockout, and four provisioned pilot accounts
  are live. Demo login returns `403`. Netlify production browser QA passed 2/2;
  `https://chowkidar-wheat.vercel.app/` remains a secondary fallback.
- **The hosted pilot is still a single-workspace deployment.** It has no
  multi-tenancy, RLS, MFA, SSO, or customer administration. It is not a
  commercial production environment.
- **Durable report storage is active on the hosted API.** New reports use
  Postgres (`STORAGE_BACKEND=database`) and survived an API redeploy with
  matching checksums. A private Supabase Storage adapter exists but is not
  enabled.
- **Render Free sleeps** after inactivity; the first request can take 30–60
  seconds. **Supabase Free can pause**; it must be restored before a demo.
  Because the scheduler is in-process, Render spin-down also pauses scheduled
  ingestion; use an always-on instance or an external scheduler for production.
- **The secondary Vercel fallback still has DNS variability on some networks.**
  On 2026-10-24 the default resolver sometimes returned unreachable Vercel edge
  IPs. Netlify is now primary, so this affects only the fallback path. The Render
  web fallback returned `502` and is not a reliable backup yet.
- **The Supabase database password is still weak.** This is accepted for the
  zero-real-user pilot and is not treated as a submission blocker; rotate it
  before any real-user or multi-tenant deployment.
- **No demo video or completed submission form** exists yet. The design artifact
  is [`DESIGN.md`](DESIGN.md), not a Figma file. The form packet is prepared with
  placeholders, but the portal has not been opened or filled.

## 2. Data and connectors

- **Two live connectors exist; three streams remain fixture-backed.**
  `GDELT` and the `US Federal Register` have real key-free connectors with
  normalization, dedupe by `(source_id, external_id)`, evidence chunking, and
  honest mode labels. Bangladesh Bank, EUR-Lex, and DHS/UFLPA still replay
  fixture data. The catalog in [`DATA_SOURCES.md`](DATA_SOURCES.md) distinguishes
  wired connectors from design targets.
- **Hybrid mode is implemented, but GDELT is externally rate-limited.** The
  public GDELT endpoint enforces roughly one request every five seconds and
  returned `429`/rate-limit HTML during local verification. Hybrid mode retries
  once, then falls back to fixtures and labels the run `fixture_fallback` with
  `status=degraded`. A hard `DATA_MODE=live` failure returns `502` and is never
  reported as a healthy live sync.
- **Scheduled ingestion is implemented, deployed, and has fired once.** The
  in-process APScheduler job runs when `ENABLE_SCHEDULER=true`; it is disabled
  in the local demo but enabled on Render (`scheduler_running=true`). An arming
  bug—passing `next_run_time=None` explicitly with
  `SCHEDULER_RUN_ON_START=false`—left the job paused. The fix omits that
  argument, is covered by `apps/api/tests/test_scheduler.py`, and exposes
  `scheduler_next_run_at` in `/healthz` and `/api/v1/meta`. The first scheduled
  cycle fired on 2026-10-26 at revision `d1f285f50e67`: GDELT
  `last_synced_at=2026-10-26T09:29:36Z` (`fixture_fallback`, 0 new) and Federal
  Register `09:30:00Z` (`live`, 0 new due to dedupe), with the next run advanced
  to `10:29:36Z`. Render Free spin-down still pauses the scheduler, so reliable
  production ingestion needs an always-on instance or an external scheduler.
  n8n remains optional and is not the pilot path.
- **No licensing or terms review** for source ingestion, redistribution, or
  storage. This must precede a real deployment.
- **Rate-limit handling and connector observability are minimal.** The source row
  stores `last_sync_mode`, `last_signal_count`, `last_synced_at`, and a sanitized
  `last_error`; there is no per-connector latency/cost dashboard or replay
  protection beyond external-ID dedupe.
- **No internal document ingestion pipeline in the demo.** The evidence corpus
  is seeded; Docling/PDF parsing is optional and not on the demo path.
- **The company, suppliers, seeded signals, and quotes are synthetic.** They are
  not allegations about real entities. The product labels the seeded data as a
  demo. Live Federal Register/GDELT rows are real public documents but are
  retrieved for a fictional company scenario.

## 3. AI and evaluation

- **Hybrid mode is implemented and deployed; hosted live inference is not
  enabled.** Local hybrid runs completed with Gemini 3.5 Flash and Groq
  `gpt-oss-120b`; the hosted service reports `llm_mode=hybrid` but
  `llm_live_ready=false` because provider keys are absent on Render. Working
  Gemini/Groq keys exist only in the gitignored local `.env`. Hosted pipeline
  inference therefore uses the deterministic fallback. The deterministic mock
  path remains the safe fallback.
- **Provider reliability is variable.** Gemini 3.8 Flash timed out locally and
  Gemini Pro Latest had zero free-tier quota; the defaults now use Gemini 3.5
  Flash. A 90-second per-provider cooldown prevents repeated timeouts. This is
  not a production SLA.
- **The bounded repair loop is deterministic and narrow.** It re-retrieves a
  verbatim quote and a citation once; it does not rewrite the risk, change the
  score, or call another model. One local smoke run still left a risk in
  `needs_review` after repair, which is the intended honest outcome when the
  evidence cannot be grounded.
- **The golden set is seven hand-built synthetic cases.** The 7/7 result measures
  pipeline contract compliance and citation grounding on that set, not
  generalization to unseen regulations.
- **Expected priorities and keywords were authored with the mock outputs.** This
  is not an independent legal or model-quality benchmark.
- **No human legal/compliance labels.** No advisor reviewed the content or the
  priorities.
- **No adversarial corpus.** Prompt-injection markers and prohibited-language
  checks exist, but there is no broad red-team evaluation.
- **No live embeddings or reranker.** `EMBEDDING_MODE=mock` and deterministic
  vectors are the default. BGE-M3 and reranking are not installed/benchmarked.
- **RAGAS, Phoenix, and Docling are optional and not on the demo path.**
- **No model cost/latency benchmark** for live mode, and no per-provider
  reliability history.
- **The verifier reduces risk; it does not prove correctness.** A human remains
  responsible for every material decision.

## 4. Security and identity

- **No multi-tenant isolation or Postgres RLS.** The pilot has one workspace and
  one local `users` table. Do not put unrelated customers in one deployment.
- **Browser tokens are stored in local storage** by the current Zustand client.
  A hardened deployment should use HttpOnly, SameSite cookies with CSRF
  protection and a short access-token lifetime.
- **Rate limits are process-local.** They work for one Render instance but do not
  coordinate across replicas; a shared Redis/Postgres limiter is backlog.
- **No MFA, SSO, organization management, invitation email flow, or password
  reset UI.**
- **No external anchoring of the audit hash chain.** The chain is append-only and
  verifiable inside the application/database; a database administrator could
  rewrite both data and hashes.
- **No formal security audit, penetration test, or DLP system.** PII redaction is
  pattern-based and incomplete.
- **No secrets manager.** Platform environment variables are the current store.
- **No CSRF protection** because the current API uses bearer tokens, not cookies;
  this changes if cookies are adopted.
- **No per-user audit of report downloads** beyond the authenticated request and
  standard application logs.

## 5. Operations

- **Single API instance.** No horizontal scaling, queue-backed pipeline, or
  idempotency keys for concurrent runs.
- **No production monitoring/alerting.** Sentry and PostHog are optional and not
  configured. There are no SLOs, paging, or dashboards.
- **No tested backup/restore schedule** for the free Supabase project. The
  runbook documents manual `pg_dump`/`pg_restore`, not an automated policy.
- **No load test.** Rate limits and database pool settings are sized for a demo,
  not measured traffic.
- **No zero-downtime migration process.** The container runs migrations on boot;
  a destructive migration needs a maintenance plan.
- **No incident response team or on-call rotation.** The runbook is
  single-maintainer guidance.

## 6. Product and UX

- **One seeded company and one scenario.** No onboarding, company creation,
  supplier import, or document upload in the demo.
- **No billing, plans, quotas, or customer administration.**
- **No real email delivery** (notifications, invitations, password reset).
- **English + Bengali UI chrome only.** Legal source text and generated reports
  remain in English; translation quality is not evaluated.
- **Accessibility was not audited** (keyboard-only, screen reader, contrast,
  reduced motion). Basic semantic HTML and labels exist.
- **Mobile was smoke-checked, not fully designed.** The primary target is a
  desktop compliance workspace.
- **Chromium was the primary browser test target.** Firefox/Safari were not
  exhaustively verified.
- **PDF output is a generated audit pack, not a designed legal document.**
- **No Figma source is linked.** [`DESIGN.md`](DESIGN.md) is the design artifact
  and the public GitHub link is the substitute.

## 7. Legal, compliance, and ethics

- **Not legal advice.** The product provides risk intelligence and reviewable
  signals; it does not determine liability or guarantee compliance.
- **No lawyer or compliance advisor reviewed the content, disclaimers, or
  scenario.** This is an accepted constraint for the preliminary round.
- **No privacy policy, terms of service, DPA, or data-retention policy** for real
  users.
- **No data-residency review** beyond the current Supabase/Render/Netlify/Vercel regions.
- **Supplier-risk signals can harm reputations if treated as findings.** The UI
  uses signal/risk/needs-review language and requires human verification, but
  this is not a complete due-process safeguard.
- **No independent fairness/bias audit.** The scenario and golden set can encode
  coverage and language bias.

## 8. Evaluation and submission

- **No real users, design partners, revenue, or letters of intent.** The
  validation kit exists in [`VALIDATION.md`](VALIDATION.md), but the evidence log
  records `0 interviews`, `0 LOIs`, and `0 paying customers`.
- **No measured accuracy on real exporter data.**
- **No final public demo video.** [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) is ready;
  the form packet uses a clearly marked placeholder.
- **No Figma file.** [`DESIGN.md`](DESIGN.md) is the design artifact and the
  public GitHub link is the substitute.
- **Team-size, NRB, and female-member facts** are intentionally left blank by
  the user's 2026-10-26 decision. No diversity bonus is claimed.
- **No legal review of the submission copy.**
- **The official form has not been opened or filled.** The user approved filling
  it with placeholders for unknown or unfinished data, but submission requires a
  separate explicit approval. See [`SUBMISSION.md`](SUBMISSION.md) section 10.

## 9. What “production-ready” means here

It means the master-prompt production path is **live and verified**: Supabase
email/password auth, local role authorization, demo lockout, durable report
storage, rate limits, settings, hosted browser QA, and operational
documentation. It does **not** mean commercial SaaS readiness, validated legal
accuracy, live coverage for all five streams, hosted live LLM inference, or a
security certification. The remaining gaps are listed above rather than hidden.
