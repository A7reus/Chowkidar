# Production pilot path

**Status:** **live and verified as a production pilot.** The hosted API runs
with Supabase email/password auth (`AUTH_MODE=supabase`, `DEMO_MODE=false`), four
pilot accounts are provisioned, demo login is disabled, and reports are stored
in Postgres. Netlify is the primary web origin and Vercel is the secondary
fallback. Netlify production browser QA passed 2/2 on 2026-10-25; the most
recently verified hosted health check on 2026-10-26 reported revision
`2bfaed71372c` with `status=ok`, `database=ok`, `auth_mode=supabase`,
`demo_mode=false`, `llm_mode=mock`, and `data_mode=fixture`. This is a
single-workspace production pilot, not a commercial customer deployment.

> **Local vs hosted (2026-10-26):** live connectors, hybrid LLM mode, the
> bounded repair loop, and the scheduler are implemented and locally verified.
> They are **not deployed** to Render yet. The hosted service remains
> `DATA_MODE=fixture` and `LLM_MODE=mock` until the migration and environment
> cutover in section 2.8 is executed.

This document defines “production-ready” for Chowkidar's preliminary round as
the production path required by `prompts/MASTER_PROMPT.md`: real authentication,
durable report storage, demo access disabled, and bounded request rates. It does
**not** claim commercial SaaS readiness (multi-tenant isolation, billing, 24/7
operations, legal review, or universal live source coverage).

---

## 1. What is implemented

| Capability | Implementation | Verification |
|---|---|---|
| Supabase Auth login | `POST /api/v1/auth/login` proxies Supabase's password grant. The browser never receives the anon/service-role keys. | Hosted QA: all four accounts; `test_auth_production.py` |
| Refresh and logout | `POST /api/v1/auth/refresh` and `/logout` proxy Supabase sessions; the web client refreshes before expiry and clears the session on failure. | Hosted QA: refresh rotated for all four roles; browser sign-out |
| Authorization | The local `users` table is authoritative for role, name, and active status. Supabase `app_metadata.role` is not trusted. | Hosted `/auth/me` and role-restriction checks |
| Demo separation | Demo role cards and demo login exist only when `AUTH_MODE=dev` **and** `DEMO_MODE=true`. In Supabase mode, `/auth/demo-login` returns `403` and `/auth/config` returns no demo users. | Hosted API + browser checks |
| Durable reports | `STORAGE_BACKEND=database` stores report bytes in Postgres; `supabase` stores them in a private Supabase Storage bucket and falls back to Postgres if the bucket is unavailable. `local` remains the default for offline demos. | Hosted PDF/JSON/Markdown downloads; checksum match after redeploy |
| Report integrity | SHA-256, byte size, storage backend, and ETag are recorded and returned; downloads are authenticated and `no-store`. | Hosted checksum, ETag, and cache-header checks |
| Rate limits | Process-local sliding-window limits on auth and mutating endpoints. | Hosted `429` + `Retry-After` check |
| Production UI | Login switches from demo cards to email/password from `/auth/config`; demo badge and role switching disappear for managed accounts; `/settings` shows profile, runtime modes, storage, and session controls. | Hosted admin + viewer browser QA, including mobile |
| Health/config visibility | `/healthz` reports `auth_mode`, `demo_mode`, `llm_mode`, `data_mode`; `/api/v1/meta` reports storage backend. | Hosted `/healthz` and `/api/v1/meta` |

### Deliberate limitations

- **Two live connectors are implemented; three streams remain fixture-backed.**
  `GDELT` and the `US Federal Register` run through real connectors when
  `DATA_MODE=hybrid` or `live` is enabled. Bangladesh Bank, EUR-Lex, and UFLPA
  still replay fixtures. GDELT is externally rate-limited and may fall back to
  fixtures with a visible `fixture_fallback` label. The hosted service has not
  yet been cut over to the new modes.
- **Scheduled ingestion is implemented but not enabled on Render.** The
  in-process APScheduler job runs when `ENABLE_SCHEDULER=true`; n8n is optional
  and not the pilot path.
- **Hybrid LLM mode is implemented but not hosted yet.** Local runs used Gemini
  3.5 Flash and Groq `gpt-oss-120b`; the hosted service still reports
  `llm_mode=mock` until keys and the environment cutover are applied.
- **Tokens are held in browser storage** by the current client (Zustand
  `persist`). A hardened deployment should move refresh tokens to HttpOnly,
  SameSite cookies with CSRF protection. Treat this as a pilot limitation.
- **Rate limits are process-local.** Render Free runs one API instance; a
  multi-instance deployment needs Redis or a database-backed limiter.
- **No multi-tenant row-level security.** The pilot has one workspace and one
  local user table. Do not put unrelated customers in the same deployment.
- **No external audit anchoring, MFA, email delivery, or billing.**
- **No legal/compliance advisor sign-off.** The product's own disclaimer says it
  provides risk intelligence, not legal advice.

### Current hosted state

| Item | Value |
|---|---|
| API | `https://chowkidar-api.onrender.com` |
| Web — primary | `https://ch0wkidar.netlify.app` |
| Web — secondary | `https://chowkidar-wheat.vercel.app` |
| Auth | Supabase email/password; `AUTH_MODE=supabase`, `DEMO_MODE=false` |
| Accounts | `admin@chowkidar.app`, `analyst@chowkidar.app`, `approver@chowkidar.app`, `viewer@chowkidar.app` |
| Credentials | Gitignored `docs/private/supabase-credentials.local.md`, mode `600` |
| Report storage | Postgres (`STORAGE_BACKEND=database`) |
| Runtime QA | Netlify run passed 2/2; the most recent hosted health check on 2026-10-26 reported revision `2bfaed71372c` with `llm_mode=mock` and `data_mode=fixture`. API, role, report, browser, mobile, CORS, and rate-limit checks passed. |
| Remaining external constraint | Vercel default DNS is variable on some networks; it is only the secondary fallback. See [`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md). |

---

## 2. Hosted cutover checklist

> The current pilot completed sections 2.1–2.4 on 2026-10-24 and the
> Netlify-primary CORS cutover on 2026-10-25. Keep this checklist as the
> reproducible cutover and key-rotation runbook for a future deployment.

### 2.1 Collect secrets

Open <https://supabase.com/dashboard>, select the project, and use the
dashboard's **Connect** button or these pages:

| Value | Where to find it | Use |
|---|---|---|
| Project URL | Project Settings → API, or Connect | `SUPABASE_URL` |
| Public key | Project Settings → API Keys; use `sb_publishable_*` or the legacy `anon` JWT | `SUPABASE_ANON_KEY` |
| Server key | Project Settings → API Keys; use `sb_secret_*` or the legacy `service_role` JWT. Never expose it in the browser. | `SUPABASE_SERVICE_ROLE_KEY` |
| Postgres connection | Project Settings → Database → Connection string → Session pooler | Only needed for the normal provisioning script, not for the running API (Render already has `DATABASE_URL`) |
| JWT signing | Project Settings → JWT Keys | Only needed for legacy HS256 projects (`SUPABASE_JWT_SECRET`); new asymmetric projects use the JWKS endpoint automatically |

The API sends new `sb_*` keys only in the `apikey` header. Legacy JWT keys are
also sent as a bearer token for compatibility. Access tokens are verified from
the project JWKS by default; if the project still uses the legacy HS256 signing
secret, also set `SUPABASE_JWT_SECRET`.

Keep the keys in the gitignored local `.env` (or `docs/private/`) for
provisioning. Do not commit or publish the server key or database password.
The `.env` in this repository is ignored; the generated pilot passwords live in
the gitignored private access note.

Generate a random `DEV_JWT_SECRET` even though Supabase mode does not use demo
tokens; it prevents an accidental dev fallback from using a default secret:

```bash
openssl rand -hex 32
```

### 2.2 Supabase Auth settings

1. Enable the Email provider under **Authentication → Providers**.
2. For the pilot, either keep “Confirm email” off or let the provisioning script
   create already-confirmed users. The script sets `email_confirm: true`.
3. Set the Site URL to the primary web origin:
   `https://ch0wkidar.netlify.app`.
4. Add both the Netlify and Vercel origins to the redirect allow list if email
   links are enabled.

The current project has the Email provider enabled and uses ES256/JWKS. The
access tokens are validated against the project JWKS; no HS256 secret is set.

### 2.3 Provision the four accounts

The script creates/updates the four Supabase Auth users, maps their Supabase UUIDs
onto the local role rows, and writes generated passwords to
`docs/private/supabase-credentials.local.md` (gitignored, mode `0600`):

```bash
cd apps/api
SUPABASE_URL='https://<ref>.supabase.co' \
SUPABASE_SERVICE_ROLE_KEY='<service-role-key>' \
DATABASE_URL='postgresql+psycopg://...' \
uv run python -m scripts.provision_supabase_users
```

Optional overrides: `CHOWKIDAR_ADMIN_EMAIL`, `CHOWKIDAR_ANALYST_EMAIL`,
`CHOWKIDAR_APPROVER_EMAIL`, `CHOWKIDAR_VIEWER_EMAIL`, the matching `_NAME`
variables, and `CHOWKIDAR_<ROLE>_PASSWORD` for each role.

If you do not have the hosted `DATABASE_URL`, use the pilot-only auth-only mode.
It creates the Supabase users but leaves the local rows untouched; the API maps
them by email on first login:

```bash
cd apps/api
SUPABASE_URL='https://<ref>.supabase.co' \
SUPABASE_SERVICE_ROLE_KEY='<server-key>' \
uv run python -m scripts.provision_supabase_users \
  --auth-only --seeded-emails
```

`--seeded-emails` uses the existing `admin@chowkidar.demo` and
`analyst@chowkidar.demo` rows. This is acceptable for the seeded pilot workspace,
but change the local emails to real pilot addresses when database access is
available. The normal script is preferred because it writes
`users.supabase_user_id` and lets the owner change emails without breaking the
mapping.

The script reuses the seeded local user row for each role so existing audit and
approval references remain valid. It prints only IDs and the credential file
path, not the passwords. The current hosted database has all four rows mapped by
`supabase_user_id`; the accounts are active and confirmed.

### 2.4 Render API environment

Set these in the Render dashboard (or update `infra/render.yaml` only after the
values are ready). Save the URL and keys first, then set `AUTH_MODE=supabase` and
`DEMO_MODE=false` in one save; the API fails fast if Supabase auth is selected
without the URL and public key. Render should redeploy on save; trigger a manual
deploy if it does not.

```dotenv
AUTH_MODE=supabase
DEMO_MODE=false
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_JWT_AUDIENCE=authenticated

# Durable by default; switch to supabase after the bucket is verified.
STORAGE_BACKEND=database
REPORT_STORAGE_BUCKET=chowkidar-reports

RATE_LIMIT_ENABLED=true
AUTH_RATE_LIMIT_PER_MINUTE=10
MUTATION_RATE_LIMIT_PER_MINUTE=30
```

If `STORAGE_BACKEND` is omitted, `APP_ENV=production` defaults it to `database`
so reports survive restarts. Set the web origins exactly:

```dotenv
CORS_ORIGINS=https://ch0wkidar.netlify.app,https://chowkidar-wheat.vercel.app
WEB_URL=https://ch0wkidar.netlify.app
```

`CORS_ORIGINS` is a comma-separated exact-origin list. `WEB_URL` is a single
canonical origin, not a list; keep it on Netlify. The API container runs
`alembic upgrade head` at boot; the report-storage migration must be present
before the first production report.

### 2.5 Web environments

Netlify is primary; Vercel is the secondary fallback. Neither needs Supabase
keys. Both need only:

```dotenv
NEXT_PUBLIC_API_URL=https://chowkidar-api.onrender.com
```

Netlify builds from the repository root with package directory `apps/web` and
uses `netlify.toml`. Vercel uses root directory `apps/web` and
`apps/web/vercel.json`. Redeploy after changing a `NEXT_PUBLIC_*` value because
it is inlined at build time. The login page discovers demo vs password mode from
the API at runtime.

### 2.6 Optional Supabase Storage

After database storage is verified, set `STORAGE_BACKEND=supabase`. The API
creates a **private** bucket named `chowkidar-reports` on the first upload. If
bucket creation or upload fails, the API stores the report in Postgres and
records `storage_warning` in the report summary; downloads still work. Keep the
service-role key on the API only.

### 2.7 Rollback

If production auth is misconfigured, do **not** silently re-enable demo access on
a deployment that may contain real data. Roll back the API deploy or fix the
Supabase environment. `AUTH_MODE=dev` + `DEMO_MODE=true` is only acceptable for a
fresh synthetic demo deployment.

### 2.8 Connector, hybrid LLM, and scheduler cutover

This cutover is **not yet applied** to the hosted service. Apply it only after
the new code and migration `9c1e4f2a7b10_live_connectors.py` are on the deployed
revision and the provider keys are present.

```dotenv
DATA_MODE=hybrid
LLM_MODE=hybrid
ENABLE_SCHEDULER=true
SCHEDULER_INTERVAL_MINUTES=60
SCHEDULER_RUN_ON_START=false
GEMINI_API_KEY=<key>
GROQ_API_KEY=<key>
GEMINI_FLASH_MODEL=gemini/gemini-3.5-flash
GEMINI_PRO_MODEL=gemini/gemini-3.5-flash
LLM_TIMEOUT_SECONDS=25
LLM_PROVIDER_COOLDOWN_SECONDS=90
PIPELINE_LIVE_MAX_SIGNALS=6
PIPELINE_MAX_REPAIR_ATTEMPTS=1
```

Cutover order:

1. Deploy the API revision containing the migration and connector code.
2. Confirm the boot log applies `9c1e4f2a7b10` without error.
3. Set the environment values above and redeploy.
4. Verify `/healthz` reports `data_mode=hybrid`, `llm_live_ready=true`,
   `live_connectors` containing `gdelt` and `federal_register`,
   `scheduler_enabled=true`, and `scheduler_running=true`.
5. Run one Federal Register sync and confirm `mode=live`; run it again and
   confirm `mode=live` with `0` new signals due to dedupe.
6. Run one GDELT sync. If the public API is rate-limited, confirm the run is
   `mode=fixture_fallback`, `status=degraded`, and `last_error` is sanitized. Do
   not present the fallback as a healthy live sync.
7. Run one live pipeline and inspect `repair_attempts`, `routing`, and
   verification statuses.
8. If the provider keys are absent or the live path is unreliable, revert to
   `LLM_MODE=mock` and `DATA_MODE=fixture` and disclose that state. The demo
   remains functional.

---

## 3. Hosted QA matrix

Completed against Netlify and the hosted API on 2026-10-25; the most recent
hosted health check on 2026-10-26 reported revision `2bfaed71372c`, with the
prior Vercel run retained at `fcd7fd8`:

- [x] `/healthz` returns `status: ok`, `database: ok`, `auth_mode: supabase`,
      `demo_mode: false`.
- [x] `/api/v1/auth/config` returns `password_auth: true` and no demo users.
- [x] Login with the admin account; the demo role cards are absent and the
      sidebar says **Pilot**, not **Demo**.
- [x] Logout clears the session; protected pages redirect to `/login`.
- [x] Each of the four accounts sees the expected role permissions; a viewer
      cannot approve or generate reports.
- [x] An unprovisioned Supabase user gets `403`, not a workspace session.
- [x] Dashboard, risk detail, approvals, audit verification, reports, search,
      evals, and graph load without console errors.
- [x] PDF, JSON, and Markdown report downloads succeed; checksums match the
      generated bytes.
- [x] Reports survive an API restart (database backend).
- [x] `/settings` shows the correct profile, auth mode, data/LLM/storage modes,
      and sign-out.
- [x] Mobile layout at 390 px works; no dashboard horizontal overflow.
- [x] CORS preflight from both Netlify and Vercel succeeds with the exact
      allow-origin header.
- [x] Netlify PDF generation and download succeed; the downloaded SHA-256
      matches the recorded checksum.
- [x] No secrets appear in the browser bundle, public responses, or git.
- [x] Rate limit returns `429` with `Retry-After` after the configured burst.

---

## 4. Operational notes

- Render Free spins down after inactivity; warm the API before a judging session.
- Supabase Free may pause; restore the project before recording or judging.
- Keep `docs/private/` out of git. The credentials file is generated at mode
  `0600`; provide access to judges only through the submission's private access
  field or another controlled channel, never a public commit.
- The Supabase database password is currently weak and should be rotated before
  any real-user deployment. Update Render's `DATABASE_URL` after rotation.
- The report storage migration is `82eceac00bcf_durable_report_storage.py`.
- The append-only audit chain remains the system of record for material actions;
  production cutover does not change that behavior.
