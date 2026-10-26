# Chowkidar — Operations runbook

**Scope:** the Render API + Netlify primary web + Vercel secondary web +
Supabase production pilot. Supabase email/password auth, durable Postgres
reports, hybrid data/LLM modes, and the scheduler are live. The deployment
state, QA evidence, and credential handling are in
[`PRODUCTION.md`](PRODUCTION.md).

---

## 1. Health checks

```bash
curl -sS https://chowkidar-api.onrender.com/healthz | jq
curl -sS https://chowkidar-api.onrender.com/api/v1/auth/config | jq
curl -sSI https://ch0wkidar.netlify.app/
curl -sSI https://chowkidar-wheat.vercel.app/
```

Expected hosted production pilot (verified 2026-10-26):

```json
{
  "status": "ok",
  "database": "ok",
  "auth_mode": "supabase",
  "demo_mode": false,
  "llm_mode": "hybrid",
  "llm_live_ready": false,
  "data_mode": "hybrid",
  "scheduler_enabled": true,
  "scheduler_running": true,
  "scheduler_next_run_at": "2026-10-26T09:10:00+00:00"
}
```

`llm_live_ready=false` means Gemini/Groq keys are absent on Render and hosted
inference is using the deterministic fallback. The keys may still be present in
the local `.env`; never copy them into docs or commits. Do not claim hosted live inference until it is
`true`. Once keys are added, the same endpoint should report
`llm_live_ready: true`; `live_connectors` should contain `gdelt` and
`federal_register`.

`scheduler_next_run_at=null` means the scheduler job is paused, absent, or the
API is running a build from before the arming fix. A non-null timestamp proves
the interval job is armed; it does not by itself prove a cycle has completed.
Check `last_synced_at` on `/api/v1/sources` for cycle evidence.

The local offline demo still uses `auth_mode: dev` and `demo_mode: true`; those
values on the public deployment would be a regression.

If `database` is `unavailable`, the API is degraded; check Supabase status and
Render logs before retrying.

---

## 2. Deploy

### API (Render)

- Service: `chowkidar-api`, Docker, Singapore, free plan.
- Blueprint: `infra/render.yaml`.
- The container runs `alembic upgrade head` before starting.
- Render deploys `main` automatically; a manual deploy is available in the
  dashboard.
- Cold start after idle: 30–60 seconds. Warm the API before a demo.

### Web (Netlify primary)

- Netlify site: `https://ch0wkidar.netlify.app/`.
- Repository root base, package directory `apps/web`; config in `netlify.toml`.
- Required env: `NEXT_PUBLIC_API_URL=https://chowkidar-api.onrender.com`.
- `NEXT_PUBLIC_*` is inlined at build time; redeploy after changing it.
- Netlify Free charges 15 credits per production deploy; avoid unnecessary
  redeploys. Docs-only pushes are skipped by `netlify.toml`.

### Web (Vercel secondary)

- Project root: `apps/web`; config in `apps/web/vercel.json`.
- Required env: `NEXT_PUBLIC_API_URL=https://chowkidar-api.onrender.com`.
- Vercel is a fallback only; it is not the canonical `WEB_URL`.
- If the API origin changes, update Render’s `CORS_ORIGINS` and `WEB_URL` and
  redeploy the API. Keep both web origins in `CORS_ORIGINS`.

### Database migrations

The API applies migrations on boot. To apply manually from a trusted machine:

```bash
cd apps/api
DATABASE_URL='postgresql+psycopg://...' uv run alembic upgrade head
```

Never run migrations and the seed against a database with real data unless you
intend to replace it.

### Connectors and scheduler

- `DATA_MODE=fixture|hybrid|live`; `ENABLE_SCHEDULER=true` starts the in-process
  APScheduler job. `SCHEDULER_RUN_ON_START=false` avoids a burst on cold start;
  the interval trigger still arms the first run. Never pass
  `next_run_time=None` explicitly, which pauses the job.
- The scheduler and manual sync use the same service path. The job is
  process-local, so it does not coordinate across multiple Render instances.
- Check `/healthz` or `/api/v1/meta` for `scheduler_next_run_at`; `null` means
  the job is paused or absent. A non-null timestamp confirms arming, and
  `last_synced_at` confirms an actual cycle.
- Check `/api/v1/sources` for `last_sync_mode`, `last_signal_count`,
  `last_synced_at`, and a sanitized `last_error`.
- A `fixture_fallback` run is **degraded**, not healthy. A hard `live_failed`
  run returns `502` from the sync route after persisting the failure.
- GDELT's public endpoint allows roughly one request every five seconds. Do not
  poll it manually in a loop; wait for the scheduler or retry after the window.

---

## 3. Rollback

1. Render → service → **Deploys** → choose the last known-good deploy →
   **Redeploy**.
2. Netlify → site → **Deploys** → choose the last good production deploy →
   **Publish deploy** (or roll back in the Netlify UI).
3. Vercel → project → **Deployments** → choose the last good build → **Promote**
   if the fallback is affected.
4. If a migration is implicated, stop and restore the database from backup
   before rolling back the application. Do not run a downgrade on production
   without a tested backup.
5. If production auth is broken, roll back the API or fix the Supabase env. Do
   not re-enable demo auth on a deployment that may contain real data.

---

## 4. Report storage

| Backend | Verification |
|---|---|
| `local` | Check the report file exists under `REPORT_STORAGE_DIR`; ephemeral on Render |
| `database` | `select storage_backend, size_bytes, length(content), content_sha256 from report_runs order by generated_at desc limit 5;` |
| `supabase` | Check the private `chowkidar-reports` bucket in Supabase Storage |

Downloads go through the API. A `409` means the row exists but the bytes are
missing; regenerate the report or restore the backend.

If Supabase Storage fails, the API falls back to Postgres and records
`storage_warning` in the report summary. Investigate the service-role key,
bucket name, and Supabase status.

---

## 5. Backup and restore

### Supabase database

- Use the Supabase dashboard's scheduled backups (plan-dependent) or `pg_dump`
  from a trusted machine.
- For a manual logical backup:

```bash
pg_dump "$DATABASE_URL" --format=custom --file=chowkidar-$(date +%F).dump
```

- Restore into a non-production database first:

```bash
pg_restore --clean --if-exists --no-owner --dbname="$TARGET_DATABASE_URL" chowkidar-YYYY-MM-DD.dump
```

- The audit table is append-only by convention; restoring an old dump rewinds
  the chain. Record any restore in the incident log.

### Reports

- `STORAGE_BACKEND=database` is backed up with Postgres.
- Supabase Storage buckets need their own backup/export policy.
- Local `/tmp` reports are not backed up and are lost on restart.

---

## 6. Key rotation

### Supabase service-role key

1. Create a new service-role key in Supabase.
2. Update Render’s `SUPABASE_SERVICE_ROLE_KEY` and redeploy.
3. Verify a report upload/download and the provisioning script (if needed).
4. Revoke the old key in Supabase.
5. Never commit either key.

### Supabase database password

1. Reset the password in Supabase.
2. URL-encode it if it contains special characters.
3. Update Render’s `DATABASE_URL` and redeploy.
4. Run `/healthz`; confirm `database: ok`.
5. Revoke old sessions/credentials as appropriate.

### `DEV_JWT_SECRET`

Only used in demo mode. Rotate it by setting a new random value on Render; all
demo sessions become invalid and users must log in again.

### Provider keys

Rotate Gemini/Groq keys in their consoles, update Render, redeploy, and verify
`/healthz` and one pipeline run. If the live path is unreliable, set
`LLM_MODE=mock` and disclose that state; the deterministic demo remains
functional.

---

## 7. Reset the demo

Local only:

```bash
make reset
```

Hosted synthetic pilot (only if you intend to replace the current pilot data):

```bash
cd apps/api
DATABASE_URL='postgresql+psycopg://...' uv run python -m app.db.seed
```

The seed truncates and replaces demo data. Never run it against a database with
real tenant data.

---

## 8. Incident playbooks

### API 502/503 or cold start

- Render Free sleeps after inactivity; wait 30–60 seconds and retry.
- Check Render logs for a failed migration, missing env var, or database
  connection error.
- If the database is paused (Supabase Free), restore it in the dashboard.

### Login fails in production

- `/api/v1/auth/config` should show `password_auth: true` and `demo_mode: false`.
- Check `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and the project's Email provider.
- A `401` is invalid credentials; a `403` is an authenticated but unprovisioned
  user; a `503` is an upstream Supabase/network failure.
- If the browser reports a CORS error, verify the page origin is in Render’s
  `CORS_ORIGINS`. The current allowlist must include both Netlify and Vercel.
- Check the Render logs for `SupabaseAuthError` messages. Never log passwords or
  tokens.

### Source sync fails or reports a fallback

- Check the source row's `last_sync_mode` and sanitized `last_error` via
  `GET /api/v1/sources`.
- `fixture_fallback` means the live connector failed and fixture data was used;
  the source should be `degraded`, not `healthy`. Do not present it as live.
- `live_failed` means a hard live run failed; the route returns `502` and the
  failure is persisted for audit.
- For GDELT, a `429`/rate-limit HTML response is expected under aggressive
  polling. Wait at least five seconds, or let the scheduler run.
- If the scheduler is enabled but not running, check the Render logs for an
  APScheduler startup error and confirm `scheduler_enabled`/`scheduler_running`
  in `/healthz`.
- If `scheduler_running=true` but `scheduler_next_run_at=null`, the job is
  paused. This was the behavior when `next_run_time=None` was passed with
  `SCHEDULER_RUN_ON_START=false`; deploy the arming fix and re-check.
- If the job is armed but `last_synced_at` never advances, inspect the Render
  logs for connector errors and remember that GDELT is publicly rate-limited.

### Report generation fails

- Check the API logs for `StorageError` or database errors.
- `STORAGE_BACKEND=database` requires the `82eceac00bcf` migration.
- `STORAGE_BACKEND=supabase` requires the service-role key and bucket access; a
  failed upload should fall back to Postgres.
- Verify the report row and checksum in the database.

### Audit verification fails

- `GET /api/v1/audit/verify` returns `valid: false` and the first broken event.
- Treat this as a security incident: preserve the database, do not mutate the
  audit table, and investigate application/database access.
- The current chain only covers application-path writes; external anchoring is a
  backlog item.

### Netlify URL unreachable

- Netlify is the primary origin. Check the Netlify deploy status and DNS.
- If the site is down, switch to the Vercel fallback and confirm its origin is
  still in Render’s `CORS_ORIGINS`.
- Do not change `WEB_URL`; it remains the canonical Netlify origin.

### Vercel URL unreachable

- Vercel is the secondary fallback; Netlify remains primary.
- Check DNS resolution and the Vercel deployment status.
- If the resolver returns unreachable Vercel edge IPs, try Google DNS or a
  mobile hotspot. See [`CLOUD_DEPLOYMENT_STATUS.md`](CLOUD_DEPLOYMENT_STATUS.md).
- A custom domain pointed at `cname.vercel-dns.com` is the judge-proof option.

### Rate limiting is too aggressive

- Check the `429` response's `Retry-After`.
- Limits are per client IP and process-local: `AUTH_RATE_LIMIT_PER_MINUTE` (10)
  and `MUTATION_RATE_LIMIT_PER_MINUTE` (30).
- Raise them only after confirming the traffic is legitimate. Do not disable
  limits on a public production deployment.

---

## 9. Security checklist

- [x] `AUTH_MODE=supabase`, `DEMO_MODE=false` on any deployment with real data.
- [x] Service-role key exists only in the API environment.
- [x] `CORS_ORIGINS` is an exact origin list, not `*`; it must include both
      `https://ch0wkidar.netlify.app` and
      `https://chowkidar-wheat.vercel.app`.
- [x] Report bytes are in Postgres and downloads go through the API; the
      optional Supabase Storage bucket remains private.
- [x] No secrets in git or public API responses; the deployed browser bundle was
      checked for server-key material.
- [ ] Supabase database password rotated if it was ever shared. **Still pending.**
- [x] Audit chain verified after material changes.
- [ ] Access removed for departed pilot users (`is_active=false` or Supabase
      user deletion). **N/A for the current fixed four-account pilot.**
