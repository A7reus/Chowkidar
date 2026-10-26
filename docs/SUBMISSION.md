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
have real live connectors with dedupe and a scheduler; Bangladesh Bank, EUR-Lex,
and UFLPA are fixture-backed. A rate-limited GDELT run is labelled
`fixture_fallback`, never reported as a healthy live sync. The hosted service is
still on the previous revision until the connector/hybrid cutover is deployed.

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
- **Production status:** live and verified as a production pilot. Netlify browser QA passed 2/2 at the previously verified revision `2bfaed71372c`: `/healthz` reports `auth_mode=supabase`, `demo_mode=false`, `database=ok`; admin and viewer flows passed; PDF generation/download matched SHA-256; reports use Postgres; viewer role restrictions returned `403`; and both web origins pass CORS preflight. This is a single-workspace pilot, not commercial SaaS readiness. **The connector/hybrid/repair work is implemented locally but not yet deployed to Render**; the hosted service still reports `llm_mode=mock` and `data_mode=fixture` until the cutover.
- **Video URL:** _to be added after recording — required for the official form_

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

Pilot with an RMG exporter and a compliance reviewer; enable scheduled ingestion on the hosted service; optionally enable the private Supabase Storage adapter; expand the golden set; add tenant isolation, HttpOnly sessions, MFA/SSO, and external audit anchoring.

---

## 6. Build provenance

- Base implementation produced by an AI coding agent from one frozen master prompt, v1.0.
- No iterative implementation prompts; subsequent work was QA, tests, and documentation.
- Full session record, manual changes, model names, and test evidence: [`docs/BUILD_LOG.md`](BUILD_LOG.md).
- Runtime prompt version: `2026-10-23.1` in `apps/api/app/agents/prompts.py`.
- Build-level classification is left to the submission form; this packet does not assert one beyond the evidence.

---

## 7. Known limitations

- **Live connectors are implemented for GDELT and the US Federal Register only.** Bangladesh Bank, EUR-Lex, and DHS/UFLPA remain fixture-backed. GDELT is externally rate-limited and falls back to fixtures with a `fixture_fallback` label. The hosted Render service still runs the previous revision (`DATA_MODE=fixture`, `LLM_MODE=mock`) until the migration and environment cutover are deployed.
- **Scheduled ingestion is implemented but not hosted.** The in-process APScheduler job is enabled by `ENABLE_SCHEDULER=true`; n8n remains optional and is not the pilot path.
- The hosted app is a **single-workspace production pilot**, not demo mode: `AUTH_MODE=supabase`, `DEMO_MODE=false`, four provisioned accounts, demo login `403`. It is not a multi-tenant commercial deployment.
- Reports use Postgres on the hosted API, with private Supabase Storage as an optional adapter. Local `/tmp` reports are not durable.
- Rate limits are process-local; browser tokens are in local storage rather than HttpOnly cookies. The current Supabase database password is weak and rotation is pending.
- Netlify is primary; the Vercel secondary fallback has DNS variability on some networks. Use the documented edge-IP workaround or a custom domain if the fallback is needed.
- BGE-M3, Docling, RAGAS, Phoenix, Neo4j, and n8n are optional and not on the hosted pilot path.
- Golden set is small and synthetic (7 cases). No real exporter data or accuracy benchmark. No customer interviews, LOIs, design partners, or revenue; the validation evidence log is at zero.
- No legal/compliance advisor reviewed the content. No legal advice is provided; every finding is a reviewable signal.
- No final demo video. The design artifact is [`DESIGN.md`](DESIGN.md), not a Figma file. Team-diversity facts are not confirmed.
- The official form has not been filled yet, by explicit instruction.

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
- [x] Validation kit with interview guide, LOI template, pricing hypotheses, and an honest zero-evidence log.
- [x] Design artifact [`DESIGN.md`](DESIGN.md) with wireframes, flows, tokens, and accessibility notes.
- [ ] Two-to-three-minute demo video recorded and linked.
- [ ] Team-diversity facts confirmed (see the checklist below).
- [ ] Public design link pushed (GitHub URL resolves after the commit is pushed).
- [ ] Final submission form completed before the deadline.

---

## 9. Team-data checklist (do not guess)

The official form asks for team information. The following values are **unknown**
and must be supplied by the team, not invented:

| Field | Value | Status |
|---|---|---|
| Team name | JU_StackMind | known |
| Team size | _unknown_ | **needs user input** |
| Member names and roles | _unknown_ | **needs user input** |
| Team lead / contact | _unknown_ | **needs user input** |
| NRB status (non-resident Bangladeshi) | _unknown_ | **needs user input** |
| Female team member(s) | _unknown_ | **needs user input** |
| Design link | `https://github.com/A7reus/Chowkidar/blob/main/docs/DESIGN.md` | ready after push |
| Video URL | _not recorded_ | **out of scope; needs owner** |

If the form requires a value that is not known, leave it blank or use the
form's "prefer not to say" option. Do not fill a guess.
