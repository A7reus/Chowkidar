# Chowkidar — Evaluation

**Current result (mock mode):** 7/7 golden cases; extraction accuracy, citation
coverage, verifier pass rate, legal-advice guard, and priority agreement all
report `1.0`.

This is a **demo-scale, synthetic, inspectable** set, not a legal benchmark or a
production accuracy claim.

---

## 1. What is evaluated

The golden set lives in `apps/api/app/services/evals.py` (`GOLDEN_CASES`). Each
case selects a seeded signal by `external_id` and runs the deterministic mock
path:

1. Extract an obligation.
2. Map it to a risk with severity/likelihood/exposure.
3. Score it with the deterministic scoring function.
4. Draft remediation actions.
5. Verify evidence, citation, guardrails, and prompt-injection markers.
6. Compare the result with the expected keyword and priority.

Seven cases cover:

| Case | Signal | Expected priority |
|---|---|---|
| Export-proceeds repatriation | Bangladesh Bank circular | high |
| CSDDD due diligence | EUR-Lex | medium |
| UFLPA forced labour | DHS/UFLPA | critical |
| Port disruption | GDELT | high |
| Factory fire | GDELT | high |
| Flood freight | GDELT | high |
| Export incentive | Bangladesh Bank circular | high |

---

## 2. Metrics

| Metric | Definition |
|---|---|
| Extraction accuracy | Expected keyword appears in the extracted obligation title/description |
| Citation coverage | Evidence quote is non-empty and appears verbatim in the source raw text |
| Verifier pass rate | The verifier marks the risk `verified`, with a valid citation and no prohibited content |
| No-legal-advice rate | No prohibited legal-advice phrase in the generated obligation/risk/action language |
| Priority agreement | Deterministic priority equals the expected band |

A case passes only when **all five** checks pass.

The current mock output reports every metric at `1.0`. Because the mock path and
the expected keywords were authored together, this demonstrates pipeline
contract compliance and citation grounding on the seed set; it does **not**
measure generalization to unseen regulations.

---

## 3. How to run

```bash
make evals
```

or against the API:

```bash
curl -sS -X POST http://localhost:8000/api/v1/evals/run \
  -H "Authorization: Bearer $TOKEN" | jq
```

The result is persisted in `eval_runs`; the `/evals` page shows the latest
summary and per-case notes.

---

## 4. Limitations

- **Small and synthetic:** seven hand-built cases, one company, one scenario.
- **Mock-path result:** the deterministic path is the default. Live model output
  has been smoke-tested but is not benchmarked here.
- **No human legal labels:** expected priorities and keywords are engineering
  labels, not legal opinions.
- **No adversarial set:** prompt-injection and prohibited-language checks exist,
  but the golden set does not include a broad adversarial corpus.
- **No multilingual legal text:** Bengali UI chrome exists; legal sources remain
  in their original language, and translation quality is not evaluated.
- **No production distribution:** the seed is not a random sample of real
  exporter obligations.

---

## 5. Next evaluation work

1. Build a 50–100 case set from official texts with citations and effective
   dates.
2. Add human review by a compliance professional (not a legal opinion; a
   correctness/coverage review).
3. Separate extraction, retrieval, and remediation metrics; report confidence
   intervals.
4. Add adversarial cases for prompt injection, conflicting sources, stale
   obligations, and ambiguous jurisdiction.
5. Benchmark live Gemini/Groq routes separately and record cost/latency.
6. Add regression tests that fail CI when a metric drops below a threshold.
