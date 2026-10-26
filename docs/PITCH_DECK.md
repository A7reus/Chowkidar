# Chowkidar — 10-slide pitch outline

**Use:** preliminary submission deck, 3-minute pitch, or design source.
**Rule:** every slide must be supportable by the repo or a demo screenshot. Claim
only the two implemented live connectors (GDELT + US Federal Register) with
their honest fallback labels; do not claim hosted live inference while
`llm_live_ready=false`, legal advice, or customer traction that does not exist.

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

- Dashboard: 13 signals, 8 risks, five source streams, agent run.
- Risk detail: evidence quote, citation, score breakdown, actions.
- Approval/audit: rationale, decision, hash-chain verification.

Caption: every number is from the seeded demo; every finding is synthetic.

---

## Slide 6 — AI architecture

- **LangGraph** state machine: ingest → extract → map → score → remediate →
  verify → conditional repair → persist.
- **LiteLLM** fallback: Gemini 3.5 Flash → Groq `gpt-oss-120b` → optional Ollama;
  deterministic fallback and mock mode for reproducible judging.
- **Live ingestion:** GDELT + US Federal Register connectors with dedupe and
  honest `live` / `fixture_fallback` labels; three other streams remain
  fixture-backed.
- **Hybrid retrieval:** pgvector + Postgres FTS over cited chunks.
- **Verifier:** quote grounding, citation URL, prohibited-language and
  prompt-injection checks; one bounded evidence-repair cycle.
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

- 7/7 golden cases on the deterministic path.
- Five gates: extraction accuracy, citation coverage, verifier pass rate,
  no-legal-advice rate, priority agreement.
- 75 API tests, 8 web tests, local Playwright smoke, and hosted production
  Playwright QA; Ruff/Pyright/ESLint/tsc clean.
- Honest limitation: small synthetic set; not a legal benchmark; live models and
  the repair loop are not scored here.

Visual: eval dashboard screenshot with a “demo-scale” caption.

---

## Slide 9 — Production path and moat

**Live:** Supabase email/password auth, local role mapping, durable Postgres
reports, rate limits, production login, settings, hosted QA, and runbook.
**Deployed and running:** GDELT + Federal Register live connectors, hybrid
modes, bounded repair loop, and scheduled ingestion. Federal Register live sync
and dedupe are hosted-verified; GDELT falls back under its public rate limit.
Hosted `llm_live_ready=false` because provider keys are absent on Render, so
hosted inference still uses the deterministic fallback. Working keys exist only
in the gitignored local `.env` and were probed successfully.

**Next:** add hosted provider keys and verify live hosted inference, observe a
scheduled cycle, then tenant isolation/RLS, HttpOnly sessions, MFA/SSO, external
audit anchoring, human legal review, and design-partner pilots.

**Moat:** the evidence graph + approval/audit workflow + domain-specific
evaluation, not a generic chatbot.

Visual: “local demo → live single-workspace pilot → commercial SaaS” maturity
ladder with honest labels.

---

## Slide 10 — Ask / close

**Pilot ask:** one RMG exporter and one compliance reviewer for a 4-week pilot;
feedback on obligations, evidence quality, and approval workflow.

**Team:** JU_StackMind — AI/full-stack engineering + data engineering.

**Links:** GitHub, live production pilot, API docs, video.

**Close:** See the risk. Approve the fix.

---

## Design notes

- Palette: near-black navy, teal accent, amber for pending, rose for critical.
- Type: Space Grotesk for display; Inter for body.
- Use real screenshots, not invented dashboards.
- One idea per slide; no paragraph walls.
- Label synthetic-data pilot vs customer deployment on every relevant slide.
