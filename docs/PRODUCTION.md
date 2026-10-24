# Production pilot path

**Status:** implemented in code and locally verified, but **not yet enabled on the
live deployment** because the Supabase Auth URL/keys and hosted environment
changes are not available in this workspace. The live service is still the
explicit demo (`AUTH_MODE=dev`, `DEMO_MODE=true`). Do not describe it as a
production customer deployment until the cutover and hosted QA in this document
are complete.

This document defines “production-ready” for Chowkidar's preliminary round as
the production path required by `prompts/MASTER_PROMPT.md`: real authentication,
durable report storage, demo access disabled, and bounded request rates. It does
**not** claim commercial SaaS readiness (multi-tenant isolation, billing, 24/7
operations, legal review, or live source connectors).

---

## 1. What is implemented

| Capability | Implementation | Verification |
|---|---|---|
| Supabase Auth login | `POST /api/v1/auth/login` proxies Supabase's password grant. The browser never receives the anon/service-role keys. | `test_auth_production.py`; local mock Supabase end-to-end check |
| Refresh and logout | `POST /api/v1/auth/refresh` and `/logout` proxy Supabase sessions; the web client refreshes before expiry and clears the session on failure. | Unit tests; browser check with mock Supabase |
| Authorization | The local `users` table is authoritative for role, name, and active status. Supabase `app_metadata.role` is not trusted. | `resolve_workspace_user`; `/auth/me` check |
| Demo separation | Demo role cards and demo login exist only when `AUTH_MODE=dev` **and** `DEMO_MODE=true`. In Supabase mode, `/auth/demo-login` returns `403` and `/auth/config` returns no demo users. | API + browser checks |
| Durable reports | `STORAGE_BACKEND=database` stores report bytes in Postgres; `supabase` stores them in a private Supabase Storage bucket and falls back to Postgres if the bucket is unavailable. `local` remains the default for offline demos. | Database download/checksum check; storage unit tests |
| Report integrity | SHA-256, byte size, storage backend, and ETag are recorded and returned; downloads are authenticated and `no-store`. | API check |
| Rate limits | Process-local sliding-window limits on auth and mutating endpoints. | `test_rate_limiter`/manual checks |
| Production UI | Login switches from demo cards to email/password from `/auth/config`; demo badge and role switching disappear for managed accounts; `/settings` shows profile, runtime modes, storage, and session controls. | Browser check in production mode |
| Health/config visibility | `/healthz` reports `auth_mode`, `demo_mode`, `llm_mode`, `data_mode`; `/api/v1/meta` reports storage backend. | local + hosted checks |

### Deliberate limitations

- **Live source connectors are not implemented.** `DATA_MODE=live` is not a
  supported ingestion mode; source sync replays the fixture set. The demo
  therefore uses synthetic signals even after auth is switched to production.
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

---

## 2. Hosted cutover checklist

### 2.1 Collect secrets

From the Supabase project dashboard:

- Project URL (`https://<ref>.supabase.co`)
- Publishable/anon key
- Service-role key (server-side only; never send it to the browser or commit it)
- Postgres Session pooler URL (already used by Render)

Generate a random `DEV_JWT_SECRET` even though Supabase mode does not use demo
tokens; it prevents an accidental dev fallback from using a default secret:

```bash
openssl rand -hex 32
```

### 2.2 Supabase Auth settings

1. Enable the Email provider under **Authentication → Providers**.
2. For the pilot, either keep “Confirm email” off or let the provisioning script
   create already-confirmed users. The script sets `email_confirm: true`.
3. Set the Site URL to the final web origin, for example
   `https://chowkidar-wheat.vercel.app`.
4. Add the same origin to the redirect allow list if email links are enabled.

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

The script reuses the seeded local user row for each role so existing audit and
approval references remain valid. It prints only IDs and the redacted path, not
the passwords.

### 2.4 Render API environment

Set these in the Render dashboard (or update `infra/render.yaml` only after the
values are ready):

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
so reports survive restarts. Keep `CORS_ORIGINS` exactly equal to the Vercel
origin (comma-separated if a custom domain is added). The API container runs `alembic upgrade head` at boot;
the report-storage migration must be present before the first production report.

### 2.5 Vercel web environment

No Supabase keys belong on Vercel. It only needs:

```dotenv
NEXT_PUBLIC_API_URL=https://chowkidar-api.onrender.com
```

Redeploy Vercel after changing a `NEXT_PUBLIC_*` value because it is inlined at
build time. The login page discovers demo vs password mode from the API at
runtime.

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

---

## 3. Hosted QA matrix

Run this in a private/incognito window against the final URLs after cutover:

- [ ] `/healthz` returns `status: ok`, `database: ok`, `auth_mode: supabase`,
      `demo_mode: false`.
- [ ] `/api/v1/auth/config` returns `password_auth: true` and no demo users.
- [ ] Login with the admin account; the demo role cards are absent and the
      sidebar says **Pilot**, not **Demo**.
- [ ] Logout clears the session; protected pages redirect to `/login`.
- [ ] Each of the four accounts sees the expected role permissions; a viewer
      cannot approve or generate reports.
- [ ] An unprovisioned Supabase user gets `403`, not a workspace session.
- [ ] Dashboard, risk detail, approvals, audit verification, reports, search,
      evals, and graph load without console errors.
- [ ] PDF, JSON, and Markdown report downloads succeed; checksum headers match
      the generated bytes.
- [ ] Reports survive an API restart (database or Supabase backend).
- [ ] `/settings` shows the correct profile, auth mode, data/LLM/storage modes,
      and sign-out.
- [ ] Mobile layout at 390 px works; no horizontal overflow.
- [ ] CORS preflight from the final web origin succeeds.
- [ ] No secrets appear in the browser bundle, network responses, or git.
- [ ] Rate limit returns `429` with `Retry-After` after the configured burst.

---

## 4. Operational notes

- Render Free spins down after inactivity; warm the API before a judging session.
- Supabase Free may pause; restore the project before recording or judging.
- Keep `docs/private/` out of git. The credentials file is generated at mode
  `0600` and must never be pasted into the submission form.
- The report storage migration is `82eceac00bcf_durable_report_storage.py`.
- The append-only audit chain remains the system of record for material actions;
  production cutover does not change that behavior.
