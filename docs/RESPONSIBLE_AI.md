# Chowkidar — Responsible AI

Chowkidar is **compliance risk intelligence, not legal advice**. It is designed to
help a human notice, review, and act on source-grounded signals. It does not
determine legal liability, guarantee compliance, or replace qualified counsel.

---

## 1. Evidence first

- Every obligation and risk must carry a verbatim quote, citation label, and
  source URL.
- The verifier checks that the quote appears in the source text and that the
  citation is present.
- If evidence is missing or weak, the UI shows `insufficient_evidence` or
  `needs_review` instead of inventing certainty.
- Search returns cited source chunks; it is not a free-form answer generator.

---

## 2. Human approval

- The pipeline can propose actions, but it cannot approve them.
- Material decisions require an **approver** or **admin** role and a rationale
  of at least 12 characters.
- The decision, actor, timestamp, rationale, and before/after payload are written
  to the append-only audit trail.
- The UI shows lock indicators and role-gated actions rather than hiding the
  workflow.

---

## 3. Guardrails

The verifier and policy checks look for:

- citation/quote grounding failures;
- prohibited legal-advice phrasing;
- prompt-injection markers in source text;
- missing evidence or unsupported confidence;
- invalid priority/score combinations.

These checks reduce risk; they do not prove correctness. A human reviewer remains
responsible for decisions.

---

## 4. Privacy and data sovereignty

- The pilot uses synthetic companies, suppliers, and documents. Do not treat the
  names as allegations about real entities.
- PII redaction patterns cover email, phone, national ID, passport, and IBAN
  paths that require it. This is not a complete DLP system.
- API keys and database credentials live in server-side environment variables;
  the browser never receives the Supabase service-role key.
- Supabase is the current hosted data processor. A production pilot should review
  data residency, retention, and processor terms with the customer.
- Report storage is private; downloads require an authenticated API session.

---

## 5. Fairness and bias

- The demo scenario is a Bangladeshi ready-made-garment exporter. It is not a
  representative sample of all exporters.
- Source selection, English-language legal text, and the hand-built golden set can
  encode coverage bias.
- Supplier-risk signals can create reputational harm if treated as findings of
  wrongdoing. The product uses “signal”, “risk”, and “needs review” language,
  and requires human verification.
- Do not use the system to make adverse decisions about workers, suppliers, or
  individuals without independent review and due process.

---

## 6. Transparency

- `/healthz` exposes the active auth, demo, LLM, and data modes.
- `/settings` shows the signed-in profile, auth mode, data mode, LLM mode,
  embedding mode, and report storage backend.
- The risk score is deterministic and displayed:
  `((severity × 0.40 + likelihood × 0.35 + exposure × 0.25) / 4) × 100`.
- The methodology and limitations are included in generated reports.
- The UI and reports carry the not-legal-advice disclaimer.

---

## 7. Known limitations

- No legal/compliance advisor reviewed the content.
- No live source connectors; the demo replays synthetic fixtures.
- The golden set is small and synthetic; mock-mode 1.0 is not a generalization
  claim.
- No multi-tenant RLS, MFA, external audit anchoring, or HttpOnly cookie sessions
  yet.
- Rate limiting is process-local; a multi-instance deployment needs a shared
  store.
- Browser tokens are stored in local storage in the current client.

See [`LIMITATIONS.md`](LIMITATIONS.md) for the full list.

---

## 8. Incident handling

If a user reports a harmful or wrong output:

1. Preserve the signal, evidence, prompt version, model/provider, and audit
   event IDs.
2. Do not edit the audit chain; add a new review event.
3. Mark the output `needs_review` or `insufficient_evidence`.
4. Notify the workspace owner and, if real data is involved, follow the
   customer's incident process.
5. Add a regression case to the golden set before changing the prompt.

Security issues: rotate the affected key, inspect access logs, and follow the
runbook. Do not publish exploit details before the key is revoked.
