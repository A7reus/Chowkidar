# Chowkidar — Cloud Deployment Status

- **Updated:** 2026-10-26
- **Scope:** Supabase Free + Render Free API + Netlify Free primary web + Vercel Hobby secondary web
- **Status:** The API and both web builds are live as a **production pilot**.
  Netlify is the primary web origin at <https://ch0wkidar.netlify.app/>. Vercel
  remains a secondary fallback at <https://chowkidar-wheat.vercel.app/>. Supabase
  email/password auth is enabled, four pilot accounts are provisioned, demo
  login returns `403`, and reports are stored in Postgres. The Netlify CORS
  cutover is complete and Netlify production browser QA passed 2/2 with the real
  admin and viewer accounts. This is not a claim of commercial SaaS readiness;
  see [`LIMITATIONS.md`](LIMITATIONS.md).

> **Hosted hybrid state (2026-10-26):** live GDELT/Federal Register connectors,
> hybrid modes, the bounded repair loop, and the scheduler are deployed and
> enabled. `/healthz` reports `data_mode=hybrid`, `llm_mode=hybrid`,
> `scheduler_enabled=true`, `scheduler_running=true`, and
> `llm_live_ready=false`. The scheduler job was found paused with
> `SCHEDULER_RUN_ON_START=false`; the arming fix is deployed at revision
> `94c2a19f91c4`, and `/healthz`/`/api/v1/meta` report
> `scheduler_next_run_at=2026-10-26T09:17:40Z`. The job is armed; the first
> cycle has not been observed. Federal Register live sync and dedupe are
> hosted-verified; GDELT reports `fixture_fallback` under its public rate limit.
> Gemini/Groq keys are absent on Render, so hosted pipeline inference still uses
> the deterministic fallback. Working keys exist only in the gitignored local
> `.env` and were probed successfully. The remaining operator action is to add
> the keys to Render and verify one live hosted pipeline run.

---

## 1. Public URLs

| Surface | URL | Status |
|---|---|---|
| Web — primary | <https://ch0wkidar.netlify.app/> | Live; production browser QA passed 2/2 |
| Web — secondary | <https://chowkidar-wheat.vercel.app/> | Live; DNS reachability varies by resolver |
| API | <https://chowkidar-api.onrender.com/> | Live |
| API health | <https://chowkidar-api.onrender.com/healthz> | Live: database `ok`, Supabase auth, `hybrid` modes, scheduler armed, revision `94c2a19f91c4` |
| API docs | <https://chowkidar-api.onrender.com/docs> | Live |
| Web fallback 2 | `https://chowkidar-web.onrender.com` | Service exists; currently `502` — optional |
| Repository | <https://github.com/A7reus/Chowkidar> | CI green on `main` |

The Render API service is on the **free** plan: 512 MB, no persistent disk, and
it spins down after about 15 minutes of inactivity. The first request after idle
can take 30–60 seconds. The optional Render web fallback has the same free-plan
cold-start behavior.

---

## 2. Verified checks

### Runtime and auth

- `GET /healthz` returns `status: ok`, `database: ok`, `auth_mode: supabase`,
  `demo_mode: false`, `llm_mode: hybrid`, `llm_live_ready: false`,
  `data_mode: hybrid`, `live_connectors` containing `gdelt` and
  `federal_register`, `scheduler_enabled: true`, `scheduler_running: true`, and a
  revision. The most recent hosted health check on 2026-10-26 reported revision
  `94c2a19f91c4`; docs-only pushes may advance it without runtime change.
  The scheduler arming fix adds `scheduler_next_run_at`; revision
  `94c2a19f91c4` reports `2026-10-26T09:17:40Z`, so the job is armed. A `null`
  value still means the job is paused or absent, and arming alone does not prove
  a cycle has completed.
  `llm_live_ready=false` because provider keys are absent on Render; do not
  claim hosted live inference until it is `true`.
- `GET /api/v1/auth/config` returns `password_auth: true`, `demo_mode: false`,
  and an empty `demo_users` list.
- `POST /api/v1/auth/demo-login` returns `403` with `Demo login is disabled`.
- Four Supabase users are confirmed and mapped to the seeded local roles:
  `admin@chowkidar.app`, `analyst@chowkidar.app`, `approver@chowkidar.app`, and
  `viewer@chowkidar.app`. Passwords are held only in the gitignored
  `docs/private/supabase-credentials.local.md` (mode `600`); they are not in git.
- Hosted password login and token refresh work for all four roles. A wrong
  password returns `401`.
- An authenticated Supabase user with no local workspace row returns `403`
  instead of receiving a session.
- Protected endpoints return `401` for missing or invalid tokens. `/api/v1/meta`
  is public by design.

### Browser QA

- **Netlify production browser QA passed 2/2** on 2026-10-25 at API revision
  `2bfaed71372c`, using the real admin and viewer accounts. The run covered
  managed login, dashboard, risks, approvals, signals, sources, reports, graph,
  search, evals, audit verification, `/settings`, PDF generation/download,
  viewer read-only state, mobile layout at 390 px, logout/protected-route
  redirect, and console errors.
- **Post-deploy five-stream check passed** on 2026-10-26 at API revision
  `5f224ca`: a real pilot login reached `/dashboard`, and `/sources` rendered
  Bangladesh Bank, EUR-Lex, UFLPA, GDELT, and US Federal Register. The hosted
  environment was still `mock`/`fixture` at that moment; this check verifies the
  new code and UI, not live hosted ingestion. Render subsequently applied the
  `hybrid` environment, and the live checks below supersede that state.
- The prior hosted production-auth Playwright run passed 2/2 against Vercel at
  revision `fcd7fd8`. Vercel remains the secondary fallback.
- The Netlify login page renders **Secure workspace**, the pilot case file, and
  no demo role cards.
- CORS preflight now returns `200` with the exact allow-origin header for both
  `https://ch0wkidar.netlify.app` and `https://chowkidar-wheat.vercel.app`.
- The deployed Vercel JavaScript chunks were scanned; no Supabase secret,
  service-role key, database URI, or pilot password appeared in the bundle.
- Public health, auth-config, and OpenAPI responses contain no service keys or
  bearer tokens.

### Rate limits

- The production auth limiter returns `429` with `Retry-After` after a burst of
  login attempts. The API is process-local and sized for one Render instance.

### Reports and persistence

- `/api/v1/meta` reports `storage_backend: database`.
- PDF, JSON, and Markdown reports generated through the hosted API use the
  database backend. Production report IDs:
  `b0817785-2ab8-48fd-ad02-bc82d08a861a` (PDF),
  `a334ed07-cb2a-401a-b752-9b0a34d0d783` (JSON), and
  `02423367-164e-4e9b-8a58-bea926ace193` (Markdown).
- Those three reports were generated before the `fcd7fd8` Render redeploy and
  downloaded again afterward with matching SHA-256 checksums. The PDF is 13,732
  bytes; JSON is 24,804 bytes; Markdown is 14,048 bytes.
- A new PDF was generated through the Netlify UI on 2026-10-25:
  `02bae404-9b39-4913-ac50-7d53c950b798`. It is 13,733 bytes with SHA-256
  `9bca3361b5c687ae0702c3cdc3ddf52e8ea8d61dabab1f51685544927abeeef1`.
  The downloaded bytes matched the recorded checksum and used
  `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`.
- Downloads require authentication, do not expose `storage_path`, and verify
  the stored checksum before sending bytes. Compressed formats can receive a
  weak proxy ETag; the recorded SHA-256 is the integrity reference.

### CI and local verification

- CI is green for the Netlify migration and QA-evidence docs commits, including
  `021c8b6` (API and web jobs).
- `make check` passes: 57 API tests and 8 web tests.
- Local Playwright demo smoke passes 4/4.

Baseline confirmed on the hosted API: 8 risks, 3 critical, 4 pending approvals.

---

## 3. Hosting roles and DNS

Netlify is the **primary** web origin. Vercel is the **secondary** fallback.
Both frontends point at the same Render API and use the same Supabase project.

### Vercel fallback DNS issue

On 2026-10-24, `chowkidar-wheat.vercel.app` sometimes resolved to:

```text
216.198.79.3
64.29.17.3
```

TCP connections to those addresses timed out from some networks. The same
deployment is reachable through older Vercel edge IPs:

```text
76.76.21.21
76.76.21.98
76.76.21.123
76.76.21.164
```

It is also reachable through `64.29.17.195`, which was used for the prior
Vercel browser QA with a Chromium host-resolver override. On 2026-10-25 the root
and `/login` both returned `200` through that IP, while the default resolver
still timed out:

```bash
curl -sS -I \
  --resolve chowkidar-wheat.vercel.app:443:64.29.17.195 \
  https://chowkidar-wheat.vercel.app/
```

The default resolver on the QA machine still returned the unreachable `.3`
addresses at times. Because Netlify is now primary, judges should use the
Netlify URL first. If Netlify is unavailable, use one of the Vercel workarounds:

1. **Quick local check:** switch DNS to Google `8.8.8.8` / `8.8.4.4`, flush the
   DNS cache, or use a mobile hotspot/VPN.
2. **Judge-proof option:** add a custom domain to the Vercel project and point
   its CNAME at `cname.vercel-dns.com`. After adding the domain, add that exact
   origin to Render's `CORS_ORIGINS` and redeploy.

Do not change the API URL while testing a fallback. Both web origins must remain
in `CORS_ORIGINS`.

---

## 4. Environment variables

### Netlify — primary web

The site is built from the repository root with **package directory**
`apps/web` and **base directory** empty. `netlify.toml` supplies the build
command, publish directory, Node version, pnpm hoisting, and public API URL.

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://chowkidar-api.onrender.com` |

No Supabase keys, database secrets, or Groq/Gemini keys belong on Netlify.
`NEXT_PUBLIC_*` values are public and inlined at build time; changing one
requires a redeploy.

### Vercel — secondary web

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://chowkidar-api.onrender.com` |

Vercel uses root directory `apps/web` and `apps/web/vercel.json`. It remains
configured as a fallback; no Supabase or database secrets belong there.

### Render — API

| Variable | Value |
|---|---|
| `DATABASE_URL` | Supabase **Session pooler** URI; secret, dashboard only |
| `CORS_ORIGINS` | `https://ch0wkidar.netlify.app,https://chowkidar-wheat.vercel.app` |
| `WEB_URL` | `https://ch0wkidar.netlify.app` |
| `APP_ENV` | `production` |
| `AUTH_MODE` | `supabase` |
| `DEMO_MODE` | `false` |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Set in Render; secret values are not in git |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` |
| `LLM_MODE` | `hybrid` (provider keys absent; `llm_live_ready=false`) |
| `DATA_MODE` | `hybrid` |
| `ENABLE_SCHEDULER` | `true` |
| `SCHEDULER_INTERVAL_MINUTES` | `60` |
| `SCHEDULER_RUN_ON_START` | `false` |
| `DEV_JWT_SECRET` | Generated by Render; unused in Supabase mode |
| `STORAGE_BACKEND` | `database` (also the production default when omitted) |
| `REPORT_STORAGE_DIR` | `/tmp/reports` (only used if `STORAGE_BACKEND=local`) |
| `RATE_LIMIT_ENABLED` | `true` |
| `AUTH_RATE_LIMIT_PER_MINUTE` | `10` |
| `MUTATION_RATE_LIMIT_PER_MINUTE` | `30` |
| `LOCAL_STORAGE_DIR` | `/tmp` |
| `UPLOAD_STORAGE_DIR` | `/tmp/uploads` |
| `NEO4J_*`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `SENTRY_DSN`, `POSTHOG_KEY` | Blank for the pilot |

`CORS_ORIGINS` is a comma-separated list of exact origins. `WEB_URL` is a single
canonical origin, not a list; it stays on Netlify. Do not use `*`, a trailing
slash, or a path in either value.

### Local `.env`

Local development keeps `API_URL`, `WEB_URL`, `NEXT_PUBLIC_API_URL`, and
`CORS_ORIGINS` on `localhost`. `DATABASE_URL` stays pointed at the local
Postgres database. The hosted connection string is stored locally only as
`PRODUCTION_DATABASE_URL` for provisioning and verification commands; it is
gitignored and must never be committed.

`.env` is gitignored. `.env.example` is tracked and must contain only
placeholders, never the Supabase password/URI, JWTs, or provider keys.

---

## 5. Free-tier limitations

- Netlify Free has 300 credits/month; a production deploy costs 15 credits, so
  avoid repeated production redeploys. `netlify.toml` skips docs-only pushes.
- Netlify Free includes 20 GB bandwidth and 2 credits per 10,000 requests;
  judging traffic should fit, but monitor the team usage page.
- Render free services sleep after inactivity; judges may see a cold start. The
  scheduler is in-process, so sleep also pauses scheduled ingestion; reliable
  production ingestion needs an always-on instance or an external scheduler.
- Render free storage is ephemeral, but hosted reports are stored in Postgres.
- Supabase Free projects may pause after a period of inactivity; restore the
  project before a demo/judging session.
- Vercel Hobby has no custom-domain cost, but a custom domain itself may cost
  money.
- The connector/hybrid/repair code and migration are deployed and enabled;
  Render runs `hybrid` data/LLM modes with the scheduler armed at revision
  `94c2a19f91c4` (`scheduler_next_run_at=2026-10-26T09:17:40Z`). The first
  scheduled cycle has not been observed; do not claim one until
  `last_synced_at` advances. Federal
  Register live sync is hosted-verified; GDELT falls back under its public rate
  limit. Three streams remain fixture-backed. Supabase Storage, Neo4j, and n8n
  are not part of the hosted pilot. The Supabase Storage code path exists;
  Postgres is the active report backend.
- Rate limits are process-local and sized for one Render instance. Browser
  tokens are in local storage rather than HttpOnly cookies.
- The pilot is single-workspace, has no MFA/SSO, and has no external audit
  anchoring. See [`LIMITATIONS.md`](LIMITATIONS.md).

---

## 6. Next actions

1. Add `GEMINI_API_KEY` and `GROQ_API_KEY` on Render and redeploy; verify
   `llm_live_ready=true` and one live hosted pipeline run. The hybrid data/LLM
   modes and scheduler are already applied; see
   [`PRODUCTION.md`](PRODUCTION.md) section 2.8. The keys are present only in the
   gitignored local `.env` and were probed successfully.
2. Confirm `scheduler_next_run_at` remains non-null and observe one cycle by
   checking `last_synced_at` on `/api/v1/sources`; do not claim a completed
   cycle before then.
3. Record the 2–3 minute demo video with the live Supabase login; the form packet
   uses a placeholder until then.
4. Team-diversity facts are intentionally left blank by the user's decision. The
   design artifact is [`DESIGN.md`](DESIGN.md); the public GitHub link is live
   (verified 2026-10-26). No Figma file is planned.
5. Optional: fix or remove the Render web fallback.
6. Fill the official form using [`SUBMISSION.md`](SUBMISSION.md) section 10 and
   submit only after separate explicit approval.

The weak Supabase database password is accepted for this zero-real-user pilot;
it is not a submission blocker, but rotate it before any real-user deployment.
