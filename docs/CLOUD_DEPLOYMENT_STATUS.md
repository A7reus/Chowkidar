# Chowkidar — Cloud Deployment Status

- **Updated:** 2026-10-24
- **Scope:** Supabase Free + Render Free API + Vercel Hobby web
- **Status:** The API and web app are live as a **production pilot**. Supabase
  email/password auth is enabled, four pilot accounts are provisioned, demo
  login returns `403`, and reports are stored in Postgres. Hosted API and
  browser QA passed against the real Supabase accounts; the runtime was verified
  at revision `fcd7fd8`. Later docs-only commits may advance the reported
  revision without changing runtime behavior. Vercel DNS is still variable on
  some networks. This is not a claim of commercial SaaS readiness; see
  [`LIMITATIONS.md`](LIMITATIONS.md).

---

## 1. Public URLs

| Surface | URL | Status |
|---|---|---|
| API | <https://chowkidar-api.onrender.com/> | Live |
| API health | <https://chowkidar-api.onrender.com/healthz> | Live: database `ok`, Supabase auth |
| API docs | <https://chowkidar-api.onrender.com/docs> | Live |
| Web | <https://chowkidar-wheat.vercel.app/> | Live; DNS reachability varies by resolver |
| Web fallback | `https://chowkidar-web.onrender.com` | Service exists; currently `502` — optional |
| Repository | <https://github.com/A7reus/Chowkidar> | CI green on `main` |

The Render API service is on the **free** plan: 512 MB, no persistent disk, and
it spins down after about 15 minutes of inactivity. The first request after idle
can take 30–60 seconds. The optional Render web fallback has the same free-plan
cold-start behavior.

---

## 2. Verified checks

### Runtime and auth

- `GET /healthz` returns `status: ok`, `database: ok`, `auth_mode: supabase`,
  `demo_mode: false`, `llm_mode: mock`, `data_mode: fixture`, and a revision.
  The production QA run was performed at revision `fcd7fd8b5975`.
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

### Authorization and browser QA

- Role restrictions are enforced by the API: viewer approval is `403`;
  viewer/approver report generation is `403`; analyst audit verification is
  `403`; admin audit verification is `200`.
- Hosted desktop browser QA passed for the admin: managed email/password login,
  dashboard, risks, approvals, signals, sources, reports, graph, search, evals,
  audit verification, and `/settings`.
- Hosted viewer QA passed: read-only badge, disabled report generation, no demo
  role switcher, and the managed-access note instead of a demo role-switch
  action.
- The sidebar shows **Pilot**, not **Demo**. The login page shows **Secure
  workspace** and **Hosted workspace**; demo role cards are absent.
- The admin and viewer browser flows completed without uncaught page errors,
  console errors, or `5xx` responses.
- The deployed Vercel JavaScript chunks were scanned; no Supabase secret,
  service-role key, database URI, or pilot password appeared in the bundle.
- Mobile smoke check at 390 px passed with no dashboard horizontal overflow.
- CORS preflight from `https://chowkidar-wheat.vercel.app` returns `200` with the
  exact origin.
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
- Downloads require authentication, do not expose `storage_path`, return
  `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`, and
  verify the stored checksum before sending bytes. Compressed formats can
  receive a weak proxy ETag; the recorded SHA-256 is the integrity reference.

### CI and local verification

- CI is green for `fcd7fd8` (API and web jobs).
- `make check` passes: 57 API tests and 8 web tests.
- Local Playwright demo smoke passes 4/4.
- The hosted production-auth Playwright run passed 2/2 with the real accounts.

Baseline confirmed on the hosted API: 8 risks, 3 critical, 4 pending approvals.

---

## 3. Vercel “won’t load” issue

This is **not** a failed build and not a CORS/API problem.

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

It is also reachable through `64.29.17.195`, which was used for the final
production browser QA with a Chromium host-resolver override:

```bash
curl -sS -I \
  --resolve chowkidar-wheat.vercel.app:443:64.29.17.195 \
  https://chowkidar-wheat.vercel.app/
```

The default resolver on the QA machine still returned the unreachable `.3`
addresses at times, so judges may need one of the workarounds below.

### Workarounds

1. **Quick local check:** switch DNS to Google `8.8.8.8` / `8.8.4.4`, flush the
   DNS cache, or use a mobile hotspot/VPN.
2. **Judge-proof option:** add a custom domain to the Vercel project and point
   its CNAME at `cname.vercel-dns.com`. `cname.vercel-dns.com` currently resolves
   to `76.76.21.142`, which is reachable. After adding the domain, update
   Render’s `CORS_ORIGINS` and `WEB_URL` to the new origin and redeploy.
3. **Free fallback (optional):** the Render blueprint includes `chowkidar-web`,
   a Node service that runs the Next.js standalone build. The service was
   created, but on 2026-10-24 its root returned `502`; check its Render build logs
   before relying on it. Free services sleep after inactivity.

Do not change the API URL or CORS while testing the DNS workaround; they are
already correct.

---

## 4. Environment variables

### Vercel — Production

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://chowkidar-api.onrender.com` |

No Supabase keys, database secrets, or Groq/Gemini keys are needed by the Vercel
frontend. `NEXT_PUBLIC_*` values are public and are inlined at build time;
changing one requires a redeploy.

### Render — optional web fallback (currently 502)

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://chowkidar-api.onrender.com` |
| `NODE_VERSION` | `22` |

The fallback build and standalone start path were verified locally; the first
Render deployment is currently returning `502`. It uses no database credentials.

### Render — API

| Variable | Value |
|---|---|
| `DATABASE_URL` | Supabase **Session pooler** URI; secret, dashboard only |
| `CORS_ORIGINS` | `https://chowkidar-wheat.vercel.app` |
| `WEB_URL` | `https://chowkidar-wheat.vercel.app` |
| `APP_ENV` | `production` |
| `AUTH_MODE` | `supabase` |
| `DEMO_MODE` | `false` |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Set in Render; secret values are not in git |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` |
| `LLM_MODE` | `mock` |
| `DATA_MODE` | `fixture` |
| `DEV_JWT_SECRET` | Generated by Render; unused in Supabase mode |
| `STORAGE_BACKEND` | `database` (also the production default when omitted) |
| `REPORT_STORAGE_DIR` | `/tmp/reports` (only used if `STORAGE_BACKEND=local`) |
| `RATE_LIMIT_ENABLED` | `true` |
| `AUTH_RATE_LIMIT_PER_MINUTE` | `10` |
| `MUTATION_RATE_LIMIT_PER_MINUTE` | `30` |
| `LOCAL_STORAGE_DIR` | `/tmp` |
| `UPLOAD_STORAGE_DIR` | `/tmp/uploads` |
| `NEO4J_*`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `SENTRY_DSN`, `POSTHOG_KEY` | Blank for the pilot |

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

- Render free services sleep after inactivity; judges may see a cold start.
- Render free storage is ephemeral, but hosted reports are stored in Postgres.
- Supabase Free projects may pause after a period of inactivity; restore the
  project before a demo/judging session.
- Vercel Hobby has no custom-domain cost, but a custom domain itself may cost
  money.
- No live source connectors, Supabase Storage bucket, Neo4j, n8n, or live LLM
  calls are part of the pilot. The code paths for Supabase Storage exist;
  Postgres is the active report backend.
- Rate limits are process-local and sized for one Render instance. Browser
  tokens are in local storage rather than HttpOnly cookies.
- The pilot is single-workspace, has no MFA/SSO, and has no external audit
  anchoring. See [`LIMITATIONS.md`](LIMITATIONS.md).

---

## 6. Next actions

1. Record the 2–3 minute demo video with the live Supabase login.
2. Confirm the final Figma/design link and the team-diversity facts.
3. Rotate the Supabase database password; the current one is weak and was shared
   during setup. Update Render’s `DATABASE_URL` after rotation.
4. Optional: add a custom domain to remove the Vercel DNS variability.
5. Optional: fix or remove the Render web fallback.
6. Fill and submit the official form only after finalization is complete.
