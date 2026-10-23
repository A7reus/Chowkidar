# Chowkidar — 8-Day Build Plan

**Last updated:** 2026-10-23  
**Status:** Draft v0.1  
**Deadline:** 2026-10-31, 11:59 PM GMT+6  
**Target submission:** 2026-10-31, 6:00 PM GMT+6

---

## 1. Goal

Ship a working, deployed prototype of **Chowkidar** that:
1. Monitors at least **two distinct external data streams**.
2. Maps signals to a company's obligations, policies, contracts, and suppliers.
3. Produces a **prioritized risk audit report**.
4. Generates **remediation suggestions**.
5. Provides a **human-in-the-loop approval interface**.
6. Demonstrates a credible AI-native stack: multi-agent, RAG (contextual + semantic + graph), MCP, local models, evals, guardrails, observability.

The demo must be reliable and reproducible. A recorded video is the safety net.

---

## 2. Build model and roles

**Initial build:** The AI agent (OpenCode) builds the entire base from the single master prompt. No human role assignment is needed yet.

**After the base is delivered:** The JU_StackMind team modifies and improves it. Roles will be assigned then.

| Phase | Owner | Responsibilities |
|---|---|---|
| Initial base | AI agent | Repo scaffold, backend, frontend, data model, connectors, agents, tests, docs, deployment config |
| Post-base | JU_StackMind | Review, improve, add domain depth, test with users, polish demo, submission |
| Stack decisions | User | Approve every stack choice before implementation |

> **One-prompt rule:** The base must be generated/initialized from one master prompt in a single build pass. Commits are logical checkpoints of that pass, not separate prompts.

### Critical path

1. Stack decisions approved.
2. Master prompt v1.0 finalized.
3. Git initialized with planning docs.
4. Base built in one pass with logical commits.
5. Live demo + video + submission.

---

## 3. Day-by-day plan

### Day 0 — Friday, Oct 23: Decide stack and finalize prompt

**Tasks:**
- Confirm scope and non-goals.
- **Ask the user for every stack decision** (language, package manager, frontend, backend, DB, auth, AI stack, deployment, commit tooling).
- **Finalize `prompts/MASTER_PROMPT.md` v1.0** based on approved stack.
- Initialize git with planning docs and commit conventions.
- Collect source URLs and sample documents.
- Create the fictional company dataset outline.
- Set up accounts only after the stack is approved.
- Create Figma file with 5 key screens (post-base if time).

**Output:** Approved stack, master prompt v1.0, git repo with planning docs, dataset outline.

**Acceptance:** Stack decisions recorded; master prompt reviewed; initial commit follows commit conventions.

---

### Day 1 — Saturday, Oct 24: Skeleton and data

**Tasks:**
- Scaffold Next.js + FastAPI monorepo.
- Auth + RBAC skeleton.
- Postgres schema: Company, User, Source, Document, ChangeEvent, Obligation, Supplier, Policy, Contract, Control, Risk, Action, Evidence, Approval, AuditEvent.
- Seed script with Meghna Apparel Ltd. + 40 suppliers + 12 policies + 6 contracts.
- Source registry UI/API.
- Ingestion skeleton: Federal Register + GDELT connectors.
- Store raw documents and normalized text.
- Basic dashboard shell.

**Output:** App runs locally; seed data loads; two connectors fetch data.

**Acceptance:** `docker compose up` works; seed script < 2 min; connectors return ≥ 5 documents each.

---

### Day 2 — Sunday, Oct 25: RAG and extraction

**Tasks:**
- Parser: PDF/HTML → structured text; preserve headings/articles.
- Semantic/variable chunking.
- Contextual retrieval (prepend doc/section context).
- Embeddings + pgvector; BM25 hybrid search.
- Reranker.
- Extractor Agent with structured JSON output.
- Citation storage (quote, URL, article, hash).
- Basic retrieval eval on 10 documents.

**Output:** RAG pipeline; extraction endpoint; citations in DB.

**Acceptance:** Given a regulation, return top 5 relevant chunks with citations; extraction JSON validates; citation precision ≥ 0.90 on sample.

---

### Day 3 — Monday, Oct 26: Graph, mapping, scoring

**Tasks:**
- Neo4j/Apache AGE graph schema and seed.
- Mapper Agent: obligation → policy/contract/supplier/control.
- Graph RAG query path.
- Scorer Agent: likelihood × impact, factors, confidence.
- Risk register API.
- EUR-Lex + OpenSanctions/UFLPA connectors.
- Entity resolution for suppliers/news.

**Output:** End-to-end from change → obligation → mapping → risk.

**Acceptance:** Demo change produces ≥ 3 obligations, ≥ 5 affected entities, risk score with factors.

---

### Day 4 — Tuesday, Oct 27: Remediation and approval UI

**Tasks:**
- Remediator Agent: actions, owners, deadlines, drafts.
- Approval workflow: approve/reject/assign/defer + rationale.
- Audit log.
- Risk detail page: evidence, graph, actions, approvals.
- Dashboard: risk register, filters, source health.
- Report generator (Markdown/PDF).
- Verifier Agent v1 (citation check).

**Output:** Demoable end-to-end workflow with human approval.

**Acceptance:** Approve/reject updates status; audit log records actor/time/rationale; report exports.

---

### Day 5 — Wednesday, Oct 28: Evals, guardrails, MCP, local models

**Tasks:**
- Build 30-item golden set (EU/US/Bangladesh).
- Run baselines and full pipeline; record metrics.
- Add RAGAS/DeepEval; regression script.
- PII redaction (Presidio); prompt-injection checks; citation enforcement.
- MCP servers: regulatory-feed, risk-graph, remediation.
- MCP clients: Postgres, Fetch, GitHub.
- Ollama local model path for one extraction task.
- LangSmith/Phoenix tracing; token/cost dashboard.
- Optional: 1-hour law student review of demo/disclaimers.

**Output:** Eval report, guardrails, MCP servers, traces, local model demo.

**Acceptance:** Eval report generated; citation precision ≥ 0.95 on golden set; MCP inspector shows tools; local model runs offline.

---

### Day 6 — Thursday, Oct 29: Deploy, polish, record

**Tasks:**
- Deploy frontend (Vercel), backend (Render/Fly.io), DB (Supabase/Neon), graph (Neo4j Aura).
- Cloudflare Tunnel for local demo fallback.
- Polish UI: empty states, loading, error handling, disclaimers.
- Figma final screens + architecture diagram.
- Record 2–3 minute demo video; edit; upload to YouTube (unlisted/public).
- Write GitHub README: overview, architecture, setup, demo, eval results, limitations.
- Add access note/demo credentials.

**Output:** Live URL, video, repo, Figma, README.

**Acceptance:** Live demo works from a clean browser; video shows real UI; README reproduces setup.

---

### Day 7 — Friday, Oct 30: Submission

**Tasks:**
- Fill all portal fields (Story, Proof, AI-Native Build, Data Lifecycle, Prompt Library, Team).
- Add links: GitHub, live demo, YouTube, Figma, 3 others (pitch deck, eval report, API docs).
- Add prompt library: master prompt + runtime prompts.
- Add access note.
- Verify team diversity fields (only if true).
- Internal review: read aloud, check character counts, check all required fields.
- Save draft.

**Output:** Complete draft submission.

**Acceptance:** 100% completeness; no missing required fields; links work.

---

### Day 8 — Saturday, Oct 31: Buffer and submit

**Tasks:**
- Final QA: live demo, video, repo, links, form.
- Fix any broken links or UI issues.
- Submit by **6:00 PM GMT+6**.
- Save confirmation screenshot/email.
- Post-submission: archive repo tag, backup video, export eval report.

**Output:** Submitted.

**Acceptance:** Confirmation received; backup artifacts stored.

---

## 4. Daily cadence

- **Morning (15 min):** Standup — what shipped, what's next, blockers.
- **Midday (10 min):** Demo check — does the end-to-end flow still work?
- **Evening (15 min):** Update `DECISIONS.md` session log; commit; push; tag.
- **Rule:** No new features after Day 5. Only polish, evals, and submission.

---

## 5. Cut list (pre-approved)

If behind schedule, cut in this order:
1. Bengali UI toggle.
2. Slack/email notifications.
3. Bangladesh Bank scraper.
4. Buyer-code questionnaire generator.
5. Cost dashboard.
6. "Explain this risk" chat.
7. Supplier portal.
8. Multi-model routing beyond 3 models.
9. Local model path (keep at least one local extraction demo).
10. Graph visualization (keep graph queries; simplify UI).

**Never cut:**
- Two data streams.
- Prioritized risk report.
- Remediation suggestions.
- Human approval.
- Citations/evidence.
- Audit log.
- Demo video.
- Submission fields.

---

## 6. Submission checklist

### Story
- [ ] Project name
- [ ] Elevator pitch
- [ ] Public summary
- [ ] Domain: JusticeSphere AI
- [ ] Challenge: Risk Sentinel
- [ ] Problem statement
- [ ] Solution description
- [ ] Target users
- [ ] Unique value
- [ ] Demo script
- [ ] Business model
- [ ] Impact

### Proof
- [ ] GitHub repo (public)
- [ ] Live demo URL
- [ ] YouTube video (2–3 min)
- [ ] Figma/design link
- [ ] 3 other links (pitch deck, eval report, API docs)
- [ ] Access note / demo credentials

### AI-Native Build
- [ ] Prompt library (master + runtime)
- [ ] Prompt strategy
- [ ] Token optimization
- [ ] AI stack selections
- [ ] Model use/routing
- [ ] RAG & memory
- [ ] Agent frameworks
- [ ] Fine-tuning/adaptation
- [ ] Evaluation methods
- [ ] Guardrails/safety/privacy
- [ ] AI-DLC process
- [ ] Build level (honest)
- [ ] Workflow automation
- [ ] Local/on-device LLMs
- [ ] Agentic frameworks
- [ ] Tunneling
- [ ] Anything else

### Data Lifecycle
- [ ] Sources
- [ ] Acquisition
- [ ] Parsing/processing
- [ ] Cleaning/enrichment
- [ ] Storage
- [ ] Visualization
- [ ] Analytics/delivery
- [ ] Training data
- [ ] Feedback loops
- [ ] Data quality
- [ ] Governance
- [ ] Privacy/security
- [ ] Lineage/observability

### Team
- [ ] Members and roles
- [ ] NRB status (if true)
- [ ] Female member (if true)
- [ ] Links
- [ ] Access notes

---

## 7. Demo video script (2:30)

| Time | Visual | Voiceover |
|---|---|---|
| 0:00–0:15 | Title, problem slide | "Exporters face hundreds of regulatory changes and supplier risks a year. Missing one can cost a shipment, a buyer, or a penalty." |
| 0:15–0:35 | Dashboard, source health | "Chowkidar monitors regulators, sanctions lists, and global news. Today: an EU CSDDD update, a UFLPA addition, and a supplier alert." |
| 0:35–1:05 | Change detail, evidence | "Chowkidar extracts the obligation, cites the article, and maps it to two policies and fourteen suppliers." |
| 1:05–1:30 | Graph, risk score | "The risk score explains likelihood, impact, and confidence. Four gaps need action." |
| 1:30–1:55 | Remediation + approval | "Chowkidar drafts five actions. The compliance lead approves two, rejects one, and assigns the rest. Every decision is logged." |
| 1:55–2:15 | Supplier alert | "A GDELT alert links to a sub-tier supplier. Chowkidar recommends enhanced due diligence and evidence requests." |
| 2:15–2:30 | Report + close | "From signal to signed action in minutes — with evidence, accountability, and an audit trail. Chowkidar: see the risk, approve the fix." |

**Production notes:**
- Record at 1080p, crisp audio.
- Show real UI, not slides, for at least 80% of the video.
- Use a clean demo dataset; avoid real company accusations.
- Include a disclaimer: "Chowkidar is compliance risk intelligence, not legal advice."
- Upload as unlisted or public; verify link in incognito.

---

## 8. Deployment and QA

### 8.1 Environments

- Local: Docker Compose (Postgres, Neo4j, Redis, backend, frontend, Ollama optional).
- Staging: Vercel preview + Render staging + Supabase staging.
- Production demo: Vercel + Render/Fly.io + Supabase/Neon + Neo4j Aura.
- Tunnel fallback: Cloudflare Tunnel to local.

### 8.2 QA checklist

- [ ] Sign up/login works.
- [ ] Demo credentials work.
- [ ] Seed data loads.
- [ ] Two connectors fetch data.
- [ ] Change detection works.
- [ ] Extraction returns citations.
- [ ] Graph view renders.
- [ ] Risk score displays factors.
- [ ] Remediation actions editable.
- [ ] Approve/reject works.
- [ ] Audit log records decisions.
- [ ] Report exports.
- [ ] Disclaimers visible.
- [ ] Mobile/desktop layouts acceptable.
- [ ] No console errors.
- [ ] Live URL works in incognito.
- [ ] Video link works.
- [ ] GitHub repo public and reproducible.

### 8.3 Fallbacks

- If a live API fails: use cached snapshots.
- If the live demo fails: use recorded video.
- If the graph DB fails: fall back to Postgres relational queries.
- If the external LLM fails: use local Ollama model.
- If deployment fails: use Cloudflare Tunnel to local.

---

## 9. Definition of done

- End-to-end demo runs in under 5 minutes.
- Two data streams visible.
- Prioritized risk report generated.
- Remediation actions generated and approved.
- Human-in-the-loop interface demonstrated.
- Evidence/citations visible.
- Audit log visible.
- Eval report with metrics.
- Live URL, GitHub, YouTube, Figma.
- Submission form 100% complete.
- Submitted before 6 PM GMT+6 on Oct 31.

---

## 10. Post-submission

- Tag repo `v0.1-submission`.
- Archive video and eval report.
- Backup database snapshot.
- Write a short retrospective.
- Prepare for final judging (Dec 26): polish, pilot feedback, pitch deck, live demo rehearsal.
