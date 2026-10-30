# Chowkidar — Product Specification

> **Historical document (2026-10-26):** This is the product specification as
> planned on 2026-10-23. Features marked as planned below — admin invitation and
> role-change UI, local model execution in the demo path, graph RAG, and some
> multi-agent behavior — are **not implemented**. The shipped pilot is narrower.
> Read [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) for the capability boundary,
> [`README.md`](README.md) for what is built, and
> [`docs/GAP_ANALYSIS.md`](docs/GAP_ANALYSIS.md) for remaining gaps.

**Last updated:** 2026-10-23  
**Status:** Historical specification — implemented subset documented in `README.md`
**Challenge:** JusticeSphere AI → Risk Sentinel  
**Deadline:** 2026-11-20, 11:59 PM GMT+6 (extended from 2026-10-31; confirm the exact cutoff in the portal)

---

## 1. Summary

**Chowkidar** is an agentic **compliance risk intelligence** platform for export-oriented supply chains. It monitors regulatory changes, sanctions/watchlists, and global risk signals; maps them to a company's obligations, policies, contracts, suppliers, and controls; and turns them into a prioritized risk register with evidence-backed remediation plans and human approval.

**Tagline:** *See the risk. Approve the fix.*

**Category:** Compliance risk intelligence / regulatory operations (RegTech). Not legal advice.

**Beachhead:** Bangladeshi RMG, leather, and agro-processing exporters, plus the brands and auditors that oversee them.

**Expansion:** Other export hubs (Vietnam, India, Turkey, Indonesia), other risk domains (sanctions, forced labor, ESG, privacy), and GRC platform integrations.

---

## 2. Problem and insight

### 2.1 Problem

A mid-sized export manufacturer faces a moving maze of obligations:
- Regulators: Bangladesh Bank, Department of Environment, NBR, labour authorities, export promotion bodies.
- Buyer codes: multiple brand codes of conduct, audit standards, restricted-substance lists.
- Trade rules: sanctions, export controls, UFLPA, EU CSDDD/CSRD, rules of origin.
- Supplier risk: forced labour, environmental violations, financial distress, subcontracting, strikes.
- Internal obligations: policies, contracts, certifications, corrective action plans.

Compliance teams track this in email, spreadsheets, and PDFs. Changes are missed; supplier risks surface late; evidence is scattered; audits are painful. Existing GRC tools are static dashboards and checklists — they do not read unstructured legal text, reason over supplier networks, or drive remediation.

### 2.2 Insight

The hard part is not generating text. It is:
1. **Knowing what changed** across many sources.
2. **Knowing what it touches** across a company's obligations and supply network.
3. **Knowing what to do next**, with evidence a human can approve and an auditor can verify.

Chowkidar is built around those three questions. It is a **data + workflow** product, not a chatbot.

### 2.3 Why now

- Regulatory complexity is increasing across EU, US, and Bangladesh.
- LLMs can now extract structured obligations from long legal documents with citations.
- Agentic workflows can monitor, map, and draft remediation continuously.
- Export supply chains are under pressure from buyers, regulators, and consumers to prove compliance.
- Small compliance teams cannot scale manually.

---

## 3. Target users

### 3.1 Primary persona — Ayesha, Head of Compliance

- 2,000-worker RMG exporter in Gazipur, Bangladesh.
- Exports to EU and US buyers.
- Manages 6 buyer codes, 3 regulators, 40 suppliers, 2 auditors, a team of 3.
- Tracks changes in email and Excel; prepares board reports manually.
- Measured on audit findings, buyer scorecards, and zero shipment delays.
- Needs: early warning, impact analysis, evidence, remediation tracking, board-ready reporting.

### 3.2 Secondary personas

| Persona | Need |
|---|---|
| Compliance analyst | Triage changes, gather evidence, update policies, chase suppliers |
| Internal auditor | Verify controls, sample evidence, trace decisions |
| Sustainability/ESG lead | Monitor supplier labour/environmental risk, prepare disclosures |
| COO/CFO | Prioritized risk view, cost of inaction, remediation status |
| Buyer/sourcing team | Supplier risk visibility, corrective action tracking |

### 3.3 Buyer

Head of Compliance, COO, CFO, or Chief Risk Officer. In buyer-driven programs, the brand may mandate the platform for suppliers.

### 3.4 Not the initial user

Law firms, litigation teams, consumers, or anyone seeking legal advice. Chowkidar is for compliance operations, not legal representation.

---

## 4. Product principles

1. **Evidence before opinion.** Every obligation, risk, and recommendation links to a primary source: URL, document version, article/section, exact quote, effective date, retrieval timestamp.
2. **Human in the loop.** AI drafts; a human with the right role approves, rejects, or assigns. No automated filings, no legal conclusions, no irreversible actions.
3. **Source-grounded, not source-free.** If the evidence is insufficient, the system says so and escalates. It does not guess.
4. **Compliance intelligence, not legal advice.** Clear disclaimers, conservative language, no "you are compliant" claims.
5. **Workflow-native.** The output is not a chat response; it is a risk register, an evidence ledger, an approval queue, and an audit report.
6. **Data sovereignty.** Sensitive documents can be processed by local models; PII is redacted before external calls.
7. **Explainable by design.** Every risk score shows its factors, confidence, and evidence.
8. **Audit-ready.** Every action, approval, rejection, and model output is logged with actor, timestamp, and rationale.

---

## 5. Core workflows

### 5.1 Monitor

- Poll source registry on a schedule.
- Detect new documents, versions, and changes.
- Deduplicate and classify relevance to the company's jurisdictions, sectors, and suppliers.
- Create `ChangeEvent` records with a diff/summary and severity.

### 5.2 Triage

- Rank change events by relevance, urgency, and potential impact.
- Show source, jurisdiction, effective date, affected entities, and confidence.
- Allow analyst to accept, dismiss, or escalate.

### 5.3 Investigate

- Extract obligations, entities, dates, penalties, and citations.
- Map obligations to policies, contracts, suppliers, factories, controls, and owners.
- Show a graph view: regulation → obligation → policy/control → supplier/factory.
- Show evidence side-by-side with the source text.

### 5.4 Remediate

- Generate a remediation plan: actions, owners, deadlines, dependencies, evidence required.
- Draft policy redlines, supplier questionnaires, evidence requests, and board memo sections.
- Estimate effort and risk of inaction.
- Require human approval before actions are created/assigned.

### 5.5 Approve

- Approval queue with risk, action, evidence, and recommended decision.
- Approve, reject, request changes, assign, or defer.
- Capture rationale.
- Write immutable audit events.

### 5.6 Report

- Generate a prioritized risk audit report: top risks, changes, affected entities, actions, status, evidence.
- Export to Markdown/PDF.
- Board-ready summary + appendix with citations.

### 5.7 Learn

- Approvals/rejections feed the eval set and retrieval tuning.
- Track false positives, missed risks, and remediation outcomes.
- Improve prompts, mappings, and source coverage.

---

## 6. MVP features

| ID | Feature | Description | Acceptance criteria |
|---|---|---|---|
| F1 | Source registry | Catalog of regulators, lists, news, internal docs | Add/edit/disable sources; show jurisdiction, type, refresh cadence, last sync |
| F2 | Connectors | Federal Register, EUR-Lex, GDELT, OpenSanctions/UFLPA, curated Bangladesh snapshot | Each connector fetches and normalizes at least 5 documents; failures are visible |
| F3 | Change detection | Detect new versions/entries and summarize diffs | At least 3 demo changes detected; diff shown with source link |
| F4 | Obligation extraction | Extract obligation text, article/section, jurisdiction, effective date, penalty, citation | Structured JSON; citation precision ≥ 0.95 on golden set |
| F5 | Risk graph | Entities and relationships: company, supplier, factory, buyer, regulation, obligation, policy, contract, control, risk | Graph view renders a supplier→obligation→policy path; queries return < 2s |
| F6 | Impact mapping | Map obligations/signals to affected policies, contracts, suppliers, controls | Mapping accuracy ≥ 0.80 on golden set; every mapping has evidence |
| F7 | Risk scoring | Likelihood × impact with explainable factors and confidence | Score + factors + confidence displayed; ranking NDCG@5 ≥ 0.85 |
| F8 | Remediation planner | Draft actions, owners, deadlines, policy redlines, questionnaires | At least 3 action types; human can edit before approval |
| F9 | Approval workflow | Approve/reject/assign/defer with rationale and audit log | RBAC enforced; every decision logged; no action without approval |
| F10 | Audit report | Prioritized risk report with evidence appendix | Export Markdown/PDF; includes top risks, actions, citations |
| F11 | Evidence ledger | Source quote, URL, version, timestamp, hash for every claim | Every risk/obligation links to evidence; broken links flagged |
| F12 | Admin/RBAC | Users, roles, source settings, thresholds, data retention | Admin can invite users and change roles; audit log records changes |
| F13 | Evals | Golden set, metrics, regression runs | Eval report generated in CI; baseline vs pipeline comparison |
| F14 | Observability | Traces, token/cost, latency, source freshness | LangSmith/Phoenix trace per workflow; cost per risk visible |
| F15 | MCP servers | Built: regulatory-feed, risk-graph, remediation; used: Postgres, Fetch, GitHub | MCP inspector shows tools; demo calls at least one built server |
| F16 | Local model path | Ollama + Qwen/Llama/DeepSeek for sensitive docs/offline | Local extraction works on a sample doc; switch is visible |
| F17 | Demo data | Fictional company, suppliers, policies, contracts, regulatory changes | Seed script loads in < 2 min; demo reproducible |
| F18 | Disclaimers | Legal/compliance disclaimer, source citations, human approval notice | Visible in UI, README, report, demo |

### 6.1 Nice-to-have (only if time)

- Bangladesh Bank circular scraper.
- Buyer-code questionnaire generator.
- Bengali/English UI toggle.
- Slack/email approval notifications.
- Cost dashboard.
- "Explain this risk" chat over the graph.
- CSV/PDF bulk upload with OCR.
- Supplier portal for evidence submission.

### 6.2 Non-goals (MVP)

- Legal advice, legal opinions, or compliance guarantees.
- Contract drafting, negotiation, or enforceability analysis.
- Litigation prediction or case-law research.
- Automated regulatory filings.
- ERP/SAP integration.
- Multi-tenant billing.
- Mobile app.
- All jurisdictions, all risk types, all languages.
- Autonomous actions without human approval.

---

## 7. Data model

| Entity | Key fields | Notes |
|---|---|---|
| `Company` | id, name, country, sector, size | Tenant |
| `User` | id, company_id, role, email | Roles: admin, compliance_lead, analyst, auditor |
| `Source` | id, name, type, jurisdiction, url, cadence, active | Regulator, list, news, internal |
| `Document` | id, source_id, version, title, url, published_at, effective_at, raw_text, parsed_text, hash | Versioned |
| `ChangeEvent` | id, document_id, previous_document_id, diff, summary, severity, detected_at | Created by Monitor |
| `Obligation` | id, document_id, article, text, jurisdiction, category, effective_at, penalty, confidence | Extracted |
| `Policy` | id, company_id, name, version, owner, text | Internal |
| `Contract` | id, company_id, counterparty, type, clauses, effective_at | Internal |
| `Supplier` | id, company_id, name, country, tier, sector, risk_score | External entity |
| `Factory` | id, supplier_id, name, location, certifications | Site |
| `Buyer` | id, company_id, name, code_of_conduct_url | Customer |
| `Control` | id, policy_id, name, owner, status, evidence_id | Internal control |
| `RiskSignal` | id, source_id, entity_type, entity_id, type, severity, confidence, evidence | News/sanctions/labour |
| `Risk` | id, company_id, entity_type, entity_id, obligation_id, signal_id, likelihood, impact, score, status, owner | Prioritized |
| `RemediationAction` | id, risk_id, type, description, owner, due_date, status, approval_id | Draft → approved → done |
| `Evidence` | id, risk_id/obligation_id, source_id, quote, url, version, retrieved_at, hash | Ledger |
| `Approval` | id, action_id, user_id, decision, rationale, created_at | Human decision |
| `AuditEvent` | id, company_id, actor_id, action, entity_type, entity_id, before, after, created_at | Immutable |
| `EvalRun` | id, dataset, model, prompt_version, metrics, created_at | Regression |

### 7.1 Key relationships

```
Company → Suppliers → Factories
Company → Policies → Controls
Company → Contracts → Obligations
Source → Documents → ChangeEvents → Obligations
Obligation → Risk → RemediationAction → Approval
RiskSignal → Risk → RemediationAction → Approval
Evidence → Obligation / Risk / Action
AuditEvent → everything
```

### 7.2 Graph schema

- Nodes: Company, Supplier, Factory, Buyer, Regulation, Obligation, Policy, Contract, Control, Risk, Action.
- Edges: `OWNS`, `SUPPLIES`, `OPERATES`, `SUBJECT_TO`, `IMPLEMENTS`, `AFFECTS`, `MITIGATES`, `EVIDENCED_BY`, `APPROVED_BY`.

---

## 8. Agent architecture

| Agent | Input | Output | Tools | Guardrails |
|---|---|---|---|---|
| **Monitor** | Source registry, last sync state | ChangeEvents, relevance scores | HTTP fetch, diff, dedup, classifier | Rate limits, source allowlist, robots/ToS compliance |
| **Extractor** | Document text | Obligations, entities, dates, penalties, citations (JSON) | Parser, OCR, structured-output LLM | Citation required; schema validation; confidence |
| **Mapper** | Obligations/signals, company graph | Affected policies, contracts, suppliers, controls | Graph query, hybrid RAG, reranker | Evidence per mapping; no unsupported links |
| **Scorer** | Risk, evidence, company context | Likelihood, impact, score, factors, confidence | Rules + LLM, historical calibration | Explainable factors; no hidden score |
| **Remediator** | Risk, evidence, playbooks | Actions, owners, deadlines, drafts | Templates, policy RAG, task API | Human approval; no auto-send/filing |
| **Verifier** | Claims, evidence | Supported/unsupported, contradictions, gaps | Source lookup, citation matcher, LLM judge | Reject unsupported claims; flag "insufficient evidence" |
| **Reporter** | Risk register, actions, evidence | Prioritized audit report, board memo | Templates, chart data | Citations in appendix; no legal conclusions |

### 8.1 Orchestration

- LangGraph state machine with checkpointing.
- Human-in-the-loop interrupts at approval nodes.
- Retry/fallback per agent.
- Trace every step to LangSmith/Phoenix.
- Store intermediate artifacts in Postgres/S3 for audit.

### 8.2 Agent prompts

- Stored in `prompts/runtime/`.
- Versioned; each run records prompt_version.
- Structured JSON output with schema validation.
- No free-form legal conclusions.
- Always include source quotes and URLs.

---

## 9. RAG and model routing

### 9.1 RAG pipeline

1. **Parse:** PDF/HTML → structured text, preserve headings, articles, sections, tables.
2. **Chunk:** semantic/variable chunking by legal section, not fixed tokens.
3. **Contextualize:** prepend document title, jurisdiction, effective date, section path.
4. **Embed:** BGE-M3 or OpenAI/Cohere embeddings.
5. **Index:** pgvector + BM25 (hybrid).
6. **Retrieve:** hybrid search + metadata filters (jurisdiction, date, entity).
7. **Rerank:** BGE-reranker or Cohere.
8. **Graph expand:** traverse supplier→factory→obligation→policy paths.
9. **Generate:** citation-bound answer with quotes.
10. **Verify:** check each claim against retrieved spans.

### 9.2 Model routing

| Task | Primary | Fallback | Why |
|---|---|---|---|
| Long-context legal reasoning | Claude Sonnet 4.5 | GPT-5.1 | Strong long-context, citation discipline |
| Structured extraction | GPT-5.1 / o4-mini | Claude Haiku | Reliable JSON, tool use |
| Cheap classification | Gemini 2.5 Flash | GPT-4.1 mini | Cost/latency |
| Sensitive internal docs | Qwen2.5 / Llama 3.1 via Ollama | DeepSeek-R1 local | Data sovereignty |
| Report drafting | Claude Sonnet | GPT-5.1 | Tone, structure |
| Eval judge | GPT-5.1 / Claude | Local judge | Calibration |

- Use LiteLLM for routing, retries, fallbacks, and token accounting.
- Cache embeddings and stable extractions.
- Log cost per risk assessment.

### 9.3 Memory

- Prior risk decisions and approvals.
- Supplier risk history.
- Policy versions and redlines.
- Retrieval feedback (accepted/rejected evidence).

---

## 10. No-advisor mitigations

Because the team has no legal/compliance advisor, the product must be **source-grounded and conservative**:

1. **Scope guard:** regulatory change management + supplier risk signals. No legal advice, no contract enforceability, no litigation prediction.
2. **Primary-source citations:** every obligation includes document, article/section, quote, URL, version, effective date.
3. **Verifier Agent:** checks claims against sources; unsupported claims are rejected or marked "insufficient evidence."
4. **Human approval:** no action is executed without a named human with the right role.
5. **Conservative language:** "potential obligation," "requires review," "risk signal," "recommended action." Never "you are compliant" or "this is legal."
6. **Official guidance as ground truth:** use explicit obligations from official texts; avoid ambiguous interpretation.
7. **Eval set with gold labels:** 30 explicit regulatory changes; measure extraction/citation/mapping accuracy.
8. **Disclaimers:** UI, README, report, demo.
9. **Audit trail:** every output and decision logged.
10. **Optional beta review:** a law student or compliance professional for 1 hour to review the demo script and disclaimers; not a dependency.

**Positioning line:**
> "Chowkidar does not give legal advice. It gives compliance teams an evidence-linked view of what changed, what it touches, and what to do next — and a human approves every action."

---

## 11. Evaluation plan

### 11.1 Golden dataset

- 30 regulatory changes:
  - 10 EU (e.g., CSDDD, CSRD, AI Act, GDPR updates).
  - 10 US (Federal Register, UFLPA, OFAC, SEC).
  - 10 Bangladesh (Bangladesh Bank, labour, environment, tax).
- 20 supplier risk signals:
  - Sanctions/PEP additions.
  - Forced-labour allegations.
  - Labour strikes.
  - Environmental violations.
  - Financial distress.
- Gold labels:
  - Obligation text and article/section.
  - Jurisdiction and effective date.
  - Affected entity types.
  - Citation URL/quote.
  - Risk level (low/medium/high/critical).
  - Expected remediation type.

### 11.2 Metrics

| Metric | Target | Method |
|---|---|---|
| Obligation extraction F1 | ≥ 0.85 | Exact/partial match vs gold |
| Citation precision | ≥ 0.95 | Verifier + human spot-check |
| Citation recall | ≥ 0.90 | All gold citations found |
| Mapping accuracy | ≥ 0.80 | Correct policy/supplier/control |
| Risk ranking NDCG@5 | ≥ 0.85 | Gold priority order |
| Remediation usefulness | ≥ 4/5 | LLM judge + human spot-check |
| Latency per change | < 60s | End-to-end trace |
| Cost per change | < $0.50 | Token accounting |
| False-positive rate | < 10% | Analyst review |

### 11.3 Baselines

- GPT-4.1/Claude zero-shot extraction.
- RAG-only (no graph, no verifier).
- Full pipeline.
- Local model (Qwen/Llama) on a subset.

### 11.4 Process

- Build dataset in week 1.
- Run baselines.
- Iterate prompts/retrieval.
- Regression in CI.
- Store results in `evals/results/`.
- Include a summary in the submission ("Proof" link).

---

## 12. Guardrails and responsible AI

| Area | Control |
|---|---|
| PII | Presidio redaction before external LLM calls; local models for sensitive docs |
| Prompt injection | Input sanitization, Llama Guard/Guardrails AI, tool allowlist |
| Citations | Every claim must cite a source; verifier rejects unsupported claims |
| Legal boundary | Disclaimer; no legal advice; human approval; conservative language |
| Defamation | "Risk signal" language; evidence links; right of reply; no accusations |
| Access control | RBAC; least privilege; audit log |
| Data retention | Configurable; delete on request; no training on customer data |
| Model risk | Versioned prompts/models; eval regression; fallback models |
| Human oversight | Approval queue; reject/assign/defer; rationale required |
| Transparency | Risk factors, confidence, source quotes, model/prompt version |
| Security | Encryption at rest/in transit; rate limits; secrets management |
| Compliance | GDPR-aware design; data residency options; local model path |

---

## 13. Demo scenario

### 13.1 Setup

- Fictional company: **Meghna Apparel Ltd.**, Gazipur, Bangladesh.
- 2,000 workers; exports to EU/US; 40 suppliers; 6 buyer codes.
- Synthetic internal docs: supplier list, 12 policies, 6 contracts, 3 audit reports.
- Real public sources:
  - EU CSDDD (EUR-Lex).
  - UFLPA entity list (DHS).
  - GDELT news article (real or realistic).
  - Bangladesh Labour Act section (public).
  - A public buyer code of conduct.
- Clearly label synthetic data in the demo.

### 13.2 Three acts

**Act 1 — Regulatory change (EU CSDDD)**
- Monitor detects a new/updated obligation.
- Extractor pulls 3 obligations with citations.
- Mapper links them to 2 policies, 1 contract, 14 suppliers, 4 controls.
- Scorer ranks risk 87/100 with factors.
- Remediator proposes 5 actions.
- Compliance lead approves 2, rejects 1, assigns 2.
- Audit log updates.

**Act 2 — Supplier risk signal (GDELT/UFLPA)**
- Monitor detects a news alert / entity list addition.
- Entity resolution links it to a sub-tier supplier.
- Risk signal severity high; evidence shown.
- Remediator proposes enhanced due diligence, evidence request, and a buyer notification draft.
- Compliance lead approves the due diligence task.

**Act 3 — Report**
- Generate board-ready risk report.
- Show top 5 risks, actions, owners, status, evidence appendix.
- Export PDF/Markdown.
- Close: "From signal to signed action in minutes — with evidence, accountability, and an audit trail."

### 13.3 What not to show

- Legal conclusions ("you are in violation").
- Automated filing or sending.
- A generic chatbot.
- A dashboard with no action.
- Unverified accusations against real companies.

---

## 14. Metrics

### 14.1 Product metrics

- Time from signal to triage: < 5 minutes.
- Time from triage to approved action: < 30 minutes.
- % risks with evidence: 100%.
- % actions with human approval: 100%.
- Analyst hours saved per week: target 10+.
- Audit preparation time: target 50% reduction.

### 14.2 Business metrics

- Pilot conversion: 3 LOIs / 1 pilot.
- Willingness to pay: $X per seat / $Y per supplier.
- Compliance cost avoided: penalties, delays, buyer penalties.
- Supplier coverage: 40 suppliers in pilot; 500+ in expansion.

### 14.3 Impact metrics

- Suppliers monitored.
- Workers covered.
- Audit findings reduced.
- Remediation actions closed.
- Shipment delays avoided.

---

## 15. Competitive landscape

| Competitor | Strength | Gap |
|---|---|---|
| Diligent | Board/GRC suite | Static, enterprise-heavy, weak supply-chain monitoring |
| ComplyAdvantage | Financial crime/sanctions | Fincrime focus, not regulatory obligations/supply chain |
| FiscalNote | Regulatory tracking | Policy/political risk, not operational remediation |
| OneTrust | Privacy/security governance | Privacy-centric, not export supply chain |
| Sayari | Supply chain/ownership risk | Data platform, less workflow/remediation |
| Vanta/Drata | Compliance automation | SaaS/security certifications, not export/manufacturing regulation |
| Regology | Regulatory change | Mapping, less agentic remediation |

**Chowkidar wedge:** export supply chains in emerging markets; evidence-linked obligation graph; agentic remediation; human approval; local regulatory coverage.

---

## 16. Business model

- SaaS: per compliance seat + per supplier monitored.
- Enterprise annual contract with implementation/regulatory mapping.
- API/white-label for GRC platforms and buyer-driven supplier programs.
- Land-and-expand: one business unit → global supplier network → other risk domains.
- Services: regulatory mapping, onboarding, audit support.

**Why buyers pay:**
- Avoid penalties, shipment delays, buyer penalties, and audit findings.
- Reduce manual research and evidence gathering.
- Prove due diligence to buyers, auditors, and regulators.
- Protect brand and market access.

---

## 17. Non-goals and risks

### 17.1 Non-goals

See §6.2.

### 17.2 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| No legal advisor | High | High | Evidence-first, conservative scope, human approval, disclaimers, eval set |
| Hallucination | Medium | High | Citation enforcement, verifier, "insufficient evidence" fallback |
| Data source access/rate limits | Medium | Medium | Cache, curated snapshots, fallback |
| Scope creep | High | High | MVP non-goals, cut list |
| Demo failure | Medium | High | Recorded video, local Docker fallback, seed data |
| Judge sees it as supply chain, not legal | Medium | Medium | Emphasize legal obligations, compliance buyer, audit evidence, Risk Sentinel brief |
| Defamation/false positives | Low | High | Risk-signal language, evidence, human review, no real accusations |
| Model cost/latency | Medium | Medium | Routing, caching, local models |
| One-prompt rule compliance | High | High | Finalize master prompt v1.0; single build pass; build log; no iterative human prompts |
| Team burnout | Medium | High | Buffer day, prioritize, cut nice-to-haves |

---

## 18. Open questions

1. Stack decisions: language, package manager, frontend framework, backend framework, API style, database, ORM, auth, AI stack, deployment, CI. **User approval required.**
2. Which live sources are reliable from Bangladesh.
3. Do we have a pilot user or compliance contact?
4. Can a law student review the demo for 1 hour?
5. Which demo scenario is most compelling: EU CSDDD, UFLPA, or Bangladesh Bank?
6. Do we show a Bengali UI or English only?
