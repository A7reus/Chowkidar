# Chowkidar — Cloud Deployment Status

- **Updated:** 2026-10-24
- **Scope:** Supabase Free + Render Free API + Vercel Hobby web
- **Status:** API and web are live and healthy in **demo auth mode** (`AUTH_MODE=dev`, `DEMO_MODE=true`). The durable-report and rate-limit paths are now active on the hosted API. Supabase production auth remains disabled because the project URL/keys and dashboard access are not available here. Do not call the live URL production-ready until the auth cutover in [`PRODUCTION.md`](PRODUCTION.md) is complete. The Vercel DNS workaround and optional Render web fallback are documented below.

---

## 1. Public URLs

| Surface | URL | Status |
|---|---|---|
| API | <https://chowkidar-api.onrender.com/> | Live |
| API health | <https://chowkidar-api.onrender.com/healthz> | Live: database `ok` |
| API docs | <https://chowkidar-api.onrender.com/docs> | Live |
| Web | <https://chowkidar-wheat.vercel.app/> | Live; direct browser check passed |
| Web fallback | `https://chowkidar-web.onrender.com` | Service created; currently `502` — check Render logs |
| Repository | <https://github.com/A7reus/Chowkidar> | CI green through `08d0f3a828aa` |

The Render API service is on the **free** plan: 512 MB, no persistent disk, and it spins down after about 15 minutes of inactivity. The first request after idle can take 30–60 seconds. The optional Render web fallback has the same free-plan cold-start behavior.

---

## 2. Verified checks

- `GET /healthz` returns `status: ok`, `database: ok`, `auth_mode: dev`, `demo_mode: true`, `llm_mode: mock`, `data_mode: fixture`, `revision: 08d0f3a828aa`.
- Local verification (not hosted): production auth with a mock Supabase Auth/JWKS server, database-backed report storage with checksum-matched download, demo lockout (`403`), frontend email/password login, pilot badge, and `/settings`.
- Hosted durable storage: `/api/v1/meta` reports `storage_backend: database`. A 4-page PDF report (`d5124371-2be2-410f-a4a5-0a2edf260abe`) was generated before the `08d0f3a828aa` redeploy and downloaded again after that deploy with the same SHA-256 `df9a8af9ed3011a742e5fda8d386d438ce27687d3a93cd3c161347b0e7dbaad3` (13,731 bytes), proving persistence across a restart. The download returned `Cache-Control: private, no-store`, a matching ETag, and `X-Content-Type-Options: nosniff`.
- `GET /api/v1/meta` returns the Padma Apparel demo metadata and four streams.
- CORS preflight from `https://chowkidar-wheat.vercel.app` returns `200` with the exact `access-control-allow-origin`.
- `POST /api/v1/auth/demo-login` with role `analyst` returns `200` and an analyst user. The hosted auth limiter returns `429` with `Retry-After` after 10 requests in a minute.
- The production Vercel JavaScript bundle contains `https://chowkidar-api.onrender.com`; `NEXT_PUBLIC_API_URL` was set at build time.
- A headless Chromium run against the Vercel URL (with a host-resolver override to reachable Vercel edge IP `64.29.17.195`) successfully loaded `/login`, signed in as analyst, reached `/dashboard`, and received `200` from the API for meta, dashboard summary, approvals, and pipeline runs.
- After DNS began returning `64.29.17.195` directly, a second headless Chromium run with **no** host override repeated the login and dashboard flow successfully. This confirms the public URL is functional when the resolver returns a reachable edge IP.
- Latest Vercel browser check (2026-10-24, no host override): demo login as analyst, dashboard, `/settings`, and `/reports` loaded without console errors. The Reports UI generated Markdown report `d3c0d1f9-88b7-48b1-ae43-9b87e100e12b` (`storage_backend: database`) and downloaded it as `chowkidar-audit-d3c0d1f9-88b7-48b1-ae43-9b87e100e12b.md`.

Baseline confirmed on the hosted API: 8 risks, 3 critical, 4 pending approvals.

---

## 3. Vercel “won’t load” issue

This is **not** a failed build and not a CORS/API problem.

On 2026-10-24, `chowkidar-wheat.vercel.app` initially resolved to:

```text
216.198.79.3
64.29.17.3
```

TCP connections to those addresses timed out from some networks. The same deployment is reachable through older Vercel edge IPs:

```text
76.76.21.21
76.76.21.98
76.76.21.123
76.76.21.164
```

For example, this returned `200` and the correct page:

```bash
curl -sS -I \
  --resolve chowkidar-wheat.vercel.app:443:76.76.21.21 \
  https://chowkidar-wheat.vercel.app/
```

Google Public DNS returned `64.29.17.195`, which also worked. Later on 2026-10-24 the local resolver returned `.195` too, and the direct URL loaded and passed the browser login/dashboard check. Cloudflare DNS had returned the unreachable `.3` addresses earlier.

### Workarounds

1. **Quick local check:** switch DNS to Google `8.8.8.8` / `8.8.4.4`, flush the DNS cache, or use a mobile hotspot/VPN.
2. **Judge-proof option:** add a custom domain to the Vercel project and point its CNAME at `cname.vercel-dns.com`. `cname.vercel-dns.com` currently resolves to `76.76.21.142`, which is reachable. After adding the domain, update Render’s `CORS_ORIGINS` and `WEB_URL` to the new origin and redeploy.
3. **Free fallback (optional):** the Render blueprint includes `chowkidar-web`, a Node service that runs the Next.js standalone build. The service was created, but on 2026-10-24 at 05:05 UTC its root returned `502`; check its Render build logs before relying on it. The build and standalone start command were verified locally. If it becomes healthy, add its URL to the API’s `CORS_ORIGINS` and test `/login`. Free services sleep after inactivity, so this fallback is slower than Vercel on a cold start. The Vercel URL is currently working, so this is not required for the demo.

Do not change the API URL or CORS while testing the DNS workaround; they are already correct.

---

## 4. Environment variables

### Vercel — Production

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://chowkidar-api.onrender.com` |

No Supabase keys, database secrets, or Groq/Gemini keys are needed by the Vercel frontend. `NEXT_PUBLIC_*` values are public and are inlined at build time; changing one requires a redeploy.

### Render — optional web fallback (currently 502)

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://chowkidar-api.onrender.com` |
| `NODE_VERSION` | `22` |

The fallback build and standalone start path were verified locally; the first Render deployment is currently returning `502`. It uses no database credentials.

### Render — API

| Variable | Value |
|---|---|
| `DATABASE_URL` | Supabase **Session pooler** URI; secret, dashboard only |
| `CORS_ORIGINS` | `https://chowkidar-wheat.vercel.app` (add any custom domain or fallback origin, comma-separated) |
| `WEB_URL` | Primary web origin, e.g. `https://chowkidar-wheat.vercel.app` |
| `APP_ENV` | `production` |
| `AUTH_MODE` | `dev` (demo); switch to `supabase` after the cutover |
| `DEMO_MODE` | `true` (demo); set `false` for production |
| `LLM_MODE` | `mock` |
| `DATA_MODE` | `fixture` |
| `DEV_JWT_SECRET` | Generated by Render |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Blank in demo; required for production auth/Storage |
| `STORAGE_BACKEND` | `database` (effective default because `APP_ENV=production`) |
| `REPORT_STORAGE_DIR` | `/tmp/reports` (only used if `STORAGE_BACKEND=local`) |
| `RATE_LIMIT_ENABLED` | `true` (code default) |
| `LOCAL_STORAGE_DIR` | `/tmp` |
| `UPLOAD_STORAGE_DIR` | `/tmp/uploads` |
| `NEO4J_*`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `SENTRY_DSN`, `POSTHOG_KEY` | Blank for the demo |

### Local `.env`

Local development keeps `API_URL`, `WEB_URL`, `NEXT_PUBLIC_API_URL`, and `CORS_ORIGINS` on `localhost`. Public cloud values are recorded as comments in `.env.example`; secret values must never be added there.

`.env` is gitignored. `.env.example` is tracked and must contain only placeholders, never the Supabase password/URI, JWTs, or provider keys.

---

## 5. Free-tier limitations

- Render free services sleep after inactivity; judges may see a cold start.
- Render free storage is ephemeral, but the hosted API now stores report bytes in Postgres. Local `/tmp` reports are not durable.
- Supabase Free projects may pause after a period of inactivity; restore the project before a demo/judging session.
- Vercel Hobby has no custom-domain cost, but a custom domain itself may cost money.
- No live source connectors, enabled hosted Supabase Auth, Supabase Storage, Neo4j, n8n, or live LLM calls are part of the current demo. The code paths for Supabase Auth and Supabase Storage exist; database report storage is enabled, Supabase Auth is not.

---

## 6. Next actions

1. Provide the Supabase project URL, anon key, and service-role key, then run `scripts/provision_supabase_users.py` and apply the Render environment from [`PRODUCTION.md`](PRODUCTION.md).
2. Switch `AUTH_MODE=supabase` and `DEMO_MODE=false`; redeploy and run the full hosted QA matrix in incognito.
3. Recheck the Vercel URL before recording; if DNS returns the unreachable `.3` addresses, use Google DNS or a reachable Vercel edge IP.
4. Update Render `CORS_ORIGINS`/`WEB_URL` if the final web origin changes.
5. Record the 2–3 minute demo video using the working URL.
6. Rotate the Supabase database password if the old URI was shared, then update Render’s `DATABASE_URL`.
