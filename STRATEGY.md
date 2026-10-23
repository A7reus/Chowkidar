# AI Builders Congress 2026 — Domain & Project Strategy

**Date:** 2026-10-23  
**Status:** Decision draft — no product code yet  
**Track:** Idea to Unicorn — Preliminary Submission  
**Deadline:** 2026-10-31, 11:59 PM GMT+6 (Bangladesh Standard Time)

**Update 2026-10-23:** Team confirmed strengths in AI/full-stack and data engineering, **no legal/compliance advisor**, and **no per-domain submission counts**. Decision: proceed with Chowkidar, positioned as compliance risk intelligence (not legal advice). See `DECISIONS.md`, `PRODUCT_SPEC.md`, `BUILD_PLAN.md`, and `prompts/MASTER_PROMPT.md`.

---

## 0. TL;DR

**Verdict:** JusticeSphere is a good contrarian choice. **Risk Sentinel is the right challenge inside it — but not as a generic "enterprise risk dashboard."**

**Build this:** an agentic **Regulatory & Supplier Risk Sentinel** for export-oriented supply chains. Working name: **Chowkidar** (or **Chowkidar** for a local brand). It monitors regulatory changes and supplier risk signals, maps them to a company's obligations, and turns them into evidence-backed remediation plans with human approval and an audit trail.

**Why this specific wedge:**
- It matches the official Risk Sentinel "specific ask" almost 1:1.
- It is a legal/compliance product, not a generic supply-chain ops tool.
- It has a strong Bangladesh beachhead (RMG, leather, agro-processing) and a global expansion story.
- It is demoable in 8 days with public data + a small synthetic company dataset.
- It naturally exercises the AI stack the preliminary auto-scoring rewards: multi-agent orchestration, contextual/graph RAG, MCP, local models, evals, guardrails, observability.

**Conditions:**
- **No legal advisor available:** mitigate with evidence-first design, primary-source citations, conservative scope, a verifier agent, human approval, and source-grounded evals. Position as compliance risk intelligence, not legal advice.
- Keep the MVP narrow: one persona, one risk domain, two external data streams, one approval workflow.
- Verify the "one master prompt" rule with the organizers before building. The MCP knowledge base says it applies to Idea to Unicorn; the portal wording may be more flexible.

---

## 1. What we know (and what is uncertain)

### 1.1 Sources used

| Source | What it gave us | Confidence |
|---|---|---|
| MCP server `cloudcamp://knowledge-base` | Submission guide, deadline, one-prompt rule, auto-scoring breakdown, form-field guidance | Medium — may be outdated |
| Public event API (`get_event_public_summary`) | 572 teams, 3,108 participants, 3 phases, event settings | High — live public data |
| Public `domains` and `challenges` tables | 10 domains, 50 main challenges, full challenge briefs and specific asks | High — live public data |
| Portal screenshots | Actual form tabs, required fields, completeness state | High |
| Public app code / default rubric | 5 × 20% final judging rubric | High — likely the default, but custom rubric may exist |

### 1.2 Key facts

- **Event:** International AI Builders Congress 2026, 26 December 2026, Daffodil International University, Dhaka.
- **Preliminary phase:** Idea to Unicorn — closes **31 October 2026, 11:59 PM GMT+6**.
- **Scale:** 572 teams, 3,108 participants across 10 domains and 50 challenges. Average ≈ 11 teams per challenge, but distribution is uneven.
- **Per-domain counts:** Not public. The leaderboard is disabled (`public_leaderboard: false`), and submission/team tables are RLS-protected. We cannot quantify saturation from outside; the analysis below is directional.
- **Final rubric (default):**
  - Innovation & AI-Native Design — 20%
  - Technical Excellence & Architecture — 20%
  - Business Value & Commercial Viability — 20%
  - Global Scalability & Real-World Impact — 20%
  - Responsible AI, Data Sovereignty & Presentation — 20%
- **Preliminary scoring:** The form's tabs show `AI-Native Build 0/110`, `Data Lifecycle 0/25`, `Proof 0/25`, `Story 0/30`, `Prompt Library 2 required`, `Team`. The MCP guide says the auto-scorer rewards stack completeness heavily. Treat the exact point values as guidance, not gospel.

### 1.3 The Risk Sentinel brief (official)

> **Risk Sentinel — Enterprise risk management**
>
> Risk Sentinel challenges builders to create AI-native governance systems that autonomously identify, monitor, and mitigate legal and regulatory exposure across complex global corporate structures. Solutions should leverage multi-agent orchestration for continuous compliance auditing and RAG-enhanced reasoning over massive jurisdictional legal corpora to predict liability before it manifests. The focus is on moving from reactive dashboards to proactive, agentic risk-remediation engines.
>
> **Specific ask:** Develop a functional AI agent prototype that autonomously monitors at least two distinct data streams to generate a prioritized risk audit report with automated remediation suggestions. The solution must demonstrate a clear "human-in-the-loop" interface for approving AI-generated risk mitigation actions.
>
> **Example data sources:** EDGAR, OpenLegalData.io, GDELT, Common Crawl, World Bank Open Data.
>
> **Example prompts:** multi-agent SEC + Slack insider-risk detection; Graph Document AI over nested ownership; vision agent scraping regulatory updates and updating SOPs; temporal contract-breach risk scoring; autonomous legal red-team for IP.

This brief is unusually specific. It tells us exactly what the demo must show:

1. **At least two distinct data streams** monitored autonomously.
2. **A prioritized risk audit report**.
3. **Automated remediation suggestions**.
4. **A clear human-in-the-loop approval interface**.

Any Risk Sentinel submission that does not visibly hit all four will underperform, regardless of how good the AI stack is.

---

## 2. Is JusticeSphere → Risk Sentinel optimal?

### 2.1 Domain saturation

**Hypothesis: JusticeSphere is one of the least saturated domains.**

Reasons:
- Legal/compliance tech has a domain-knowledge barrier. Most hackathon teams are generalist developers, not lawyers or compliance officers.
- It is less glamorous than Health, FinTech, Learn, Climate, or Commerce. Fewer teams self-select into it.
- The public domain record for JusticeSphere has **no `content` details** (no examples, data sources, specific ask), unlike FinSphere, CivicSphere, IndustrySphere, HealthSphere, etc. That is weak evidence that it was less promoted / less prepared, which may correlate with lower signups.
- The five JusticeSphere challenges are broad and enterprise-oriented, which tends to attract fewer student teams than consumer-facing challenges.

Counterpoints:
- Fewer teams can also mean fewer judges, less attention, or less organizational support. Verify with organizers.
- Legal-tech judges may be domain experts with a high bar. A generic LLM wrapper will be exposed quickly.
- If the domain is under-subscribed, the organizer might merge categories or reduce awards. Unlikely, but worth asking.

**What would change the answer:** If the portal or organizers show that JusticeSphere is actually crowded, or if the team cannot secure any legal/compliance domain advice, reconsider.

### 2.2 Challenge saturation inside JusticeSphere

| Challenge | Likely saturation | Why |
|---|---|---|
| **ContractMind** | **High** | Contract review/redlining is the classic legal-AI demo. Every legal-tech team can attempt it. |
| **Legal Copilot** | **High** | "ChatGPT for legal research" is the most obvious idea. Easy to prototype, hard to differentiate. |
| **ComplianceOS** | **Medium** | Regulatory change → action plan is a known GRC workflow; fewer teams than contract review, but still obvious. |
| **GovernanceIQ** | **Medium-low** | Corporate filings/ownership analysis is data-heavy; fewer product-minded teams. |
| **Risk Sentinel** | **Low** | Vague, enterprise, multi-source. Least obvious; most teams will avoid it because it is hard to scope. |

**Risk Sentinel is probably the least crowded challenge in the least crowded domain.** That is the core strategic case for your choice.

But "least crowded" is not the same as "optimal." The challenge is vague enough that many teams could submit a generic risk dashboard. The winning move is to make it **specific, evidence-linked, and workflow-native**.

### 2.3 Directional scorecard

Scores are 1–10, subjective, for discussion only.

| Option | Saturation (10 = low) | Demoability | Data access | Domain fit | AI depth | Local impact | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Justice / Risk Sentinel (narrowed)** | **9** | **8** | **7** | **9** | **9** | **9** | **8.5** |
| Justice / ComplianceOS | 7 | 8 | 8 | 9 | 8 | 8 | 8.0 |
| Justice / GovernanceIQ | 7 | 7 | 7 | 8 | 8 | 7 | 7.3 |
| Justice / ContractMind | 4 | 9 | 9 | 8 | 8 | 6 | 7.3 |
| Fin / FraudShield | 4 | 8 | 6 | 8 | 8 | 8 | 7.0 |
| Health / CareAnywhere | 3 | 7 | 5 | 8 | 8 | 9 | 6.7 |
| Infra / AgentOps | 5 | 7 | 9 | 7 | 10 | 6 | 7.3 |
| Civic / TrustID | 6 | 6 | 5 | 8 | 8 | 9 | 7.0 |
| Agri / FarmMarket | 6 | 7 | 6 | 8 | 7 | 9 | 7.2 |

### 2.4 Verdict

- **JusticeSphere:** 8.5/10. Good contrarian bet if the product is designed around source-grounded compliance operations rather than legal opinion.
- **Risk Sentinel (generic):** 6/10. Too broad; risks becoming a static GRC dashboard.
- **Risk Sentinel (narrowed to regulatory + supplier risk for export supply chains):** **9/10.** Strong fit, strong demo, strong local story, achievable MVP.

**Decision:** Stay in JusticeSphere, choose Risk Sentinel, and narrow it. The team has no legal advisor, so the product must be compliance risk intelligence — not legal advice — with citations, conservative language, and human approval.

---

## 3. What to build

### 3.1 Product concept

**Working name:** Chowkidar (the hundred-eyed watchman) — or **Chowkidar** (Bengali: প্রহরী, sentinel/guard) for a local-first brand.  
**Tagline:** *See the risk. Approve the fix.*  
**One-liner:** *Chowkidar is an agentic risk sentinel that monitors regulatory and supplier risk signals, maps them to your obligations, and turns them into approved remediation plans with an audit trail.*

**Target persona:**  
Ayesha, Head of Compliance at a 2,000-worker RMG exporter in Gazipur. She manages six buyer codes, three regulators, and 40 suppliers with a team of three. She tracks changes in email and Excel. A missed deadline can cost a shipment, a buyer relationship, or a penalty.

**Problem:**
- Regulations and buyer codes change across jurisdictions faster than manual tracking can handle.
- Supplier risk (forced labor, sanctions, environmental violations, financial distress) surfaces in news and audit reports, not in the ERP.
- GRC tools are static dashboards and checklists. They do not read unstructured legal text, reason over supplier networks, or drive remediation.
- Evidence is scattered; audits are painful; accountability is unclear.

**Solution:**
1. **Monitor** external streams: regulators, buyer codes, sanctions/watchlists, global news.
2. **Map** signals to the company's risk graph: obligations, policies, contracts, suppliers, factories, controls, owners.
3. **Prioritize** by likelihood × impact, with citations, confidence, and affected entities.
4. **Recommend** remediation: policy redlines, supplier questionnaires, evidence requests, owner/deadline tasks, board memo.
5. **Approve** through a human-in-the-loop workflow; log every decision; export an audit-ready report.

**Differentiation:**
- Not a chatbot — an **agentic remediation engine**.
- Not a static GRC dashboard — **continuous multi-source monitoring + graph reasoning**.
- Not a black box — **citations, confidence, evidence, human approval**.
- Built for **export supply chains**, not just head-office compliance. This is the wedge incumbents under-serve.

### 3.2 Why this wedge fits Risk Sentinel

| Risk Sentinel requirement | How Chowkidar satisfies it |
|---|---|
| Autonomously monitors ≥ 2 distinct data streams | Regulatory feeds (Federal Register, EUR-Lex, Bangladesh Bank/BGMEA) + risk signals (GDELT news, OpenSanctions, UFLPA) + internal documents |
| Prioritized risk audit report | Risk register scored by likelihood × impact, with evidence, affected entities, and confidence |
| Automated remediation suggestions | Policy redlines, supplier questionnaires, evidence requests, owner/deadline tasks, board report |
| Human-in-the-loop approval | Approve / reject / assign / request evidence UI; RBAC; immutable audit log |
| Multi-agent orchestration | Monitor → Extract → Map → Score → Remediate → Verify → Report |
| RAG over legal corpora | Contextual RAG, semantic chunking, hybrid search, reranking, graph RAG |
| Predict liability before it manifests | Leading indicators: regulatory changes, supplier signals, sanctions additions, news events |

### 3.3 MVP scope (8 days)

**Must have:**
- Risk graph onboarding: upload supplier list, policies, contracts (CSV/PDF) or load demo data.
- Four connectors:
  - Federal Register API (US regulatory changes)
  - EUR-Lex RSS/SPARQL (EU regulatory changes, e.g. CSDDD/CSRD)
  - GDELT API (global news signals)
  - OpenSanctions / UFLPA entity list (sanctions/forced-labor signals)
  - Optional: curated Bangladesh Bank/BGMEA snapshot
- Seven-agent pipeline: Monitor, Extract, Map, Score, Remediate, Verify, Report.
- Dashboard: risk register, risk detail with evidence, supplier graph, approval queue, audit log.
- Report export: board-ready Markdown/PDF.
- Evals: 30-item golden set, RAGAS/DeepEval, citation accuracy, regression script.
- Guardrails: PII redaction, citation enforcement, prompt-injection checks, legal disclaimer, human approval.
- MCP: three custom servers (regulatory feed, risk graph, remediation) + three external servers (Postgres, Fetch, GitHub).
- Local model path: Ollama + Qwen2.5/Llama 3.1/DeepSeek-R1 for sensitive documents and offline demo.
- Observability: LangSmith/Phoenix traces, token/cost per agent, source freshness.
- Deployment: Vercel (frontend), Render/Fly.io (backend), Supabase/Neon, Neo4j Aura; Cloudflare Tunnel for local demo.
- Submission assets: GitHub, live demo, YouTube video, Figma/architecture diagram, 3 other links.

**Nice to have (only if time):**
- Bangladesh Bank circular scraper.
- Buyer-code questionnaire generator.
- Multilingual UI (English/Bengali).
- Slack/email approval notifications.
- Cost dashboard.
- “Explain this risk” chat over the risk graph.

**Non-goals for the MVP:**
- Full legal research / case-law prediction.
- Contract drafting or redlining beyond policy redlines.
- ERP/SAP integration.
- Multi-tenant billing.
- Mobile app.
- All jurisdictions / all risk types.
- Automated legal decisions without human approval.

### 3.4 Demo script (3 minutes)

**0:00–0:20 — Problem**
> "A Bangladeshi exporter faces hundreds of regulatory changes a year across the EU, US, and Bangladesh — plus buyer codes, sanctions lists, and supplier news. Missing one can cost a shipment, a buyer relationship, or a penalty. Compliance teams track this in email and Excel."

**0:20–0:50 — Monitor**
> Dashboard: "Chowkidar monitors four streams. Today: an EU CSDDD update, a new UFLPA entity, a GDELT alert on a supplier, and a Bangladesh Bank circular."
> Show source freshness, volume, and relevance filters.

**0:50–1:40 — Detect, map, prioritize**
> Click the EU CSDDD update. Chowkidar extracts three obligations, maps them to two internal policies and 14 suppliers, flags four gaps, and cites the exact articles. Risk score: 87/100. Show the supplier graph and the "why this matters" explanation.

**1:40–2:20 — Remediate, approve**
> Chowkidar proposes five actions with owners and deadlines: update the supplier code, issue a questionnaire to four suppliers, request evidence from two, update the board memo, and schedule a training. Approve two, reject one with a reason, assign the rest. Show the audit log and the human-in-the-loop approval.

**2:20–2:50 — Second stream**
> GDELT alert: a sub-tier supplier in the network has a labor strike. Chowkidar links the entity, shows evidence, and recommends an enhanced due-diligence task. Approve it.

**2:50–3:00 — Close**
> "From signal to signed action in minutes — with evidence, accountability, and an audit trail. Chowkidar: see the risk, approve the fix."

### 3.5 Architecture

```
External sources                    Internal sources
─────────────────                   ─────────────────
Federal Register API                Supplier list (CSV)
EUR-Lex RSS/SPARQL                  Policies (PDF/DOCX)
GDELT API                           Contracts (PDF)
OpenSanctions / UFLPA               Audit reports
Bangladesh Bank / BGMEA (curated)   Prior risk decisions
        │                                   │
        └──────────────┬────────────────────┘
                       ▼
              Ingestion & parsing
        (n8n / Temporal, Unstructured, OCR)
                       ▼
          Cleaning, dedup, entity extraction
                       ▼
        ┌──────────────┴──────────────┐
        ▼                             ▼
  Postgres + pgvector            Neo4j / Apache AGE
  (documents, chunks,            (suppliers, buyers,
   embeddings, tasks)             factories, obligations,
                                  policies, controls)
        └──────────────┬──────────────┘
                       ▼
              Retrieval layer
   Hybrid search + reranking + graph traversal
                       ▼
              Agent pipeline (LangGraph)
   Monitor → Extract → Map → Score → Remediate → Verify → Report
                       ▼
              Risk register + approval UI
                       ▼
         Audit log + board report + eval feedback
```

**Models and routing:**
- Claude Sonnet 4.5 — long-context legal reasoning, report drafting.
- GPT-5.1 / o4-mini — structured extraction, tool use.
- Gemini 2.5 Flash — cheap classification, multilingual.
- DeepSeek-R1 / Qwen2.5 via Ollama — sensitive internal docs, offline demo.
- Llama 3.3 via Groq/Together — fallback.
- LiteLLM router — cost/latency/quality routing, fallbacks, token accounting.

**RAG:**
- Contextual retrieval: prepend document/chunk context before embedding.
- Semantic/variable chunking.
- Hybrid search: BM25 + dense embeddings.
- Reranking: BGE or Cohere.
- Graph RAG: supplier → factory → buyer → obligation → policy → control.
- Memory: prior risk decisions, approvals, and evidence.

**Agents:**
- **Monitor:** polls sources, dedups, classifies relevance, detects changes.
- **Extractor:** extracts obligations, entities, dates, penalties, citations.
- **Mapper:** maps obligations/signals to policies, contracts, suppliers, controls.
- **Scorer:** likelihood × impact, explains factors, assigns confidence.
- **Remediator:** drafts actions, owners, deadlines, policy redlines, questionnaires.
- **Verifier:** citation check, contradiction check, LLM-as-judge.
- **Reporter:** generates the prioritized audit report and board memo.

**MCP:**
- Built: `regulatory-feed`, `risk-graph`, `remediation`.
- Used: `postgres`, `fetch`, `github`.
- Transports: Streamable HTTP for hosted servers, stdio for local Postgres/GitHub.

**Data lifecycle:**
- Sources → acquisition → parsing → cleaning/enrichment → storage → analytics → feedback.
- Storage: Postgres (Supabase/Neon), pgvector, Neo4j Aura/Apache AGE, Supabase Storage/S3.
- Analytics: custom dashboard + Metabase/Superset optional.
- Lineage: LangSmith/Phoenix traces + OpenLineage events.
- Feedback: approvals/rejections feed the eval set and retrieval tuning.

**Evals:**
- Golden set: 30 regulatory changes (10 EU, 10 US, 10 Bangladesh) with gold obligations, affected entities, risk levels, and citations.
- 20 supplier risk signals with gold relevance/severity.
- Metrics: extraction F1 ≥ 0.85, citation precision ≥ 0.95, mapping accuracy ≥ 0.80, risk ranking NDCG@5 ≥ 0.85, remediation usefulness ≥ 4/5.
- Regression: CI on every prompt/model change; results stored in `evals/results/`.

**Guardrails:**
- PII redaction (Presidio) before external LLM calls; local models for sensitive docs.
- Prompt-injection detection (Llama Guard/Guardrails AI).
- Citation enforcement: every claim must cite a source; otherwise "insufficient evidence."
- Legal disclaimer: "risk intelligence, not legal advice"; human approval required.
- RBAC, audit log, encryption, rate limits, data retention.
- No defamatory claims: "risk signal" language, evidence links, right of reply, human review.

**Observability:**
- LangSmith/Phoenix traces per agent.
- Token/cost per risk assessment.
- Source freshness and ingestion lag.
- Approval SLA and audit trail.

### 3.6 Tech stack

> **Proposal only.** Every stack choice below requires user approval before implementation. See `DECISIONS.md`.

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 15 + TypeScript + Tailwind + shadcn/ui | Fast, demo-friendly, Vercel deploy |
| Backend | FastAPI (Python) | AI ecosystem, async, easy workers |
| Orchestration | LangGraph | Stateful multi-agent workflows, human-in-the-loop |
| Workflow automation | n8n | Connectors, scheduling, visible automation |
| Database | Postgres (Supabase/Neon) | Relational data, auth, storage |
| Vector | pgvector | Simple, sufficient for MVP |
| Graph | Neo4j Aura / Apache AGE | Supplier/obligation graph, Graph RAG |
| Queue/cache | Redis | Rate limits, background jobs |
| Models | Claude, GPT, Gemini, DeepSeek, Qwen/Llama | Multi-model routing, local fallback |
| Embeddings | BGE-M3 / OpenAI / Cohere | Multilingual, cost-effective |
| Reranker | BGE-reranker / Cohere | Retrieval quality |
| Evals | RAGAS, DeepEval, Promptfoo | RAG and agent quality |
| Observability | LangSmith / Phoenix | Traces, cost, latency |
| Deployment | Vercel + Render/Fly.io + Supabase | Fast, cheap, reliable |
| Tunneling | Cloudflare Tunnel | Local demo to public URL |
| CI/CD | GitHub Actions + Docker Compose | Reproducible builds |

### 3.7 Mapping to the preliminary scoring

Only claim what you actually implement. The auto-scorer may be automated, but judges can audit the repo and demo.

| Category | How Chowkidar earns it |
|---|---|
| Links & deliverables | YouTube demo (10), GitHub (2), live demo (1), Figma/architecture (1), 3 other links (3) |
| Team diversity | 5 members, NRB, female — only if true |
| LLM selection | Claude, GPT, Gemini, DeepSeek, Qwen/Llama |
| RAG | Contextual RAG, semantic chunking, hybrid search, reranking, graph RAG, memory |
| Frontend AI tools | v0/Cursor/Claude Artifacts for scaffolding and UI |
| Automation | n8n ingestion workflows + LangGraph agents |
| Local LLM | Ollama + Qwen2.5, Llama 3.1, DeepSeek-R1 |
| Agent frameworks | LangGraph primary, CrewAI/OpenAI Agents SDK for a sub-workflow |
| AI-DLC | BMAD-METHOD / Spec-Kit / Cursor Rules, documented |
| MCP | 3 built servers + 3 external servers, transports documented |
| Data lifecycle | 5-stage pipeline, Postgres/pgvector/Neo4j/S3, dashboard, lineage |
| Tunneling | Cloudflare Tunnel + docs |
| Evals & guardrails | RAGAS/DeepEval, Presidio, Llama Guard, citation enforcement |

### 3.8 Mapping to the final 5 × 20 rubric

| Criterion | Chowkidar story |
|---|---|
| **Innovation & AI-Native Design** | Agentic risk-remediation engine, not a dashboard; graph + regulatory diff + evidence-linked actions |
| **Technical Excellence & Architecture** | Multi-agent LangGraph, hybrid/graph RAG, model routing, MCP, evals, observability, audit trail |
| **Business Value & Commercial Viability** | Compliance cost and penalty avoidance; SaaS per compliance seat + per supplier monitored; beachhead in Bangladesh export sector; expansion to other export hubs and GRC integrations |
| **Global Scalability & Real-World Impact** | 5,000+ RMG factories in Bangladesh; millions of export workers; replicable in Vietnam, India, Turkey; improves labor/environmental compliance and supply-chain transparency |
| **Responsible AI, Data Sovereignty & Presentation** | Citations, confidence, human approval, PII redaction, local models, no legal advice, audit trail, clear demo |

### 3.9 Business model and moat

**Business model:**
- SaaS: per compliance seat + per supplier monitored.
- Enterprise annual contracts with implementation/regulatory mapping.
- API/white-label for GRC platforms and buyer-driven supplier programs.
- Land-and-expand: one business unit → global supplier network → other risk domains.

**Moat:**
- Jurisdiction-specific obligation graph and evidence corpus.
- Workflow data: approvals, rejections, remediation outcomes.
- Local partnerships (BGMEA/BKMEA, compliance consultants, buyers).
- Audit trail and integrations create switching costs.

**Competition:**
- Diligent, ComplyAdvantage, FiscalNote, OneTrust, Sayari, Vanta, Drata, Regology.
- Gap: static dashboards, expensive enterprise tools, weak emerging-market regulatory coverage, no agentic remediation across supply chains.
- Our wedge: export supply chains in emerging markets; evidence-linked remediation; local regulatory graph; human-in-the-loop.

**Validation plan:**
- 10 interviews with compliance/legal leads at RMG/leather/agro exporters.
- 3 letters of intent or pilot commitments.
- 1 design-partner pilot with a BGMEA member.
- Mentor feedback from JusticeSphere judges.

---

## 4. Execution plan

### 4.1 8-day plan

| Day | Date | Focus | Output |
|---|---|---|---|
| 0 | Fri Oct 23 | Decide scope, roles, name; confirm no-advisor mitigations; verify one-prompt rule; write master prompt | Approved strategy, team roles, master prompt v1 |
| 1 | Sat Oct 24 | Scaffold repo, auth, DB schema, risk graph, demo data, ingestion skeleton | Running app, schema, seed data |
| 2 | Sun Oct 25 | Parsing, embeddings, hybrid search, contextual/semantic chunking, graph RAG | RAG pipeline, retrieval eval |
| 3 | Mon Oct 26 | Agents: Monitor, Extract, Map, Score, Remediate, Verify; approval UI | End-to-end risk workflow |
| 4 | Tue Oct 27 | Dashboard, risk register, evidence view, supplier graph, report export | Demoable UI |
| 5 | Wed Oct 28 | Evals, guardrails, observability, model routing, local models, MCP servers | Eval report, MCP servers, traces |
| 6 | Thu Oct 29 | Polish, deploy, Cloudflare Tunnel, record video, GitHub README, Figma | Live demo, video, repo, design link |
| 7 | Fri Oct 30 | Fill submission form, prompt library, all text fields, links, team diversity | Complete draft submission |
| 8 | Sat Oct 31 | Buffer, QA, dry run, submit by 6 PM GMT+6 | Submitted |

**Rule:** Submit by 6 PM, not 11:59 PM. Portals fail under load.

### 4.2 Master prompt plan

The MCP guide says Idea to Unicorn requires **one master prompt** that generates or initializes the entire system, followed only by confirmation triggers. Treat this as a hard constraint until the organizers say otherwise.

**Master prompt modules (required):**
1. Core product & AI instructions: concept, users, features, journeys, demo persona.
2. Data architecture: schemas, entities, vector store, graph, pipelines.
3. Admin module: users, roles, RBAC, analytics, settings.
4. Security module: auth, rate limits, encryption, PII, prompt injection, audit.
5. Documentation module: architecture, API, install, runbook.
6. Audit reporting: logs, token usage, compliance checks, report templates.
7. Presentation & pitch deck: slide structure, value prop, market, demo script.
8. Deployment: Docker, CI/CD, env vars, Cloudflare Tunnel, Vercel/Render.

**Process:**
- Write `prompts/master.md` as the single source of truth.
- Execute it once with an AI coding tool (Claude Code/Cursor) to generate the scaffold.
- Record the execution log and any confirmation triggers in `docs/build-log.md`.
- Store runtime system prompts in `prompts/runtime/` as generated artifacts.
- If the rule allows iteration, document exactly what was changed and why. Do not misrepresent the build level.

**Open question:** Ask the organizers whether the one-prompt rule applies to the entire build or only the prompt challenge. The portal wording and the MCP guide may differ.

### 4.3 Submission checklist

**Story tab:**
- Project name
- Elevator pitch
- Public summary
- Domain: JusticeSphere AI
- Challenge: Risk Sentinel
- Problem statement
- Solution description
- Target users
- Unique value proposition
- Demo script / user journey
- Business model
- Impact

**Proof tab:**
- GitHub repository (public, README, setup, architecture)
- Live demo URL
- YouTube video (2–3 min, crisp audio, real UI)
- Figma/design link (wireframes + architecture)
- 3 other links (pitch deck, eval report, API docs)
- Access note (demo credentials)

**AI-Native Build tab:**
- Product concept
- Prompt library (master prompt + runtime prompts)
- Prompt strategy
- Token optimization
- AI stack selections
- Model use and routing
- RAG & memory
- Agent frameworks & orchestration
- Fine-tuning/adaptation
- Evaluation & quality measures
- Guardrails, safety & privacy
- AI-DLC process
- Build level (honest)
- Workflow automation
- Local/on-device LLMs
- Agentic frameworks
- Tunneling
- Anything else

**Data Lifecycle tab:**
- Data sources
- Acquisition methods
- Parsing/processing
- Cleaning/enrichment
- Storage targets
- Visualization
- Analytics/delivery
- Training data
- Feedback loops
- Data quality
- Governance/compliance
- Privacy/security
- Lineage/observability

**Prompt Library tab:**
- Master prompt (the one)
- System prompts (runtime, generated)
- Chain-of-thought / reasoning prompts
- Eval/judge prompts

**Team tab:**
- Members, roles, skills
- NRB status (only if true)
- Female member (only if true)
- GitHub/LinkedIn links
- Access notes

### 4.4 Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Scope creep | High | High | MVP non-goals; one persona, one workflow, two streams |
| No legal/compliance advisor | High | High | Evidence-first design, primary-source citations, verifier agent, conservative scope, disclaimers, human approval, source-grounded evals; optional 1-hour law-student review |
| Data source API changes/rate limits | Medium | Medium | Cache; curated snapshots; fallback data |
| Legal accuracy/hallucination | Medium | High | Citation enforcement; verifier agent; golden set; human review |
| Defamation/false positives | Low | High | "Risk signal" language; evidence links; right of reply; no accusations |
| Demo failure | Medium | High | Recorded video; Docker Compose local fallback; seed data |
| Model cost/latency | Medium | Medium | Router; caching; local models; small models for classification |
| One-prompt rule ambiguity | High | Medium | Ask organizers; keep build log; design master prompt carefully |
| Saturation assumption wrong | Medium | Medium | Check portal/organizers; pivot to ComplianceOS if needed |
| Team burnout | Medium | High | Buffer day; prioritize; cut nice-to-haves |
| Judge mismatch (seen as supply chain, not legal) | Medium | Medium | Emphasize legal obligations, compliance buyer, audit evidence, Risk Sentinel brief mapping |

---

## 5. Decision needed today

1. **Confirm the wedge:** Regulatory & Supplier Risk Sentinel for export supply chains. Yes/no.
2. **Legal/compliance advisor:** Not available. Confirm the mitigation plan (evidence-first, conservative scope, human approval, optional 1-hour beta review).
3. **Team roles:** Who owns frontend, backend/AI, data, design, pitch, submission?
4. **Time commitment:** How many hours/day for the next 8 days?
5. **Name:** Chowkidar vs Chowkidar vs another name.
6. **One-prompt rule:** Can you ask the organizers/WhatsApp group today?
7. **Per-domain counts:** Already confirmed unavailable; proceed with directional saturation analysis.

---

## 6. What not to build

- A generic "ChatGPT for legal" or "ChatGPT for risk" chatbot.
- A contract-review clone (ContractMind is crowded; you chose Risk Sentinel).
- A static GRC dashboard with no agentic remediation.
- A product that makes legal decisions without human approval.
- A product that claims to cover all jurisdictions and all risk types in the MVP.
- A product that scrapes personal data or makes unverified accusations about companies.

---

## 7. Bottom line

Your instinct is good: **JusticeSphere → Risk Sentinel is likely a better expected-value bet than the crowded Health/Fin/Learn/Commerce domains.** But the challenge is broad, and a generic entry will be forgettable. The winning move is to own a **specific, high-stakes workflow**: regulatory and supplier risk for export supply chains, with evidence-linked remediation and human approval.

Build **Chowkidar**. Keep it narrow. Make the demo undeniable. Max the AI-native stack honestly. Stay evidence-first and conservative. Submit early.
