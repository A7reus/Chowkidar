# Chowkidar — Demo video script

**Target length:** 2:30–2:50. Hard stop at 3:00.
**Narrative:** See the risk. Approve the fix.
**Recording state:** the live production pilot (`AUTH_MODE=supabase`,
`DEMO_MODE=false`) with a managed Supabase account. Show the real email/password
sign-in path. The data is synthetic; say “pilot workspace” and do not imply it is
a customer deployment. If production is unavailable, record the local demo and
label it **local demo**, not the hosted pilot.

---

## Pre-flight (10 minutes before recording)

- [ ] Warm the API: open `/healthz` and wait for `status: ok` with
      `auth_mode: supabase` and `demo_mode: false`.
- [ ] Confirm the Netlify URL resolves and that login reaches the API:
      <https://ch0wkidar.netlify.app/>. If the URL does not resolve, use the
      Vercel fallback and the documented DNS workaround in
      [`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md).
- [ ] Open the web app in a clean incognito window.
- [ ] Log in once with the managed analyst account; passwords stay in the
      private access note and must be blurred if they appear on screen.
- [ ] Set browser zoom to 100%; hide bookmarks and notifications.
- [ ] Close extra tabs; use a 1440×900 or 1920×1080 window.
- [ ] Confirm the microphone level and record a 10-second test.
- [ ] Have the report download folder open.
- [ ] Prepare the approver and admin sessions (two browsers or logout/login).
- [ ] Rehearse the click path once without recording.

---

## Shot list

### 0:00–0:15 — Opening

**Screen:** Login page or dashboard, slow cursor movement.

**Say:**
> “Exporters face a moving wall of EU, US, and Bangladesh rules, plus supplier
> risk. Chowkidar watches the streams, finds what applies, and prepares the fix
> for a human to approve. It is compliance risk intelligence, not legal advice.”

### 0:15–0:35 — Sign in

**Screen:** Production login → managed email/password → dashboard. Do not show
the password field contents; cut or blur while typing.

**Say:**
> “This is a managed workspace with role-based access. I’m signing in as the
> analyst. The browser never sees the Supabase service key; the API verifies the
> session and maps it to the local role.”

### 0:35–1:05 — Dashboard

**Screen:** Dashboard; hover the source-health cards; point at the risk counts.

**Say:**
> “Padma Apparel is a fictional Gazipur ready-made-garment exporter selling to
> the EU and US. The seeded stream set produced twelve signals and eight cited
> risks: three critical, three high. The badges show the current auth, LLM, data,
> and storage modes, so nobody has to guess what is running.”

### 1:05–1:40 — Risk detail

**Screen:** Open the critical UFLPA risk. Scroll the score breakdown, evidence
quote, citation, verifier status, and actions.

**Say:**
> “This US-bound order is critical. The score is deterministic: severity four,
> likelihood four, exposure four. The exact UFLPA quote and citation are shown.
> The verifier confirms the quote is grounded in the source. The proposed actions
> have owners, due dates, and priorities — but nothing is approved yet.”

### 1:40–2:05 — Signals and graph

**Screen:** Signals list → open a signal; then graph → click a supplier and a risk
node.

**Say:**
> “Signals keep the raw source text, not just an AI summary. The graph maps the
> company to buyers, suppliers, obligations, and risks. Every node has an
> inspector; clicking a risk opens its evidence.”

### 2:05–2:30 — Human approval

**Screen:** Switch to the Approver session. Open Approvals → decision dialog →
enter rationale → approve. Show the success state.

**Say:**
> “As the approver, I review the evidence and record a decision. The API enforces
> the role. The decision writes an audit event with the actor, timestamp,
> rationale, and before/after payload. This is the human gate.”

### 2:30–2:50 — Audit + report + close

**Screen:** Admin audit verify → green integrity state; Reports → generate PDF →
open the downloaded PDF; return to dashboard.

**Say:**
> “The audit log is append-only and hash-chained; verify recomputes every link.
> The report packages the score method, evidence, actions, approvals, and
> limitations. Chowkidar turns regulatory and supplier signals into a ranked
> audit and a signed human decision. See the risk. Approve the fix.”

**End card:** Chowkidar · JU_StackMind · GitHub URL · live URL · “Not legal advice.”

---

## Fallback if something fails

| Failure | Recovery |
|---|---|
| API cold start | Cut the pause; keep talking over the dashboard; retry the action. |
| Login fails | Use the pre-warmed logged-in tab or a second prepared session. Do not switch to a demo role card for a production-labelled video. |
| Report generation slow | Show the previously downloaded PDF; say “generated in the same session”. |
| Graph clipping | Use the inspector panel; do not resize the window mid-recording. |
| Supabase/network error | Stop; do not record a broken production claim. If production stays down, record the local demo and label it **local demo** on screen and in the description. |

## Post-record checklist

- [ ] Trim dead air; keep under 3:00.
- [ ] Add captions for the product name and “not legal advice”.
- [ ] Blur any email addresses or secrets that should not be public.
- [ ] Upload as unlisted/public YouTube; copy the link.
- [ ] Add the link to `docs/SUBMISSION.md` and the official form.
