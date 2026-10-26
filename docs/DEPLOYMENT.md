# Chowkidar — Deployment

**Status (2026-10-26):** the Supabase database is provisioned, migrated, and
seeded. The Render API and both web builds are live as a **production pilot**:
Netlify is the primary web origin, Vercel is the secondary fallback, and
Supabase email/password auth (`AUTH_MODE=supabase`, `DEMO_MODE=false`) is
enabled with four provisioned accounts, demo login disabled, and durable
Postgres report storage. Netlify production browser QA passed 2/2; the most
recent hosted health check on 2026-10-26 reported revision `94c2a19f91c4` with
`llm_mode=hybrid`, `data_mode=hybrid`, `scheduler_running=true`, and
`scheduler_next_run_at=2026-10-26T09:17:40Z`. The scheduler job is armed; the
first cycle has not been observed. Federal
Register live sync, GDELT fallback, and a hosted pipeline run are verified;
hosted LLM inference is not enabled because provider keys are absent on Render.
Working keys exist only in the gitignored local `.env`. See
[`PRODUCTION.md`](PRODUCTION.md) and
[`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md). This is a
single-workspace pilot, not a commercial multi-tenant deployment.

> **Hosted hybrid state (2026-10-26):** live GDELT/Federal Register connectors,
> hybrid modes, the bounded repair loop, and the scheduler are deployed and the
> Render environment now runs `DATA_MODE=hybrid`, `LLM_MODE=hybrid`, and
> `ENABLE_SCHEDULER=true`. Federal Register sync is hosted-verified live; GDELT
> is externally rate-limited and reports `fixture_fallback`. `llm_live_ready`
> is `false` because Gemini/Groq keys are not set, so hosted inference still
> falls back deterministically. See [`PRODUCTION.md`](PRODUCTION.md) section 2.8.

**Target region:** Supabase `ap-northeast-1` (Tokyo); Render `singapore`;
Netlify and Vercel global edge. The cross-region API/database hop is acceptable
for the pilot.

---

## 1. Topology

| Component | Platform | Notes |
|---|---|---|
| Web console (primary) | Netlify | Repository root base, package directory `apps/web` |
| Web console (secondary) | Vercel | Root directory `apps/web` |
| API | Render (Docker) | `infra/render.yaml`, health check `/healthz` |
| Database | Supabase Postgres | pgvector extension required |
| Reports | Postgres (`STORAGE_BACKEND=database`) or Supabase Storage | Durable; local disk remains for offline demos |
| Auth | Supabase Auth (production path) | Demo adapter remains available only with `AUTH_MODE=dev` + `DEMO_MODE=true` |
| Graph | Neo4j Aura | Optional; the API graph view uses seeded relational data |
| Scheduling | In-process APScheduler | Implemented and deployed with `ENABLE_SCHEDULER=true`; job armed at revision `94c2a19f91c4` (`scheduler_next_run_at=2026-10-26T09:17:40Z`); first cycle pending |
| Monitoring | Sentry / PostHog | Optional keys |

The free Render service has no persistent disk. `infra/render.yaml` therefore
uses `STORAGE_BACKEND=database`, and production mode defaults to `database` if
the variable is omitted, so generated reports survive restarts. Uploads
still use `/tmp` and are ephemeral. Supabase Storage can replace database report
storage after the bucket is verified.

---

## 2. Prerequisites

Create accounts and collect:

- A Supabase project with pgvector enabled and a **Session pooler** connection
  string.
- A Render account (free plan).
- A Netlify account (free plan) for the primary web app.
- A Vercel Hobby account for the secondary fallback.
- For production auth: the Supabase project URL, anon key, and service-role key.
- Optional: Neo4j Aura URI/user/password, Sentry DSN, PostHog key, Gemini and
  Groq API keys.

Never commit or publish secrets. Put them directly into platform environment
variables. The service-role key belongs only on the API. The local `.env` and
`docs/private/` are gitignored.

---

## 3. Supabase

### 3.1 Database

1. Create a project in the region closest to Render. The current project is in
   `ap-northeast-1` (Tokyo).
2. In the SQL editor, enable pgvector:

   ```sql
   create extension if not exists vector;
   ```

3. Copy the **Session pooler** URI from **Connect**. Use port `5432`, not the
   transaction pooler on port `6543`, because migrations need session semantics:

   ```text
   postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
   ```

   The direct `db.<project-ref>.supabase.co` host can be IPv6-only; the pooler is
   the reliable path from Render. URL-encode special characters in the password,
   or reset it to letters and numbers only.

4. To recreate the schema from a trusted machine:

   ```bash
   cd apps/api
   export DATABASE_URL='postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require'
   uv run alembic upgrade head
   EMBEDDING_MODE=mock uv run python -m app.db.seed
   unset DATABASE_URL
   ```

   The seed truncates and replaces demo data. Never run it against a database
   that contains real tenant data.

5. The API container runs `alembic upgrade head` on boot. A fresh deploy against
   an empty database is safe; the seed is a separate data step.

### 3.2 Auth and Storage (production path)

1. Enable the Email provider under **Authentication → Providers**.
2. Set the Site URL to the primary Netlify origin and add both the Netlify and
   Vercel origins to the redirect allow list if email links are enabled.
3. Run the provisioning script from `apps/api` with the service-role key and the
   production `DATABASE_URL`:

   ```bash
   SUPABASE_URL='https://<ref>.supabase.co' \
   SUPABASE_SERVICE_ROLE_KEY='<key>' \
   DATABASE_URL='postgresql+psycopg://...' \
   uv run python -m scripts.provision_supabase_users
   ```

   It creates/updates four confirmed accounts, maps their Supabase UUIDs to the
   local `users` rows, and writes passwords to
   `docs/private/supabase-credentials.local.md` (gitignored, mode `0600`).

4. Set `AUTH_MODE=supabase`, `DEMO_MODE=false`, `SUPABASE_URL`,
   `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and
   `SUPABASE_JWT_AUDIENCE=authenticated` on the API. Then redeploy.
5. Verify `/api/v1/auth/config` reports `password_auth: true`, `demo_mode: false`,
   and no demo users. Verify the demo login endpoint returns `403`.
6. For report storage, keep `STORAGE_BACKEND=database` initially. After the
   database path is verified, switch to `supabase` and confirm the private
   `chowkidar-reports` bucket exists. A failed upload falls back to Postgres.

The detailed checklist, limitations, and browser QA matrix are in
[`PRODUCTION.md`](PRODUCTION.md).

---

## 4. Render (API)

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint** and select `infra/render.yaml`.
3. Set the secret environment variables marked `sync: false`:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | Supabase **Session pooler** connection string |
   | `CORS_ORIGINS` | `https://ch0wkidar.netlify.app,https://chowkidar-wheat.vercel.app` |
   | `WEB_URL` | `https://ch0wkidar.netlify.app` (single canonical origin) |
   | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Required for production auth; enter in the dashboard, never in git |
   | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Leave blank; optional Aura credentials |
   | `GEMINI_API_KEY`, `GROQ_API_KEY` | Required only for live/hybrid LLM mode; leave blank for deterministic mock mode |
   | `SENTRY_DSN`, `POSTHOG_KEY` | Leave blank; optional |

   `CORS_ORIGINS` accepts a comma-separated list of exact origins. `WEB_URL` is
   the canonical primary origin, not a list. Do not use `*`, a trailing slash,
   or a path in either value.

4. The blueprint uses:
   - Docker context `.`
   - Dockerfile `apps/api/Dockerfile`
   - health check `/healthz`
   - free plan (spins down after inactivity)
   - `STORAGE_BACKEND=database` for durable reports
   - rate limits enabled
5. Deploy and wait for the health check. On the free plan, the first request
   after idle can take 30–60 seconds. Verify:

   ```bash
   curl https://<api-domain>/healthz
   curl https://<api-domain>/docs
   ```

6. Copy the API URL. After the web apps are live, set `CORS_ORIGINS` to the
   comma-separated Netlify and Vercel origins and `WEB_URL` to the Netlify
   origin. Saving the environment triggers a redeploy.

### Production auth on Render

The hosted service sets `AUTH_MODE=supabase` and `DEMO_MODE=false`.
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` are entered
in the Render dashboard and are not in git. `DEV_JWT_SECRET` remains generated
but is unused in Supabase mode.

The blueprint in `infra/render.yaml` reflects the same production mode. On a new
Render service, set the Supabase secrets and `DATABASE_URL` before the first
deploy. The API fails fast if Supabase auth is selected without the URL and
public key. See [`PRODUCTION.md`](PRODUCTION.md) for provisioning and QA.

---

## 5. Netlify (primary web)

The repository root contains `netlify.toml`. Netlify builds the web package from
the pnpm workspace and installs its Next.js/OpenNext adapter automatically.

1. In Netlify, choose **Add new project → Import an existing project** and
   select the GitHub repository.
2. Use branch `main`.
3. Leave **Base directory** empty (repository root).
4. Set **Package directory** to `apps/web`. This UI-only setting is what makes
   Netlify detect Next.js correctly.
5. `netlify.toml` supplies the rest:
   - Build command: `pnpm --filter @chowkidar/web build`
   - Publish directory: `apps/web/.next`
   - Node 22
   - `PNPM_FLAGS=--shamefully-hoist`
   - `NEXT_PUBLIC_API_URL=https://chowkidar-api.onrender.com`
6. Deploy to production, not a deploy preview. Copy the exact
   `https://<site>.netlify.app` URL.
7. In Render, set `CORS_ORIGINS` to the comma-separated Netlify and Vercel
   origins, and `WEB_URL` to the Netlify origin. Redeploy Render and wait for
   `/healthz` to pass.
8. Open the Netlify URL and verify the login page. The hosted pilot shows
   email/password; a local `AUTH_MODE=dev` deployment shows the four demo role
   cards.

Netlify Free uses credits. A production deploy costs 15 credits, so avoid
unnecessary redeploys. The `ignore` rule in `netlify.toml` skips docs-only
pushes, but always forces the first build.

### 5.1 Vercel (secondary fallback)

1. Import the repository into a Vercel Hobby project.
2. Set **Root Directory** to `apps/web`.
3. Enable “Include source files outside of the Root Directory” so the pnpm
   workspace and lockfile are available.
4. Framework preset: **Next.js**. Select Node.js 22.x. Set the install command to
   `cd ../.. && pnpm install --frozen-lockfile`; leave the build command at its
   default.
5. Set the only required environment variable:

   | Variable | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<api-domain>` |

   `NEXT_PUBLIC_API_URL` is public and inlined at build time. If you change it,
   redeploy. Supabase keys belong only on the API.

6. Deploy. Copy the exact production domain, not a preview URL.
7. Keep the Vercel origin in Render's `CORS_ORIGINS`. It does not need to be
   `WEB_URL`; Netlify is the canonical primary.
8. Vercel remains a fallback only. If its DNS is unreachable, use the
   documented workaround or a custom domain.

`apps/web/vercel.json` pins the framework preset. If your Vercel workspace
installs from the repo root instead, leave the default install command; pnpm
resolves the workspace.

### 5.2 Optional Render web fallback

`infra/render.yaml` also defines `chowkidar-web`, a free Node service that runs
the Next.js standalone build. It is not required when Netlify or Vercel is
reachable.

- Build: installs the workspace, builds `@chowkidar/web`, and copies
  `.next/static` into the standalone output.
- Start: `node apps/web/.next/standalone/apps/web/server.js`.
- Env: `NEXT_PUBLIC_API_URL=https://chowkidar-api.onrender.com`,
  `NODE_VERSION=22`.
- The service was created by the Blueprint but returned `502` on 2026-10-24;
  check its Render build logs before relying on it.
- If it becomes healthy, add `https://chowkidar-web.onrender.com` to the API’s
  `CORS_ORIGINS` and test `/login`. Free services sleep after inactivity.

---

## 6. Local production-like check

Before deploying, run:

```bash
make check
make e2e        # API + web running
docker build -f apps/api/Dockerfile -t chowkidar-api .
```

Then run the API container against the local database:

```bash
docker run --rm -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -e DATABASE_URL='postgresql+psycopg://chowkidar:chowkidar@host.docker.internal:5432/chowkidar' \
  -e AUTH_MODE=dev -e DEMO_MODE=true -e DEV_JWT_SECRET=local-test \
  -e STORAGE_BACKEND=database \
  chowkidar-api
```

The container runs migrations first. If the database is unreachable, startup
fails loudly rather than serving a broken API.

For a production-auth smoke test locally, point the API at a Supabase project or
a mock Auth/JWKS server, set `AUTH_MODE=supabase` and `DEMO_MODE=false`, and use
an account whose Supabase UUID or email is present in the local `users` table.

---

## 7. Post-deploy smoke checklist

Production pilot QA completed against Netlify on 2026-10-25; the most recent
hosted health check on 2026-10-26 reported revision `2bfaed71372c`:

- [x] `/healthz` returns `status: ok`, `database: ok`, `auth_mode: supabase`,
      `demo_mode: false`.
- [x] `/docs` renders OpenAPI.
- [x] Email/password login works for all four provisioned accounts.
- [x] Demo login returns `403` and `/auth/config` lists no demo users.
- [x] Dashboard shows 8 risks, 4 pending approvals, 13 signals, source health.
- [x] Risk detail shows evidence quote, citation, score breakdown, actions.
- [x] Viewer and approver mutations are role-restricted.
- [x] Admin can verify the audit chain.
- [x] Analyst/admin can generate and download PDF, JSON, and Markdown reports.
- [x] Reports survive an API restart with `STORAGE_BACKEND=database`.
- [x] Search returns cited chunks.
- [x] Evals page shows 7/7 and five gates for analyst/admin.
- [x] Graph renders all 30 nodes.
- [x] CORS allows both the Netlify and Vercel origins.
- [x] Browser QA found no console errors or `5xx` responses on Netlify.
- [x] Netlify PDF generation/download and viewer read-only state passed.
- [x] No secrets appear in public responses or git history.

Local demo mode keeps the one-click role cards and `AUTH_MODE=dev`; use the
local seed baseline for offline judging. The full production matrix is in
[`PRODUCTION.md`](PRODUCTION.md).

---

## 8. Rollback and data

- Render keeps previous deploys; roll back from the dashboard.
- Reseeding replaces demo data. Do not run the seed against a real tenant.
- Database-backed reports survive restarts; local `/tmp` reports do not.
- Supabase Storage buckets should remain private; downloads go through the API.
- Back up Supabase before schema changes. Alembic is the only schema path.
- If production auth is misconfigured, fix the Supabase environment or roll back
  the deploy. Do not re-enable demo access on a deployment that may hold real
  data.

---

## 9. Current blockers

| Blocker | Impact |
|---|---|
| Hosted LLM keys | `llm_live_ready=false`; hosted inference still uses deterministic fallback until Gemini/Groq keys are added |
| Scheduled cycle observation | The arming fix is deployed at revision `94c2a19f91c4`; `/healthz` and `/api/v1/meta` report `scheduler_next_run_at=2026-10-26T09:17:40Z`, so the job is armed. The first cycle is not observed yet. |
| Supabase database password | Current password is weak; rotate before any real-user deployment |
| Public demo video | Pending; required for the official form |
| Design link | `docs/DESIGN.md` is public at the GitHub URL. No Figma file. |
| Team-diversity facts | Team size, NRB status, and female-member status are unconfirmed |
| No Neo4j Aura | Graph uses relational demo data |
| No Sentry/PostHog keys | Observability remains local/optional |
| No legal/compliance advisor | Accepted constraint; conservative design and human approval |
| Vercel DNS variability | Secondary fallback only; some networks may need a custom domain |
| Render web fallback | Currently `502`; optional while Netlify and Vercel are reachable |

---

## 10. Hardening backlog

1. HttpOnly cookie sessions with CSRF protection (replace localStorage tokens).
2. Multi-tenant isolation, Postgres RLS, and separate database roles.
3. Shared rate limiting (Redis or Postgres) for multi-instance deployments.
4. Broader licensed source connectors, replay protection, and per-source quotas beyond the two live connectors.
5. Real BGE-M3 embeddings and a larger human-labeled eval set.
6. Queue-backed pipeline execution and idempotency keys.
7. PII retention policy and data-subject deletion workflow.
8. External anchoring of audit head hashes.
9. MFA and organization-level SSO.
