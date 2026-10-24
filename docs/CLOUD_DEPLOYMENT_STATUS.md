# Chowkidar — Cloud Deployment Status

- **Updated:** 2026-10-24
- **Scope:** Supabase Free + Render Free API + Vercel Hobby web
- **Status:** API is live and healthy. The Vercel web build is live and a direct browser check passed on 2026-10-24. Vercel’s DNS answers can vary by resolver/edge IP, so the workaround and optional Render web fallback are documented below.

---

## 1. Public URLs

| Surface | URL | Status |
|---|---|---|
| API | <https://chowkidar-api.onrender.com/> | Live |
| API health | <https://chowkidar-api.onrender.com/healthz> | Live: database `ok` |
| API docs | <https://chowkidar-api.onrender.com/docs> | Live |
| Web | <https://chowkidar-wheat.vercel.app/> | Live; direct browser check passed |
| Web fallback | `https://chowkidar-web.onrender.com` | Service created; currently `502` — check Render logs |
| Repository | <https://github.com/A7reus/Chowkidar> | CI green |

The Render API service is on the **free** plan: 512 MB, no persistent disk, and it spins down after about 15 minutes of inactivity. The first request after idle can take 30–60 seconds. The optional Render web fallback has the same free-plan cold-start behavior.

---

## 2. Verified checks

- `GET /healthz` returns `status: ok`, `database: ok`, `auth_mode: dev`, `llm_mode: mock`, `data_mode: fixture`.
- `GET /api/v1/meta` returns the Padma Apparel demo metadata and four streams.
- CORS preflight from `https://chowkidar-wheat.vercel.app` returns `200` with the exact `access-control-allow-origin`.
- `POST /api/v1/auth/demo-login` with role `analyst` returns `200` and an analyst user.
- The production Vercel JavaScript bundle contains `https://chowkidar-api.onrender.com`; `NEXT_PUBLIC_API_URL` was set at build time.
- A headless Chromium run against the Vercel URL (with a host-resolver override to reachable Vercel edge IP `64.29.17.195`) successfully loaded `/login`, signed in as analyst, reached `/dashboard`, and received `200` from the API for meta, dashboard summary, approvals, and pipeline runs.
- After DNS began returning `64.29.17.195` directly, a second headless Chromium run with **no** host override repeated the login and dashboard flow successfully. This confirms the public URL is functional when the resolver returns a reachable edge IP.

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
| `AUTH_MODE` | `dev` |
| `DEMO_MODE` | `true` |
| `LLM_MODE` | `mock` |
| `DATA_MODE` | `fixture` |
| `DEV_JWT_SECRET` | Generated by Render |
| `REPORT_STORAGE_DIR` | `/tmp/reports` |
| `LOCAL_STORAGE_DIR` | `/tmp` |
| `UPLOAD_STORAGE_DIR` | `/tmp/uploads` |
| `NEO4J_*`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `SENTRY_DSN`, `POSTHOG_KEY` | Blank for the demo |

### Local `.env`

Local development keeps `API_URL`, `WEB_URL`, `NEXT_PUBLIC_API_URL`, and `CORS_ORIGINS` on `localhost`. Public cloud values are recorded as comments in `.env.example`; secret values must never be added there.

`.env` is gitignored. `.env.example` is tracked and must contain only placeholders, never the Supabase password/URI, JWTs, or provider keys.

---

## 5. Free-tier limitations

- Render free services sleep after inactivity; judges may see a cold start.
- Render free storage is ephemeral. Reports generated in `/tmp` are lost on restart or spin-down; download them in the same session.
- Supabase Free projects may pause after a period of inactivity; restore the project before a demo/judging session.
- Vercel Hobby has no custom-domain cost, but a custom domain itself may cost money.
- No live source connectors, hosted Supabase Auth, Supabase Storage, Neo4j, n8n, or live LLM calls are part of this demo.

---

## 6. Next actions

1. Direct Vercel URL currently works. Recheck it before recording; if DNS returns the unreachable `.3` addresses again, use Google DNS or a reachable Vercel edge IP.
2. Vercel direct URL works; no fallback is required. If a judge-proof custom domain is desired, add one; if the Render fallback is needed, inspect its `502` build logs first.
3. Update Render `CORS_ORIGINS`/`WEB_URL` if the final web origin changes.
4. Record the 2–3 minute demo video using the working URL.
5. Rotate the Supabase database password if the old URI was shared, then update Render’s `DATABASE_URL`.
