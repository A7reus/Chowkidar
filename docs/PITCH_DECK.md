# Chowkidar — 10-slide pitch outline

**Use:** preliminary submission deck, 3-minute pitch, or Figma source.
**Rule:** every slide must be supportable by the repo or a demo screenshot. Do
not claim live connectors, legal advice, or customer traction that does not exist.

---

## Slide 1 — Title

**Chowkidar**  
*See the risk. Approve the fix.*

Agentic compliance risk intelligence for export supply chains.

JU_StackMind · International AI Builders Congress 2026 · JusticeSphere AI →
Risk Sentinel

Visual: dark operations-console hero, Padma Apparel case file, live URL.

---

## Slide 2 — The problem

Export-focused SMEs face overlapping EU, US, and home-country rules, sanctions
and watchlists, buyer codes, and supplier incidents.

- Compliance work lives in spreadsheets and email.
- Rules change faster than small teams can track.
- Missed obligations mean shipment delays, penalties, and no defensible trail.
- Generic GRC tools produce dashboards, not evidence-backed decisions.

Visual: three-column “regulation / supplier signal / internal policy” collision.

---

## Slide 3 — The wedge

**Regulatory + supplier risk for export supply chains**, starting with
Bangladesh ready-made garments.

Why this wedge:

- Concrete, high-frequency obligations (CSDDD, UFLPA, Bangladesh Bank).
- Multi-tier supplier data is fragmented.
- Buyers demand evidence, not assurances.
- A focused workflow can be evaluated against real public texts.

---

## Slide 4 — The product

One workspace from signal to signed decision:

1. Monitor distinct streams.
2. Extract cited obligations.
3. Map exposure to company/supplier context.
4. Score deterministically.
5. Draft owned, dated remediation.
6. Verify evidence and guardrails.
7. Route material actions to a human approver.
8. Export an audit pack and keep a hash-chained log.

Visual: five-step pipeline with human gate highlighted.

---

## Slide 5 — Product tour

Three screenshots:

- Dashboard: 12 signals, 8 risks, source health, agent run.
- Risk detail: evidence quote, citation, score breakdown, actions.
- Approval/audit: rationale, decision, hash-chain verification.

Caption: every number is from the seeded demo; every finding is synthetic.

---

## Slide 6 — AI architecture

- **LangGraph** state machine: ingest → extract → map → score → remediate →
  verify → persist.
- **LiteLLM** fallback: Gemini Flash → Groq → Gemini Pro; deterministic mock mode
  for reproducible judging.
- **Hybrid retrieval:** pgvector + Postgres FTS over cited chunks.
- **Verifier:** quote grounding, citation URL, prohibited-language and
  prompt-injection checks.
- **Human-in-the-loop:** role-gated approval, append-only audit chain.
- **Read-only MCP:** other agents can inspect evidence without mutating state.

Visual: architecture diagram from `docs/ARCHITECTURE.md`.

---

## Slide 7 — Evidence and trust

- Evidence-first: no quote → “insufficient evidence”, not a guess.
- Deterministic score, LLM for explanation only.
- Every material action is audited; the chain is verifiable.
- Reports include methodology and limitations.
- Not legal advice; human sign-off is mandatory.

Visual: risk detail crop + audit verify card + report page.

---

## Slide 8 — Evaluation

- 7/7 golden cases in mock mode.
- Five gates: extraction, citation coverage, verifier pass, no-legal-advice,
  priority agreement.
- 57 API tests, 8 web tests, Playwright smoke; Ruff/Pyright/ESLint/tsc clean.
- Honest limitation: small synthetic set; not a legal benchmark.

Visual: eval dashboard screenshot with a “demo-scale” caption.

---

## Slide 9 — Production path and moat

**Built:** Supabase Auth proxy, local role mapping, durable report storage
(Postgres/Supabase), rate limits, production login, settings, runbook.

**Next:** live source connectors, tenant isolation/RLS, HttpOnly sessions,
external audit anchoring, human legal review, design-partner pilots.

**Moat:** the evidence graph + approval/audit workflow + domain-specific
evaluation, not a generic chatbot.

Visual: “demo → pilot → production” maturity ladder with honest labels.

---

## Slide 10 — Ask / close

**Pilot ask:** one RMG exporter and one compliance reviewer for a 4-week pilot;
feedback on obligations, evidence quality, and approval workflow.

**Team:** JU_StackMind — AI/full-stack engineering + data engineering.

**Links:** GitHub, live demo (currently demo mode), API docs, video.

**Close:** See the risk. Approve the fix.

---

## Design notes

- Palette: near-black navy, teal accent, amber for pending, rose for critical.
- Type: Space Grotesk for display; Inter for body.
- Use real screenshots, not invented dashboards.
- One idea per slide; no paragraph walls.
- Label demo vs production state on every relevant slide.
