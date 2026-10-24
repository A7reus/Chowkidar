# Chowkidar — Deployment

**Status (2026-10-24):** the Supabase database is provisioned, migrated, and
seeded. The Render API and Vercel web app are live as a **production pilot**:
Supabase email/password auth (`AUTH_MODE=supabase`, `DEMO_MODE=false`), four
provisioned accounts, demo login disabled, and durable Postgres report storage.
Hosted API and browser QA passed; see [`PRODUCTION.md`](PRODUCTION.md) and
[`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md). This is a
single-workspace pilot, not a commercial multi-tenant deployment.

**Target region:** Supabase `ap-northeast-1` (Tokyo); Render `singapore`; Vercel
global edge. The cross-region API/database hop is acceptable for the pilot.

---

## 1. Topology

| Component | Platform | Notes |
|---|---|---|
| Web console | Vercel | Root directory `apps/web` |
| API | Render (Docker) | `infra/render.yaml`, health check `/healthz` |
| Database | Supabase Postgres | pgvector extension required |
| Reports | Postgres (`STORAGE_BACKEND=database`) or Supabase Storage | Durable; local disk remains for offline demos |
| Auth | Supabase Auth (production path) | Demo adapter remains available only with `AUTH_MODE=dev` + `DEMO_MODE=true` |
| Graph | Neo4j Aura | Optional; the API graph view uses seeded relational data |
| Scheduling | n8n | Optional; not on the demo path |
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
- A Vercel Hobby account.
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
2. Set the Site URL and redirect allow list to the final web origin.
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
   | `CORS_ORIGINS` | `https://<your-vercel-domain>` (comma-separated for additional origins) |
   | `WEB_URL` | Same as the primary web origin |
   | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Required for production auth; enter in the dashboard, never in git |
   | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Leave blank; optional Aura credentials |
   | `GEMINI_API_KEY`, `GROQ_API_KEY` | Leave blank for mock mode; optional live mode |
   | `SENTRY_DSN`, `POSTHOG_KEY` | Leave blank; optional |

   `CORS_ORIGINS` accepts a comma-separated list of exact origins. Do not use
   `*`, a trailing slash, or a path.

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

6. Copy the API URL. After Vercel is live, update `CORS_ORIGINS` and `WEB_URL` to
   the exact Vercel production origin. Saving the environment triggers a
   redeploy.

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

## 5. Vercel (web)

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
7. Return to Render and set `CORS_ORIGINS` and `WEB_URL` to that domain. Redeploy
   Render and wait for `/healthz` to pass.
8. Open the Vercel URL and verify the login page. The hosted pilot shows
   email/password; a local `AUTH_MODE=dev` deployment shows the four demo role
   cards.

`apps/web/vercel.json` pins the framework preset. If your Vercel workspace
installs from the repo root instead, leave the default install command; pnpm
resolves the workspace.

### 5.1 Optional Render web fallback

`infra/render.yaml` also defines `chowkidar-web`, a free Node service that runs
the Next.js standalone build. It is not required when Vercel is reachable.

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

Current production pilot (completed on 2026-10-24 at revision `fcd7fd8`):

- [x] `/healthz` returns `status: ok`, `database: ok`, `auth_mode: supabase`,
      `demo_mode: false`.
- [x] `/docs` renders OpenAPI.
- [x] Email/password login works for all four provisioned accounts.
- [x] Demo login returns `403` and `/auth/config` lists no demo users.
- [x] Dashboard shows 8 risks, 4 pending approvals, 12 signals, source health.
- [x] Risk detail shows evidence quote, citation, score breakdown, actions.
- [x] Viewer and approver mutations are role-restricted.
- [x] Admin can verify the audit chain.
- [x] Analyst/admin can generate and download PDF, JSON, and Markdown reports.
- [x] Reports survive an API restart with `STORAGE_BACKEND=database`.
- [x] Search returns cited chunks.
- [x] Evals page shows 7/7 and five gates for analyst/admin.
- [x] Graph renders all 30 nodes.
- [x] CORS allows the Vercel origin.
- [x] Browser QA found no console errors or `5xx` responses.
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
| Live source connectors | `DATA_MODE=live` is not implemented; signals remain synthetic |
| Supabase database password | Current password is weak; rotate before any real-user deployment |
| Public demo video | Pending; required for the official form |
| Final Figma/design link | Pending |
| Team-diversity facts | Team size, NRB status, and female-member status are unconfirmed |
| No Neo4j Aura | Graph uses relational demo data |
| No Sentry/PostHog keys | Observability remains local/optional |
| No legal/compliance advisor | Accepted constraint; conservative design and human approval |
| Vercel DNS variability | Some networks may need a custom domain; see cloud status |
| Render web fallback | Currently `502`; optional while Vercel is reachable |

---

## 10. Hardening backlog

1. HttpOnly cookie sessions with CSRF protection (replace localStorage tokens).
2. Multi-tenant isolation, Postgres RLS, and separate database roles.
3. Shared rate limiting (Redis or Postgres) for multi-instance deployments.
4. Live, licensed source connectors with replay protection and per-source quotas.
5. Real BGE-M3 embeddings and a larger human-labeled eval set.
6. Queue-backed pipeline execution and idempotency keys.
7. PII retention policy and data-subject deletion workflow.
8. External anchoring of audit head hashes.
9. MFA and organization-level SSO.
