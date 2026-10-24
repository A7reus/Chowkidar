# Competition Context — International AI Builders Congress 2026

**Last captured:** 2026-10-23  
**Purpose:** durable record of the official competition context, submission form, scoring signals, and the authoritative domain/challenge list. This file exists so a context-window reset does not lose the event requirements.

**Authority order**

1. The official submission portal and current event announcements.
2. The user-supplied domain/challenge list in this file. It is newer than the MCP knowledge base.
3. The MCP knowledge base and the captured screenshots.

> If older MCP content conflicts with the domain/challenge list below, **use the list below**.

---

## 0. Bottom line for Chowkidar

- **Track:** Idea to Unicorn
- **Domain:** JusticeSphere AI
- **Challenge:** Risk Sentinel
- **Preliminary deadline:** 2026-10-31, 11:59 PM GMT+6 (Bangladesh Standard Time)
- **Target submission:** 2026-10-30, leaving 2026-10-31 as buffer
- **Official portal:** <https://cloudcampbd.com>

The official guide **does not say “demo only.”** It explicitly asks for:

> “production-grade, AI-native applications, automated pipelines, and scalable startups”
>
> “functional, deployed AI applications solving real-world problems”
>
> “live interactive demos”

It also awards points for a **Live Demo URL**, deployment/tunneling, MCP integration, RAG, local models, agent frameworks, AI-DLC, evaluation, guardrails, and data-lifecycle documentation.

**Therefore:** submit a **deployed, working, judge-accessible demo** with truthful disclosures. That is different from pretending to be a full commercial compliance platform. Add the score-bearing features that are actually implemented and demonstrable; do not check boxes for capabilities we do not have.

---

## 1. Official MCP server — access notes

The event supplied an MCP server with a private knowledge-base resource.

- **Base host:** `https://cloudcamp-bd-mcp.equisaas-bd.com`
- **Endpoint pattern:** `/api/sse/<event-access-token>`
- **Server identity:** `cloudcamp-mcp`, version `1.29.0`
- **Protocol observed:** `2025-06-18`
- **Tools:** none (`tools/list` returned an empty list)
- **Prompts:** none
- **Resource:** one resource, `cloudcamp://knowledge-base`
- **Resource description:** “The complete, exhaustive, A-to-Z context for the AI Builders Congress 2026.”
- **Resource MIME type:** `text/plain` (the content is actually an HTML document)

The full event token and a local raw copy are intentionally **not committed** to this public repository. They are stored in the gitignored local note:

```text
docs/private/competition-context.local.md
```

### How to connect

A plain `GET` with `Accept: text/event-stream` only produced keepalive `: ping` lines. The working path was a **POST JSON-RPC 2.0 request to the same SSE URL**:

```http
POST /api/sse/<event-access-token>
Content-Type: application/json
Accept: application/json, text/event-stream
```

Example initialize payload:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": { "name": "chowkidar-context", "version": "0.1" }
  }
}
```

The response is an SSE-framed JSON-RPC message:

```text
event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}
```

Useful calls:

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"resources/list","params":{}}
{"jsonrpc":"2.0","id":4,"method":"resources/read","params":{"uri":"cloudcamp://knowledge-base"}}
```

The returned HTML was converted to text for analysis. The local raw copies are:

```text
docs/private/cloudcamp-kb-2026-10-23.html
docs/private/cloudcamp-kb-2026-10-23.txt
```

---

## 2. Official knowledge-base summary

### Event and objectives

The guide describes the event as a global hackathon for AI developers, prompt engineers, and entrepreneurs. Its core objectives:

1. Build functional, deployed AI applications solving real-world problems.
2. Implement agentic workflows, retrieval-augmented generation (RAG), and Model Context Protocol (MCP) integrations.
3. Demonstrate rigorous AI Development Lifecycle (AI-DLC) methodology and clean engineering.
4. Deliver pitch-ready documentation and live interactive demos.

### Tracks

- **Idea to Unicorn**
- **Zero to Launch**

### Preliminary deadline

**October 31, 2026, 11:59 PM GMT+6.** Submissions go through the official portal.

### Single master prompt rule

For the Zero to Launch and Idea to Unicorn prompt challenges, the guide states a **one-prompt-only** rule: one comprehensive master prompt must generate or initialize the entire system architecture, modules, documentation, and deployment flow.

The master prompt must cover all eight modules:

1. Core product and AI instructions — concept, target users, features, journeys, demo persona.
2. Data architecture — schemas, models, vector store, pipelines.
3. Admin module — user management, RBAC, analytics, settings.
4. Security module — authentication, rate limiting, encryption, vulnerability guardrails.
5. Documentation module — architecture, API reference, installation.
6. Audit reporting — audit logging, token usage, compliance checks.
7. Presentation and pitch deck — slide structure, value proposition, market analysis.
8. Deployment requirements — infrastructure, Docker, CI/CD, environment configuration.

After the master prompt executes, permitted user interaction is limited to explicit confirmation triggers such as “Click to approve,” “Click to continue,” “Click to proceed,” “Yes,” “Continue,” and “Deploy.”

Chowkidar’s master prompt is `prompts/MASTER_PROMPT.md` v1.0. The build log is `docs/BUILD_LOG.md`.

---

## 3. Official submission form — fields and points

The guide’s field specification is reproduced below. The portal screenshots show additional structured fields (especially the AI-Native Build and Data Lifecycle tabs), so treat this as the minimum field set.

| Field | Requirement | Max points | Notes |
|---|---|---:|---|
| Project title | Required string | — | Clear, memorable name |
| Tagline / elevator pitch | Required string | — | One sentence |
| YouTube video URL | Valid YouTube link | **10** | 2–3 minutes; working software UI, features, workflow; crisp audio |
| GitHub repository URL | Valid public GitHub link | **2** | Source, README, setup/config |
| Live demo URL | Valid public URL | **1** | App running on the internet |
| Figma / design link | Valid URL | **1** | Mockups, wireframes, or architecture diagrams |
| Other links | Up to 3 URLs | **3** | 1 point each |
| Access note | Optional text | — | Test accounts or credential instructions |
| Team composition | 1–5 members | **5** | 1 point per registered member, capped at 5 |
| NRB member bonus | Boolean | **1** | At least one Non-Resident Bangladeshi member |
| Female member bonus | Boolean | **1** | At least one female registered member |
| Prompt strategy | Tiered description | **5** | System prompts, chain-of-thought structures |
| Token optimization notes | ≥ 50 chars | **3** | Compression, caching, pruning, routing |
| AI-DLC process notes | ≥ 100 chars | **3–4** | AWS Kiro, BMAD-METHOD, Spec-Kit, Cursor Rules, etc. |
| Agent / orchestration notes | ≥ 80 chars | **2** | Multi-agent execution, tool invocation, decision loops |
| Fine-tuning / adaptation notes | ≥ 80 chars | **2** | LoRA, instruction tuning, dataset curation |
| Evaluation and quality methods | ≥ 80 chars | **3** | Accuracy measurement, LLM-as-judge, benches, evals |
| Guardrails / safety / privacy | ≥ 80 chars | **3** | Sanitization, PII redaction, moderation |
| Tunneling usage notes | ≥ 80 chars | **2** | Cloudflare Tunnel, ngrok, localtunnel |
| Data quality measures | ≥ 80 chars | **2** | Validation, deduplication, schema enforcement |
| Privacy and compliance notes | ≥ 80 chars | **2–3** | Storage, consent, security standards |
| Lineage and observability notes | ≥ 80 chars | **2** | Logging, tracing, telemetry, lineage |

### Portal screenshots show these extra structured areas

The form is more than a text box. It asks for structured disclosure across tabs:

- **AI Build Story**
- **Prompt Strategy**
- **Token Optimization**
- **Workflow Automation**
- **AI Models Used**
- **Local / Open-Source LLMs**
- **RAG & Retrieval**
- **Tools & Agents**
- **AI-DLC & Engineering**
- **MCP usage**
- **Agent frameworks**
- **Fine-tuning / adaptation**
- **Evaluation and quality**
- **Guardrails, safety and privacy**
- **Frontend AI tools** (up to 5)
- **Workflow automation tools** (up to 5)
- **Build Level** and a longer **Build Story**
- **Data sources**, acquisition, types, storage, quality, privacy, lifecycle, lineage, governance, open-source stack, outbound APIs, pipeline orchestration, cost/performance
- **Publicly hosted environment / deployment**
- **Local environment publishing / tunneling** options including ngrok, Cloudflare Tunnel, Tailscale Funnel, localtunnel, bore, Serveo, Pagekite, GitHub Codespaces port forwarding, and others
- **Team** tab

The form uses character minimums such as 50, 80, 100, 150, 200, and 250 characters. Empty fields can make the submission look incomplete even when the underlying project is strong.

---

## 4. Auto-scoring signals from the MCP guide

The guide says: “Auto-Scoring Evaluator Enabled” and “Maximizing points across all scoring modules guarantees top placement on the preliminary leaderboard.”

### Category weights

| Category | Published max |
|---|---:|
| Links & Deliverables | 15 |
| Team Diversity | 7 |
| AI Stack, RAG & Models | 110+ |
| Data Lifecycle & Pipelines | 25 |
| MCP Integration & Transports | 20+ |
| Environment & Tunneling | 6 |

### Itemized signals

| Category | Signal | Points |
|---|---|---:|
| AI stack | At least one LLM listed | 5 |
| RAG | 1 point each for Naive RAG, Vector DB, Contextual RAG, Semantic Chunking, Late Interaction, Graph RAG | Max 5 |
| RAG bonus | Contextual RAG (Anthropic-style) | 5 |
| RAG bonus | Variable / semantic chunking | 3 |
| RAG bonus | Contextual RAG + variable chunking combo | 3 |
| RAG bonus | Graph RAG / knowledge graph | 5 |
| Frontend AI tools | 1 point each (Lovable, v0, Bolt.new, Cursor, Claude Artifacts, Gemini Canvas, ChatGPT Canvas) | Max 5 |
| Automation tools | 1 point each (n8n, Zapier, Make, Airflow, Temporal, Dagster, Prefect, LangGraph, Windmill, Activepieces) | Max 4 |
| Automation bonus | n8n workflow automation | 2 |
| Local LLM runtimes | 1 point each (Ollama, LM Studio, vLLM, llama.cpp, Apple MLX, GPT4All, TGI, TensorRT-LLM) | Max 3 |
| Local LLM bonus | Ollama runtime | 2 |
| Local models run | 2 points per local model (Kimi, DeepSeek, GLM, Llama 3, Qwen, etc.) | Max 8 |
| Agent frameworks | 1 point each (Hermes, OpenClaw, LangGraph, CrewAI, AutoGen, OpenAI Swarm, OpenAI Agents SDK, Letta) | Max 5 |
| AI-DLC frameworks | 1 point each (AWS Kiro, AWS AI-DLC, BMAD-METHOD, Spec-Kit, Cursor Rules, Cline Memory Bank) | Max 3 |
| MCP built | 1 point per MCP server built by the team | Max 3 |
| MCP used | 1 point per external MCP server integrated | Max 3 |
| MCP architecture | Transports (SSE/Stdio), clients/hosts disclosure, reuse notes | 6 |
| Tunneling | Publishing a local environment to the internet (ngrok, Cloudflare Tunnel) | 4 |

> Arithmetic note: the guide’s category ceilings and itemized rows do not reconcile exactly (for example, the listed link items sum to 17 while the category says 15; the itemized AI-stack rows sum to less than the stated 110+). Use this as a **priority map**, not a precise ledger. The live portal may compute differently.

### The guide’s own 100% checklist

The guide tells participants to:

- Upload a crisp 2–3 minute YouTube video showing real working software.
- Make the GitHub repository public with a complete README and setup steps.
- Deploy to Vercel/Render/Railway and include Figma/design links.
- Ensure the single master prompt covers all eight modules.
- Meet every character minimum.
- Check off all used LLMs, RAG methods, frontend builders, workflow tools, and agent frameworks.
- Include Ollama/local-model details if applicable.
- Explicitly list built and used MCP servers.
- Document Cloudflare Tunnel/ngrok deployment details.
- Verify team registration, NRB status, and gender indicators.

This is the clearest evidence that **deployment and completeness are part of the intended preliminary submission**, not optional polish.

---

## 5. Portal screenshot review

Captured in `preli-submission-ss/` (local-only, gitignored).

### Observed form state

- New Submission screen for **International AI Builders Congress**.
- Team: **JU_StackMind**.
- Phase: **Idea to Unicorn — Preliminary Submission**.
- Submission completeness: **0/9 required · 0%** because the form was blank during capture, not because the project is incomplete.
- Tabs: **Story /30**, **Proof /25**, **AI-Native Build /10**, **Data Lifecycle /25**, **Prompt Library /2**, **Team**.
- The **Proof** and **Prompt Library** tabs say “Save the submission first” before links/build provenance can be added.
- The submit button is disabled until the required fields are filled.

### Required fields shown by the portal

1. Project Name
2. Elevator Pitch
3. Public Summary
4. Problem Statement
5. Solution Description
6. Data & AI Provenance
7. Tooling & IDE
8. YouTube Video
9. Demo / Live Links

**Domain** and **Challenge** are dropdowns without a visible red asterisk in the captured screenshots, but they should be filled because the project maps directly to JusticeSphere AI → Risk Sentinel.

### What the form is actually testing

It is a **proof and disclosure form**:

- Can the team explain the problem and solution?
- Is there a working demo and a public repository?
- Can the team show how AI was used to build the product and how AI runs inside it?
- Is there a real data lifecycle, not just a prompt wrapper?
- Are claims backed by links, screenshots, videos, and code?

It is **not** asking for a SOC 2 report, multi-tenant billing, a legal opinion, or a production SLA. It is also **not** saying a local-only demo is sufficient. The live-demo and deployment fields make that clear.

---

## 6. Authoritative domains and challenges

The user supplied this list on 2026-10-23. It supersedes any older domain/challenge list from the MCP server or cached notes.

### FoodSphere AI

Intelligent, safe, low-waste food systems from farm to consumer.

- Future Foods
- Smart Food Chain
- Food Waste Zero
- Nutrition Intelligence
- Food Safety Sentinel

### HealthSphere AI

Accessible, ethical, AI-augmented care — from prediction and triage to personalized medicine and intelligent hospitals.

- SmartHospital
- ChronicCare AI
- PersonalMD
- CareAnywhere
- PredictRx

### FinSphere AI

Inclusive, secure financial intelligence — credit, fraud defense, wealth, SME capital, and borderless money movement.

- WealthPilot
- CreditForAll
- FraudShield
- Borderless Money
- SME Capital Engine

### LearnSphere AI

Adaptive, inclusive, scalable learning and career systems aligned to real employment outcomes.

- AI Teacher
- Career Navigator
- SkillBridge
- Global Talent Marketplace
- Workforce Ready

### ClimateSphere AI

AI for decarbonization, resilience, water, energy, and the circular economy.

- CarbonIQ
- Climate Shield
- AquaGuard
- Energy Brain
- Circular Future

### CivicSphere AI

Trustworthy digital public infrastructure, citizen services, and transparent governance.

- TrustID
- Citizen First
- GovCopilot
- Smart Nation
- Transparent Government

### AgriSphere AI

Precision, climate-smart agriculture and fair market access for farmers.

- Precision Farm
- Crop Guardian
- FarmMarket
- YieldMax
- Climate Smart Farming

### IndustrySphere AI

Intelligent, resilient, sustainable industrial operations and supply chains.

- Factory Brain
- Predictive Plant
- Quality Vision
- Supply Chain Nexus
- Green Manufacturing

### CommerceSphere AI

AI-native commerce intelligence — growth, personalization, demand, and creator economy.

- GrowthPilot
- HyperPersonal
- Customer Genome
- DemandIQ
- Creator Commerce

### JusticeSphere AI

Legal, compliance, and trust technologies.

- ContractMind
- ComplianceOS
- Legal Copilot
- GovernanceIQ
- **Risk Sentinel** ← Chowkidar

### InfraSphere AI

The foundational layer — secure AI, agent operations, knowledge systems, and human+AI work.

- SecureAI
- WorkforceOS
- Knowledge Grid
- AgentOps
- Human+AI

---

## 7. Chowkidar truthful capability ledger

This is the short version. The detailed limitations are in `docs/ARCHITECTURE.md`, `docs/ENVIRONMENT.md`, and `docs/SUBMISSION.md`.

| Capability | Current status | Can we claim it? |
|---|---|---|
| Next.js operations console | Built | Yes |
| FastAPI REST API + OpenAPI | Built | Yes |
| Postgres + pgvector storage | Built | Yes |
| LangGraph ingest → extract → map → score → remediate → verify → persist | Built | Yes |
| Four source categories (Bangladesh Bank, EUR-Lex, UFLPA/DHS, GDELT) | Fixture-replayed, with source UI and sync endpoint | Yes, as **fixture-replayed source streams**, not live ingestion |
| Prioritized risk scoring + evidence citations | Built | Yes |
| Human-in-the-loop approval with role checks | Built | Yes |
| Hash-chained audit log | Built | Yes |
| PDF/JSON/Markdown reports | Built | Yes |
| Hybrid retrieval: pgvector + Postgres FTS + reranking | Implemented; mock embeddings by default, live BGE-M3 optional and not installed | Yes, with the mock/live distinction disclosed |
| Read-only FastMCP server (stdio) | Built and manually exercised | Yes |
| External MCP server integrated into the product | Not yet; the event MCP was used for research only | **No** until integrated |
| Live LLM mode | Groq-only live pipeline tested; Gemini quota unreliable; mock is default | Yes, with the provider limitation disclosed |
| Local Ollama model run | Route exists in LiteLLM fallback; not validated/run in the demo | **No** until actually run |
| n8n workflow | Compose service and scaffolding exist; not part of the demo path | **No** until wired and demonstrated |
| Fine-tuning / LoRA | Not implemented | **No** |
| Contextual RAG, semantic chunking, Graph RAG, late interaction | Not implemented | **No** |
| Supabase Auth hosted login | Implemented: API password/refresh/logout proxy, JWKS verification, local role mapping, production login UI; not enabled on the live service until keys are set | **Partially — code ready, hosted cutover pending** |
| Supabase Storage + database reports | Implemented: private bucket adapter with Postgres fallback; database is the hosted default after the next deploy | **Partially — code ready, live image still `/tmp` until deploy** |
| Neo4j graph projection | Not wired; graph UI reads Postgres | **No** |
| Multi-tenant isolation, SSO, billing, SOC 2, legal review | Not implemented | **No** |
| Public deployment | Render API + Vercel web live in demo mode; Vercel edge-IP workaround needed on some networks | **Yes, demo mode; production cutover pending** |

### Why this matters

The form’s checkboxes are self-reported, but the submission can be audited against the repository, video, and live app. A false checkbox is a credibility and integrity risk. The right strategy is:

1. Implement the high-ROI items we can actually demonstrate.
2. Disclose the limitations precisely.
3. Never trade truthfulness for a checkbox.

---

## 8. Highest-ROI additions before submission

These are ranked by score and credibility per unit of work. They do **not** require turning Chowkidar into a full commercial platform.

### Must do

1. **Deploy the app publicly.** Vercel web + Render API + Supabase Postgres, or a stable Cloudflare Tunnel if cloud accounts are unavailable. Verify in incognito, with CORS and `NEXT_PUBLIC_API_URL` set correctly.
2. **Record the 2–3 minute YouTube demo.** Show the working UI, one critical risk with evidence, approver decision, audit verification, and report generation.
3. **Fill every form field with existing evidence.** The text fields are worth many points and cost only careful writing.
4. **Add the GitHub URL, live URL, video URL, and access note.**
5. **Add Figma/design and up to three other links.** Architecture diagrams, API docs, prompt library, and the video can serve as “other links.”
6. **Get team composition data from the team.** Size, NRB status, and female-member status are worth 7 points and cannot be invented.

### Worth doing if time permits

7. **MCP disclosure and, if feasible, one real external MCP integration.** The built read-only server already earns “MCP built” and architecture credit. “MCP used” requires an actual external server in the product path.
8. **Run and validate Ollama with a small local model.** The code path exists; actually running it lets us truthfully select the local-runtime and local-model options.
9. **Wire one n8n workflow.** A scheduled source-sync or pipeline-run workflow would make the n8n bonus truthful.
10. **Add semantic/contextual chunking only if actually implemented.** Do not claim it from a checklist.

### Do not do just for checkboxes

- Multi-tenancy, SSO, billing, SOC 2, legal review, or enterprise SLAs. They are not in the preliminary rubric and would consume the remaining time.
- Fake live connectors, fake local models, fake MCP integrations, or fake RAG techniques.
- A full rewrite of the working demo.

---

## 9. Open questions for the team

These cannot be answered from the repository:

- Registered team size and member names.
- NRB status for any member.
- Female-member status for the team-diversity bonus.
- Cloud accounts: Supabase, Render, and Vercel are configured. Neo4j Aura, Sentry, and PostHog remain optional and unconfigured.
- Whether a Figma/design file exists, or whether an architecture diagram can serve as the design link.
- YouTube channel access for uploading the demo.
- Permission to install/run Ollama and n8n for extra truthful checkboxes.

---

## 10. Related files

- `docs/SUBMISSION.md` — submission packet, demo script, form copy, asset checklist.
- `docs/ARCHITECTURE.md` — system design and boundaries.
- `docs/DEPLOYMENT.md` — Render/Vercel/Supabase deployment steps.
- `docs/ENVIRONMENT.md` — exact local/live environment matrix.
- `docs/MCP.md` — Chowkidar’s own read-only MCP server.
- `docs/BUILD_LOG.md` — AI build provenance and manual changes.
- `prompts/MASTER_PROMPT.md` — the single master prompt.
- `preli-submission-ss/` — local-only portal screenshots.
