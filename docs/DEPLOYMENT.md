# Chowkidar — Deployment

**Status (2026-10-24):** the Supabase database is provisioned, migrated, and
seeded. The Render API and Vercel web app are live. The hosted service is still
the explicit **demo** (`AUTH_MODE=dev`, `DEMO_MODE=true`). The production-auth,
durable-storage, and rate-limit code is implemented and locally verified, but
the Supabase Auth keys and hosted environment changes are not available yet. See
[`PRODUCTION.md`](PRODUCTION.md) for the cutover and QA checklist.

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
uses `STORAGE_BACKEND=database` so generated reports survive restarts. Uploads
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

Never paste secrets into chat or commit them. Put them directly into platform
environment variables. The service-role key belongs only on the API.

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
   | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Production-auth cutover only |
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

### Demo auth on Render

The blueprint currently sets `AUTH_MODE=dev` and `DEMO_MODE=true` so judges can
log in with one click. `DEV_JWT_SECRET` is generated by Render. This is a
**demo-only** configuration; do not use it for real company data. The code is
ready for the Supabase Auth cutover; it is not enabled until the keys are set.

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
8. Open the Vercel URL and verify the login page. In demo mode it shows the four
   role cards; in production mode it shows email/password.

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

Demo mode:

- [ ] `/healthz` returns `status: ok`, `database: ok`, `auth_mode: dev`,
      `demo_mode: true`.
- [ ] `/docs` renders OpenAPI.
- [ ] Login works for all four demo roles.
- [ ] Dashboard shows 8 risks, 4 pending approvals, 12 signals, source health.
- [ ] Risk detail shows evidence quote, citation, score breakdown, actions.
- [ ] Approver can record a decision with rationale.
- [ ] Admin can verify the audit chain.
- [ ] Analyst can generate and download a PDF report.
- [ ] Report survives an API restart with `STORAGE_BACKEND=database`.
- [ ] Search returns cited chunks.
- [ ] Evals page shows 7/7 and five gates.
- [ ] Graph renders all 30 nodes.
- [ ] CORS allows the Vercel origin.
- [ ] No secrets appear in the browser bundle or git history.

Production pilot: run the full matrix in [`PRODUCTION.md`](PRODUCTION.md).

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
| Supabase Auth keys | Production login cannot be enabled or hosted-QA'd |
| Render/Vercel dashboard access | Hosted env changes must be applied by the owner |
| Live source connectors | `DATA_MODE=live` is not implemented; signals remain synthetic |
| Public demo video | Pending; required for the official form |
| No Neo4j Aura | Graph falls back to relational demo data |
| No Sentry/PostHog keys | Observability remains local/optional |
| No legal/compliance advisor | Accepted constraint; conservative design and human approval |
| Vercel DNS variability | Some networks may need a custom domain; see cloud status |

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
